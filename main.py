import logging
import jinja2
import os
import urllib2

from google.appengine.api import users

import webapp2

from webapp2_extras import auth, sessions
from webapp2_extras.routes import RedirectRoute

from agar.auth import authentication_required
from agar.config import Config
from agar.env import on_production_server

from models import User


class COALConfig(Config):
    _prefix = "COAL"

    USER_WHITELIST = []
    API_PASSWORD = ''
    SECRET_KEY = ''

config = COALConfig.get_config()


class JinjaHandler(webapp2.RequestHandler):
    _filters = {}
    _globals = {'uri_for': webapp2.uri_for}

    @webapp2.cached_property
    def jinja2(self):
        return jinja2.get_jinja2(factory=self.jinja2_factory)

    def jinja2_factory(self, app):
        j = jinja2.Jinja2(app)
        j.environment.filters.update(self._filters)
        j.environment.globals.update(self._globals)
        j.environment.loader = jinja2.FileSystemLoader(os.path.dirname(__file__))
        return j

    def get_template_args(self, template_args=None):
        return template_args

    def render_template(self, filename, context={}):
        context = self.get_template_args(context)
        if not on_production_server:
            logging.info("Template values: {0}".format(context))
        self.response.write(self.jinja2.render_template(filename, **context))


def get_callback_url(handler, next_url=None):
    if next_url is None:
        next_url = handler.request.path_qs
    callback_url = handler.uri_for('login_callback')
    if next_url:
        callback_url = "{0}?next_url={1}".format(callback_url, urllib2.quote(next_url))
    return callback_url


def get_login_url(handler, next_url=None):
    callback_url = get_callback_url(handler, next_url=next_url)
    if users.get_current_user() is None:
        return users.create_login_url(callback_url)
    return callback_url


def authenticate(handler, required=True, admin=False):
    user_dict = handler.auth.get_user_by_session()
    if not user_dict:
        user = None
    else:
        user = handler.auth.store.user_model.get_by_id(user_dict['user_id'])
    if user is not None:
        allowed = None
        for wlu in config.USER_WHITELIST:
            if user.email == wlu['email']:
                allowed = wlu
                update = False
                if not user.active:
                    user.active = True
                    update = True
                if user.admin != allowed['admin']:
                    user.admin = allowed['admin']
                    update = True
                if user.username != allowed['username']:
                    user.username = allowed['username']
                    update = True
                if update:
                    user.put()
        if not allowed:
            user.active = False
            user.put()
            user = None
    if required and not user:
        handler.redirect(get_login_url(handler), abort=True)
    if admin and not user.admin:
        handler.redirect('/', abort=True)
    return user


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
        user_info = self.auth.get_user_by_session()
        return user_info

    @webapp2.cached_property
    def user(self):
        user, timestamp = self.auth.store.user_model.get_by_id(self.user_info['user_id']) if self.user_info else (None, None)
        return user

    def logged_in(self):
        return self.auth.get_user_by_session() is not None

    def logout(self, redirect_url=None):
        redirect_url = redirect_url or '/'
        self.auth.unset_session()
        logout_url = users.create_logout_url(redirect_url)
        self.redirect(logout_url)

    def dispatch(self):
        try:
            super(UserAwareHandler, self).dispatch()
        finally:
            self.session_store.save_sessions(self.response)

    def get_template_args(self, template_args=None):
        args = dict()
        if template_args:
            args.update(template_args)
        args['flashes'] = self.session.get_flashes()
        args['request'] = self.request


class GoogleAppEngineUserAuthHandler(UserAwareHandler):
    def login_callback(self):
        next_url = self.request.params.get('next_url', '')
        gae_user = users.get_current_user()
        if not gae_user:
            self.redirect(get_login_url(self, next_url=next_url), abort=True)
        auth_id = User.get_gae_user_auth_id(gae_user=gae_user)
        user = self.auth.store.user_model.get_by_auth_id(auth_id)
        if user:
            # existing user. just log them in.
            self.auth.set_session(self.auth.store.user_to_dict(user))
            # update access for gae admins
            if users.is_current_user_admin():
                if not (user.active and user.admin):
                    user.admin = True
                    user.put()
        else:
            # check whether there's a user currently logged in
            # then, create a new user if no one is signed in,
            # otherwise add this auth_id to currently logged in user.
            if self.logged_in and self.user:
                u = self.user
                u.auth_ids.append(auth_id)
                u.populate(email=gae_user.email(), nickname=gae_user.nickname())
                if users.is_current_user_admin():
                    u.admin = True
                u.put()
            else:
                ok, user = self.auth.store.user_model.create_user(
                    auth_id,
                    email=gae_user.email(),
                    nickname=gae_user.nickname(),
                    admin=users.is_current_user_admin()
                )
                if ok:
                    self.auth.set_session(self.auth.store.user_to_dict(user))
                else:
                    logging.debug('create_user() returned False with strings: %s' % user)
                    user = None
                    self.auth.unset_session()
        if not (user and user.active):
            next_url = '/'
        self.redirect(next_url or '/')


class BaseHander(GoogleAppEngineUserAuthHandler):
    def head(self, *args):
        """Head is used by Twitter. If not there the tweet button shows 0"""
        pass


class MainHandler(BaseHander):
    @authentication_required(authenticate=authenticate)
    def get(self):
        self.response.write("""Hello, MINECRAFT world.""")


application = webapp2.WSGIApplication(
    [
        RedirectRoute('/login_callback', handler='main.GoogleAppEngineUserAuthHandler:login_callback', name='login_callback'),
        RedirectRoute('/logout', handler='main.GoogleAppEngineUserAuthHandler:logout', name='logout'),
        ('/.*', MainHandler),
    ],
    config={
        'webapp2_extras.sessions': {'secret_key': config.SECRET_KEY},
        'webapp2_extras.auth': {'user_model': 'models.User'}
    },
    debug=not on_production_server
)
