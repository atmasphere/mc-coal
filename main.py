import logging

from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.ext.ndb import Cursor
from google.appengine.ext.webapp import blobstore_handlers

import webapp2

from webapp2_extras.routes import RedirectRoute

from wtforms import form, fields, validators, widgets

from agar.auth import authentication_required
from agar.env import on_production_server

from base_handler import uri_for_pagination
import channel
from config import coal_config
from models import get_whitelist_user, User, Player, LogLine, PlaySession, ScreenShot, Command, Server, UsernameClaim
import search
from user_auth import get_login_uri, UserBase, UserHandler, authenticate, authenticate_admin, authenticate_public


class HomeHandler(UserHandler):
    @authentication_required(authenticate=authenticate_public)
    def get(self):
        server_key = Server.global_key()
        user = self.request.user
        if user and user.active:
            open_sessions_query = PlaySession.query_latest_open(server_key)
            # Get open sessions
            playing_usernames = []
            open_sessions = []
            for open_session in open_sessions_query:
                if open_session.username and open_session.username not in playing_usernames:
                    playing_usernames.append(open_session.username)
                    open_sessions.append(open_session)
            # Get new chats
            new_chats_query = LogLine.query_latest_events()
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
                'chats_cursor': chats_cursor,
                'logout_url': webapp2.uri_for('logout')
            }
        elif user:  # Logged in, but not on white-list and active
            context = {'logout_url': webapp2.uri_for('logout')}
        else:  # Not logged in
            context = {'login_url': get_login_uri(self)}
        self.render_template('home.html', context=context)


class PagingHandler(UserHandler):
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
    def get(self):
        self.request.user.record_chat_view()
        query_string = self.request.get('q', None)
        # Search
        if query_string:
            page = 0
            cursor = self.request.get('cursor', None)
            if cursor and cursor.startswith('PAGE_'):
                page = int(cursor.strip()[5:])
            offset = page*coal_config.RESULTS_PER_PAGE
            results, number_found, _ = search.search_log_lines('chat:{0}'.format(query_string), limit=coal_config.RESULTS_PER_PAGE, offset=offset)
            previous_cursor = next_cursor = None
            if page > 0:
                previous_cursor = u'PAGE_{0}&q={1}'.format(page - 1 if page > 0 else 0, query_string)
            if number_found > offset + coal_config.RESULTS_PER_PAGE:
                next_cursor = u'PAGE_{0}&q={1}'.format(page + 1, query_string)
        # Latest
        else:
            results, previous_cursor, next_cursor = self.get_results_with_cursors(
                LogLine.query_latest_events(), LogLine.query_oldest_events(), coal_config.RESULTS_PER_PAGE
            )

        context = {'chats': results, 'query_string': query_string or ''}

        if self.request.is_xhr:
            self.render_xhr_response(context, next_cursor)
        else:
            self.render_html_response(context, next_cursor, previous_cursor)

    def render_xhr_response(self, context, next_cursor):
        if next_cursor:
            context.update({
                'next_uri': uri_for_pagination('chats', cursor=next_cursor)
            })
        self.response.headers['Content-Type'] = 'text/javascript'
        self.render_template('chats.js', context=context)

    def render_html_response(self, context, next_cursor, previous_cursor):
        user = self.request.user
        channel_token = channel.token_for_user(user)
        context.update({
            'next_cursor': next_cursor,
            'previous_cursor': previous_cursor,
            'channel_token': channel_token,
            'username': user.play_name,
        })
        self.render_template('chats.html', context=context)

    @authentication_required(authenticate=authenticate)
    def post(self):
        server_key = Server.global_key()
        try:
            user = self.request.user
            if not (user and user.active):
                self.abort(404)
            form = ChatForm(self.request.POST)
            if form.validate():
                chat = u"/say {0}".format(form.chat.data)
                Command.push(server_key, user.play_name, chat)
        except Exception, e:
            logging.error(u"Error POSTing chat: {0}".format(e))
            self.abort(500)
        self.response.set_status(201)


class PlayersHandler(PagingHandler):
    @authentication_required(authenticate=authenticate)
    def get(self):
        server_key = Server.global_key()
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            Player.query_all_reverse(server_key), Player.query_all(server_key), coal_config.RESULTS_PER_PAGE
        )
        context = {'players': results, 'previous_cursor': previous_cursor, 'next_cursor': next_cursor}
        self.render_template('players.html', context=context)


class PlaySessionsHandler(PagingHandler):
    @authentication_required(authenticate=authenticate)
    def get(self):
        server_key = Server.global_key()
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            PlaySession.query_latest(server_key), PlaySession.query_oldest(server_key), coal_config.RESULTS_PER_PAGE
        )
        context = {'play_sessions': results, 'previous_cursor': previous_cursor, 'next_cursor': next_cursor}
        self.render_template('play_sessions.html', context=context)


class ScreenShotUploadHandler(UserHandler):
    @authentication_required(authenticate=authenticate)
    def get(self):
        url = webapp2.uri_for('screen_shot_uploaded')
        upload_url = blobstore.create_upload_url(url)
        context = {'upload_url': upload_url}
        self.render_template('screen_shot_upload.html', context=context)


class ScreenShotUploadedHandler(blobstore_handlers.BlobstoreUploadHandler, UserBase):
    @authentication_required(authenticate=authenticate)
    def post(self):
        blob_info = self.get_uploads('file')[0]
        ScreenShot.create(Server.global_key(), self.request.user, blob_info=blob_info)
        self.redirect(webapp2.uri_for('screen_shots'))


class ScreenShotsHandler(PagingHandler):
    @authentication_required(authenticate=authenticate)
    def get(self):
        server_key = Server.global_key()
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            ScreenShot.query_latest(server_key), ScreenShot.query_oldest(server_key), 5
        )
        context = {'screen_shots': results, 'previous_cursor': previous_cursor, 'next_cursor': next_cursor}
        self.render_template('screen_shots.html', context=context)


class ScreenShotRemoveHandler(UserHandler):
    @authentication_required(authenticate=authenticate)
    def post(self, key):
        try:
            screen_shot_key = ndb.Key(urlsafe=key)
            screen_shot = screen_shot_key.get()
            if screen_shot is not None:
                screen_shot.key.delete()
        except Exception, e:
            logging.error(u"Error removing screen shot: {0}".format(e))
        self.redirect(webapp2.uri_for('screen_shots'))


class AdminHandler(PagingHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self):
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            User.query_by_email(), User.query_by_email_reverse(), coal_config.RESULTS_PER_PAGE
        )
        servers = []
        for server in Server.query():
            servers.append(server)
        context = {'servers': servers}
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


class UserForm(form.Form):
    active = fields.BooleanField(u'Active', [validators.Optional()])
    admin = fields.BooleanField(u'Admin', [validators.Optional()])
    usernames = StringListField(u'Usernames', validators=[validators.Optional(), UniqueUsernames()])

    def __init__(self, user=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.user = user


class UsersHandler(PagingHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self):
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            User.query_by_email(), User.query_by_email_reverse(), coal_config.RESULTS_PER_PAGE
        )
        context = {'users': results, 'previous_cursor': previous_cursor, 'next_cursor': next_cursor}
        self.render_template('users.html', context=context)


class UserEditHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self, key):
        try:
            user_key = ndb.Key(urlsafe=key)
            user = user_key.get()
            if user is None or get_whitelist_user(user.email) is not None:
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
            if user.white_list is not None:
                self.abort(405)  # Method Not Allowed
            form = UserForm(user=user, formdata=self.request.POST, obj=user)
            if form.validate():
                user.active = form.active.data
                user.admin = form.admin.data
                user.set_usernames(form.usernames.data)
                user.usernames = form.usernames.data
                user.put()
                self.redirect(webapp2.uri_for('users'))
        except Exception, e:
            logging.error(u"Error POSTing user: {0}".format(e))
            self.abort(404)
        context = {'edit_user': user, 'form': form}
        self.render_template('user.html', context=context)


class UserRemoveHandler(UserHandler):
    @authentication_required(authenticate=authenticate_admin)
    def post(self, key):
        try:
            user_key = ndb.Key(urlsafe=key)
            user = user_key.get()
            if user is None:
                self.abort(404)
            if user.white_list is not None:
                self.abort(405)  # Method Not Allowed
            user.key.delete()
        except Exception, e:
            logging.error(u"Error removing user: {0}".format(e))
        self.redirect(webapp2.uri_for('users'))


class UserProfileForm(form.Form):
    email = fields.StringField(u'Email', [validators.Optional(), validators.Email(message=u'Invalid email address.')])
    nickname = fields.StringField(u'Nickname', validators=[validators.Optional()])


class UniqueUsername(object):
    def __init__(self, user=None):
        self.user = user

    def __call__(self, form, field):
        username = field.data
        u = User.lookup(username=username)
        if u is not None:
            raise validators.ValidationError("Username '{0}' is already assigned to a user".format(username))


class UsernameClaimForm(form.Form):
    username = fields.StringField(u'Username', validators=[validators.DataRequired(), UniqueUsername()])


class UserProfileHandler(UserHandler):
    @authentication_required(authenticate=authenticate)
    def get(self):
        next_url = self.request.params.get('next_url', webapp2.uri_for('home'))
        user = self.request.user
        form = UserProfileForm(obj=user)
        claim_form = UsernameClaimForm()
        context = {'edit_user': user, 'form': form, 'claim_form': claim_form, 'next_url': next_url}
        self.render_template('user_profile.html', context=context)

    @authentication_required(authenticate=authenticate)
    def post(self):
        next_url = self.request.params.get('next_url', webapp2.uri_for('home'))
        user = self.request.user
        form = UserProfileForm(self.request.POST, user)
        if form.validate():
            user.email = form.email.data
            user.nickname = form.nickname.data
            user.put()
            self.redirect(next_url)
        claim_form = UsernameClaimForm()
        context = {'edit_user': user, 'form': form, 'claim_form': claim_form, 'next_url': next_url}
        self.render_template('user_profile.html', context=context)


class UsernameClaimHandler(UserHandler):
    @authentication_required(authenticate=authenticate)
    def post(self):
        next_url = self.request.params.get('next_url', webapp2.uri_for('user_profile'))
        form = UsernameClaimForm(self.request.POST)
        if form.validate():
            username = form.username.data
            UsernameClaim.get_or_create(username=username, user_key=self.request.user.key)
        self.redirect(next_url)


application = webapp2.WSGIApplication(
    [
        RedirectRoute('/', handler=HomeHandler, name="home"),
        RedirectRoute('/chats', handler=ChatsHandler, strict_slash=True, name="chats"),
        RedirectRoute('/players/claim', handler=UsernameClaimHandler, strict_slash=True, name="username_claim"),
        RedirectRoute('/players', handler=PlayersHandler, strict_slash=True, name="players"),
        RedirectRoute('/sessions', handler=PlaySessionsHandler, strict_slash=True, name="play_sessions"),
        RedirectRoute('/screen_shot_upload', handler=ScreenShotUploadHandler, strict_slash=True, name="screen_shot_upload"),
        RedirectRoute('/screen_shot_uploaded', handler=ScreenShotUploadedHandler, strict_slash=True, name="screen_shot_uploaded"),
        RedirectRoute('/screen_shots', handler=ScreenShotsHandler, strict_slash=True, name="screen_shots"),
        RedirectRoute('/screen_shots/<key>/remove', handler=ScreenShotRemoveHandler, strict_slash=True, name="screen_shot_remove"),
        RedirectRoute('/profile', handler=UserProfileHandler, strict_slash=True, name="user_profile"),
        RedirectRoute('/admin', handler=AdminHandler, strict_slash=True, name="admin"),
        RedirectRoute('/admin/users', handler=UsersHandler, strict_slash=True, name="users"),
        RedirectRoute('/admin/users/<key>', handler=UserEditHandler, strict_slash=True, name="user"),
        RedirectRoute('/admin/users/<key>/remove', handler=UserRemoveHandler, strict_slash=True, name="user_remove")
    ],
    config={
        'webapp2_extras.sessions': {
            'secret_key': coal_config.SECRET_KEY,
            'cookie_args': {'max_age': coal_config.COOKIE_MAX_AGE}
        },
        'webapp2_extras.auth': {'user_model': 'models.User', 'token_max_age': coal_config.COOKIE_MAX_AGE}
    },
    debug=not on_production_server
)

from user_auth import routes as user_auth_routes
from api import routes as api_routes
from image import routes as image_routes
from oauth import routes as oauth_routes
routes = user_auth_routes + api_routes + image_routes + oauth_routes
for route in routes:
     application.router.add(route)
