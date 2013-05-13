import datetime
import logging
import urllib2

from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.ext.ndb import Cursor
from google.appengine.ext.webapp import blobstore_handlers

import webapp2

from webapp2_extras import auth, sessions, jinja2
from webapp2_extras.routes import RedirectRoute

from wtforms import form, fields, validators

from agar.auth import authentication_required
from agar.env import on_production_server

import channel
from config import coal_config
from filters import FILTERS
from models import get_whitelist_user, User, Server, Player, LogLine, PlaySession, ScreenShot, Command
import search


def uri_for_pagination(name, cursor=None):
    uri = webapp2.uri_for(name)
    if cursor is not None and cursor != 'START':
        if cursor.startswith('PAGE_0'):
            uri = u"{0}{1}{2}".format(uri, '&' if '?' in uri else '?', cursor[7:])
        else:
            uri = u"{0}{1}cursor={2}".format(uri, '&' if '?' in uri else '?', cursor)
    return uri


class JinjaHandler(webapp2.RequestHandler):
    _filters = FILTERS
    _globals = {
        'uri_for': webapp2.uri_for,
        'uri_for_pagination': uri_for_pagination
    }

    @webapp2.cached_property
    def jinja2(self):
        return jinja2.get_jinja2(factory=self.jinja2_factory)

    def jinja2_factory(self, app):
        j = jinja2.Jinja2(app)
        j.environment.filters.update(self._filters)
        j.environment.globals.update(self._globals)
        return j

    def get_template_context(self, context=None):
        return context

    def render_template(self, filename, context={}):
        context = self.get_template_context(context)
        self.response.write(self.jinja2.render_template(filename, **context))


def get_callback_url(handler, next_url=None):
    if next_url is None:
        next_url = handler.request.path_qs
    callback_url = handler.uri_for('login_callback')
    if next_url:
        callback_url = "{0}?next_url={1}".format(callback_url, urllib2.quote(next_url))
    return callback_url


def get_login_url(handler, next_url=None):
    return users.create_login_url(get_callback_url(handler, next_url=next_url))


def authenticate(handler, required=True, admin=False):
    user = handler.user
    if user is not None:
        update = False
        wlu = get_whitelist_user(user.email)
        if wlu:
            if not user.active:
                user.active = True
                update = True
            if user.admin != wlu['admin']:
                user.admin = wlu['admin']
                update = True
            if user.username != wlu['username']:
                user.username = wlu['username']
                update = True
        if update:
            user.put()
    if required and not (user and user.active):
        handler.redirect(webapp2.uri_for('home'), abort=True)
    if admin and not user.admin:
        handler.redirect(webapp2.uri_for('home'), abort=True)
    return user


def authenticate_public(handler):
    return authenticate(handler, required=False, admin=False)


def authenticate_admin(handler):
    return authenticate(handler, required=True, admin=True)


class UserAwareHandler(JinjaHandler):
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
        redirect_url = redirect_url or webapp2.uri_for('home')
        self.auth.unset_session()
        logout_url = users.create_logout_url(redirect_url)
        self.redirect(logout_url)

    def dispatch(self):
        try:
            super(UserAwareHandler, self).dispatch()
        finally:
            self.session_store.save_sessions(self.response)

    def get_template_context(self, context=None):
        template_context = dict()
        if context:
            template_context.update(context)
        template_context['flashes'] = self.session.get_flashes()
        template_context['request'] = self.request
        template_context['user'] = self.user
        template_context['config'] = coal_config
        template_context['server'] = Server.global_key().get()
        bg_img = ScreenShot.random()
        if bg_img is not None:
            template_context['bg_img'] = bg_img.blurred_image_serving_url
        return template_context


class GoogleAppEngineUserAuthHandler(UserAwareHandler):
    def login_callback(self):
        next_url = self.request.params.get('next_url', '')
        user = None
        gae_user = users.get_current_user()
        logging.info("GAE_USER: {0}".format(gae_user.email()))
        if gae_user:
            auth_id = User.get_gae_user_auth_id(gae_user=gae_user)
            user = self.auth.store.user_model.get_by_auth_id(auth_id)
            if user:
                logging.info("EXISTING_USER: {0}".format(user.email))
                # existing user. just log them in.
                self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
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
                    logging.info("NEW_USER")
                    ok, user = self.auth.store.user_model.create_user(
                        auth_id,
                        email=gae_user.email(),
                        nickname=gae_user.nickname(),
                        active=users.is_current_user_admin(),
                        admin=users.is_current_user_admin(),
                        last_login=datetime.datetime.now()
                    )
                    if ok:
                        self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
                    else:
                        logging.error('create_user() returned False with strings: %s' % user)
                        user = None
                        self.auth.unset_session()
        if not (user and user.active):
            next_url = webapp2.uri_for('home')
        self.redirect(next_url or webapp2.uri_for('home'))


class BaseHander(UserAwareHandler):
    def head(self, *args):
        """Head is used by Twitter. If not there the tweet button shows 0"""
        pass


class HomeHandler(BaseHander):
    @authentication_required(authenticate=authenticate_public)
    def get(self):
        user = self.request.user
        if user and user.active:
            open_sessions_query = PlaySession.query_latest_open()
            # Get open sessions
            playing_usernames = []
            open_sessions = []
            for open_session in open_sessions_query:
                if open_session.username and open_session.username not in playing_usernames:
                    playing_usernames.append(open_session.username)
                    open_sessions.append(open_session)
            # Get new chats
            new_chats_query = LogLine.query_latest_chats()
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
            context = {'login_url': get_login_url(self)}
        self.render_template('home.html', context=context)


class PagingHandler(BaseHander):
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
    chat = fields.TextField(u'Chat', validators=[validators.DataRequired()])


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
                LogLine.query_latest_chats(), LogLine.query_oldest_chats(), coal_config.RESULTS_PER_PAGE
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
        channel_token = channel.token_for_user(self.request.user)
        context.update({
            'next_cursor': next_cursor,
            'previous_cursor': previous_cursor,
            'channel_token': channel_token,
            'username': self.request.user.username,
        })
        self.render_template('chats.html', context=context)

    @authentication_required(authenticate=authenticate)
    def post(self):
        try:
            user = self.request.user
            if not (user and user.active):
                self.abort(404)
            form = ChatForm(self.request.POST)
            if form.validate():
                chat = u"/say {0}".format(form.chat.data)
                Command.push(user.username, chat)
        except Exception, e:
            logging.error(u"Error POSTing chat: {0}".format(e))
            self.abort(500)
        self.response.set_status(201)


class PlayersHandler(PagingHandler):
    @authentication_required(authenticate=authenticate)
    def get(self):
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            Player.query_all_reverse(), Player.query_all(), coal_config.RESULTS_PER_PAGE
        )
        context = {'players': results, 'previous_cursor': previous_cursor, 'next_cursor': next_cursor}
        self.render_template('players.html', context=context)


class PlaySessionsHandler(PagingHandler):
    @authentication_required(authenticate=authenticate)
    def get(self):
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            PlaySession.query_latest(), PlaySession.query_oldest(), coal_config.RESULTS_PER_PAGE
        )
        context = {'play_sessions': results, 'previous_cursor': previous_cursor, 'next_cursor': next_cursor}
        self.render_template('play_sessions.html', context=context)


class ScreenShotUploadHandler(BaseHander):
    @authentication_required(authenticate=authenticate)
    def get(self):
        url = webapp2.uri_for('screen_shot_uploaded')
        upload_url = blobstore.create_upload_url(url)
        context = {'upload_url': upload_url}
        self.render_template('screen_shot_upload.html', context=context)


class ScreenShotUploadedHandler(blobstore_handlers.BlobstoreUploadHandler):
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
        user_info = self.auth.get_user_by_session()
        return user_info

    @webapp2.cached_property
    def user(self):
        user = self.auth.store.user_model.get_by_id(self.user_info['user_id']) if self.user_info else None
        return user

    @authentication_required(authenticate=authenticate)
    def post(self):
        blob_info = self.get_uploads('file')[0]
        ScreenShot.create(self.request.user.username, blob_info=blob_info)
        self.redirect(webapp2.uri_for('screen_shots'))


class ScreenShotsHandler(PagingHandler):
    @authentication_required(authenticate=authenticate)
    def get(self):
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            ScreenShot.query_latest(), ScreenShot.query_oldest(), coal_config.RESULTS_PER_PAGE
        )
        context = {'screen_shots': results, 'previous_cursor': previous_cursor, 'next_cursor': next_cursor}
        self.render_template('screen_shots.html', context=context)


class ScreenShotRemoveHandler(BaseHander):
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


class UserForm(form.Form):
    active = fields.BooleanField(u'Active', [validators.Optional()])
    admin = fields.BooleanField(u'Admin', [validators.Optional()])
    username = fields.TextField(u'Username', validators=[validators.Optional()])


class UsersHandler(PagingHandler):
    @authentication_required(authenticate=authenticate_admin)
    def get(self):
        results, previous_cursor, next_cursor = self.get_results_with_cursors(
            User.query_by_email(), User.query_by_email_reverse(), coal_config.RESULTS_PER_PAGE
        )
        context = {'users': results, 'previous_cursor': previous_cursor, 'next_cursor': next_cursor}
        self.render_template('users.html', context=context)


class UserEditHandler(BaseHander):
    @authentication_required(authenticate=authenticate_admin)
    def get(self, key):
        try:
            user_key = ndb.Key(urlsafe=key)
            user = user_key.get()
            if user is None or get_whitelist_user(user.email) is not None:
                self.abort(404)
            form = UserForm(obj=user)
        except Exception, e:
            logging.error(u"Error POSTing user: {0}".format(e))
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
            form = UserForm(self.request.POST, user)
            if form.validate():
                user.active = form.active.data
                user.admin = form.admin.data
                user.username = form.username.data
                user.put()
                self.redirect(webapp2.uri_for('users'))
        except Exception, e:
            logging.error(u"Error POSTing user: {0}".format(e))
            self.abort(404)
        context = {'edit_user': user, 'form': form}
        self.render_template('user.html', context=context)


class UserRemoveHandler(BaseHander):
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


application = webapp2.WSGIApplication(
    [
        RedirectRoute('/login_callback', handler='main.GoogleAppEngineUserAuthHandler:login_callback', name='login_callback'),
        RedirectRoute('/logout', handler='main.GoogleAppEngineUserAuthHandler:logout', name='logout'),
        RedirectRoute('/', handler=HomeHandler, name="home"),
        RedirectRoute('/chats', handler=ChatsHandler, strict_slash=True, name="chats"),
        RedirectRoute('/players', handler=PlayersHandler, strict_slash=True, name="players"),
        RedirectRoute('/sessions', handler=PlaySessionsHandler, strict_slash=True, name="play_sessions"),
        RedirectRoute('/screen_shot_upload', handler=ScreenShotUploadHandler, strict_slash=True, name="screen_shot_upload"),
        RedirectRoute('/screen_shot_uploaded', handler=ScreenShotUploadedHandler, strict_slash=True, name="screen_shot_uploaded"),
        RedirectRoute('/screen_shots', handler=ScreenShotsHandler, strict_slash=True, name="screen_shots"),
        RedirectRoute('/screen_shot/<key>/remove', handler=ScreenShotRemoveHandler, strict_slash=True, name="screen_shot_remove"),
        RedirectRoute('/users', handler=UsersHandler, strict_slash=True, name="users"),
        RedirectRoute('/user/<key>', handler=UserEditHandler, strict_slash=True, name="user"),
        RedirectRoute('/user/<key>/remove', handler=UserRemoveHandler, strict_slash=True, name="user_remove")
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
