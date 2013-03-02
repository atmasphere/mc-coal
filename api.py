from functools import wraps
import logging

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
        self.json_response(response, status_code=201)

application = webapp2.WSGIApplication(
    [
        ('/api/ping', PingHandler),
    ],
    debug=not on_production_server
)
