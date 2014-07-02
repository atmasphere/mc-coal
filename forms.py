from google.appengine.api import urlfetch
from google.appengine.ext import ndb

import pytz

from wtforms import fields, validators, widgets

from models import Server, User, MinecraftDownload


class StringListField(fields.Field):
    widget = widgets.TextInput()

    def __init__(self, label='', validators=None, remove_duplicates=True, **kwargs):
        super(StringListField, self).__init__(label, validators, **kwargs)
        self.remove_duplicates = remove_duplicates

    def _value(self):
        if self.data:
            return u', '.join(self.data)
        else:
            return u''

    def process_data(self, value):
        if value:
            self.data = [x.strip() for x in value]
        else:
            self.data = []
        if self.remove_duplicates:
            self.data = list(self._remove_duplicates(self.data))

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [x.strip() for x in valuelist[0].split(',')]
        else:
            self.data = []
        if self.remove_duplicates:
            self.data = list(self._remove_duplicates(self.data))

    @classmethod
    def _remove_duplicates(cls, seq):
        d = {}
        for item in seq:
            if item and item not in d:
                d[item] = True
                yield item


class UniqueShortName(object):
    def __init__(self, server=None):
        self.server = server

    def __call__(self, form, field):
        server = self.server or form.server
        short_name = field.data
        try:
            ndb.Key(urlsafe=short_name)
            raise validators.ValidationError(
                "Short name can't be a valid key string".format(short_name)
            )
        except:
            pass
        s = Server.get_by_short_name(short_name)
        if s is not None:
            if server is None or s.key != server.key:
                raise validators.ValidationError(
                    "Short name '{0}' is already assigned to another server".format(short_name)
                )


class UniqueUsername(object):
    def __call__(self, form, field):
        username = field.data
        u = User.lookup(username=username)
        if u is not None:
            raise validators.ValidationError("Username '{0}' is already assigned to a user".format(username))


class UniqueUsernames(object):
    def __init__(self, user=None):
        self.user = user

    def __call__(self, form, field):
        user = self.user or form.user
        usernames = field.data
        for username in usernames:
            u = User.lookup(username=username)
            if u is not None:
                if user is None or u.key != user.key:
                    raise validators.ValidationError("Username '{0}' is already assigned to a user".format(username))


class AtLeastOneAdmin(object):
    def __call__(self, form, field):
        if not field.data and form.user.admin and User.is_single_admin():
            raise validators.ValidationError("Can't demote this user. There must always be at least one admin user.")


class ValidTimezone(object):
    def __call__(self, form, field):
        timezone = field.data
        try:
            pytz.timezone(timezone)
        except:
            raise validators.ValidationError("Not a valid timezone".format(timezone))


class UniquePort(object):
    def __init__(self, server=None):
        self.server = server

    def __call__(self, form, field):
        server = self.server or form.server
        port = field.data
        if port:
            port = int(port)
            if port in Server.reserved_ports(ignore_server=server):
                raise validators.ValidationError("Port {0} is already reserved for another server".format(port))


class UniqueVersion(object):
    def __call__(self, form, field):
        version = field.data
        md = MinecraftDownload.lookup(version)
        if md is not None:
            raise validators.ValidationError("Minecraft version '{0}' is already assigned".format(version))


class VersionUrlExists(object):
    def __call__(self, form, field):
        url = field.data
        result = urlfetch.fetch(url=url, method=urlfetch.HEAD)
        if result.status_code >= 400:
            raise validators.ValidationError("Error ({0}) fetching url".format(result.status_code))


class RestfulStringField(fields.StringField):
    def process_data(self, value):
        if value:
            self.data = value
        else:
            self.data = None

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist[0]
        else:
            self.data = None


class RestfulBooleanField(fields.BooleanField):
    def process_data(self, value):
        if value is not None:
            b = value.lower()
            if b and (b[0] == 'n' or b[0] == 'f' or b[0] == '0'):
                self.data = False
            else:
                self.data = bool(value)
        else:
            self.data = self.default

    def process_formdata(self, valuelist):
        if valuelist:
            b = valuelist[0].lower()
            if b and (b[0] == 'n' or b[0] == 'f' or b[0] == '0'):
                self.data = False
            else:
                self.data = bool(valuelist[0])
        else:
            self.data = self.default


class RestfulSelectField(fields.SelectField):
    def process_data(self, value):
        try:
            if value is not None:
                self.data = self.coerce(value)
            else:
                self.data = None
        except (ValueError, TypeError):
            self.data = None

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = self.coerce(valuelist[0])
            except ValueError:
                raise ValueError(self.gettext('Invalid Choice: could not coerce'))
        else:
            self.data = None
