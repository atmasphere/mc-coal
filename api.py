import datetime
from functools import wraps
import logging

from google.appengine.ext import ndb

from pytz.gae import pytz

import webapp2

from wtforms import form, fields, validators

from agar.auth import authentication_required

from restler.serializers import json_response as restler_json_response
from restler.serializers import ModelStrategy

from config import coal_config
from models import Server, User, Player, PlaySession, LogLine, Command, ScreenShot
from models import CHAT_TAG, DEATH_TAG
from oauth import authenticate_agent_oauth_required, authenticate_user_required


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


class JsonHandler(webapp2.RequestHandler):
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
                super(JsonHandler, self).handle_exception(exception, debug_mode)
        else:
            code = 500
            logging.error(errors)
        self.json_response({}, status_code=code, errors=errors)


class OptionalBooleanField(fields.BooleanField):
    def process_data(self, value):
        if value is not None:
            self.data = bool(value)
        else:
            self.data = None

    def process_formdata(self, valuelist):
        if not valuelist:
            self.data = self.default
        else:
            self.data = valuelist[0] == 'True'


class PingForm(form.Form):
    server_name = fields.StringField(validators=[validators.InputRequired(), validators.Length(max=500)])
    is_server_running = OptionalBooleanField(validators=[validators.Optional()])
    server_day = fields.IntegerField(validators=[validators.Optional()])
    server_time = fields.IntegerField(validators=[validators.Optional()])
    is_raining = OptionalBooleanField(validators=[validators.Optional()])
    is_thundering = OptionalBooleanField(validators=[validators.Optional()])
    timestamp = fields.DateTimeField(validators=[validators.Optional()])


class PingHandler(JsonHandler):
    @authentication_required(authenticate=authenticate_agent_oauth_required)
    @validate_params(form_class=PingForm)
    def post(self):
        form = self.request.form
        is_server_running = form.is_server_running.data
        server_day = form.server_day.data
        server_time = form.server_time.data
        is_raining = form.is_raining.data
        is_thundering = form.is_thundering.data
        timestamp = form.timestamp.data
        server = Server.global_key().get()
        server.update_is_running(
            is_server_running,
            last_ping=datetime.datetime.now(),
            server_day=server_day,
            server_time=server_time,
            is_raining=is_raining,
            is_thundering=is_thundering,
            timestamp=timestamp
        )
        last_log_line = LogLine.get_last_line_with_timestamp()
        response = {
            'last_line': last_log_line.line if last_log_line is not None else None,
            'commands': Command.pop_all()
        }
        self.json_response(response, status_code=200)


class LogLineForm(form.Form):
    line = fields.StringField(validators=[validators.InputRequired()])
    zone = fields.StringField(validators=[validators.InputRequired()])


class LogLineHandler(JsonHandler):
    @authentication_required(authenticate=authenticate_agent_oauth_required)
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


class MultiPageJsonHandler(JsonHandler, MultiPage):
    pass


SERVER_FIELDS = ['version', 'is_running', 'server_day', 'server_time', 'is_raining', 'is_thundering']
SERVER_FIELD_FUNCTIONS = {
    'last_ping': lambda o: api_datetime(o.last_ping),
    'created': lambda o: api_datetime(o.created),
    'updated': lambda o: api_datetime(o.updated)
}
SERVER_STRATEGY = ModelStrategy(Server).include(*SERVER_FIELDS).include(**SERVER_FIELD_FUNCTIONS)


class ServerHandler(JsonHandler):
    @authentication_required(authenticate=authenticate_user_required)
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


class UsersHandler(MultiPageJsonHandler):
    @authentication_required(authenticate=authenticate_user_required)
    @validate_params(form_class=MultiPageForm)
    def get(self):
        self.json_response(self.fetch_page(User.query_by_email(), results_name='users'), USER_STRATEGY)


class UserKeyHandler(JsonHandler):
    def get_user_by_key(self, key, abort=True):
        fail_code = 404
        if key == 'self':
            fail_code = 403
            user = self.request.user
        else:
            try:
                user_key = ndb.Key(urlsafe=key)
                user = user_key.get()
            except Exception:
                user = None
        if abort and not user:
            self.abort(fail_code)
        return user

    @authentication_required(authenticate=authenticate_user_required)
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


class PlayersHandler(MultiPageJsonHandler):
    @authentication_required(authenticate=authenticate_user_required)
    @validate_params(form_class=MultiPageForm)
    def get(self):
        self.json_response(self.fetch_page(Player.query_by_username(), results_name='players'), PLAYER_STRATEGY)


class PlayerKeyUsernameHandler(JsonHandler):
    def get_player_by_key_or_username(self, key_username, abort_404=True):
        try:
            player_key = ndb.Key(urlsafe=key_username)
            player = player_key.get()
        except Exception:
            player = Player.lookup(key_username)
        if abort_404 and not player:
            self.abort(404)
        return player

    @authentication_required(authenticate=authenticate_user_required)
    def get(self, key_username):
        player = self.get_player_by_key_or_username(key_username)
        self.json_response(player, PLAYER_STRATEGY)


PLAY_SESSION_FIELDS = ['username']
PLAY_SESSION_FIELD_FUNCTIONS = {
    'key': lambda o: o.key.urlsafe(),
    'player_key': lambda o: o.player.key.urlsafe() if o.player is not None else None,
    'user_key': lambda o: o.user.key.urlsafe() if o.user is not None else None,
    'login_timestamp': lambda o: api_datetime(o.login_timestamp, zone=o.zone),
    'logout_timestamp': lambda o: api_datetime(o.logout_timestamp, zone=o.zone),
    'duration': lambda o: o.duration.total_seconds(),
    'login_logline_key': lambda o: o.login_log_line_key.urlsafe() if o.login_log_line_key is not None else None,
    'logout_logline_key': lambda o: o.logout_log_line_key.urlsafe() if o.logout_log_line_key is not None else None,
    'created': lambda o: api_datetime(o.created),
    'updated': lambda o: api_datetime(o.updated)
}
PLAY_SESSION_STRATEGY = ModelStrategy(PlaySession).include(*PLAY_SESSION_FIELDS).include(**PLAY_SESSION_FIELD_FUNCTIONS)


class PlaySessionsForm(MultiPageForm):
    since = fields.DateTimeField(validators=[validators.Optional()])
    before = fields.DateTimeField(validators=[validators.Optional()])


class PlaySessionsHandler(MultiPageJsonHandler):
    def get_player_by_key_or_username(self, key_username, abort_404=True):
        try:
            player_key = ndb.Key(urlsafe=key_username)
            player = player_key.get()
        except Exception:
            player = Player.lookup(key_username)
        if abort_404 and not player:
            self.abort(404)
        return player

    @authentication_required(authenticate=authenticate_user_required)
    @validate_params(form_class=PlaySessionsForm)
    def get(self, key_username=None):
        username = None
        if key_username:
            player = self.get_player_by_key_or_username(key_username)
            username = player.username
        since = self.request.form.since.data or None
        before = self.request.form.before.data or None
        query = PlaySession.query_latest(username=username, since=since, before=before)
        self.json_response(self.fetch_page(query, results_name='sessions'), PLAY_SESSION_STRATEGY)


class PlaySessionKeyHandler(JsonHandler):
    def get_play_session_by_key(self, key, abort_404=True):
        try:
            play_session_key = ndb.Key(urlsafe=key)
            play_session = play_session_key.get()
        except Exception:
            play_session = None
        if abort_404 and not play_session:
            self.abort(404)
        return play_session

    @authentication_required(authenticate=authenticate_user_required)
    def get(self, key):
        play_session = self.get_play_session_by_key(key)
        self.json_response(play_session, PLAY_SESSION_STRATEGY)


CHAT_FIELDS = ['username', 'line', 'chat']
CHAT_FIELD_FUNCTIONS = {
    'key': lambda o: o.key.urlsafe(),
    'player_key': lambda o: o.player.key.urlsafe() if o.player is not None else None,
    'user_key': lambda o: o.user.key.urlsafe() if o.user is not None else None,
    'timestamp': lambda o: api_datetime(o.timestamp, zone=o.zone),
    'created': lambda o: api_datetime(o.created),
    'updated': lambda o: api_datetime(o.updated)
}
CHAT_STRATEGY = ModelStrategy(LogLine).include(*CHAT_FIELDS).include(**CHAT_FIELD_FUNCTIONS)


class ChatForm(MultiPageForm):
    q = fields.StringField(validators=[validators.Optional()])
    since = fields.DateTimeField(validators=[validators.Optional()])
    before = fields.DateTimeField(validators=[validators.Optional()])


class ChatPostForm(form.Form):
    chat = fields.StringField(validators=[validators.DataRequired()])


class ChatHandler(MultiPageJsonHandler):
    def get_player_by_key_or_username(self, key_username, abort_404=True):
        try:
            player_key = ndb.Key(urlsafe=key_username)
            player = player_key.get()
        except Exception:
            player = Player.lookup(key_username)
        if abort_404 and not player:
            self.abort(404)
        return player

    @authentication_required(authenticate=authenticate_user_required)
    @validate_params(form_class=ChatForm)
    def get(self, key_username=None):
        username = None
        if key_username:
            player = self.get_player_by_key_or_username(key_username)
            username = player.username
        since = self.request.form.since.data or None
        before = self.request.form.before.data or None
        q = self.request.form.q.data or None
        if q:
            query_string = u"chat:{0}".format(q)
            cursor = self.request.form.cursor.data or None
            results, next_cursor = LogLine.search_api(query_string, size=self.size, username=username, tag=CHAT_TAG, since=since, before=before, cursor=cursor)
            response = {'chats': results}
            if next_cursor is not None:
                results, _ = LogLine.search_api(query_string, size=self.size, username=username, tag=CHAT_TAG, since=since, before=before, cursor=next_cursor)
                if results:
                    response['cursor'] = next_cursor
            self.json_response(response, CHAT_STRATEGY)
        else:
            query = LogLine.query_api(username=username, tag=CHAT_TAG, since=since, before=before)
            self.json_response(self.fetch_page(query, results_name='chats'), CHAT_STRATEGY)

    @authentication_required(authenticate=authenticate_user_required)
    @validate_params(form_class=ChatPostForm)
    def post(self):
        user = self.request.user
        chat = u"/say {0}".format(self.request.form.chat.data)
        Command.push(user.name, chat)
        self.response.set_status(201)


class ChatKeyHandler(JsonHandler):
    def get_log_line_by_key(self, key, abort_404=True):
        try:
            log_line_key = ndb.Key(urlsafe=key)
            log_line = log_line_key.get()
        except Exception:
            log_line = None
        if abort_404 and not log_line:
            self.abort(404)
        return log_line

    @authentication_required(authenticate=authenticate_user_required)
    def get(self, key):
        log_line = self.get_log_line_by_key(key)
        if CHAT_TAG not in log_line.tags:
            self.abort(404)
        self.json_response(log_line, CHAT_STRATEGY)


DEATH_FIELDS = ['username', 'line']
DEATH_FIELD_FUNCTIONS = {
    'key': lambda o: o.key.urlsafe(),
    'message': lambda o: o.death_message,
    'player_key': lambda o: o.player.key.urlsafe() if o.player is not None else None,
    'user_key': lambda o: o.user.key.urlsafe() if o.user is not None else None,
    'timestamp': lambda o: api_datetime(o.timestamp, zone=o.zone),
    'created': lambda o: api_datetime(o.created),
    'updated': lambda o: api_datetime(o.updated)
}
DEATH_STRATEGY = ModelStrategy(LogLine).include(*DEATH_FIELDS).include(**DEATH_FIELD_FUNCTIONS)


class DeathForm(MultiPageForm):
    q = fields.StringField(validators=[validators.Optional()])
    since = fields.DateTimeField(validators=[validators.Optional()])
    before = fields.DateTimeField(validators=[validators.Optional()])


class DeathHandler(MultiPageJsonHandler):
    def get_player_by_key_or_username(self, key_username, abort_404=True):
        try:
            player_key = ndb.Key(urlsafe=key_username)
            player = player_key.get()
        except Exception:
            player = Player.lookup(key_username)
        if abort_404 and not player:
            self.abort(404)
        return player

    @authentication_required(authenticate=authenticate_user_required)
    @validate_params(form_class=DeathForm)
    def get(self, key_username=None):
        username = None
        if key_username:
            player = self.get_player_by_key_or_username(key_username)
            username = player.username
        since = self.request.form.since.data or None
        before = self.request.form.before.data or None
        q = self.request.form.q.data or None
        if q:
            query_string = u"death_message:{0}".format(q)
            cursor = self.request.form.cursor.data or None
            results, next_cursor = LogLine.search_api(query_string, size=self.size, username=username, tag=DEATH_TAG, since=since, before=before, cursor=cursor)
            response = {'deaths': results}
            if next_cursor is not None:
                results, _ = LogLine.search_api(query_string, size=self.size, username=username, tag=DEATH_TAG, since=since, before=before, cursor=next_cursor)
                if results:
                    response['cursor'] = next_cursor
            self.json_response(response, DEATH_STRATEGY)
        else:
            query = LogLine.query_api(username=username, tag=DEATH_TAG, since=since, before=before)
            self.json_response(self.fetch_page(query, results_name='deaths'), DEATH_STRATEGY)


class DeathKeyHandler(JsonHandler):
    def get_log_line_by_key(self, key, abort_404=True):
        try:
            log_line_key = ndb.Key(urlsafe=key)
            log_line = log_line_key.get()
        except Exception:
            log_line = None
        if abort_404 and not log_line:
            self.abort(404)
        return log_line

    @authentication_required(authenticate=authenticate_user_required)
    def get(self, key):
        log_line = self.get_log_line_by_key(key)
        if DEATH_TAG not in log_line.tags:
            self.abort(404)
        self.json_response(log_line, DEATH_STRATEGY)


LOG_LINE_FIELDS = ['username', 'line', 'log_level', 'ip', 'port', 'location', 'chat', 'tags']
LOG_LINE_FIELD_FUNCTIONS = {
    'key': lambda o: o.key.urlsafe(),
    'player_key': lambda o: o.player.key.urlsafe() if o.player is not None else None,
    'user_key': lambda o: o.user.key.urlsafe() if o.user is not None else None,
    'timestamp': lambda o: api_datetime(o.timestamp, zone=o.zone),
    'created': lambda o: api_datetime(o.created),
    'updated': lambda o: api_datetime(o.updated)
}
LOG_LINE_STRATEGY = ModelStrategy(LogLine).include(*LOG_LINE_FIELDS).include(**LOG_LINE_FIELD_FUNCTIONS)


class LogLineForm(MultiPageForm):
    q = fields.StringField(validators=[validators.Optional()])
    tag = fields.StringField(validators=[validators.Optional()])
    since = fields.DateTimeField(validators=[validators.Optional()])
    before = fields.DateTimeField(validators=[validators.Optional()])


class LogLinesHandler(MultiPageJsonHandler):
    def get_player_by_key_or_username(self, key_username, abort_404=True):
        try:
            player_key = ndb.Key(urlsafe=key_username)
            player = player_key.get()
        except Exception:
            player = Player.lookup(key_username)
        if abort_404 and not player:
            self.abort(404)
        return player

    @authentication_required(authenticate=authenticate_user_required)
    @validate_params(form_class=LogLineForm)
    def get(self, key_username=None):
        username = None
        if key_username:
            player = self.get_player_by_key_or_username(key_username)
            username = player.username
        since = self.request.form.since.data or None
        before = self.request.form.before.data or None
        q = self.request.form.q.data or None
        tag = self.request.form.tag.data or None
        if q:
            query_string = u"line:{0}".format(q)
            cursor = self.request.form.cursor.data or None
            results, next_cursor = LogLine.search_api(query_string, size=self.size, username=username, tag=tag, since=since, before=before, cursor=cursor)
            response = {'loglines': results}
            if next_cursor is not None:
                results, _ = LogLine.search_api(query_string, size=self.size, username=username, tag=tag, since=since, before=before, cursor=next_cursor)
                if results:
                    response['cursor'] = next_cursor
            self.json_response(response, LOG_LINE_STRATEGY)
        else:
            query = LogLine.query_api(username=username, tag=tag, since=since, before=before)
            self.json_response(self.fetch_page(query, results_name='loglines'), LOG_LINE_STRATEGY)


class LogLineKeyHandler(JsonHandler):
    def get_log_line_by_key(self, key, abort_404=True):
        try:
            log_line_key = ndb.Key(urlsafe=key)
            log_line = log_line_key.get()
        except Exception:
            log_line = None
        if abort_404 and not log_line:
            self.abort(404)
        return log_line

    @authentication_required(authenticate=authenticate_user_required)
    def get(self, key):
        log_line = self.get_log_line_by_key(key)
        self.json_response(log_line, LOG_LINE_STRATEGY)


SCREEN_SHOT_FIELDS = ['username', 'random_id']
SCREEN_SHOT_FIELD_FUNCTIONS = {
    'key': lambda o: o.key.urlsafe(),
    'player_key': lambda o: o.player.key.urlsafe() if o.player is not None else None,
    'user_key': lambda o: o.user.key.urlsafe() if o.user is not None else None,
    'original_url': lambda o: o.get_serving_url(),
    'blurred_url': lambda o: o.blurred_image_serving_url,
    'created': lambda o: api_datetime(o.created),
    'updated': lambda o: api_datetime(o.updated)
}
SCREEN_SHOT_STRATEGY = ModelStrategy(ScreenShot).include(*SCREEN_SHOT_FIELDS).include(**SCREEN_SHOT_FIELD_FUNCTIONS)


class ScreenShotForm(MultiPageForm):
    since = fields.DateTimeField(validators=[validators.Optional()])
    before = fields.DateTimeField(validators=[validators.Optional()])


class ScreenShotsHandler(MultiPageJsonHandler):
    def get_player_by_key_or_username(self, key_username, abort_404=True):
        try:
            player_key = ndb.Key(urlsafe=key_username)
            player = player_key.get()
        except Exception:
            player = Player.lookup(key_username)
        if abort_404 and not player:
            self.abort(404)
        return player

    @authentication_required(authenticate=authenticate_user_required)
    @validate_params(form_class=ScreenShotForm)
    def get(self, key_username=None):
        username = None
        if key_username:
            player = self.get_player_by_key_or_username(key_username)
            username = player.username
        since = self.request.form.since.data or None
        before = self.request.form.before.data or None
        query = ScreenShot.query_latest(username=username, since=since, before=before)
        self.json_response(self.fetch_page(query, results_name='screenshots'), SCREEN_SHOT_STRATEGY)


class ScreenShotKeyHandler(JsonHandler):
    def get_screen_shot_by_key(self, key, abort_404=True):
        try:
            screen_shot_key = ndb.Key(urlsafe=key)
            screen_shot = screen_shot_key.get()
        except Exception:
            screen_shot = None
        if abort_404 and not screen_shot:
            self.abort(404)
        return screen_shot

    @authentication_required(authenticate=authenticate_user_required)
    def get(self, key):
        screen_shot = self.get_screen_shot_by_key(key)
        self.json_response(screen_shot, SCREEN_SHOT_STRATEGY)


routes = [
    webapp2.Route('/api/agent/ping', 'api.PingHandler', name='api_agent_ping'),
    webapp2.Route('/api/agent/log_line', 'api.LogLineHandler', name='api_agent_log_line'),

    webapp2.Route('/api/v1/data/servers', 'api.ServerHandler', name='api_data_servers'),
    webapp2.Route('/api/v1/data/users/<key>', 'api.UserKeyHandler', name='api_data_user_key'),
    webapp2.Route('/api/v1/data/users', 'api.UsersHandler', name='api_data_users'),
    webapp2.Route('/api/v1/data/players/<key_username>/sessions', 'api.PlaySessionsHandler', name='api_data_player_sessions'),
    webapp2.Route('/api/v1/data/players/<key_username>/loglines', 'api.LogLinesHandler', name='api_data_player_loglines'),
    webapp2.Route('/api/v1/data/players/<key_username>/chats', 'api.ChatHandler', name='api_data_player_chats'),
    webapp2.Route('/api/v1/data/players/<key_username>/deaths', 'api.DeathHandler', name='api_data_player_deaths'),
    webapp2.Route('/api/v1/data/players/<key_username>/screenshots', 'api.ScreenShotsHandler', name='api_data_player_screenshots'),
    webapp2.Route('/api/v1/data/players/<key_username>', 'api.PlayerKeyUsernameHandler', name='api_data_player_key_username'),
    webapp2.Route('/api/v1/data/players', 'api.PlayersHandler', name='api_data_players'),
    webapp2.Route('/api/v1/data/sessions/<key>', 'api.PlaySessionKeyHandler', name='api_data_session_key'),
    webapp2.Route('/api/v1/data/sessions', 'api.PlaySessionsHandler', name='api_data_sessions'),
    webapp2.Route('/api/v1/data/chats/<key>', 'api.ChatKeyHandler', name='api_data_chat_key'),
    webapp2.Route('/api/v1/data/chats', 'api.ChatHandler', name='api_data_chats'),
    webapp2.Route('/api/v1/data/deaths/<key>', 'api.DeathKeyHandler', name='api_data_death_key'),
    webapp2.Route('/api/v1/data/deaths', 'api.DeathHandler', name='api_data_deaths'),
    webapp2.Route('/api/v1/data/loglines/<key>', 'api.LogLineKeyHandler', name='api_data_logline_key'),
    webapp2.Route('/api/v1/data/loglines', 'api.LogLinesHandler', name='api_data_loglines'),
    webapp2.Route('/api/v1/data/screenshots/<key>', 'api.ScreenShotKeyHandler', name='api_data_screenshot_key'),
    webapp2.Route('/api/v1/data/screenshots', 'api.ScreenShotsHandler', name='api_data_screenshots')
]
