import datetime
import json
import logging
import urllib2
from urlparse import urlparse

from google.appengine.api import users, urlfetch

import webapp2
from webapp2_extras import auth, sessions
from webapp2_extras.routes import RedirectRoute

from base_handler import JinjaHandler
from config import coal_config
from models import User, ScreenShot


def get_gae_callback_uri(handler, next_url=None):
    try:
        callback_url = handler.uri_for('gae_login_callback')
    except:
        callback_url = '/gae_login_callback'
    if next_url:
        callback_url = "{0}?next_url={1}".format(callback_url, urllib2.quote(next_url))
    return callback_url


def get_gae_login_uri(handler, next_url=None):
    return users.create_login_url(get_gae_callback_uri(handler, next_url=next_url))


def get_ia_callback_uri(handler, next_url=None):
    try:
        callback_url = handler.uri_for('ia_login_callback', _full=True)
    except:
        callback_url = '/ia_login_callback'
    if next_url:
        callback_url = "{0}?next_url={1}".format(callback_url, urllib2.quote(next_url))
    return callback_url


def get_login_uri(handler, next_url=None):
    query_params = {}
    if next_url is not None:
        query_params['next_url'] = next_url
    return handler.uri_for('login', **query_params)


def authenticate(handler, required=True, admin=False):
    next_url = handler.request.path_qs
    user = handler.user
    if user is not None:
        update = False
        if admin and not user.admin and User.query().filter(User.admin == True).count(keys_only=True, limit=1) == 0:
            user.admin = True
            user.active = True
            update = True
        if update:
            user.put()
    if required and not (user and user.active):
        handler.redirect(get_login_uri(handler, next_url), abort=True)
    if admin and not user.admin:
        handler.redirect(get_login_uri(handler, next_url), abort=True)
    return user


def authenticate_public(handler):
    return authenticate(handler, required=False, admin=False)


def authenticate_admin(handler):
    return authenticate(handler, required=True, admin=True)


class UserBase(object):
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
        return self.auth.store.user_model.get_by_id(self.user_info['user_id']) if self.user_info else None


class UserHandler(JinjaHandler, UserBase):
    @property
    def logged_in(self):
        return self.user is not None

    def logout(self, redirect_url=None):
        redirect_url = redirect_url or webapp2.uri_for('main')
        self.auth.unset_session()
        self.redirect(redirect_url)

    def dispatch(self):
        try:
            super(UserHandler, self).dispatch()
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
        server = template_context['server'] = template_context.get('server', None) or getattr(self.request, 'server', None)
        if server is not None:
            bg_img = ScreenShot.random(server.key)
            if bg_img is not None:
                template_context['bg_img'] = bg_img.blurred_image_serving_url
        return template_context


class LoginHandler(UserHandler):
    def get(self):
        next_url = self.request.params.get('next_url', None)
        ia_redirect_uri = get_ia_callback_uri(self, next_url)
        gae_login_uri = get_gae_login_uri(self, next_url)
        context = {
            'ia_redirect_uri': ia_redirect_uri,
            'gae_login_uri': gae_login_uri
        }
        self.render_template('login.html', context=context)


class AuthHandler(UserHandler):
    def login_auth_id(self, auth_id, is_admin=False, email=None, nickname=None):
        next_url = self.request.params.get('next_url', None)
        user = self.auth.store.user_model.get_by_auth_id(auth_id)
        if user:
            # Existing user
            self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
        else:
            if not self.logged_in:
                # New user
                ok, user = self.auth.store.user_model.create_user(auth_id, email=email, nickname=nickname)
                if ok:
                    self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
                    next_url = webapp2.uri_for('user_profile', next_url=next_url or webapp2.uri_for('main'))
                else:
                    user = None
                    self.auth.unset_session()
                    logging.error('create_user() returned False with strings: %s' % user)
            else:
                # Existing logged-in user with new auth_id
                user = self.user
                if auth_id not in user.auth_ids:
                    user.auth_ids.append(auth_id)
                user.email = user.email or email
                user.nickname = user.nickname or nickname
        if is_admin and not (user.active and user.admin):
            user.active = True
            user.admin = True
        user.last_login = datetime.datetime.now()
        user.put()
        if not (user and user.active and next_url):
            next_url = webapp2.uri_for('main')
        self.redirect(next_url)


class GoogleAppEngineUserHandler(AuthHandler):
    def login_callback(self):
        gae_user = users.get_current_user()
        auth_id = User.get_gae_user_auth_id(gae_user=gae_user) if gae_user else None
        is_admin = users.is_current_user_admin()
        email = gae_user.email() if gae_user else None
        nickname = gae_user.nickname() if gae_user else None
        self.login_auth_id(auth_id, is_admin=is_admin, email=email, nickname=nickname)


class IndieAuthUserHandler(AuthHandler):
    def login_callback(self):
        token = self.request.params.get('token', None)
        url = "http://indieauth.com/verify?token={0}".format(token)
        response = urlfetch.fetch(url)
        auth_data = json.loads(response.content)
        error = auth_data.get('error', None)
        error_description = auth_data.get('error', None)
        if error is not None:
            message = "IndieAuth Error {0}: {1}".format(error, error_description)
            logging.error(message)
            raise Exception(message)
        me = auth_data.get('me', None)
        if me:
            me = urlparse(me).netloc or me
        auth_id = User.get_indie_auth_id(me=me)
        self.login_auth_id(auth_id, nickname=me)


routes = [
    RedirectRoute('/login', handler='user_auth.LoginHandler', name='login'),
    RedirectRoute('/logout', handler='user_auth.UserHandler:logout', name='logout'),
    RedirectRoute('/gae_login_callback', handler='user_auth.GoogleAppEngineUserHandler:login_callback', name='gae_login_callback'),
    RedirectRoute('/ia_login_callback', handler='user_auth.IndieAuthUserHandler:login_callback', name='ia_login_callback')
]
