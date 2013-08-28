import json
import logging
import os
import sys
from urllib import urlencode

for d in os.environ["PATH"].split(":"):
    dev_appserver_path = os.path.join(d, "dev_appserver.py")
    if os.path.isfile(dev_appserver_path):
        sdk_path = os.path.abspath(os.path.dirname(os.path.realpath(dev_appserver_path)))
        sys.path.insert(0, sdk_path)
        import dev_appserver
        dev_appserver.fix_sys_path()

from agar.test.base_test import BaseTest
from agar.test.web_test import WebTest

from oauth import Client, Token
import main
import models


TEST_USER_EMAIL = 'admin@example.com'
TEST_CLIENT_ID = 'test_client'
TEST_REDIRECT_URI = 'https://localhost/'
TEST_CLIENT_SECRET = 'a_secret'


class OauthTest(BaseTest, WebTest):
    APPLICATION = main.application
    URL = None
    ALLOWED = []

    @property
    def url(self):
        return self.URL

    def setUp(self):
        super(OauthTest, self).setUp()
        logging.disable(logging.ERROR)

    def tearDown(self):
        super(OauthTest, self).tearDown()
        logging.disable(logging.NOTSET)

    def log_in_user(self, email=None, is_active=True, is_admin=False):
        email = email or TEST_USER_EMAIL
        super(OauthTest, self).log_in_user(email, is_admin=is_admin)
        response = self.app.get('/login_callback')
        cookies = response.headers.get('Set-Cookie')
        self.auth_cookie = cookies[0:cookies.find(';')] if cookies else None
        self.assertRedirects(response, to='/')
        self.current_user = models.User.lookup(email=email)
        self.current_user.active = is_active
        self.current_user.put()
        return self.current_user

    def log_in_admin(self, email=TEST_USER_EMAIL):
        return self.log_in_user(email=email, is_admin=True)

    def log_out_user(self):
        response = self.get('/logout')
        self.assertRedirects(response)
        self.auth_cookie = None
        try:
            del os.environ['USER_EMAIL']
        except KeyError:
            pass
        try:
            del os.environ['USER_ID']
        except KeyError:
            pass
        try:
            del os.environ['USER_IS_ADMIN']
        except KeyError:
            pass

    def get_authorization_code(self, email=None):
        self.log_in_user(email=email)
        url = '/oauth/auth'
        query_params = {
            'client_id': TEST_CLIENT_ID,
            'redirect_uri': TEST_REDIRECT_URI,
            'response_type': 'code'
        }
        response = self.get(url, params=query_params)
        self.assertOK(response)
        csrf_string = 'name="csrf_token" type="hidden" value="'
        begin = response.body.find(csrf_string) + len(csrf_string)
        end = response.body.find('"', begin)
        csrf_token = response.body[begin:end]
        if query_params:
            query_params = urlencode(query_params, doseq=True)
            if '?' in url:
                url += '&'
            else:
                url += '?'
            url += query_params
        params = {'csrf_token': csrf_token, 'authorize': 'Approve'}
        response = self.post(url, params)
        self.assertRedirects(response)
        self.assertRegexpMatches(response.headers['Location'], ur"https://localhost/\?code=.+")
        self.assertEqual(1, Client.query().count())
        start = response.headers['Location'].find('=')
        code = response.headers['Location'][start+1:]
        self.log_out_user()
        return code

    def get_tokens(self, email=None):
        url = '/oauth/token'
        code = self.get_authorization_code(email=email)
        params = {
            'code': code,
            'grant_type': 'authorization_code',
            'client_id': TEST_CLIENT_ID,
            'client_secret': TEST_CLIENT_SECRET,
            'redirect_uri': TEST_REDIRECT_URI,
        }
        response = self.post(url, params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(4, body)
        return (body['access_token'], body['refresh_token'])

    def assertMethodNotAllowed(self, response):
        error = u'Response did not return a 405 METHOD NOT ALLOWED (status code was {0})\nBody: {1}'.format(response.status_int, response.body)
        self.assertEqual(response.status_int, 405, error)

    def get(self, url, params=None, headers=None, access_token=None):
        if access_token is not None:
            if headers is None:
                headers = {}
            headers.update({'Authorization': 'Bearer ' + str(access_token)})
        return super(OauthTest, self).get(url, params=params, headers=headers)

    def post(self, url, params='', headers=None, upload_files=None, access_token=None):
        if access_token is not None:
            if headers is None:
                headers = {}
            headers.update({'Authorization': 'Bearer ' + str(access_token)})
        return super(OauthTest, self).post(url, params=params, headers=headers, upload_files=upload_files)


class AuthorizationCodeHandlerTest(OauthTest):
    URL = '/oauth/auth'
    ALLOWED = ['GET', 'POST']

    def setUp(self):
        super(AuthorizationCodeHandlerTest, self).setUp()
        self.user = self.log_in_user()

    def get(self, url, params=None, headers=None):
        extra_environ = None
        if getattr(self, 'auth_cookie', None):
            extra_environ = {'HTTP_COOKIE': self.auth_cookie.replace('=', '%3D').replace('%3D', '=', 1)}
        return self.app.get(url, params=params, headers=headers, extra_environ=extra_environ, status="*", expect_errors=True)

    def post(self, url, params='', headers=None, upload_files=None):
        extra_environ = None
        if getattr(self, 'auth_cookie', None):
            extra_environ = {'HTTP_COOKIE': self.auth_cookie.replace('=', '%3D').replace('%3D', '=', 1)}
        return self.app.post(url, params=params, headers=headers, extra_environ=extra_environ, upload_files=upload_files, status="*", expect_errors=True)

    def test_get(self):
        params = {'client_id': TEST_CLIENT_ID, 'redirect_uri': TEST_REDIRECT_URI, 'response_type': 'code'}
        response = self.get(self.url, params=params)
        self.assertOK(response)

    def test_post_authorize(self):
        url = self.url
        query_params = {
            'client_id': TEST_CLIENT_ID,
            'redirect_uri': TEST_REDIRECT_URI,
            'response_type': 'code'
        }
        response = self.get(self.url, params=query_params)
        self.assertOK(response)
        csrf_string = 'name="csrf_token" type="hidden" value="'
        begin = response.body.find(csrf_string) + len(csrf_string)
        end = response.body.find('"', begin)
        csrf_token = response.body[begin:end]
        if query_params:
            query_params = urlencode(query_params, doseq=True)
            if '?' in url:
                url += '&'
            else:
                url += '?'
            url += query_params
        params = {'csrf_token': csrf_token, 'authorize': 'Approve'}
        response = self.post(url, params)
        self.assertRedirects(response)
        self.assertRegexpMatches(response.headers['Location'], ur"https://localhost/\?code=.+")
        self.assertEqual(1, Client.query().count())

    def test_post_deny_new_client(self):
        url = self.url
        query_params = {
            'client_id': TEST_CLIENT_ID,
            'redirect_uri': TEST_REDIRECT_URI,
            'response_type': 'code'
        }
        response = self.get(self.url, params=query_params)
        self.assertOK(response)
        csrf_string = 'name="csrf_token" type="hidden" value="'
        begin = response.body.find(csrf_string) + len(csrf_string)
        end = response.body.find('"', begin)
        csrf_token = response.body[begin:end]
        if query_params:
            query_params = urlencode(query_params, doseq=True)
            if '?' in url:
                url += '&'
            else:
                url += '?'
            url += query_params
        params = {'csrf_token': csrf_token, 'deny': 'Deny'}
        response = self.post(url, params)
        self.assertRedirects(response, to=TEST_REDIRECT_URI+"?error=unauthorized_client")
        self.assertEqual(0, Client.query().count())

    def test_post_deny_existing_client(self):
        Client.get_or_insert('test_client', client_id=TEST_CLIENT_ID, redirect_uri=TEST_REDIRECT_URI)
        url = self.url
        query_params = {
            'client_id': TEST_CLIENT_ID,
            'redirect_uri': TEST_REDIRECT_URI,
            'response_type': 'code'
        }
        response = self.get(self.url, params=query_params)
        self.assertOK(response)
        csrf_string = 'name="csrf_token" type="hidden" value="'
        begin = response.body.find(csrf_string) + len(csrf_string)
        end = response.body.find('"', begin)
        csrf_token = response.body[begin:end]
        if query_params:
            query_params = urlencode(query_params, doseq=True)
            if '?' in url:
                url += '&'
            else:
                url += '?'
            url += query_params
        params = {'csrf_token': csrf_token, 'deny': 'Deny'}
        response = self.post(url, params)
        self.assertRedirects(response, to=TEST_REDIRECT_URI+"?error=access_denied")
        self.assertEqual(1, Client.query().count())

    def test_get_no_auth(self):
        if self.url:
            self.log_out_user()
            response = self.get(self.url)
            if 'GET' in self.ALLOWED:
                self.assertRedirects(response)
            else:
                self.assertMethodNotAllowed(response)

    def test_post_no_auth(self):
        if self.url:
            self.log_out_user()
            response = self.post(self.url)
            if 'POST' in self.ALLOWED:
                self.assertRedirects(response)
            else:
                self.assertMethodNotAllowed(response)


class TokenHandlerTest(OauthTest):
    URL = '/oauth/token'
    ALLOWED = ['POST']

    def setUp(self):
        super(TokenHandlerTest, self).setUp()
        self.user = self.log_in_user()
        self.log_out_user()

    def test_post_authorization_code(self):
        code = self.get_authorization_code()
        params = {
            'code': code,
            'grant_type': 'authorization_code',
            'client_id': TEST_CLIENT_ID,
            'client_secret': TEST_CLIENT_SECRET,
            'redirect_uri': TEST_REDIRECT_URI,
        }
        response = self.post(self.url, params)
        self.assertOK(response)
        self.assertEqual(1, Token.query().count())
        token = Token.query().get()
        self.assertIsNotNone(token)
        self.assertIsNotNone(token.access_token)
        self.assertIsNotNone(token.refresh_token)
        self.assertEqual(token.client_id, TEST_CLIENT_ID)
        self.assertEqual(token.user_key, self.user.key)
        self.assertEqual(token.token_type, 'Bearer')
        self.assertGreater(token.expires_in, 0)
        self.assertFalse(token.is_expired)
        body = json.loads(response.body)
        self.assertLength(4, body)
        self.assertEqual(body['access_token'], token.access_token)
        self.assertEqual(body['refresh_token'], token.refresh_token)
        self.assertEqual(body['token_type'], token.token_type)
        self.assertEqual(body['expires_in'], token.expires_in)

    def test_post_invalid(self):
        self.get_authorization_code()
        params = {}
        response = self.post(self.url, params)
        self.assertBadRequest(response)
        self.assertEqual(0, Token.query().count())
        body = json.loads(response.body)
        self.assertLength(1, body)
        self.assertEqual(body['error'], 'invalid_request')

    def test_post_invalid_client(self):
        code = self.get_authorization_code()
        params = {
            'code': code,
            'grant_type': 'authorization_code',
            'client_id': 'invalid',
            'client_secret': TEST_CLIENT_SECRET,
            'redirect_uri': TEST_REDIRECT_URI,
        }
        response = self.post(self.url, params)
        self.assertBadRequest(response)
        self.assertEqual(0, Token.query().count())
        body = json.loads(response.body)
        self.assertLength(1, body)
        self.assertEqual(body['error'], 'invalid_client')

    def test_post_invalid_authorization_code(self):
        code = self.get_authorization_code()
        params = {
            'code': code+'invalid_code',
            'grant_type': 'authorization_code',
            'client_id': TEST_CLIENT_ID,
            'client_secret': TEST_CLIENT_SECRET,
            'redirect_uri': TEST_REDIRECT_URI,
        }
        response = self.post(self.url, params)
        self.assertBadRequest(response)
        self.assertEqual(0, Token.query().count())
        body = json.loads(response.body)
        self.assertLength(1, body)
        self.assertEqual(body['error'], 'invalid_grant')

    def test_post_refresh_token(self):
        access_token, refresh_token = self.get_tokens()
        old_token_key = Token.query().get().key
        params = {
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
            'client_id': TEST_CLIENT_ID,
            'client_secret': TEST_CLIENT_SECRET,
            'redirect_uri': TEST_REDIRECT_URI,
        }
        response = self.post(self.url, params)
        self.assertOK(response)
        self.assertEqual(1, Token.query().count())
        token = Token.query().get()
        self.assertNotEqual(token.key, old_token_key)
        self.assertNotEqual(token.access_token, access_token)
        self.assertNotEqual(token.refresh_token, refresh_token)
        self.assertIsNotNone(token)
        self.assertIsNotNone(token.access_token)
        self.assertIsNotNone(token.refresh_token)
        self.assertEqual(token.client_id, TEST_CLIENT_ID)
        self.assertEqual(token.user_key, self.user.key)
        self.assertEqual(token.token_type, 'Bearer')
        self.assertGreater(token.expires_in, 0)
        self.assertFalse(token.is_expired)
        body = json.loads(response.body)
        self.assertLength(4, body)
        self.assertEqual(body['access_token'], token.access_token)
        self.assertEqual(body['refresh_token'], token.refresh_token)
        self.assertEqual(body['token_type'], token.token_type)
        self.assertEqual(body['expires_in'], token.expires_in)

    def test_post_invalid_refresh_token(self):
        access_token, refresh_token = self.get_tokens()
        old_token_key = Token.query().get().key
        params = {
            'refresh_token': 'invalid_token',
            'grant_type': 'refresh_token',
            'client_id': TEST_CLIENT_ID,
            'client_secret': TEST_CLIENT_SECRET,
            'redirect_uri': TEST_REDIRECT_URI,
        }
        response = self.post(self.url, params)
        self.assertBadRequest(response)
        self.assertEqual(1, Token.query().count())
        token = Token.query().get()
        self.assertEqual(token.key, old_token_key)
        body = json.loads(response.body)
        self.assertLength(1, body)
        self.assertEqual(body['error'], 'invalid_grant')


class TestHandlerTest(OauthTest):
    URL = '/oauth/test'
    ALLOWED = ['GET']

    def test_get(self):
        access_token, refresh_token = self.get_tokens()
        response = self.get(self.url, access_token=access_token)
        self.assertOK(response)

    def test_get_no_token(self):
        access_token, refresh_token = self.get_tokens()
        response = self.get(self.url)
        self.assertUnauthorized(response)

    def test_get_invalid_token(self):
        access_token, refresh_token = self.get_tokens()
        response = self.get(self.url, access_token='invalid_token')
        self.assertUnauthorized(response)

    def test_expired_token(self):
        from config import coal_config
        expires_in = coal_config.OAUTH_TOKEN_EXPIRES_IN
        coal_config.OAUTH_TOKEN_EXPIRES_IN = 0
        access_token, refresh_token = self.get_tokens()
        response = self.get(self.url, access_token=access_token)
        self.assertUnauthorized(response)
        coal_config.OAUTH_TOKEN_EXPIRES_IN = expires_in
