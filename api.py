import datetime
from functools import wraps
import logging
import re

from google.appengine.ext import ndb

import webapp2

from pytz.gae import pytz

from wtforms import form, fields, validators

from agar.auth import authentication_required
from agar.env import on_production_server

from restler.serializers import json_response as restler_json_response

from config import coal_config
from models import Server, LogLine, Location, PlaySession
from models import CONNECTION_TAG, LOGIN_TAG, LOGOUT_TAG
from models import CHAT_TAG
from models import SERVER_TAG, PERFORMANCE_TAG, OVERLOADED_TAG, STOPPING_TAG, STARTING_TAG

LOGIN_TAGS = [CONNECTION_TAG, LOGIN_TAG]
LOGOUT_TAGS = [CONNECTION_TAG, LOGOUT_TAG]
CHAT_TAGS = [CHAT_TAG]
OVERLOADED_TAGS = [SERVER_TAG, PERFORMANCE_TAG, OVERLOADED_TAG]
STOPPING_TAGS = [SERVER_TAG, STOPPING_TAG]
STARTING_TAGS = [SERVER_TAG, STARTING_TAG]


def validate_params(form_class):
    def decorator(request_method):
        @wraps(request_method)
        def wrapped(handler, *args, **kwargs):
            valid = False
            form = None
            request = handler.request
            while True:
                try:
                    form = form_class(request.params)
                    valid = form.validate()
                except Exception, e:
                    errors = "Unhandled form parsing exception: {0}".format(str(e))
                    handler.json_response({}, status_code=400, errors=errors)
                    logging.error(errors)
                    try:
                        logging.error(handler.request)
                    except Exception, e:
                        logging.error("Can't log the request: {0}".format(str(e)))
                if valid:
                    handler.request.form = form
                    request_method(handler, *args, **kwargs)
                    return
                else:
                    try:
                        message = form.errors
                    except:
                        message = "Exception creating Form"
                    handler.json_response({}, status_code=400, errors=message)
                    logging.error(message)
                    return
        return wrapped
    return decorator


class JsonRequestHandler(webapp2.RequestHandler):
    def _setup_context(self, context):
        if not context:
            context = {}
        context['request'] = self.request
        return context

    def _setup_data(self, model_or_query, errors=None):
        data = dict()
        if errors is not None:
            data['errors'] = errors
        else:
            data = model_or_query
        return data

    def json_response(self, model_or_query, strategy=None, status_code=200, errors=None, context=None):
        context = self._setup_context(context)
        data = self._setup_data(model_or_query, errors=errors)
        return restler_json_response(self.response, data, strategy=strategy, status_code=status_code, context=context)

    def handle_exception(self, exception, debug_mode):
        errors = exception.message or str(exception)
        if isinstance(exception, webapp2.HTTPException):
            code = exception.code
            if code == 404:
                super(JsonRequestHandler, self).handle_exception(exception, debug_mode)
        else:
            code = 500
            logging.error(errors)
        self.json_response({}, status_code=code, errors=errors)


def authenticate(handler):
    if handler.request.get('p', None) != coal_config.API_PASSWORD:
        handler.abort(403)
    return None


class OptionalBooleanField(fields.BooleanField):
    def process_data(self, value):
        if value is not None:
            self.data = bool(value)
        else:
            self.data = None

    def process_formdata(self, valuelist):
        if not valuelist:
            self.data = None
        else:
            self.data = valuelist[0] == 'True'


class PingForm(form.Form):
    server_name = fields.StringField(validators=[validators.InputRequired(), validators.Length(max=500)])
    is_server_running = OptionalBooleanField(validators=[validators.Optional()])


class PingHandler(JsonRequestHandler):
    @authentication_required(authenticate=authenticate)
    @validate_params(form_class=PingForm)
    def post(self):
        is_server_running = self.request.form.is_server_running.data
        server = Server.global_key().get()
        server.update_is_running(is_server_running, last_ping=datetime.datetime.now())
        last_log_line = LogLine.get_last_line_with_timestamp()
        response = {'last_line': last_log_line.line if last_log_line is not None else None}
        self.json_response(response, status_code=200)


class LogLineForm(form.Form):
    line = fields.StringField(validators=[validators.InputRequired()])
    zone = fields.StringField(validators=[validators.InputRequired()])


class LogLineHandler(JsonRequestHandler):
    @authentication_required(authenticate=authenticate)
    @validate_params(form_class=LogLineForm)
    def post(self):
        status_code = 200
        line = self.request.form.line.data
        zone = self.request.form.zone.data
        try:
            tz = pytz.timezone(zone)
        except:
            tz = pytz.utc
        existing_line = LogLine.lookup_line(line)
        if existing_line is None:
            log_line = handle_new_line(line, tz)
            if log_line is not None:
                status_code = 201
        self.json_response({}, status_code=status_code)


def dts_to_naive_utc(dts, tz):
    dt = datetime.datetime.strptime(dts, "%Y-%m-%d %H:%M:%S")
    dt = tz.localize(dt)
    return dt.astimezone(pytz.utc).replace(tzinfo=None)


def safe_float_from_string(float_string):
    try:
        return float(float_string)
    except:
        return None


def handle_new_line(line, tz):
    log_line = handle_logged_in(line, tz)
    if log_line is None:
        log_line = handle_lost_connection(line, tz)
    if log_line is None:
        log_line = handle_chat(line, tz)
    if log_line is None:
        log_line = handle_overloaded_log(line, tz)
    if log_line is None:
        log_line = handle_server_stop(line, tz)
    if log_line is None:
        log_line = handle_server_start(line, tz)
    if log_line is None:
        log_line = handle_timestamp_log(line, tz)
    if log_line is None:
        log_line = handle_unknown_log(line, tz)
    return log_line


@ndb.transactional
def handle_logged_in(line, timezone):
    match = re.search(ur"([\w-]+) ([\w:]+) \[(\w+)\] (\w+)\[/([\w.]+):(\w+)\].+\((-?\w.+), (-?\w.+), (-?\w.+)\)", line)
    if match and 'logged in' in line:
        dts = "{0} {1}".format(match.group(1), match.group(2))
        naive_utc_dt = dts_to_naive_utc(dts, timezone)
        log_level = match.group(3)
        username = match.group(4)
        ip = match.group(5)
        port = match.group(6)
        location_x = safe_float_from_string(match.group(7))
        location_y = safe_float_from_string(match.group(8))
        location_z = safe_float_from_string(match.group(9))
        log_line = LogLine.create(
            line, timezone.zone,
            timestamp=naive_utc_dt,
            log_level=log_level,
            username=username,
            ip=ip,
            port=port,
            location=Location(x=location_x, y=location_y, z=location_z),
            tags=LOGIN_TAGS
        )
        PlaySession.create(username, naive_utc_dt, timezone.zone, log_line.key)
        return log_line
    return None


@ndb.transactional
def handle_lost_connection(line, timezone):
    match = re.search(ur"([\w-]+) ([\w:]+) \[(\w+)\] (\w+)", line)
    if match and 'lost connection' in line:
        dts = "{0} {1}".format(match.group(1), match.group(2))
        naive_utc_dt = dts_to_naive_utc(dts, timezone)
        log_level = match.group(3)
        username = match.group(4)
        log_line = LogLine.create(
            line, timezone.zone,
            timestamp=naive_utc_dt,
            log_level=log_level,
            username=username,
            tags=LOGOUT_TAGS
        )
        PlaySession.close_current(username, naive_utc_dt, log_line.key)
        return log_line
    return None


def handle_chat(line, timezone):
    match = re.search(ur"([\w-]+) ([\w:]+) \[(\w+)\] \<(\w+)\> (.+)", line)
    if match:
        dts = "{0} {1}".format(match.group(1), match.group(2))
        naive_utc_dt = dts_to_naive_utc(dts, timezone)
        log_level = match.group(3)
        user = match.group(4)
        chat = match.group(5)
        return LogLine.create(
            line, timezone.zone,
            timestamp=naive_utc_dt,
            log_level=log_level,
            username=user,
            chat=chat,
            tags=CHAT_TAGS
        )
    return None


def handle_overloaded_log(line, timezone):
    match = re.search(ur"([\w-]+) ([\w:]+) \[WARNING\] Can't keep up! Did the system time change, or is the server overloaded\?", line)
    if match:
        dts = "{0} {1}".format(match.group(1), match.group(2))
        naive_utc_dt = dts_to_naive_utc(dts, timezone)
        return LogLine.create(
            line, timezone.zone,
            timestamp=naive_utc_dt,
            log_level='WARNING',
            tags=OVERLOADED_TAGS
        )
    return None


@ndb.transactional
def handle_server_stop(line, timezone):
    match = re.search(ur"([\w-]+) ([\w:]+) \[(\w+)\] Stopping server", line)
    if match:
        dts = "{0} {1}".format(match.group(1), match.group(2))
        naive_utc_dt = dts_to_naive_utc(dts, timezone)
        log_level = match.group(3)
        log_line = LogLine.create(
            line, timezone.zone,
            timestamp=naive_utc_dt,
            log_level=log_level,
            tags=STOPPING_TAGS
        )
        open_sessions_query = PlaySession.query_open()
        for session in open_sessions_query:
            session.close(naive_utc_dt, log_line.key)
        return log_line
    return None


@ndb.transactional
def handle_server_start(line, timezone):
    match = re.search(ur"([\w-]+) ([\w:]+) \[(\w+)\] Starting minecraft server version ([\S:]+)", line)
    if match:
        dts = "{0} {1}".format(match.group(1), match.group(2))
        naive_utc_dt = dts_to_naive_utc(dts, timezone)
        log_level = match.group(3)
        server_version = match.group(4)
        server = Server.global_key().get()
        server.version = server_version
        server.put()
        log_line = LogLine.create(
            line, timezone.zone,
            timestamp=naive_utc_dt,
            log_level=log_level,
            tags=STARTING_TAGS
        )
        open_sessions_query = PlaySession.query_open()
        for session in open_sessions_query:
            session.close(naive_utc_dt, log_line.key)
        return log_line
    return None


def handle_timestamp_log(line, timezone):
    match = re.search(ur"([\w-]+) ([\w:]+) \[(\w+)\] (.+)", line)
    if match:
        dts = "{0} {1}".format(match.group(1), match.group(2))
        naive_utc_dt = dts_to_naive_utc(dts, timezone)
        log_level = match.group(3)
        return LogLine.create(
            line, timezone.zone,
            timestamp=naive_utc_dt,
            log_level=log_level,
            tags=[]
        )
    return None


def handle_unknown_log(line, timezone):
    return LogLine.create(line, timezone.zone, tags=[])


class MultiPageForm(form.Form):
    size = fields.IntegerField(default=10, validators=[validators.NumberRange(min=1, max=50)])
    cursor = fields.StringField(validators=[validators.Optional()])


class MultiPageHandler():
    @property
    def size(self):
        return self.request.form.size.data or self.request.form.size.default

    @property
    def cursor(self):
        cursor = self.request.form.cursor.data
        if cursor:
            try:
                cursor = ndb.Cursor.from_websafe_string(cursor)
            except Exception, e:
                self.abort(400, {'cursor': e.message})
        return cursor or None

    def fetch_page(self, query, results_name='results'):
        results, cursor, more = query.fetch_page(self.size, start_cursor=self.cursor)
        response = {results_name: results}
        if more:
            response['cursor'] = cursor.to_websafe_string()
        return response


application = webapp2.WSGIApplication(
    [
        webapp2.Route('/api/ping', PingHandler, name='api_ping'),
        webapp2.Route('/api/log_line', LogLineHandler, name='api_log_line'),
    ],
    debug=not on_production_server
)
