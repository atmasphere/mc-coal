import datetime
from functools import wraps
import logging

from google.appengine.ext import ndb

import webapp2

from wtforms import form, fields, validators

from agar.auth import authentication_required
from agar.env import on_production_server

from restler.serializers import json_response as restler_json_response
from restler.serializers import ModelStrategy

from config import coal_config
from models import Server, LogLine, Player


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
                    errors = u"Unhandled form parsing exception: {0}".format(e)
                    handler.json_response({}, status_code=400, errors=errors)
                    logging.error(errors)
                    try:
                        logging.error(handler.request)
                    except Exception, e:
                        logging.error(u"Can't log the request: {0}".format(e))
                if valid:
                    handler.request.form = form
                    request_method(handler, *args, **kwargs)
                    return
                else:
                    try:
                        message = form.errors
                    except:
                        message = u"Exception creating Form"
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
        existing_line = LogLine.lookup_line(line)
        if existing_line is None:
            log_line = LogLine.create(line, zone)
            if log_line is not None:
                status_code = 201
        self.json_response({}, status_code=status_code)


class MultiPageForm(form.Form):
    size = fields.IntegerField(default=10, validators=[validators.NumberRange(min=1, max=50)])
    cursor = fields.StringField(validators=[validators.Optional()])


class MultiPage():
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


class MultiPageJsonHandler(JsonRequestHandler, MultiPage):
    pass


# PLAYER_FIELDS = ['username', 'last_login_timestamp', 'last_session_duration', 'is_playing']
# PLAYER_FIELD_FUNCTIONS = [
#     {'key': lambda o: o.key.urlsafe()},
#     {'user_key': lambda o: o.user.key.urlsafe() if o.user is not None else None}
# ]
# PLAYER_STRATEGY = ModelStrategy(Player) + PLAYER_FIELDS
# PLAYER_STRATEGY += PLAYER_FIELD_FUNCTIONS


# class PlayerHandler(MultiPageJsonHandler):
#     @authentication_required(authenticate=authenticate)
#     @validate_params(form_class=MultiPageForm)
#     def get(self):
#         self.json_response(self.fetch_page(Player.query_by_username(), results_name='players'), PLAYER_STRATEGY)


application = webapp2.WSGIApplication(
    [
        webapp2.Route('/api/agent/ping', PingHandler, name='api_agent_ping'),
        webapp2.Route('/api/agent/log_line', LogLineHandler, name='api_agent_log_line'),

        # webapp2.Route('/api/user/players', PlayerHandler, name='api_user_players')
    ],
    debug=not on_production_server
)
