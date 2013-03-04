import datetime

from google.appengine.ext import ndb
from google.appengine.ext.ndb import polymodel
from google.appengine.api import users

import webapp2_extras.appengine.auth.models as auth_models

from pytz.gae import pytz

CONNECTION_TAG = 'connection'
LOGIN_TAG = 'login'
LOGOUT_TAG = 'logout'
CHAT_TAG = 'chat'
SERVER_TAG = 'server'
PERFORMANCE_TAG = 'performance'
OVERLOADED_TAG = 'overloaded'


def itersubclasses(cls, _seen=None):
    """
    itersubclasses(cls)

    Generator over all subclasses of a given class, in depth first order.

    TAB: Found here: http://code.activestate.com/recipes/576949-find-all-subclasses-of-a-given-class/

    >>> list(itersubclasses(int)) == [bool]
    True
    >>> class A(object): pass
    >>> class B(A): pass
    >>> class C(A): pass
    >>> class D(B,C): pass
    >>> class E(D): pass
    >>>
    >>> for cls in itersubclasses(A):
    ...     print(cls.__name__)
    B
    D
    E
    C
    >>> # get ALL (new-style) classes currently defined
    >>> [cls.__name__ for cls in itersubclasses(object)] #doctest: +ELLIPSIS
    ['type', ...'tuple', ...]
    """

    if not isinstance(cls, type):
        raise TypeError('itersubclasses must be called with '
                        'new-style classes, not %.100r' % cls)
    if _seen is None:
        _seen = set()
    try:
        subs = cls.__subclasses__()
    except TypeError:  # fails only when cls is type
        subs = cls.__subclasses__(cls)
    for sub in subs:
        if sub not in _seen:
            _seen.add(sub)
            yield sub
            for sub in itersubclasses(sub, _seen):
                yield sub


def dts_to_naive_utc(dts, tz):
    dt = datetime.datetime.strptime(dts, "%Y-%m-%d %H:%M:%S")
    dt = tz.localize(dt)
    return dt.astimezone(pytz.utc).replace(tzinfo=None)


def zone_to_timezone(zone):
    try:
        timezone = pytz.timezone(zone)
    except:
        timezone = pytz.utc
    return timezone


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


class Location(ndb.Model):
    x = ndb.FloatProperty()
    y = ndb.FloatProperty()
    z = ndb.FloatProperty()


class LogLine(ndb.Model):
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

    @property
    def timezone(self):
        return zone_to_timezone(self.zone)

    @property
    def user(self):
        username = getattr(self, 'username', None)
        if username is not None:
            return User.lookup(username=self.username)
        return None

    @classmethod
    def create(cls, line, zone, **kwargs):
        instance = cls(line=line, zone=zone, **kwargs)
        instance.put()
        return instance

    @classmethod
    def get_line(cls, line):
        return cls.query().filter(cls.line == line).get()

    @classmethod
    def query_latest(cls):
        return cls.query().order(-cls.created)

    @classmethod
    def get_last_line(cls):
        return cls.query_latest().get()

    @classmethod
    def query_latest_with_timestamp(cls):
        return cls.query().filter(cls.has_timestamp == True).order(-cls.timestamp)

    @classmethod
    def get_last_line_with_timestamp(cls):
        return cls.query_latest_with_timestamp().get()

    @classmethod
    def query_by_tags(cls, tags):
        return cls.query().filter(cls.tags == tags)

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
