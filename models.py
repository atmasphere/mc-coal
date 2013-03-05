import datetime

from google.appengine.ext import ndb
from google.appengine.api import users, memcache

import webapp2_extras.appengine.auth.models as auth_models

from pytz.gae import pytz

CONNECTION_TAG = 'connection'
LOGIN_TAG = 'login'
LOGOUT_TAG = 'logout'
CHAT_TAG = 'chat'
SERVER_TAG = 'server'
PERFORMANCE_TAG = 'performance'
OVERLOADED_TAG = 'overloaded'
STOPPING_TAG = 'stopping'
STARTING_TAG = 'starting'


def dts_to_naive_utc(dts, tz):
    dt = datetime.datetime.strptime(dts, "%Y-%m-%d %H:%M:%S")
    dt = tz.localize(dt)
    return dt.astimezone(pytz.utc).replace(tzinfo=None)


def name_to_timezone(name):
    try:
        timezone = pytz.timezone(name)
    except:
        timezone = pytz.utc
    return timezone


class User(auth_models.User):
    active = ndb.BooleanProperty(default=False)
    admin = ndb.BooleanProperty(default=False)
    email = ndb.StringProperty()
    nickname = ndb.StringProperty()
    username = ndb.StringProperty()
    last_chat_view = ndb.DateTimeProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def player(self):
        if self.username:
            return Player.get_or_create(self.username)
        return None

    def record_chat_view(self, dt=None):
        if dt is None:
            dt = datetime.datetime.now()
        self.last_chat_view = dt
        self.put()

    def is_player(self, player):
        if player is not None:
            return player.username == self.username
        return False

    @classmethod
    def get_gae_user_auth_id(cls, gae_user_id=None, gae_user=None):
        if not gae_user_id:
            gae_user_id = gae_user.user_id() if gae_user else 'ANON'
        return 'gaeuser:{0}'.format(gae_user_id)

    @classmethod
    def get_by_gae_user(cls, gae_user_id=None, gae_user=None):
        return cls.get_by_auth_id(cls.get_gae_user_auth_id(gae_user_id=gae_user_id, gae_user=gae_user))

    @classmethod
    def create_by_gae_user(cls, gae_user=None):
        if not gae_user:
            gae_user = users.get_current_user()
        if gae_user:
            return cls.create_user(
                cls.get_gae_user_auth_id(gae_user=gae_user),
                email=gae_user.email(),
                nickname=gae_user.nickname()
            )
        return False, None

    @classmethod
    def lookup(cls, email=None, username=None):
        if email is not None or username is not None:
            query = cls.query()
            if email is not None:
                query = query.filter(ndb.StringProperty('email') == email)
            if username is not None:
                query = query.filter(ndb.StringProperty('username') == username)
            return query.get()
        return None


class Server(ndb.Model):
    name = ndb.StringProperty()
    version = ndb.StringProperty()
    is_running = ndb.BooleanProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def players_query(self):
        return Player.query_all_players()

    @classmethod
    def create(cls, key_name, **kwargs):
        instance = cls(**kwargs)
        instance.put()
        return instance

    @classmethod
    def get_or_insert_key(cls):
        data = memcache.get('global_key')
        if data is not None:
            return ndb.Key(urlsafe=data)
        else:
            server = Server.get_or_insert('global_server')
            memcache.add('global_key', server.key.urlsafe())
            return server.key

    @classmethod
    def global_key(cls):
        return cls.get_or_insert_key()


class ServerModel(ndb.Model):
    @classmethod
    def server_query(cls):
        return cls.query(ancestor=Server.global_key())


class Player(ServerModel):
    username = ndb.StringProperty(required=True)

    @property
    def user(self):
        if self.username:
            return User.query().filter(username=self.username).get()
        return None

    @property
    def is_playing(self):
        return PlaySession.current(self.username) is not None

    @property
    def last_login(self):
        last_session = PlaySession.last(self.username)
        if last_session is not None:
            return last_session.login_timestamp

    @property
    def last_session_duration(self):
        last_session = PlaySession.last(self.username)
        if last_session is not None:
            login_timestamp = last_session.login_timestamp or datetime.datetime.now()
            logout_timestamp = last_session.logout_timestamp or datetime.datetime.now()
            return logout_timestamp - login_timestamp
        return None

    def is_user(self, user):
        if user is not None:
            return user.username == self.username
        return False

    @classmethod
    def get_or_create(cls, username):
        return cls.get_or_insert(username, parent=Server.global_key(), username=username)

    @classmethod
    def query_all(cls):
        return cls.server_query().order(cls.username)

    @classmethod
    def query_all_reverse(cls):
        return cls.server_query().order(-cls.username)

    @classmethod
    def lookup(cls, username):
        if username is not None:
            parent = Server.global_key()
            key = ndb.Key(cls, username, parent=parent)
        return key.get() if key is not None else None


class Location(ndb.Model):
    x = ndb.FloatProperty()
    y = ndb.FloatProperty()
    z = ndb.FloatProperty()


class UsernameModel(ServerModel):
    @property
    def user(self):
        return User.lookup(username=self.username)

    @property
    def player(self):
        return Player.lookup(self.username)

    def is_user(self, user):
        return self.username == user.username if user else False


class LogLine(UsernameModel):
    line = ndb.StringProperty(required=True)
    zone = ndb.StringProperty(required=True)
    timestamp = ndb.DateTimeProperty()
    has_timestamp = ndb.ComputedProperty(lambda self: self.timestamp is not None)
    log_level = ndb.StringProperty()
    username = ndb.StringProperty()
    ip = ndb.StringProperty()
    port = ndb.StringProperty()
    location = ndb.StructuredProperty(Location)
    chat = ndb.StringProperty()
    tags = ndb.StringProperty(repeated=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def _pre_put_hook(self):
        if self.username:
            Player.get_or_create(self.username)

    @property
    def timezone(self):
        return name_to_timezone(self.zone)

    @classmethod
    def create(cls, line, zone, **kwargs):
        instance = cls(parent=Server.global_key(), line=line, zone=zone, **kwargs)
        instance.put()
        if instance.username:
            Player.get_or_create(instance.username)
        return instance

    @classmethod
    def lookup_line(cls, line):
        return cls.server_query().filter(cls.line == line).get()

    @classmethod
    def query_latest(cls):
        return cls.server_query().order(-cls.created)

    @classmethod
    def get_last_line(cls):
        return cls.query_latest().get()

    @classmethod
    def query_latest_with_timestamp(cls):
        return cls.server_query().filter(cls.has_timestamp == True).order(-cls.timestamp)

    @classmethod
    def get_last_line_with_timestamp(cls):
        return cls.query_latest_with_timestamp().get()

    @classmethod
    def query_by_tags(cls, tags):
        return cls.server_query().filter(cls.tags == tags)

    @classmethod
    def query_latest_chats(cls):
        return cls.query_by_tags(CHAT_TAG).order(-cls.timestamp)

    @classmethod
    def query_oldest_chats(cls):
        return cls.query_by_tags(CHAT_TAG).order(cls.timestamp)

    @classmethod
    def query_latest_logins(cls):
        return cls.query_by_tags(LOGIN_TAG).order(-cls.timestamp)

    @classmethod
    def query_oldest_logins(cls):
        return cls.query_by_tags(LOGIN_TAG).order(cls.timestamp)

    @classmethod
    def query_latest_logouts(cls):
        return cls.query_by_tags(LOGOUT_TAG).order(-cls.timestamp)

    @classmethod
    def query_oldest_logouts(cls):
        return cls.query_by_tags(LOGOUT_TAG).order(cls.timestamp)


class PlaySession(UsernameModel):
    username = ndb.StringProperty()
    login_timestamp = ndb.DateTimeProperty(required=True)
    logout_timestamp = ndb.DateTimeProperty()
    zone = ndb.StringProperty(required=True)
    login_log_line = ndb.KeyProperty(kind=LogLine)
    logout_log_line = ndb.KeyProperty(kind=LogLine)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def duration(self):
        if self.login_timestamp is not None:
            logout_timestamp = self.logout_timestamp
            if not logout_timestamp:
                logout_timestamp = datetime.datetime.now()
            return self.logout_timestamp - self.login_timestamp
        return None

    def close(self, timestamp, logout_log_line_key):
        self.logout_timestamp = timestamp
        self.logout_log_line = logout_log_line_key
        self.put()

    @classmethod
    def create(cls, username, timestamp, zone, login_log_line_key, **kwargs):
        current = cls.current(username)
        if current:
            current.close(timestamp, login_log_line_key)
        instance = cls(
            parent=Server.global_key(),
            username=username,
            login_timestamp=timestamp,
            zone=zone,
            login_log_line=login_log_line_key,
            **kwargs
        )
        instance.put()
        return instance

    @classmethod
    def close_current(cls, username, timestamp, logout_log_line_key):
        current = cls.current(username)
        if current:
            current.close(timestamp, logout_log_line_key)
        return current

    @classmethod
    def query_open(cls):
        return cls.server_query().filter(cls.logout_timestamp == None)

    @classmethod
    def query_current(cls, username):
        return cls.query_open().filter(cls.username == username)

    @classmethod
    def query_last(cls, username):
        return cls.server_query().filter(cls.username == username).order(-cls.login_timestamp)

    @classmethod
    def last(cls, username):
        return cls.query_last(username).get()

    @classmethod
    def current(cls, username):
        return cls.query_current(username).get()

    @classmethod
    def query_latest(cls):
        return cls.server_query().order(-cls.login_timestamp)

    @classmethod
    def query_oldest(cls):
        return cls.server_query().order(cls.login_timestamp)
