from cStringIO import StringIO
import datetime
import logging
import re
import random
import string

from google.appengine.ext import blobstore, ndb, deferred
from google.appengine.api import users, memcache, mail, app_identity

import webapp2_extras.appengine.auth.models as auth_models

from pytz.gae import pytz

try:
    from PIL import Image, ImageFilter
except ImportError:
    Image = ImageFilter = None

from restler.decorators import ae_ndb_serializer

from channel import ServerChannels

from config import coal_config
from image import NdbImage
import search


UNICODE_ASCII_DIGITS = string.digits.decode('ascii')
AGENT_CLIENT_ID = 'mc-coal-agent'
TICKS_PER_PLAY_SECOND = 20
UNKNOWN_TAG = 'unknown'
TIMESTAMP_TAG = 'timestamp'
CONNECTION_TAG = 'connection'
LOGIN_TAG = 'login'
LOGOUT_TAG = 'logout'
CHAT_TAG = 'chat'
SERVER_TAG = 'server'
PERFORMANCE_TAG = 'performance'
OVERLOADED_TAG = 'overloaded'
STOPPING_TAG = 'stopping'
STARTING_TAG = 'starting'
DEATH_TAG = 'death'
CLAIM_TAG = 'claim'
COAL_TAG = 'coal'
LOGIN_TAGS = [TIMESTAMP_TAG, CONNECTION_TAG, LOGIN_TAG]
LOGOUT_TAGS = [TIMESTAMP_TAG, CONNECTION_TAG, LOGOUT_TAG]
CHAT_TAGS = [TIMESTAMP_TAG, CHAT_TAG]
OVERLOADED_TAGS = [TIMESTAMP_TAG, SERVER_TAG, PERFORMANCE_TAG, OVERLOADED_TAG]
STOPPING_TAGS = [TIMESTAMP_TAG, SERVER_TAG, STOPPING_TAG]
STARTING_TAGS = [TIMESTAMP_TAG, SERVER_TAG, STARTING_TAG]
DEATH_TAGS = [TIMESTAMP_TAG, DEATH_TAG]
CLAIM_TAGS = [TIMESTAMP_TAG, CLAIM_TAG]
COAL_TAGS = [TIMESTAMP_TAG, COAL_TAG]
TIMESTAMP_TAGS = [TIMESTAMP_TAG, UNKNOWN_TAG]
CHANNEL_TAGS_SET = set(['login', 'logout', 'chat', 'death'])
REGEX_TAGS = [
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+)\[/(?P<ip>[\w.]+):(?P<port>\w+)\] logged in.+\((?P<location_x>-?\w.+), (?P<location_y>-?\w.+), (?P<location_z>-?\w.+)\)"
        ],
        LOGIN_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) lost connection: disconnect.+"
        ],
        LOGOUT_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] \[Server\] \<COAL\> (?P<chat>.+)",
        ],
        COAL_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] \<(?P<username>\w+)\> coal:claim:(?P<code>.+)",
        ],
        CLAIM_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] \<(?P<username>\w+)\> (?P<chat>.+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] \[Server\] \<(?P<username>[\w@\.]+)\> (?P<chat>.+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] \[Server\] (?P<chat>.+)"
        ],
        CHAT_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] Can't keep up! Did the system time change, or is the server overloaded\?"
        ],
        OVERLOADED_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] Stopping server"
        ],
        STOPPING_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] Starting minecraft server version (?P<server_version>[\S:]+)"
        ],
        STARTING_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was squashed by a falling anvil",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was pricked to death",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) walked into a cactus whilst trying to escape (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was shot by arrow",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) drowned whilst trying to escape (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) drowned",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) blew up",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was blown up by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) hit the ground too hard",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell off a ladder",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell off some vines",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell out of the water",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell from a high place",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell into a patch of fire",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell into a patch of cacti",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was doomed to fall by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was shot off some vines by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was blown from a high place by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) went up in flames",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) burned to death",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was burnt to a crisp whilst fighting (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) walked into a fire whilst fighting (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was slain by (?P<username_mob>\w+) using (?P<weapon>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was slain by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was shot by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was fireballed by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was killed by magic",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was killed by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) got finished off by (?P<username_mob>\w+) using (?P<weapon>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) tried to swim in lava while trying to escape (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) tried to swim in lava",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) died",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) starved to death",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) suffocated in a wall",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was killed while trying to hurt (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was pummeled by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell out of the world",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell from a high place and fell out of the world",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was knocked into the void by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) withered away",
        ],
        DEATH_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] .+"
        ],
        TIMESTAMP_TAGS
    )
]


def seconds_since_epoch(dt):
    if not dt:
        return None
    return (dt - datetime.datetime(1970, 1, 1)).total_seconds()


def safe_float_from_string(float_string):
    try:
        return float(float_string)
    except:
        return None


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


def get_whitelist_user(email):
    for wlu in coal_config.USER_WHITELIST:
        if email == wlu['email']:
            return wlu
    return None


@ae_ndb_serializer
class User(auth_models.User):
    active = ndb.BooleanProperty(default=False)
    admin = ndb.BooleanProperty(default=False)
    authorized_client_ids = ndb.StringProperty(repeated=True)
    email = ndb.StringProperty()
    nickname = ndb.StringProperty()
    usernames = ndb.StringProperty(repeated=True)
    last_login = ndb.DateTimeProperty()
    last_chat_view = ndb.DateTimeProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def white_list(self):
        return get_whitelist_user(self.email)

    @property
    def username(self):
        if self.usernames:
            return self.usernames[0]
        return None

    @property
    def name(self):
        return self.nickname or self.email

    @property
    def play_name(self):
        if self.username:
            return self.username
        if self.nickname:
            return '*{0}'.format(self.nickname)
        return self.email

    @property
    def unauthenticated_claims(self):
        return UsernameClaim.query_unauthenticated_by_user_key(self.key).fetch()

    def add_username(self, username):
        if username not in self.usernames:
            self.usernames.append(username)

    def set_usernames(self, usernames):
        for username in usernames:
            u = User.lookup(username=username)
            if u is not None and u.key != self.key:
                raise Exception("Username already taken: {0}".format(username))
        self.usernames = usernames

    def get_player(self, server_key):
        if self.username:
            return Player.get_or_create(server_key, self.username)
        return None

    def record_chat_view(self, dt=None):
        if dt is None:
            dt = datetime.datetime.now()
        self.last_chat_view = dt
        self.put()

    def is_client_id_authorized(self, client_id):
        return client_id in self.authorized_client_ids

    def authorize_client_id(self, client_id):
        if client_id and client_id not in self.authorized_client_ids:
            self.authorized_client_ids.append(client_id)
            self.put()

    def unauthorize_client_id(self, client_id):
        from oauth import authorization_provider
        if client_id and client_id in self.authorized_client_ids:
            self.authorized_client_ids.remove(client_id)
            self.put()
        authorization_provider.discard_client_user_tokens(client_id, self.key)

    def is_username(self, username):
        return username in self.usernames if username is not None else False

    def is_player(self, player):
        if player is not None:
            return self.is_username(player.username)
        return False

    @classmethod
    def _pre_delete_hook(cls, key):
        user = key.get()
        values = []
        for auth_id in user.auth_ids:
            unique = '%s.auth_id:%s' % (user.__class__.__name__, auth_id)
            values.append(unique)
        user.unique_model.delete_multi(values)

    @classmethod
    def get_gae_user_auth_id(cls, gae_user_id=None, gae_user=None):
        if not gae_user_id:
            gae_user_id = gae_user.user_id() if gae_user else None
        return 'gaeuser:{0}'.format(gae_user_id) if gae_user_id else None

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
    def get_indie_auth_id(cls, me=None):
        return 'indieuser:{0}'.format(me) if me else None

    @classmethod
    def lookup(cls, email=None, username=None):
        if email is not None or username is not None:
            query = cls.query()
            if email is not None:
                query = query.filter(ndb.StringProperty('email') == email)
            if username is not None:
                query = query.filter(ndb.StringProperty('usernames') == username)
            return query.get()
        return None

    @classmethod
    def query_by_email(cls):
        return cls.query().order(cls.email)

    @classmethod
    def query_by_email_reverse(cls):
        return cls.query().order(-cls.email)


@ae_ndb_serializer
class UsernameClaim(ndb.Model):
    user_key = ndb.KeyProperty()
    username = ndb.StringProperty()
    code = ndb.StringProperty()
    authenticated = ndb.DateTimeProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def _pre_put_hook(self):
        if self.code is None:
            self.code = ''.join([random.choice(UNICODE_ASCII_DIGITS) for x in xrange(5)])

    @classmethod
    def authenticate(cls, username, code):
        claim_query = cls.query()
        claim_query = claim_query.filter(cls.username == username)
        claim_query = claim_query.filter(cls.code == code)
        claim_query = claim_query.filter(cls.authenticated == None)
        claim = claim_query.get()
        if claim is not None:
            user = claim.user_key.get()
            if user is not None:
                claim.authenticated = datetime.datetime.now()
                claim.put()
                user.add_username(username)
                user.put()
                return True
        return False

    @classmethod
    def get_or_create(cls, username, user_key):
        claim_query = cls.query(ancestor=user_key)
        claim_query = claim_query.filter(cls.username == username)
        claim_query = claim_query.filter(cls.user_key == user_key)
        claim_query = claim_query.filter(cls.authenticated == None)
        claim = claim_query.get()
        if claim is None:
            claim = cls(parent=user_key, username=username, user_key=user_key)
            claim.put()
        return claim

    @classmethod
    def query_unauthenticated_by_user_key(cls, user_key):
        claim_query = cls.query(ancestor=user_key)
        claim_query = claim_query.filter(cls.user_key == user_key)
        claim_query = claim_query.filter(cls.authenticated == None)
        return claim_query


# @ae_ndb_serializer
# class Invite(ndb.Model):
#     user_key = ndb.KeyProperty()
#     redeemed = ndb.DateTimeProperty(auto_now_add=True)
#     created = ndb.DateTimeProperty(auto_now_add=True)
#     updated = ndb.DateTimeProperty(auto_now=True)


@ae_ndb_serializer
class Server(ndb.Model):
    name = ndb.StringProperty()
    version = ndb.StringProperty()
    is_running = ndb.BooleanProperty()
    last_ping = ndb.DateTimeProperty()
    last_server_day = ndb.IntegerProperty()
    last_server_time = ndb.IntegerProperty()
    is_raining = ndb.BooleanProperty()
    is_thundering = ndb.BooleanProperty()
    timestamp = ndb.DateTimeProperty()
    agent_key = ndb.KeyProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def players_query(self):
        return Player.query_all_players()

    @property
    def server_day(self):
        return self.last_server_day

    @property
    def server_time(self):
        st = self.last_server_time
        if self.is_running and self.timestamp is not None and st is not None:
            d = datetime.datetime.now() - self.timestamp
            st += d.seconds * TICKS_PER_PLAY_SECOND
            if st >= 24000:
                st %= 24000
        return st

    @property
    def agent(self):
        return self.agent_key.get() if self.agent_key is not None else None

    def check_is_running(self):
        if self.last_ping is None or self.last_ping < datetime.datetime.now() - datetime.timedelta(minutes=2):
            logging.info("Haven't heard from the agent since {0}. Setting server status is UNKNOWN.".format(self.last_ping))
            self.update_is_running(None)

    def update_version(self, server_version):
        if server_version is not None:
            if self.version != server_version:
                self.version = server_version
                self.put()

    def update_is_running(self, is_running, last_ping=None, server_day=None, server_time=None, is_raining=None, is_thundering=None, timestamp=None):
        was_running = self.is_running
        record_ping = False
        if (server_day is not None and server_day != self.last_server_day) or (server_time is not None and server_time != self.last_server_time):
            self.timestamp = timestamp or datetime.datetime.now()
            if server_day is not None:
                self.last_server_day = server_day
            if server_time is not None:
                self.last_server_time = server_time
            record_ping = True
        if is_raining != self.is_raining or is_thundering != self.is_thundering:
            self.is_raining = is_raining
            self.is_thundering = is_thundering
            record_ping = True
        if last_ping is not None:
            if self.last_ping is None or self.last_ping < last_ping - datetime.timedelta(minutes=1):
                record_ping = True
        if record_ping or (was_running != is_running):
            self.is_running = is_running
            if last_ping is not None:
                self.last_ping = last_ping
            self.put()
            if was_running != is_running:
                if is_running == True:
                    status = 'RUNNING'
                elif is_running == False:
                    status = 'DOWN'
                else:
                    status = 'UNKNOWN'
                tf = '%A, %B %d, %Y %I:%M:%S %p'
                now_utc_dt = pytz.utc.localize(datetime.datetime.now())
                now_ts = now_utc_dt.astimezone(pytz.timezone(coal_config.TIMEZONE)).strftime(tf)
                last_ping_ts = "NEVER"
                if self.last_ping:
                    last_ping_utc_dt = pytz.utc.localize(self.last_ping)
                    last_ping_ts = last_ping_utc_dt.astimezone(pytz.timezone(coal_config.TIMEZONE)).strftime(tf)
                body = 'The {0} server status is {1} as of {2}.\n\nThe last agent ping was on {3}'.format(
                    coal_config.TITLE,
                    status,
                    now_ts,
                    last_ping_ts
                )
                admin_emails = []
                admin_emails = [user.email for user in User.query().filter(User.admin == True) if user.email]
                if admin_emails:
                    mail.send_mail(
                        sender='noreply@{0}.appspotmail.com'.format(app_identity.get_application_id()),
                        to=admin_emails,
                        subject="{0} server status is {1}".format(coal_config.TITLE, status),
                        body=body
                    )

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        instance.put()
        if instance.agent_key is None:
            from oauth import Client, authorization_provider
            existing_agent_client = True
            while existing_agent_client:
                random_int = ''.join([random.choice(UNICODE_ASCII_DIGITS) for x in xrange(5)])
                client_id = Client.get_key_name("{0}-{1}".format(AGENT_CLIENT_ID, random_int))
                agent_client_key = Client.get_key(client_id)
                existing_agent_client = agent_client_key.get()
            agent_client = Client(
                key=agent_client_key,
                client_id=client_id,
                server_key=instance.key,
                redirect_uris=['/'],
                scope=['agent'],
                secret=authorization_provider.generate_client_secret()
            )
            agent_client.put()
            instance.agent_key = agent_client.key
            instance.put()
        return instance

    @classmethod
    def global_key(cls):
        server_key = None
        data = memcache.get('global_server_key')
        if data is not None:
            server_key = ndb.Key(urlsafe=data)
        else:
            server = Server.query().order(Server.created).get()
            if server is None:
                server = Server.create()
            server_key = server.key
            memcache.add('global_server_key', server_key.urlsafe())
        return server_key


class ServerModel(ndb.Model):
    @property
    def server_key(self):
        return self.key.parent()

    @classmethod
    def server_query(cls, server_key=None):
        return cls.query(ancestor=server_key)


@ae_ndb_serializer
class Player(ServerModel):
    username = ndb.StringProperty(required=True)
    last_login_timestamp = ndb.DateTimeProperty()

    @property
    def user(self):
        if self.username:
            return User.query().filter(User.usernames == self.username).get()
        return None

    @property
    def is_playing(self):
        return PlaySession.current(self.server_key, self.username) is not None

    @property
    def last_session_duration(self):
        last_session = PlaySession.last(self.server_key, self.username)
        return last_session.duration if last_session is not None else None

    @property
    def last_login_timestamp_sse(self):
        return seconds_since_epoch(self.last_login_timestamp)

    def is_user(self, user):
        if user is not None:
            return user.username == self.username
        return False

    def _post_put_hook(self, future):
        search.add_player(self)

    @classmethod
    def is_valid_username(cls, username):
        if username and '@' not in username and '*' not in username:
            return True
        return False

    @classmethod
    def _post_delete_hook(cls, key, future):
        search.remove_player(key)

    @classmethod
    def get_or_create(cls, server_key, username):
        return cls.get_or_insert(username, parent=server_key, username=username)

    @classmethod
    def query_all(cls, server_key):
        return cls.server_query(server_key).order(cls.last_login_timestamp)

    @classmethod
    def query_all_reverse(cls, server_key):
        return cls.server_query(server_key).order(-cls.last_login_timestamp)

    @classmethod
    def query_by_username(cls, server_key):
        return cls.server_query(server_key).order(cls.username)

    @classmethod
    def lookup(cls, server_key, username):
        key = None
        if username is not None:
            key = ndb.Key(cls, username, parent=server_key)
        return key.get() if key is not None else None


@ae_ndb_serializer
class Location(ndb.Model):
    x = ndb.FloatProperty()
    y = ndb.FloatProperty()
    z = ndb.FloatProperty()


class UsernameModel(ServerModel):
    username = ndb.StringProperty()

    @property
    def user(self):
        return User.lookup(username=self.username)

    @property
    def player(self):
        return Player.lookup(self.server_key, self.username)

    def is_user(self, user):
        return self.username in user.usernames if self.username and user else False


@ae_ndb_serializer
class LogLine(UsernameModel):
    line = ndb.StringProperty(required=True)
    zone = ndb.StringProperty(required=True)
    timestamp = ndb.DateTimeProperty()
    has_timestamp = ndb.ComputedProperty(lambda self: self.timestamp is not None)
    log_level = ndb.StringProperty()
    ip = ndb.StringProperty()
    port = ndb.StringProperty()
    location = ndb.StructuredProperty(Location)
    chat = ndb.StringProperty()
    death_message = ndb.StringProperty()
    username_mob = ndb.StringProperty()
    weapon = ndb.StringProperty()
    code = ndb.StringProperty()
    tags = ndb.StringProperty(repeated=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def _pre_put_hook(self):
        if not self.tags:
            self.tags = [UNKNOWN_TAG]
        if TIMESTAMP_TAG not in self.tags and self.timestamp is not None:
            self.tags.insert(0, TIMESTAMP_TAG)

    def _post_put_hook(self, future):
        if Player.is_valid_username(self.username):
            Player.get_or_create(self.server_key, self.username)
        search.add_log_line(self)
        self.send_message()

    def send_message(self):
        tags_set = set(self.tags)
        tags = list(tags_set.intersection(CHANNEL_TAGS_SET))
        if tags:
            ServerChannels.send_message(self, tags[0])

    @property
    def timezone(self):
        return name_to_timezone(self.zone)

    @property
    def timestamp_sse(self):
        return seconds_since_epoch(self.timestamp)

    @classmethod
    def _post_delete_hook(cls, key, future):
        search.remove_log_line(key)

    @classmethod
    def create(cls, server, line, zone, **kwargs):
        try:
            tz = pytz.timezone(zone)
        except:
            tz = pytz.utc
        zone = tz.zone
        kwargs['tags'] = [UNKNOWN_TAG]
        for regexes, tags in REGEX_TAGS:
            match = None
            for regex in regexes:
                match = re.match(regex, line)
                if match:
                    gd = match.groupdict()
                    d = gd.pop('date', None)
                    t = gd.pop('time', None)
                    if d and t:
                        dts = "{0} {1}".format(d, t)
                        kwargs['timestamp'] = dts_to_naive_utc(dts, tz)
                    location_x = gd.pop('location_x', None)
                    location_y = gd.pop('location_y', None)
                    location_z = gd.pop('location_z', None)
                    if location_x and location_y and location_z:
                        kwargs['location'] = Location(
                            x=safe_float_from_string(location_x),
                            y=safe_float_from_string(location_y),
                            z=safe_float_from_string(location_z)
                        )
                    kwargs.update(gd)
                    kwargs['tags'] = tags
                    if DEATH_TAG in tags:
                        username = kwargs['username']
                        i = line.find(username) + len(username) + 1
                        kwargs['death_message'] = line[i:]
                    break
            if match:
                break
        server.update_version(kwargs.pop('server_version', None))
        log_line = cls(parent=server.key, line=line, zone=zone, **kwargs)
        log_line.put()
        if LOGIN_TAG in log_line.tags:
            PlaySession.create(log_line.server_key, log_line.username, log_line.timestamp, zone, log_line.key)
        if LOGOUT_TAG in log_line.tags:
            PlaySession.close_current(log_line.server_key, log_line.username, log_line.timestamp, log_line.key)
        if STARTING_TAG in log_line.tags or STOPPING_TAG in log_line.tags:
            open_sessions_query = PlaySession.query_open(log_line.server_key)
            for session in open_sessions_query:
                session.close(log_line.timestamp, log_line.key)
        if CLAIM_TAG in log_line.tags:
            if UsernameClaim.authenticate(log_line.username, log_line.code):
                message = "Username claim succeeded."
            else:
                message = "Username claim failed."
            chat = u"/tell {0} {1}".format(log_line.username, message)
            Command.push(log_line.server_key, 'COAL', chat)
        return log_line

    @classmethod
    def lookup_line(cls, server_key, line):
        return cls.server_query(server_key).filter(cls.line == line).get()

    @classmethod
    def query_latest(cls, server_key):
        return cls.server_query(server_key).order(-cls.created)

    @classmethod
    def get_last_line(cls, server_key):
        return cls.query_latest(server_key).get()

    @classmethod
    def query_latest_with_timestamp(cls, server_key):
        return cls.server_query(server_key).filter(cls.has_timestamp == True).order(-cls.timestamp)

    @classmethod
    def get_last_line_with_timestamp(cls, server_key):
        return cls.query_latest_with_timestamp(server_key).get()

    @classmethod
    def query_latest_username(cls, server_key, username):
        return cls.query_latest_with_timestamp(server_key).filter(cls.username == username)

    @classmethod
    def query_by_tags(cls, server_key, tags):
        return cls.server_query(server_key).filter(cls.tags == tags)

    @classmethod
    def query_latest_chats(cls, server_key):
        return cls.query_by_tags(server_key, CHAT_TAG).order(-cls.timestamp)

    @classmethod
    def query_oldest_chats(cls, server_key):
        return cls.query_by_tags(server_key, CHAT_TAG).order(cls.timestamp)

    @classmethod
    def query_latest_logins(cls, server_key):
        return cls.query_by_tags(server_key, LOGIN_TAG).order(-cls.timestamp)

    @classmethod
    def query_oldest_logins(cls, server_key):
        return cls.query_by_tags(server_key, LOGIN_TAG).order(cls.timestamp)

    @classmethod
    def query_latest_logouts(cls, server_key):
        return cls.query_by_tags(server_key, LOGOUT_TAG).order(-cls.timestamp)

    @classmethod
    def query_oldest_logouts(cls, server_key):
        return cls.query_by_tags(server_key, LOGOUT_TAG).order(cls.timestamp)

    @classmethod
    def query_latest_events(cls, server_key):
        return cls.server_query(server_key).filter(cls.tags.IN([CHAT_TAG, LOGIN_TAG, LOGOUT_TAG, DEATH_TAG])).order(-cls.timestamp, cls.key)

    @classmethod
    def query_oldest_events(cls, server_key):
        return cls.server_query(server_key).filter(cls.tags.IN([CHAT_TAG, LOGIN_TAG, LOGOUT_TAG, DEATH_TAG])).order(cls.timestamp, cls.key)

    @classmethod
    def query_api(cls, server_key, username=None, tag=None, since=None, before=None):
        query = cls.query_latest_with_timestamp(server_key)
        if username:
            query = query.filter(cls.username == username)
        if tag:
            query = query.filter(cls.tags == tag)
        if since:
            query = query.filter(cls.timestamp >= since)
        if before:
            query = query.filter(cls.timestamp < before)
        return query

    @classmethod
    def search_api(cls, server_key, q, size=None, username=None, tag=None, since=None, before=None, cursor=None):
        query_string = u"{0}".format(q)
        if username is not None:
            query_string = u"{0} username:{1}".format(query_string, username)
        if tag is not None:
            query_string = u"{0} tags:{1}".format(query_string, tag)
        if since is not None:
            query_string = u"{0} timestamp_sse >= {1}".format(query_string, seconds_since_epoch(since))
        if before is not None:
            query_string = u"{0} timestamp_sse < {1}".format(query_string, seconds_since_epoch(before))
        results, _, next_cursor = search.search_log_lines(query_string, server_key=server_key, limit=size or coal_config.RESULTS_PER_PAGE, cursor=cursor)
        return results, next_cursor if next_cursor else None


@ae_ndb_serializer
class Command(UsernameModel):
    command = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def to_dict(self):
        return {'username': self.username, 'command': self.command}

    @classmethod
    def push(cls, server_key, username, command, **kwargs):
        instance = cls(
            parent=server_key,
            username=username,
            command=command,
            **kwargs
        )
        instance.put()
        return instance

    @classmethod
    @ndb.transactional
    def pop_all(cls, server_key):
        commands = []
        query = cls.server_query(server_key).order(cls.created)
        for command in query:
            commands.append(command.to_dict)
            command.key.delete()
        return commands


@ae_ndb_serializer
class PlaySession(UsernameModel):
    login_timestamp = ndb.DateTimeProperty(required=True)
    logout_timestamp = ndb.DateTimeProperty()
    zone = ndb.StringProperty(required=True)
    login_log_line_key = ndb.KeyProperty(kind=LogLine)
    logout_log_line_key = ndb.KeyProperty(kind=LogLine)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def duration(self):
        login_timestamp = self.login_timestamp or datetime.datetime.now()
        logout_timestamp = self.logout_timestamp or datetime.datetime.now()
        return logout_timestamp - login_timestamp

    def close(self, timestamp, logout_log_line_key):
        self.logout_timestamp = timestamp
        self.logout_log_line_key = logout_log_line_key
        self.put()

    @classmethod
    @ndb.transactional
    def create(cls, server_key, username, timestamp, zone, login_log_line_key, **kwargs):
        current = cls.current(server_key, username)
        if current:
            current.close(timestamp, login_log_line_key)
        instance = cls(
            parent=server_key,
            username=username,
            login_timestamp=timestamp,
            zone=zone,
            login_log_line_key=login_log_line_key,
            **kwargs
        )
        instance.put()
        player = Player.get_or_create(instance.server_key, username)
        player.last_login_timestamp = timestamp
        player.put()
        return instance

    @classmethod
    def close_current(cls, server_key, username, timestamp, logout_log_line_key):
        current = cls.current(server_key, username)
        if current:
            current.close(timestamp, logout_log_line_key)
        return current

    @classmethod
    def query_open(cls, server_key):
        return cls.server_query(server_key).filter(cls.logout_timestamp == None)

    @classmethod
    def query_latest_open(cls, server_key):
        return cls.query_open(server_key).order(-cls.login_timestamp)

    @classmethod
    def query_current(cls, server_key, username):
        return cls.query_open(server_key).filter(cls.username == username)

    @classmethod
    def current(cls, server_key, username):
        return cls.query_current(server_key, username).get()

    @classmethod
    def last(cls, server_key, username):
        return cls.query_latest(server_key, username=username).get()

    @classmethod
    def query_latest(cls, server_key, username=None, since=None, before=None):
        query = cls.server_query(server_key).order(-cls.login_timestamp)
        if username:
            query = query.filter(cls.username == username)
        if since:
            query = query.filter(cls.login_timestamp >= since)
        if before:
            query = query.filter(cls.login_timestamp < before)
        return query

    @classmethod
    def query_oldest(cls, server_key, username=None):
        query = cls.server_query(server_key).order(cls.login_timestamp)
        if username:
            query = query.filter(cls.username == username)
        return query


class GaussianBlurFilter(ImageFilter.Filter):
    name = "GaussianBlur"

    def __init__(self, radius=10):
        self.radius = radius

    def filter(self, image):
        return image.gaussian_blur(self.radius)


def blur(screen_shot_key):
    screen_shot = ndb.Key(urlsafe=screen_shot_key).get()
    screen_shot.create_blurred()


@ae_ndb_serializer
class ScreenShot(NdbImage, ServerModel):
    user_key = ndb.KeyProperty()
    random_id = ndb.FloatProperty()
    blurred_image_key = ndb.KeyProperty(kind=NdbImage)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def _pre_delete_hook(cls, key):
        super(ScreenShot, cls)._pre_delete_hook(key)
        instance = key.get()
        blurred_image = instance.blurred_image
        if blurred_image is not None:
            blurred_image.key.delete()

    @property
    def user(self):
        return self.user_key.get() if self.user_key is not None else None

    @property
    def blurred_image(self):
        return self.blurred_image_key.get() if self.blurred_image_key else None

    @property
    def blurred_image_serving_url(self):
        blurred_image = self.blurred_image
        if blurred_image is not None:
            return blurred_image.get_serving_url()
        return None

    def generate_blurred_image_data(self):
        blob_reader = blobstore.BlobReader(self.blob_key)
        pil_image = Image.open(blob_reader)
        screen_shot_filter = GaussianBlurFilter()
        pil_image = pil_image.filter(screen_shot_filter)
        output = StringIO()
        pil_image.save(output, format="png")
        pil_image_data = output.getvalue()
        output.close()
        return pil_image_data

    def create_blurred(self):
        blurred_image = NdbImage.create(parent=self.key, data=self.generate_blurred_image_data(), mime_type='image/png')
        self.blurred_image_key = blurred_image.key
        self.put()

    @classmethod
    def create(cls, server_key, user, **kwargs):
        instance = super(ScreenShot, cls).create(parent=server_key, **kwargs)
        instance.user_key = user.key if user else None
        instance.username = user.username if user else None
        instance.random_id = random.random()
        instance.put()
        deferred.defer(blur, instance.key.urlsafe())
        return instance

    @classmethod
    def random(cls, server_key):
        count = ScreenShot.server_query(server_key).count(limit=101)
        if not count:
            return None
        # Small enough for offset?
        if count <= 100:
            offset = random.randrange(count)
            screen_shot = ScreenShot.server_query().order(cls.random_id).get(offset=offset)
        else:  # Use statistics
            screen_shot = ScreenShot.server_query().filter(cls.random_id > random.random()).order(cls.random_id).get()
            if screen_shot is None:
                screen_shot = ScreenShot.server_query().order(cls.random_id).get()
        return screen_shot

    @classmethod
    def query_latest(cls, server_key, user_key=None, since=None, before=None):
        query = cls.server_query(server_key).order(-cls.created)
        if user_key:
            query = query.filter(cls.user_key == user_key)
        if since:
            query = query.filter(cls.created >= since)
        if before:
            query = query.filter(cls.created < before)
        return query

    @classmethod
    def query_oldest(cls, server_key):
        return cls.server_query(server_key).order(cls.created)
