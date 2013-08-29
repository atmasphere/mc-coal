import datetime
import logging

from pyoauth2.provider import AuthorizationProvider, ResourceAuthorization, ResourceProvider
from pyoauth2.utils import random_ascii_string, url_query_params

from google.appengine.ext import ndb

import webapp2
from webapp2_extras.routes import RedirectRoute

from wtforms import fields
from wtforms.ext.csrf.session import SessionSecureForm

from agar.auth import authentication_required

from config import coal_config
from user_auth import UserHandler, authenticate


class Client(ndb.Model):
    client_id = ndb.StringProperty(required=True)
    redirect_uri = ndb.StringProperty()
    active = ndb.BooleanProperty(default=True)
    secret = ndb.StringProperty()
    email = ndb.StringProperty()
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def _pre_put_hook(self):
        if not self.secret:
            self.secret = random_ascii_string(COALAuthorizationProvider().token_length)


class AuthorizationCode(ndb.Model):
    code = ndb.StringProperty(required=True)
    client_id = ndb.StringProperty(required=True)
    user_key = ndb.KeyProperty(required=True)
    scope = ndb.StringProperty()
    expires_in = ndb.IntegerProperty(default=60)
    expires = ndb.ComputedProperty(lambda self: self.created + datetime.timedelta(seconds=self.expires_in) if self.expires_in is not None else None)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def is_expired(self):
        return datetime.datetime.now() > self.expires if self.expires is not None else False


class Token(ndb.Model):
    access_token = ndb.StringProperty(required=True)
    refresh_token = ndb.StringProperty(required=True)
    client_id = ndb.StringProperty(required=True)
    user_key = ndb.KeyProperty(required=True)
    scope = ndb.StringProperty()
    token_type = ndb.StringProperty()
    expires_in = ndb.IntegerProperty()
    expires = ndb.ComputedProperty(lambda self: self.created + datetime.timedelta(seconds=self.expires_in) if self.expires_in is not None else None)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @property
    def is_expired(self):
        return datetime.datetime.now() > self.expires if self.expires is not None else False


class COALAuthorizationProvider(AuthorizationProvider):
    def get_authorization_code_key_name(self, client_id, code):
        return '{0}-{1}'.format(client_id, code)

    @property
    def token_expires_in(self):
        return coal_config.OAUTH_TOKEN_EXPIRES_IN

    def validate_client_id(self, client_id):
        client = ndb.Key(Client, client_id).get()
        if client is not None and client.active:
            return True
        return False

    def validate_client_secret(self, client_id, client_secret):
        return True

    def validate_redirect_uri(self, client_id, redirect_uri):
        client = ndb.Key(Client, client_id).get()
        if client is not None and client.redirect_uri is not None and client.redirect_uri == redirect_uri:
            return True
        return False

    def validate_scope(self, client_id, scope):
        return True

    def validate_access(self, client_id):
        return webapp2.get_request().user.is_client_id_authorized(client_id)

    def from_authorization_code(self, client_id, code, scope):
        key_name = self.get_authorization_code_key_name(client_id, code)
        key = ndb.Key(AuthorizationCode, key_name)
        auth_code = key.get()
        if auth_code is not None and auth_code.is_expired:
            key.delete()
            auth_code = None
        return auth_code

    def from_refresh_token(self, client_id, refresh_token, scope):
        token_query = Token.query()
        token_query = token_query.filter(Token.client_id == client_id)
        token_query = token_query.filter(Token.refresh_token == refresh_token)
        return token_query.get()

    def persist_authorization_code(self, client_id, code, scope):
        user = webapp2.get_request().user
        key_name = self.get_authorization_code_key_name(client_id, code)
        key = ndb.Key(AuthorizationCode, key_name)
        if key.get() is not None:
            raise Exception("duplicate_authorization_code")
        auth_code = AuthorizationCode(key=key, code=code, client_id=client_id, scope=scope, user_key=user.key)
        auth_code.put()

    def persist_token_information(self, client_id, scope, access_token, token_type, expires_in, refresh_token, data):
        auth_code = data
        key = ndb.Key(Token, access_token)
        if key.get() is not None:
            raise Exception("duplicate_access_token")
        if self.from_refresh_token(client_id, refresh_token, scope):
            raise Exception("duplicate_refresh_token")
        token = Token(key=key, access_token=access_token, refresh_token=refresh_token, client_id=client_id, user_key=auth_code.user_key, scope=scope, token_type=token_type, expires_in=expires_in)
        token.put()

    def discard_authorization_code(self, client_id, code):
        key_name = self.get_authorization_code_key_name(client_id, code)
        key = ndb.Key(AuthorizationCode, key_name)
        key.delete()

    def discard_refresh_token(self, client_id, refresh_token):
        token = self.from_refresh_token(client_id, refresh_token, None)
        if token is not None:
            token.key.delete()

    def discard_client_user_tokens(self, client_id, user_key):
        token_query = Token.query()
        token_query = token_query.filter(Token.client_id == client_id)
        token_query = token_query.filter(Token.user_key == user_key)
        keys = [key for key in token_query.iter(keys_only=True)]
        ndb.delete_multi(keys)

authorization_provider = COALAuthorizationProvider()


class COALResourceAuthorization(ResourceAuthorization):
    user_key = None


class COALResourceProvider(ResourceProvider):
    @property
    def authorization_class(self):
        return COALResourceAuthorization

    def get_authorization_header(self):
        return webapp2.get_request().headers.get('Authorization', None)

    def validate_access_token(self, access_token, authorization):
        key = ndb.Key(Token, access_token)
        token = key.get()
        if token is not None and not token.is_expired:
            authorization.is_valid = True
            authorization.client_id = token.client_id
            authorization.user_key = token.user_key
            if token.expires is not None:
                d = datetime.datetime.now() - token.expires
                authorization.expires_in = d.seconds

resource_provider = COALResourceProvider()


class BaseSecureForm(SessionSecureForm):
    SECRET_KEY = coal_config.SECRET_KEY
    TIME_LIMIT = datetime.timedelta(minutes=20)


class AuthForm(BaseSecureForm):
    grant = fields.SubmitField('Grant', id='submit_button')
    deny = fields.SubmitField('Deny', id='submit_button')


class PyOAuth2Base(object):
    @property
    def client_id(self):
        return url_query_params(self.request.url).get('client_id', None)

    @property
    def redirect_uri(self):
        return url_query_params(self.request.url).get('redirect_uri', None)

    def set_response(self, response):
        self.response.set_status(response.status_code)
        self.response.headers.update(response.headers)
        self.response.write(response.text)


class AuthorizationCodeHandler(UserHandler, PyOAuth2Base):
    def set_authorization_code_response(self):
        response = authorization_provider.get_authorization_code_from_uri(self.request.url)
        self.set_response(response)

    @authentication_required(authenticate=authenticate)
    def get(self):
        if self.user.is_client_id_authorized(self.client_id):
            self.user.unauthorize_client_id(self.client_id)
        form = AuthForm(csrf_context=self.session)
        context = {'url': self.request.url, 'form': form, 'client_id': self.client_id}
        self.render_template('auth.html', context=context)

    @authentication_required(authenticate=authenticate)
    def post(self):
        form = AuthForm(self.request.POST, csrf_context=self.session)
        if form.validate():
            if form.grant.data:
                Client.get_or_insert(self.client_id, client_id=self.client_id, redirect_uri=self.redirect_uri)
                self.user.authorize_client_id(self.client_id)
            else:
                self.user.unauthorize_client_id(self.client_id)
            self.set_authorization_code_response()
        elif form.csrf_token.errors:
            logging.error(form.csrf_token.errors)
        else:
            form = AuthForm(csrf_context=self.session)
            context = {'url': self.request.url, 'form': form, 'client_id': self.client_id}
            self.render_template('auth.html', context=context)


class ShowAuthorizationCodeHandler(UserHandler, PyOAuth2Base):
    @authentication_required(authenticate=authenticate)
    def get(self):
        code = self.request.GET.get('code', None)
        error = self.request.GET.get('error', None)
        context = {'code': code, 'error': error}
        self.render_template('oauth_show.html', context=context)


class TokenHandler(webapp2.RequestHandler, PyOAuth2Base):
    def set_access_token_response(self):
        response = authorization_provider.get_token_from_post_data(self.request.POST)
        self.set_response(response)

    def post(self):
        self.set_access_token_response()


class TestHandler(webapp2.RequestHandler):
    def get(self):
        authorization = resource_provider.get_authorization()
        if not (authorization.is_oauth and authorization.is_valid):
            self.abort(401)
        self.response.headers['Content-Type'] = "application/json"
        client_id = authorization.client_id
        user = authorization.user_key.get()
        auth_header = self.request.headers.get('Authorization', None)
        body = u"{{'authorization': {0}, 'client_id': {1}".format(auth_header, client_id)
        if user:
            body += u", 'user': {0}}}".format(user.nickname)
        else:
            body = u"}}"
        self.response.set_status(200)
        self.response.out.write(body)


routes = [
    RedirectRoute('/oauth/auth', handler='oauth.AuthorizationCodeHandler', methods=['GET', 'POST'], name='oauth_auth'),
    RedirectRoute('/oauth/token', handler='oauth.TokenHandler', methods=['POST'], name='oauth_token'),
    RedirectRoute('/oauth/show', handler='oauth.ShowAuthorizationCodeHandler', methods=['GET'], name='oauth_show'),
    RedirectRoute('/oauth/test', handler='oauth.TestHandler', methods=['GET'], name='oauth_test')
]
