import datetime
from functools import wraps
import logging
import re

import webapp2

from pytz.gae import pytz

from wtforms import form, fields, validators

from agar.auth import authentication_required
from agar.env import on_production_server

from restler.serializers import json_response as restler_json_response

from main import COALConfig

from models import LogLine, ConnectLine, DisconnectLine, ChatLine, TimeStampLogLine

config = COALConfig.get_config()


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
    if handler.request.get('p', None) != config.API_PASSWORD:
        handler.abort(403)
    return None


class PingForm(form.Form):
    server_name = fields.StringField(validators=[validators.InputRequired(), validators.Length(max=500)])


class PingHandler(JsonRequestHandler):
    @authentication_required(authenticate=authenticate)
    @validate_params(form_class=PingForm)
    def post(self):
        last_log_line = TimeStampLogLine.get_last_line()
        response = {'last_line': last_log_line.line if last_log_line is not None else None}
        self.json_response(response, status_code=200)


class LogLineForm(form.Form):
    line = fields.StringField(validators=[validators.InputRequired()])
    zone = fields.StringField(validators=[validators.InputRequired()])


class LogLineHandler(JsonRequestHandler):
    @authentication_required(authenticate=authenticate)
    @validate_params(form_class=LogLineForm)
    def post(self):
        line = self.request.form.line.data
        zone = self.request.form.zone.data
        try:
            tz = pytz.timezone(zone)
        except:
            tz = pytz.utc
        try:
            log_line, created = handle_logged_in(line, tz)
            if not log_line:
                log_line, created = handle_lost_connection(line, tz)
            if not log_line:
                log_line, created = handle_chat(line, tz)
            if not log_line:
                log_line, created = handle_timestamp_log(line, tz)
            if not log_line:
                log_line, created = handle_unknown_log(line, tz)
        except Exception, e:
            logging.error(e)
        self.json_response({}, status_code=201 if log_line and created else 200)


def dts_to_naive_utc(dts, tz):
    dt = datetime.datetime.strptime(dts, "%Y-%m-%d %H:%M:%S")
    dt = tz.localize(dt)
    return dt.astimezone(pytz.utc).replace(tzinfo=None)


def safe_float_from_string(float_string):
    try:
        return float(float_string)
    except:
        return None


def handle_logged_in(line, tz):
    if 'logged in' in line:
        existing_connect_line = ConnectLine.get_line(line)
        if existing_connect_line is not None:
            return existing_connect_line, False
        match = re.search(r"([\w-]+) ([\w:]+) \[(\w+)\] (\w+)\[/([\w.]+):(\w+)\].+\((\w.+), (\w.+), (\w.+)\)", line)
        if match:
            dts = "{0} {1}".format(match.group(1), match.group(2))
            naive_utc_dt = dts_to_naive_utc(dts, tz)
            log_level = match.group(3)
            user = match.group(4)
            ip = match.group(5)
            port = match.group(6)
            location_x = safe_float_from_string(match.group(7))
            location_y = safe_float_from_string(match.group(8))
            location_z = safe_float_from_string(match.group(9))
            connect_line = ConnectLine(
                line=line,
                zone=tz.zone,
                timestamp=naive_utc_dt,
                log_level=log_level,
                username=user,
                ip=ip,
                port=port,
                location_x=location_x,
                location_y=location_y,
                location_z=location_z
            )
            connect_line.put()
            return connect_line, True
    return None, False


def handle_lost_connection(line, tz):
    if 'lost connection' in line:
        existing_disconnect_line = DisconnectLine.get_line(line)
        if existing_disconnect_line is not None:
            return existing_disconnect_line, False
        match = re.search(r"([\w-]+) ([\w:]+) \[(\w+)\] (\w+)", line)
        if match:
            dts = "{0} {1}".format(match.group(1), match.group(2))
            naive_utc_dt = dts_to_naive_utc(dts, tz)
            log_level = match.group(3)
            user = match.group(4)
            disconnect_line = DisconnectLine(
                line=line,
                zone=tz.zone,
                timestamp=naive_utc_dt,
                log_level=log_level,
                username=user
            )
            disconnect_line.put()
            return disconnect_line, True
    return None, False


def handle_chat(line, tz):
    match = re.search(r"([\w-]+) ([\w:]+) \[(\w+)\] \<(\w+)\> (.+)", line)
    if match:
        existing_disconnect_line = ChatLine.get_line(line)
        if existing_disconnect_line is not None:
            return existing_disconnect_line, False
        dts = "{0} {1}".format(match.group(1), match.group(2))
        naive_utc_dt = dts_to_naive_utc(dts, tz)
        log_level = match.group(3)
        user = match.group(4)
        chat = match.group(5)
        chat_line = ChatLine(
            line=line,
            zone=tz.zone,
            timestamp=naive_utc_dt,
            log_level=log_level,
            username=user,
            chat=chat
        )
        chat_line.put()
        return chat_line, True
    return None, False


def handle_timestamp_log(line, tz):
    match = re.search(r"([\w-]+) ([\w:]+) \[(\w+)\] (.+)", line)
    if match:
        existing_disconnect_line = TimeStampLogLine.get_line(line)
        if existing_disconnect_line is not None:
            return existing_disconnect_line, False
        dts = "{0} {1}".format(match.group(1), match.group(2))
        naive_utc_dt = dts_to_naive_utc(dts, tz)
        log_level = match.group(3)
        timestamp_line = TimeStampLogLine(
            line=line,
            zone=tz.zone,
            timestamp=naive_utc_dt,
            log_level=log_level,
        )
        timestamp_line.put()
        return timestamp_line, True
    return None, False


def handle_unknown_log(line, tz):
    existing_log_line = LogLine.get_line(line)
    if existing_log_line is not None:
        return existing_log_line, False
    log_line = LogLine(
        line=line,
        zone=tz.zone
    )
    log_line.put()
    return log_line, True


application = webapp2.WSGIApplication(
    [
        webapp2.Route('/api/ping', PingHandler, name='api_ping'),
        webapp2.Route('/api/log_line', LogLineHandler, name='api_log_line'),
    ],
    debug=not on_production_server
)
