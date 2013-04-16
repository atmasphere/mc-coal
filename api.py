import datetime
from functools import wraps
import logging

from google.appengine.api import users
from google.appengine.ext import ndb

from pytz.gae import pytz

import webapp2
from webapp2_extras import auth, sessions

from wtforms import form, fields, validators

from agar.auth import authentication_required
from agar.env import on_production_server

from restler.serializers import json_response as restler_json_response
from restler.serializers import ModelStrategy

from config import coal_config
from models import Server, User, Player, PlaySession, LogLine, Command


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
        response = {
            'last_line': last_log_line.line if last_log_line is not None else None,
            'commands': Command.pop_all()
        }
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


class GoogleAppEngineUserAuthHandler(webapp2.RequestHandler):
    @webapp2.cached_property
    def session_store(self):
        return sessions.get_store(request=self.request)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session(backend="datastore")

    @webapp2.cached_property
    def auth(self):
        return auth.get_auth(request=self.request)

    @webapp2.cached_property
    def user_info(self):
        return self.auth.get_user_by_session()

    @webapp2.cached_property
    def user(self):
        user_info = self.user_info
        user = self.auth.store.user_model.get_by_id(user_info['user_id']) if user_info else None
        return user

    def logged_in(self):
        return self.user is not None

    def logout(self, redirect_url=None):
        redirect_url = redirect_url or '/'
        self.auth.unset_session()
        logout_url = users.create_logout_url(redirect_url)
        self.redirect(logout_url)

    def dispatch(self):
        try:
            super(GoogleAppEngineUserAuthHandler, self).dispatch()
        finally:
            self.session_store.save_sessions(self.response)

    def login_callback(self):
        user = None
        gae_user = users.get_current_user()
        if gae_user:
            auth_id = User.get_gae_user_auth_id(gae_user=gae_user)
            user = self.auth.store.user_model.get_by_auth_id(auth_id)
            if user:
                # existing user. just log them in.
                self.auth.set_session(self.auth.store.user_to_dict(user))
                # update access for gae admins
                if users.is_current_user_admin():
                    if not (user.active and user.admin):
                        user.active = True
                        user.admin = True
                user.last_login = datetime.datetime.now()
                user.put()
            else:
                # check whether there's a user currently logged in
                # then, create a new user if no one is signed in,
                # otherwise add this auth_id to currently logged in user.
                if self.logged_in and self.user:
                    u = self.user
                    if auth_id not in u.auth_ids:
                        u.auth_ids.append(auth_id)
                    u.populate(
                        email=gae_user.email(),
                        nickname=gae_user.nickname(),
                        last_login=datetime.datetime.now()
                    )
                    if users.is_current_user_admin():
                        u.admin = True
                    u.put()
                else:
                    ok, user = self.auth.store.user_model.create_user(
                        auth_id,
                        email=gae_user.email(),
                        nickname=gae_user.nickname(),
                        active=users.is_current_user_admin(),
                        admin=users.is_current_user_admin(),
                        last_login=datetime.datetime.now()
                    )
                    if ok:
                        self.auth.set_session(self.auth.store.user_to_dict(user))
                    else:
                        logging.error('create_user() returned False with strings: %s' % user)
                        user = None
                        self.auth.unset_session()
        self.redirect('/')


def api_datetime(dt, zone=None, dt_format=u"%Y-%m-%d %H:%M:%S", tz_format=u"%Z%z"):
    if dt:
        utc_dt = pytz.UTC.localize(dt)
        try:
            tz = pytz.timezone(zone or coal_config.TIMEZONE)
        except:
            tz = pytz.utc
        tz_dt = utc_dt.astimezone(tz) if utc_dt else None
        dt_tz_format = "{0} {1}".format(dt_format, tz_format) if tz_format else dt_format
        return tz_dt.strftime(dt_tz_format) if tz_dt else utc_dt.strftime(dt_format)
    return None


def authenticate_user_or_password(handler):
    user = handler.user
    if not (user and user.active):
        return authenticate(handler)
    return None


class UserAwareHandler(JsonRequestHandler):
    @webapp2.cached_property
    def auth(self):
        return auth.get_auth(request=self.request)

    @webapp2.cached_property
    def user_info(self):
        return self.auth.get_user_by_session()

    @webapp2.cached_property
    def user(self):
        user_info = self.user_info
        user = self.auth.store.user_model.get_by_id(user_info['user_id']) if user_info else None
        return user


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


class MultiPageUserAwareHandler(UserAwareHandler, MultiPage):
    pass


SERVER_FIELDS = ['version', 'is_running']
SERVER_FIELD_FUNCTIONS = {
    'last_ping': lambda o: api_datetime(o.last_ping),
    'created': lambda o: api_datetime(o.created),
    'updated': lambda o: api_datetime(o.updated)
}
SERVER_STRATEGY = ModelStrategy(Server).include(*SERVER_FIELDS).include(**SERVER_FIELD_FUNCTIONS)


class ServerHandler(UserAwareHandler):
    @authentication_required(authenticate=authenticate_user_or_password)
    def get(self):
        server = Server.global_key().get()
        self.json_response(server, SERVER_STRATEGY)


USER_FIELDS = ['active', 'admin', 'email', 'nickname', 'username']
USER_FIELD_FUNCTIONS = {
    'key': lambda o: o.key.urlsafe(),
    'player_key': lambda o: o.player.key.urlsafe() if o.player is not None else None,
    'last_coal_login': lambda o: api_datetime(o.last_login),
    'last_chat_view': lambda o: api_datetime(o.last_chat_view),
    'created': lambda o: api_datetime(o.created),
    'updated': lambda o: api_datetime(o.updated)
}
USER_STRATEGY = ModelStrategy(User).include(*USER_FIELDS).include(**USER_FIELD_FUNCTIONS)


class UsersHandler(MultiPageUserAwareHandler):
    @authentication_required(authenticate=authenticate_user_or_password)
    @validate_params(form_class=MultiPageForm)
    def get(self):
        self.json_response(self.fetch_page(User.query_by_email(), results_name='users'), USER_STRATEGY)


class UserKeyHandler(UserAwareHandler):
    def get_user_by_key(self, key, abort_404=True):
        try:
            user_key = ndb.Key(urlsafe=key)
            user = user_key.get()
        except Exception:
            user = None
        if abort_404 and not user:
            self.abort(404)
        return user

    @authentication_required(authenticate=authenticate_user_or_password)
    def get(self, key):
        user = self.get_user_by_key(key)
        self.json_response(user, USER_STRATEGY)


PLAYER_FIELDS = ['username', 'is_playing']
PLAYER_FIELD_FUNCTIONS = {
    'key': lambda o: o.key.urlsafe(),
    'user_key': lambda o: o.user.key.urlsafe() if o.user is not None else None,
    'last_login': lambda o: api_datetime(o.last_login_timestamp),
    'last_session_duration': lambda o: o.last_session_duration.total_seconds() if o.last_session_duration is not None else None
}
PLAYER_STRATEGY = ModelStrategy(Player).include(*PLAYER_FIELDS).include(**PLAYER_FIELD_FUNCTIONS)


class PlayersHandler(MultiPageUserAwareHandler):
    @authentication_required(authenticate=authenticate_user_or_password)
    @validate_params(form_class=MultiPageForm)
    def get(self):
        self.json_response(self.fetch_page(Player.query_by_username(), results_name='players'), PLAYER_STRATEGY)


class PlayerKeyUsernameHandler(UserAwareHandler):
    def get_player_by_key_or_username(self, key_username, abort_404=True):
        try:
            player_key = ndb.Key(urlsafe=key_username)
            player = player_key.get()
        except Exception:
            player = Player.lookup(key_username)
        if abort_404 and not player:
            self.abort(404)
        return player

    @authentication_required(authenticate=authenticate_user_or_password)
    def get(self, key_username):
        player = self.get_player_by_key_or_username(key_username)
        self.json_response(player, PLAYER_STRATEGY)


PLAY_SESSION_FIELDS = ['username']
PLAY_SESSION_FIELD_FUNCTIONS = {
    'key': lambda o: o.key.urlsafe(),
    'player_key': lambda o: o.player.key.urlsafe() if o.user is not None else None,
    'user_key': lambda o: o.user.key.urlsafe() if o.user is not None else None,
    'login_timestamp': lambda o: api_datetime(o.login_timestamp, zone=o.zone),
    'logout_timestamp': lambda o: api_datetime(o.logout_timestamp, zone=o.zone),
    'duration': lambda o: o.duration.total_seconds(),
    'login_log_line_key': lambda o: o.login_log_line_key.urlsafe() if o.login_log_line_key is not None else None,
    'logout_log_line_key': lambda o: o.logout_log_line_key.urlsafe() if o.logout_log_line_key is not None else None,
    'created': lambda o: api_datetime(o.created),
    'updated': lambda o: api_datetime(o.updated)
}
PLAY_SESSION_STRATEGY = ModelStrategy(PlaySession).include(*PLAY_SESSION_FIELDS).include(**PLAY_SESSION_FIELD_FUNCTIONS)


class PlaySessionsForm(MultiPageForm):
    username = fields.StringField(validators=[validators.Optional()])


class PlaySessionsHandler(MultiPageUserAwareHandler):
    @authentication_required(authenticate=authenticate_user_or_password)
    @validate_params(form_class=PlaySessionsForm)
    def get(self):
        query = PlaySession.query_latest(username=self.request.form.username.data)
        self.json_response(self.fetch_page(query, results_name='play_sessions'), PLAY_SESSION_STRATEGY)


class PlaySessionKeyHandler(UserAwareHandler):
    def get_play_session_by_key(self, key, abort_404=True):
        try:
            play_session_key = ndb.Key(urlsafe=key)
            play_session = play_session_key.get()
        except Exception:
            play_session = None
        if abort_404 and not play_session:
            self.abort(404)
        return play_session

    @authentication_required(authenticate=authenticate_user_or_password)
    def get(self, key):
        play_session = self.get_play_session_by_key(key)
        self.json_response(play_session, PLAY_SESSION_STRATEGY)


application = webapp2.WSGIApplication(
    [
        webapp2.Route('/api/agent/ping', PingHandler, name='api_agent_ping'),
        webapp2.Route('/api/agent/log_line', LogLineHandler, name='api_agent_log_line'),

        webapp2.Route('/login_callback', handler='api.GoogleAppEngineUserAuthHandler:login_callback', name='login_callback'),
        webapp2.Route('/logout', handler='api.GoogleAppEngineUserAuthHandler:logout', name='logout'),

        webapp2.Route('/api/data/server', ServerHandler, name='api_data_server'),
        webapp2.Route('/api/data/user/<key>', UserKeyHandler, name='api_data_user_key'),
        webapp2.Route('/api/data/user', UsersHandler, name='api_data_user'),
        webapp2.Route('/api/data/player/<key_username>', PlayerKeyUsernameHandler, name='api_data_player_key_username'),
        webapp2.Route('/api/data/player', PlayersHandler, name='api_data_player'),
        webapp2.Route('/api/data/play_session/<key>', PlaySessionKeyHandler, name='api_data_play_session_key'),
        webapp2.Route('/api/data/play_session', PlaySessionsHandler, name='api_data_play_session'),
    ],
    config={
        'webapp2_extras.sessions': {'secret_key': coal_config.SECRET_KEY},
        'webapp2_extras.auth': {'user_model': 'models.User'}
    },
    debug=not on_production_server
)
