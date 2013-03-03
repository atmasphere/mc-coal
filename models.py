from google.appengine.ext import ndb
from google.appengine.ext.ndb import polymodel
from google.appengine.api import users

import webapp2_extras.appengine.auth.models as auth_models


class User(auth_models.User):
    active = ndb.BooleanProperty(default=False)
    admin = ndb.BooleanProperty(default=False)
    email = ndb.StringProperty()
    nickname = ndb.StringProperty()
    username = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

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
        query = cls.query()
        if email is not None:
            query = query.filter(ndb.StringProperty('email') == email)
        if username is not None:
            query = query.filter(ndb.StringProperty('username') == username)
        return query.get()


class LogLine(polymodel.PolyModel):
    line = ndb.StringProperty()
    zone = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def user(self):
        username = getattr(self, 'username', None)
        if username is not None:
            return User.lookup(username=self.username)
        return None

    @classmethod
    def get_line(cls, line):
        return cls.query().filter(ndb.StringProperty('line') == line).get()

    @classmethod
    def get_last_line(cls):
        return cls.query().order(-ndb.StringProperty('created')).get()


class TimeStampLogLine(LogLine):
    timestamp = ndb.DateTimeProperty(required=True)
    log_level = ndb.StringProperty(required=True)

    @classmethod
    def get_last_line(cls):
        return cls.query().order(-ndb.StringProperty('timestamp')).get()


class ConnectionEventLine(TimeStampLogLine):
    username = ndb.StringProperty(required=True)

    @property
    def user(self):
        return User.lookup(username=self.username)


class ConnectLine(ConnectionEventLine):
    ip = ndb.StringProperty()
    port = ndb.StringProperty()
    location_x = ndb.FloatProperty()
    location_y = ndb.FloatProperty()
    location_z = ndb.FloatProperty()


class DisconnectLine(ConnectionEventLine):
    pass


class ChatLine(TimeStampLogLine):
    username = ndb.StringProperty(required=True)
    chat = ndb.StringProperty(required=True)
