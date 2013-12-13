import logging
import os

from google.appengine.api import lib_config
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.ext.ndb import Cursor
from google.appengine.ext.webapp import blobstore_handlers

from pytz.gae import pytz

import webapp2

from webapp2_extras.routes import RedirectRoute

from wtforms import form, fields, validators, widgets

from base_handler import uri_for_pagination
from channel import ServerChannels
import gce
from models import User, Player, LogLine, PlaySession, ScreenShot, Command, Server, UsernameClaim
import search
from user_auth import UserBase, UserHandler, authentication_required, authenticate, authenticate_admin


ON_SERVER = not os.environ.get('SERVER_SOFTWARE', 'Development').startswith('Development')
RESULTS_PER_PAGE = 50
TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones if tz.startswith('U')] + \
[(tz, tz) for tz in pytz.common_timezones if not tz.startswith('U')]


class MainHandlerBase(UserHandler):
    def get_template_context(self, context=None):
        template_context = super(MainHandlerBase, self).get_template_context(context=context)
        server = template_context['server'] = template_context.get('server', None) or getattr(self.request, 'server', None)
        if server is not None:
            bg_img = ScreenShot.random(server.key)
            if bg_img is not None:
                template_context['bg_img'] = bg_img.blurred_image_serving_url
        return template_context

    def redirect_to_server(self, route_name):
        server_keys = Server.query_all().fetch(2, keys_only=True)
        if server_keys and len(server_keys) == 1:
            self.redirect(webapp2.uri_for(route_name, server_key=server_keys[0].urlsafe()), abort=True)
        else:
            self.redirect(webapp2.uri_for('main'), abort=True)

    def get_server_by_key(self, key, route_name, abort=True):
        if key is None:
            self.redirect_to_server(route_name)
        try:
            server_key = ndb.Key(urlsafe=key)
            server = server_key.get()
            if server is not None and not server.active:
                server = None
        except Exception:
            server = None
        if abort and not server:
            self.abort(404)
        self.request.server = server
        return self.request.server

    def head(self):
        self.get()
        self.response.clear()


class MainHandler(MainHandlerBase):
    @authentication_required(authenticate=authenticate)
    def get(self):
        servers = Server.query_all().fetch(100)
        if self.request.user and self.request.user.active:
            if servers and len(servers) == 1:
                self.redirect(webapp2.uri_for('home', server_key=servers[0].key.urlsafe()), abort=True)
        context = {
            'servers': servers
        }
        self.render_template('main.html', context=context)


class HomeHandler(MainHandlerBase):
    @authentication_required(authenticate=authenticate)
    def get(self, server_key=None):
        server = self.get_server_by_key(server_key, 'home')
        open_sessions_query = PlaySession.query_latest_open(server.key)
        # Get open sessions
        playing_usernames = []
        open_sessions = []
        for open_session in open_sessions_query:
            if open_session.username and open_session.username not in playing_usernames:
                playing_usernames.append(open_session.username)
                open_sessions.append(open_session)
        # Get new chats
        new_chats_query = LogLine.query_latest_events(server.key)
        last_chat_view = self.request.user.last_chat_view
        if last_chat_view is not None:
            new_chats_query = new_chats_query.filter(LogLine.timestamp > last_chat_view)
        new_chats, chats_cursor, more = new_chats_query.fetch_page(20)
        if new_chats:
            self.request.user.record_chat_view(new_chats[0].timestamp)
        # Render with context
        context = {
            'open_sessions': open_sessions,
            'new_chats': new_chats,
            'chats_cursor': chats_cursor
        }
        self.render_template('home.html', context=context)


class PagingHandler(MainHandlerBase):
    def get_results_with_cursors(self, query, reverse_query, size):
        cursor = self.request.get('cursor', None)
        if cursor:
            try:
                cursor = Cursor.from_websafe_string(cursor)
            except:
                cursor = None
        next_cursor = previous_cursor = None
        if cursor is not None:
            reverse_cursor = cursor.reversed()
            reverse_results, reverse_next_cursor, reverse_more = reverse_query.fetch_page(
                size, start_cursor=reverse_cursor
            )
            if reverse_more:
                previous_cursor = reverse_next_cursor.reversed()
                previous_cursor = previous_cursor.to_websafe_string()
            else:
                previous_cursor = 'START'
        results, next_cursor, more = query.fetch_page(size, start_cursor=cursor)
        if more:
            next_cursor = next_cursor.to_websafe_string()
        else:
            next_cursor = None
        return results, previous_cursor, next_cursor


class ChatForm(form.Form):
    chat = fields.StringField(u'Chat', validators=[validators.DataRequired()])


class ChatsHandler(PagingHandler):
    @authentication_required(authenticate=authenticate)
    def get(self, server_key=None):
        server = self.get_server_by_key(server_key, 'chats')
        self.request.user.record_chat_view()
        query_string = self.request.get('q', None)
        # Search
        if query_string:
            page = 0
            cursor = self.request.get('cursor', None)
            if cursor and cursor.startswith('PAGE_'):
                page = int(cursor.strip()[5:])
            offset = page*RESULTS_PER_PAGE
            results, number_found, _ = search.search_log_lines('chat:{0}'.format(query_string), server_key=server.key, limit=RESULTS_PER_PAGE, offset=offset)
            previous_cursor = next_cursor = None
            if page > 0:
                previous_cursor = u'PAGE_{0}&q={1}'.format(page - 1 if page > 0 else 0, query_string)
            if number_found > offset + RESULTS_PER_PAGE:
                next_cursor = u'PAGE_{0}&q={1}'.format(page + 1, query_string)
        # Latest
        else:
            results, previous_cursor, next_cursor = self.get_results_with_cursors(
                LogLine.query_latest_events(server.key), LogLine.query_oldest_events(server.key), RESULTS_PER_PAGE
            )

        context = {'chats': results, 'query_string': query_string or ''}

        if self.request.is_xhr:
            self.render_xhr_response(server.key, context, next_cursor)
        else:
            self.render_html_response(server.key, context, next_cursor, previous_cursor)

    def render_xhr_response(self, server_key, context, next_cursor):
        if next_cursor:
            context.update({
                'next_uri': uri_for_pagination('chats', server_key=server_key.urlsafe(), cursor=next_cursor)
            })
        self.response.headers['Content-Type'] = 'text/javascript'
        self.render_template('chats.js', context=context)

    def render_html_response(self, server_key, context, next_cursor, previous_cursor):
        user = self.request.user
        channel_token = ServerChannels.create_channel(server_key, user)
        context.update({
            'next_cursor': next_cursor,
            'previous_cursor': previous_cursor,
            'channel_token': channel_token,
            'username': user.get_server_play_name(server_key),
        })
        self.render_template('chats.html', context=context)

    @authentication_required(authenticate=authenticate)
    def post(self, server_key=None):
        server = self.get_server_by_key(server_key, 'chats')
        try:
            user = self.request.user
            if not (user and user.active):
                self.abort(404)
            form = ChatForm(self.request.POST)
            if form.validate():
                chat = u"/say {0}".format(form.chat.data)
                Command.push(server.key, user.get_server_play_name(server.key), chat)
        except Exception, e:
            logging.error(u"Error POSTing chat: {0}".format(e))
            self.abort(500)
        self.response.set_status(201)


class PlayersHandler(PagingHandler):
    @authentication_required(authenticate=authenticate)
    def get(self, server_key=None):
        server = self.get_server_by_key(server_key, 'players')
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            Player.query_all_reverse(server.key), Player.query_all(server.key), RESULTS_PER_PAGE
        )
        context = {'players': results, 'previous_cursor': previous_cursor, 'next_cursor': next_cursor}
        self.render_template('players.html', context=context)


class PlaySessionsHandler(PagingHandler):
    @authentication_required(authenticate=authenticate)
    def get(self, server_key=None):
        server = self.get_server_by_key(server_key, 'play_sessions')
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            PlaySession.query_latest(server.key), PlaySession.query_oldest(server.key), RESULTS_PER_PAGE
        )
        context = {'play_sessions': results, 'previous_cursor': previous_cursor, 'next_cursor': next_cursor}
        self.render_template('play_sessions.html', context=context)


class ScreenShotUploadHandler(MainHandlerBase):
    @authentication_required(authenticate=authenticate)
    def get(self, server_key):
        server = self.get_server_by_key(server_key, 'home')
        url = webapp2.uri_for('screenshot_uploaded', server_key=server.key.urlsafe())
        upload_url = blobstore.create_upload_url(url)
        context = {'upload_url': upload_url}
        self.render_template('screen_shot_upload.html', context=context)


class ScreenShotUploadedHandler(blobstore_handlers.BlobstoreUploadHandler, UserBase):
    def redirect_to_server(self, route_name):
        server_keys = Server.query_all().fetch(2, keys_only=True)
        if server_keys and len(server_keys) == 1:
            self.redirect(webapp2.uri_for(route_name, server_key=server_keys[0].urlsafe()), abort=True)
        else:
            self.redirect(webapp2.uri_for('main'), abort=True)

    def get_server_by_key(self, key, route_name, abort=True):
        if key is None:
            self.redirect_to_server(route_name)
        try:
            server_key = ndb.Key(urlsafe=key)
            server = server_key.get()
        except Exception:
            server = None
        if abort and not server:
            self.abort(404)
        self.request.server = server
        return self.request.server

    @authentication_required(authenticate=authenticate)
    def post(self, server_key):
        server = self.get_server_by_key(server_key, 'home')
        blob_info = self.get_uploads('file')[0]
        ScreenShot.create(server.key, self.request.user, blob_info=blob_info)
        self.redirect(webapp2.uri_for('screenshots', server_key=server.key.urlsafe()))


class ScreenShotsHandler(PagingHandler):
    @authentication_required(authenticate=authenticate)
    def get(self, server_key=None):
        server = self.get_server_by_key(server_key, 'screenshots')
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            ScreenShot.query_latest(server.key), ScreenShot.query_oldest(server.key), 5
        )
        context = {'screenshots': results, 'previous_cursor': previous_cursor, 'next_cursor': next_cursor}
        self.render_template('screen_shots.html', context=context)


class ScreenShotBlurHandler(MainHandlerBase):
    def post(self, key=None):
        try:
            screenshot = ndb.Key(urlsafe=key).get()
            if screenshot is not None:
                screenshot.create_blurred()
        except Exception, e:
            logging.error(u"Error creating blurred screen shot: {0}".format(e))


class ScreenShotRemoveHandler(MainHandlerBase):
    @authentication_required(authenticate=authenticate)
    def post(self, server_key, key):
        server = self.get_server_by_key(server_key, 'screenshots')
        try:
            screenshot_key = ndb.Key(urlsafe=key)
            if screenshot_key.parent() != server.key:
                self.abort(404)
            screenshot = screenshot_key.get()
            if screenshot is not None:
                screenshot.key.delete()
        except Exception, e:
            logging.error(u"Error removing screen shot: {0}".format(e))
        self.redirect(webapp2.uri_for('screenshots', server_key=server.key.urlsafe()))


class AdminHandler(PagingHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self):
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            User.query_all(), User.query_all_reverse(), RESULTS_PER_PAGE
        )
        servers = []
        for server in Server.query():
            servers.append(server)
        instance = gce.Instance.singleton()
        context = {'servers': servers, 'instance': instance}
        self.render_template('admin.html', context=context)


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


class UserForm(form.Form):
    active = fields.BooleanField(u'Active', [validators.Optional()])
    admin = fields.BooleanField(u'Admin', [AtLeastOneAdmin()])
    usernames = StringListField(u'Usernames', validators=[validators.Optional(), UniqueUsernames()])

    def __init__(self, user=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.user = user


class UsersHandler(PagingHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self):
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            User.query_all(), User.query_all_reverse(), RESULTS_PER_PAGE
        )
        context = {'users': results, 'previous_cursor': previous_cursor, 'next_cursor': next_cursor}
        self.render_template('users.html', context=context)


class UserEditHandler(MainHandlerBase):
    @authentication_required(authenticate=authenticate_admin)
    def get(self, key):
        try:
            user_key = ndb.Key(urlsafe=key)
            user = user_key.get()
            if user is None:
                self.abort(404)
            form = UserForm(user=user, obj=user)
        except Exception, e:
            logging.error(u"Error GETting user: {0}".format(e))
            self.abort(404)
        context = {'edit_user': user, 'form': form}
        self.render_template('user.html', context=context)

    @authentication_required(authenticate=authenticate_admin)
    def post(self, key):
        try:
            user_key = ndb.Key(urlsafe=key)
            user = user_key.get()
            if user is None:
                self.abort(404)
            form = UserForm(user=user, formdata=self.request.POST, obj=user)
            if form.validate():
                user.active = form.active.data
                user.admin = form.admin.data
                user.set_usernames(form.usernames.data)
                user.put()
                self.redirect(webapp2.uri_for('users'))
        except Exception, e:
            logging.error(u"Error POSTing user: {0}".format(e))
            self.abort(404)
        context = {'edit_user': user, 'form': form}
        self.render_template('user.html', context=context)


class UserRemoveHandler(MainHandlerBase):
    @authentication_required(authenticate=authenticate_admin)
    def post(self, key):
        try:
            user_key = ndb.Key(urlsafe=key)
            user = user_key.get()
            if user is None:
                self.abort(404)
            if user.admin:
                self.abort(405)  # Method Not Allowed
            user.key.delete()
        except Exception, e:
            logging.error(u"Error removing user: {0}".format(e))
        self.redirect(webapp2.uri_for('users'))


class ValidTimezone(object):
    def __call__(self, form, field):
        timezone = field.data
        try:
            pytz.timezone(timezone)
        except:
            raise validators.ValidationError("Not a valid timezone".format(timezone))


class UserProfileForm(form.Form):
    email = fields.StringField(u'Email', validators=[validators.Optional(), validators.Email(message=u'Invalid email address.')])
    nickname = fields.StringField(u'Nickname', validators=[validators.Optional()])
    timezone_name = fields.SelectField(u'Timezone', choices=TIMEZONE_CHOICES, validators=[ValidTimezone()])


class UniqueUsername(object):
    def __call__(self, form, field):
        username = field.data
        u = User.lookup(username=username)
        if u is not None:
            raise validators.ValidationError("Username '{0}' is already assigned to a user".format(username))


class UsernameClaimForm(form.Form):
    username = fields.StringField(u'Username', validators=[validators.DataRequired(), UniqueUsername()])


class UserProfileHandler(MainHandlerBase):
    @authentication_required(authenticate=authenticate)
    def get(self):
        next_url = self.request.params.get('next_url', webapp2.uri_for('main'))
        user = self.request.user
        form = UserProfileForm(obj=user)
        claim_form = UsernameClaimForm()
        context = {'edit_user': user, 'form': form, 'claim_form': claim_form, 'next_url': next_url}
        self.render_template('user_profile.html', context=context)

    @authentication_required(authenticate=authenticate)
    def post(self):
        next_url = self.request.params.get('next_url', webapp2.uri_for('main'))
        user = self.request.user
        form = UserProfileForm(self.request.POST, user)
        if form.validate():
            user.email = form.email.data
            user.nickname = form.nickname.data
            user.timezone_name = form.timezone_name.data
            user.put()
            self.redirect(next_url)
        claim_form = UsernameClaimForm()
        context = {'edit_user': user, 'form': form, 'claim_form': claim_form, 'next_url': next_url}
        self.render_template('user_profile.html', context=context)


class UsernameClaimHandler(MainHandlerBase):
    @authentication_required(authenticate=authenticate)
    def post(self):
        next_url = self.request.params.get('next_url', webapp2.uri_for('user_profile'))
        form = UsernameClaimForm(self.request.POST)
        if form.validate():
            username = form.username.data
            UsernameClaim.get_or_create(username=username, user_key=self.request.user.key)
        self.redirect(next_url)


class ServersHandler(PagingHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self):
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            Server.query_all(), Server.query_all_reverse(), RESULTS_PER_PAGE
        )
        context = {'servers': results, 'previous_cursor': previous_cursor, 'next_cursor': next_cursor}
        self.render_template('servers.html', context=context)


class ServerForm(form.Form):
    name = fields.StringField(u'Name', [validators.Required()])
    address = fields.StringField(u'Address', [validators.Optional()])


class ServerCreateHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self):
        form = ServerForm()
        context = {'form': form}
        self.render_template('server_create.html', context=context)

    @authentication_required(authenticate=authenticate_admin)
    def post(self):
        try:
            form = ServerForm(formdata=self.request.POST)
            if form.validate():
                Server.create(name=form.name.data, address=form.address.data)
                self.redirect(webapp2.uri_for('servers'))
        except Exception, e:
            logging.error(u"Error POSTing server: {0}".format(e))
            self.abort(404)
        context = {'form': form}
        self.render_template('server_create.html', context=context)


class ServerEditHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self, key):
        try:
            server_key = ndb.Key(urlsafe=key)
            server = server_key.get()
            if server is None:
                self.abort(404)
            form = ServerForm(obj=server)
        except Exception, e:
            logging.error(u"Error GETting server: {0}".format(e))
            self.abort(404)
        context = {'edit_server': server, 'form': form}
        self.render_template('server.html', context=context)

    @authentication_required(authenticate=authenticate_admin)
    def post(self, key):
        try:
            server_key = ndb.Key(urlsafe=key)
            server = server_key.get()
            if server is None:
                self.abort(404)
            form = ServerForm(formdata=self.request.POST, obj=server)
            if form.validate():
                server.name = form.name.data
                server.address = form.address.data
                server.put()
                self.redirect(webapp2.uri_for('servers'))
        except Exception, e:
            logging.error(u"Error POSTing server: {0}".format(e))
            self.abort(404)
        context = {'edit_server': server, 'form': form}
        self.render_template('server.html', context=context)


class ServerDeactivateHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def post(self, key):
        try:
            server_key = ndb.Key(urlsafe=key)
            server = server_key.get()
            if server is None:
                self.abort(404)
            server.active = False
            server.put()
        except Exception, e:
            logging.error(u"Error deactivating server: {0}".format(e))
        self.redirect(webapp2.uri_for('servers'))


class InstanceForm(form.Form):
    zone = fields.SelectField(u'Zone', validators=[validators.DataRequired()])

    def __init__(self, *args, **kwargs):
        super(InstanceForm, self).__init__(*args, **kwargs)
        self.zone.choices = [(z, z) for z in gce.get_zones() or []]


class InstanceConfigureHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self):
        instance = gce.Instance.singleton()
        form = InstanceForm(obj=instance)
        context = {'form': form, 'instance': instance}
        self.render_template('instance_configure.html', context=context)

    @authentication_required(authenticate=authenticate_admin)
    def post(self):
        form = InstanceForm(self.request.POST)
        if form.validate():
            instance = gce.Instance.singleton()
            instance.zone=form.zone.data
            instance.put()
            self.redirect(webapp2.uri_for('admin'))
        context = {'form': form}
        self.render_template('instance_configure.html', context=context)


class InstanceStartHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def post(self):
        instance = gce.Instance.singleton()
        instance.start()
        self.redirect(webapp2.uri_for('admin'))


class InstanceStopHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def post(self):
        instance = gce.Instance.singleton()
        instance.stop()
        self.redirect(webapp2.uri_for('admin'))


coal_config = lib_config.register('COAL', {
    'SECRET_KEY': 'a_secret_string',
    'COOKIE_MAX_AGE': 2592000,
    'OAUTH_TOKEN_EXPIRES_IN': 3600
})


application = webapp2.WSGIApplication(
    [
        RedirectRoute('/', handler=MainHandler, name="main"),
        RedirectRoute('/players/claim', handler=UsernameClaimHandler, strict_slash=True, name="username_claim"),
        RedirectRoute('/chats', handler=ChatsHandler, strict_slash=True, name="naked_chats"),
        RedirectRoute('/players', handler=PlayersHandler, strict_slash=True, name="naked_players"),
        RedirectRoute('/sessions', handler=PlaySessionsHandler, strict_slash=True, name="naked_play_sessions"),
        RedirectRoute('/screenshots', handler=ScreenShotsHandler, strict_slash=True, name="naked_screenshots_lol"),
        RedirectRoute('/screenshots/<key>/create_blur', handler=ScreenShotBlurHandler, strict_slash=True, name="naked_screenshots_blur"),
        RedirectRoute('/servers/<server_key>', handler=HomeHandler, name="home"),
        RedirectRoute('/servers/<server_key>/chats', handler=ChatsHandler, strict_slash=True, name="chats"),
        RedirectRoute('/servers/<server_key>/players', handler=PlayersHandler, strict_slash=True, name="players"),
        RedirectRoute('/servers/<server_key>/sessions', handler=PlaySessionsHandler, strict_slash=True, name="play_sessions"),
        RedirectRoute('/servers/<server_key>/screenshot_upload', handler=ScreenShotUploadHandler, strict_slash=True, name="screenshot_upload"),
        RedirectRoute('/servers/<server_key>/screenshot_uploaded', handler=ScreenShotUploadedHandler, strict_slash=True, name="screenshot_uploaded"),
        RedirectRoute('/servers/<server_key>/screenshots', handler=ScreenShotsHandler, strict_slash=True, name="screenshots"),
        RedirectRoute('/servers/<server_key>/screenshots/<key>/remove', handler=ScreenShotRemoveHandler, strict_slash=True, name="screenshot_remove"),
        RedirectRoute('/profile', handler=UserProfileHandler, strict_slash=True, name="user_profile"),
        RedirectRoute('/admin', handler=AdminHandler, strict_slash=True, name="admin"),
        RedirectRoute('/admin/users', handler=UsersHandler, strict_slash=True, name="users"),
        RedirectRoute('/admin/users/<key>', handler=UserEditHandler, strict_slash=True, name="user"),
        RedirectRoute('/admin/users/<key>/remove', handler=UserRemoveHandler, strict_slash=True, name="user_remove"),
        RedirectRoute('/admin/server_create', handler=ServerCreateHandler, strict_slash=True, name="server_create"),
        RedirectRoute('/admin/servers', handler=ServersHandler, strict_slash=True, name="servers"),
        RedirectRoute('/admin/servers/<key>', handler=ServerEditHandler, strict_slash=True, name="server"),
        RedirectRoute('/admin/servers/<key>/deactivate', handler=ServerDeactivateHandler, strict_slash=True, name="server_deactivate"),
        RedirectRoute('/admin/instance/configure', handler=InstanceConfigureHandler, strict_slash=True, name="instance_configure"),
        RedirectRoute('/admin/instance/start', handler=InstanceStartHandler, strict_slash=True, name="instance_start"),
        RedirectRoute('/admin/instance/stop', handler=InstanceStopHandler, strict_slash=True, name="instance_stop"),
    ],
    config={
        'webapp2_extras.sessions': {
            'secret_key': coal_config.SECRET_KEY,
            'cookie_args': {'max_age': coal_config.COOKIE_MAX_AGE}
        },
        'webapp2_extras.auth': {'user_model': 'models.User', 'token_max_age': coal_config.COOKIE_MAX_AGE}
    },
    debug=not ON_SERVER
)

from user_auth import routes as user_auth_routes
from api import routes as api_routes
from image import routes as image_routes
from oauth import routes as oauth_routes
routes = user_auth_routes + api_routes + image_routes + oauth_routes
for route in routes:
     application.router.add(route)
