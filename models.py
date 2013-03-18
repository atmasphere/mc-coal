from cStringIO import StringIO
import datetime
import logging
import re
import random

from google.appengine.ext import ndb, blobstore, deferred
from google.appengine.api import users, memcache, mail, app_identity

import webapp2_extras.appengine.auth.models as auth_models

from pytz.gae import pytz

try:
    from PIL import Image, ImageFilter
except ImportError:
    Image = ImageFilter = None

from agar.image import NdbImage as AgarImage

from config import coal_config
import search

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
LOGIN_TAGS = [TIMESTAMP_TAG, CONNECTION_TAG, LOGIN_TAG]
LOGOUT_TAGS = [TIMESTAMP_TAG, CONNECTION_TAG, LOGOUT_TAG]
CHAT_TAGS = [TIMESTAMP_TAG, CHAT_TAG]
OVERLOADED_TAGS = [TIMESTAMP_TAG, SERVER_TAG, PERFORMANCE_TAG, OVERLOADED_TAG]
STOPPING_TAGS = [TIMESTAMP_TAG, SERVER_TAG, STOPPING_TAG]
STARTING_TAGS = [TIMESTAMP_TAG, SERVER_TAG, STARTING_TAG]
TIMESTAMP_TAGS = [TIMESTAMP_TAG, UNKNOWN_TAG]
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
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] \<(?P<username>\w+)\> (?P<chat>.+)"
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
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] .+"
        ],
        TIMESTAMP_TAGS
    )
]


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


class User(auth_models.User):
    active = ndb.BooleanProperty(default=False)
    admin = ndb.BooleanProperty(default=False)
    email = ndb.StringProperty()
    nickname = ndb.StringProperty()
    username = ndb.StringProperty()
    last_login = ndb.DateTimeProperty()
    last_chat_view = ndb.DateTimeProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def player(self):
        if self.username:
            return Player.get_or_create(self.username)
        return None

    @property
    def white_list(self):
        return get_whitelist_user(self.email)

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

    @classmethod
    def query_by_email(cls):
        return cls.query().order(cls.email)

    @classmethod
    def query_by_email_reverse(cls):
        return cls.query().order(-cls.email)


class Server(ndb.Model):
    name = ndb.StringProperty()
    version = ndb.StringProperty()
    is_running = ndb.BooleanProperty()
    last_ping = ndb.DateTimeProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def players_query(self):
        return Player.query_all_players()

    def check_is_running(self):
        if self.last_ping is None or self.last_ping < datetime.datetime.now() - datetime.timedelta(minutes=2):
            logging.info("Haven't heard from the agent since {0}. Setting server status is UNKNOWN.".format(self.last_ping))
            self.update_is_running(None)

    def update_is_running(self, is_running, last_ping=None):
        was_running = self.is_running
        if was_running != is_running or last_ping is not None:
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
                admin_emails = [user.email for user in User.query().filter(User.admin == True)]
                if admin_emails:
                    mail.send_mail(
                        sender='noreply@{0}.appspotmail.com'.format(app_identity.get_application_id()),
                        to=admin_emails,
                        subject="{0} server status is {1}".format(coal_config.TITLE, status),
                        body=body
                    )

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
    last_login_timestamp = ndb.DateTimeProperty()

    @property
    def user(self):
        if self.username:
            return User.query().filter(username=self.username).get()
        return None

    @property
    def is_playing(self):
        return PlaySession.current(self.username) is not None

    @property
    def _last_login_timestamp(self):
        last_session = PlaySession.last(self.username)
        if last_session is not None:
            return last_session.login_timestamp
        return None

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

    def _post_put_hook(self, future):
        search.add_player(self)

    @classmethod
    def _post_delete_hook(cls, key, future):
        search.remove_player(key)

    @classmethod
    def get_or_create(cls, username):
        return cls.get_or_insert(username, parent=Server.global_key(), username=username)

    @classmethod
    def query_all(cls):
        return cls.server_query().order(cls.last_login_timestamp)

    @classmethod
    def query_all_reverse(cls):
        return cls.server_query().order(-cls.last_login_timestamp)

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
    username = ndb.StringProperty()

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
        if not self.tags:
            self.tags = [UNKNOWN_TAG]
        if TIMESTAMP_TAG not in self.tags and self.timestamp is not None:
            self.tags.insert(0, TIMESTAMP_TAG)

    def _post_put_hook(self, future):
        search.add_log_line(self)

    @property
    def timezone(self):
        return name_to_timezone(self.zone)

    @classmethod
    def _post_delete_hook(cls, key, future):
        search.remove_log_line(key)

    @classmethod
    @ndb.transactional
    def create(cls, line, zone, **kwargs):
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
                    break
            if match:
                break
        server_version = kwargs.pop('server_version', None)
        if server_version is not None:
            server = Server.global_key().get()
            server.version = server_version
            server.put()
        log_line = cls(parent=Server.global_key(), line=line, zone=zone, **kwargs)
        log_line.put()
        if log_line.username:
            Player.get_or_create(log_line.username)
        if LOGIN_TAG in log_line.tags:
            PlaySession.create(log_line.username, log_line.timestamp, zone, log_line.key)
        if LOGOUT_TAG in log_line.tags:
            PlaySession.close_current(log_line.username, log_line.timestamp, log_line.key)
        if STARTING_TAG in log_line.tags or STOPPING_TAG in log_line.tags:
            open_sessions_query = PlaySession.query_open()
            for session in open_sessions_query:
                session.close(log_line.timestamp, log_line.key)
        return log_line

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
            return logout_timestamp - self.login_timestamp
        return None

    def close(self, timestamp, logout_log_line_key):
        self.logout_timestamp = timestamp
        self.logout_log_line = logout_log_line_key
        self.put()

    @classmethod
    @ndb.transactional
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
        player = Player.get_or_create(username)
        player.last_login_timestamp = timestamp
        player.put()
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
    def query_latest_open(cls):
        return cls.query_open().order(-cls.login_timestamp)

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

if ImageFilter is not None:
    class MyGaussianBlur(ImageFilter.Filter):
        name = "GaussianBlur"

        def __init__(self, radius=2):
            self.radius = radius

        def filter(self, image):
            return image.gaussian_blur(self.radius)


def blur(screen_shot_key):
    screen_shot = ndb.Key(urlsafe=screen_shot_key).get()
    screen_shot.create_blurred()


class ScreenShot(AgarImage, UsernameModel):
    random_id = ndb.FloatProperty()
    blurred_image_key = ndb.KeyProperty(kind=AgarImage)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def _pre_delete_hook(cls, key):
        instance = key.get()
        blurred_image = instance.blurred_image
        if blurred_image is not None:
            blurred_image.key.delete()

    @property
    def blurred_image(self):
        return self.blurred_image_key.get() if self.blurred_image_key else None

    @property
    def blurred_image_serving_url(self):
        blurred_image = self.blurred_image
        if blurred_image is not None:
            return blurred_image.get_serving_url()
        return None

    def create_blurred(self):
        blob_reader = blobstore.BlobReader(self.blob_key)
        pil_image = Image.open(blob_reader)
        my_filter = MyGaussianBlur(radius=10)
        pil_image = pil_image.filter(my_filter)
        output = StringIO()
        pil_image.save(output, format="png")
        pil_image_data = output.getvalue()
        output.close()
        blurred_image = AgarImage.create(parent=self.key, data=pil_image_data, mime_type='image/png')
        self.blurred_image_key = blurred_image.key
        self.put()

    @classmethod
    def create(cls, username, **kwargs):
        instance = super(ScreenShot, cls).create(parent=Server.global_key(), **kwargs)
        instance.username = username
        instance.random_id = random.random()
        instance.put()
        deferred.defer(blur, instance.key.urlsafe())
        return instance

    @classmethod
    def random(cls):
        count = ScreenShot.server_query().count(limit=101)
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
    def query_latest(cls):
        return cls.server_query().order(-cls.created)

    @classmethod
    def query_oldest(cls):
        return cls.server_query().order(cls.created)
