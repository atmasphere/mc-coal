import datetime
from functools import wraps
import logging
import re

import webapp2

from wtforms import form, fields, validators

from agar.auth import authentication_required
from agar.env import on_production_server

from restler.serializers import json_response as restler_json_response

from main import COALConfig

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
        response = {'server_name': self.request.form.server_name.data}
        self.json_response(response, status_code=200)


def handle_logged_in(line):
    if 'logged in' in line:
        match = re.search(r"([\w-]+) ([\w:]+) \[(\w+)\] (\w+)\[/([\w.]+):(\w+)\].+\((\w.+), (\w.+), (\w.+)\)", line)
        dts = "{0} {1}".format(match.group(1), match.group(2))
        dt = datetime.datetime.strptime(dts, "%Y-%m-%d %H:%M:%S")
        log_level = match.group(3)
        user = match.group(4)
        ip = match.group(5)
        port = match.group(6)
        location = (match.group(7), match.group(8), match.group(9))
        print
        print "LOG IN EVENT"
        print "DATE: {0}".format(dt)
        print "LOG LEVEL: {0}".format(log_level)
        print "USER: {0}".format(user)
        print "IP: {0}".format(ip)
        print "PORT: {0}".format(port)
        print "LOCATION: {0}".format(location)


def handle_lost_connection(line):
    if 'lost connection' in line:
        match = re.search(r"([\w-]+) ([\w:]+) \[(\w+)\] (\w+)", line)
        dts = "{0} {1}".format(match.group(1), match.group(2))
        dt = datetime.datetime.strptime(dts, "%Y-%m-%d %H:%M:%S")
        log_level = match.group(3)
        user = match.group(4)
        print
        print "LOG OUT EVENT"
        print "DATE: {0}".format(dt)
        print "LOG LEVEL: {0}".format(log_level)
        print "USER: {0}".format(user)


def handle_public_chat(line):
    match = re.search(r"([\w-]+) ([\w:]+) \[(\w+)\] \<(\w+)\> (.+)", line)
    if match:
        dts = "{0} {1}".format(match.group(1), match.group(2))
        dt = datetime.datetime.strptime(dts, "%Y-%m-%d %H:%M:%S")
        log_level = match.group(3)
        user = match.group(4)
        chat = match.group(5)
        print
        print "CHAT EVENT"
        print "DATE: {0}".format(dt)
        print "LOG LEVEL: {0}".format(log_level)
        print "USER: {0}".format(user)
        print "CHAT: {0}".format(chat)


application = webapp2.WSGIApplication(
    [
        ('/api/ping', PingHandler),
    ],
    debug=not on_production_server
)
