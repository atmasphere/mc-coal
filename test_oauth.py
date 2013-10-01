from testing_utils import fix_sys_path; fix_sys_path()

import json
import logging
import os
from urllib import urlencode

from google.appengine.ext import ndb

from agar.test.base_test import BaseTest
from agar.test.web_test import WebTest

from oauth import Client, Token
import main
import models


TEST_USER_EMAIL = 'admin@example.com'
TEST_CLIENT_ID = 'test_client'
TEST_REDIRECT_URI = 'https://localhost/'
TEST_CLIENT_SECRET = 'a_secret'
TEST_CLIENT_NAME = 'test_client_name'
TEST_CLIENT_URI = 'http://example.com'
TEST_LOGO_URI = 'http://example.com/logo.png'
TEST_CLIENT_SECRET = 'client_secret'
TEST_REGISTRATION_ACCESS_TOKEN = 'registration_access_token'

NUM_CLIENT_FIELDS = 10


class OauthTest(BaseTest, WebTest):
    APPLICATION = main.application
    URL = None
    ALLOWED = []

    @property
    def url(self):
        return self.URL

    def setUp(self):
        super(OauthTest, self).setUp()
        key = ndb.Key(Client, TEST_CLIENT_ID)
        data = {
            'client_id': TEST_CLIENT_ID,
            'redirect_uris': [TEST_REDIRECT_URI],
            'name': TEST_CLIENT_NAME,
            'uri': TEST_CLIENT_URI,
            'logo_uri': TEST_LOGO_URI,
            'scope': ['data'],
            'secret': TEST_CLIENT_SECRET,
            'secret_expires_at': 0,
            'registration_access_token': TEST_REGISTRATION_ACCESS_TOKEN
        }
        self.client = Client(key=key, **data)
        self.client.put()

    def tearDown(self):
        super(OauthTest, self).tearDown()

    def log_in_user(self, email=None, is_active=True, is_admin=False):
        email = email or TEST_USER_EMAIL
        super(OauthTest, self).log_in_user(email, is_admin=is_admin)
        response = self.app.get('/gae_login_callback')
        cookies = response.headers.get('Set-Cookie')
        self.auth_cookie = cookies[0:cookies.find(';')] if cookies else None
        self.assertRedirects(response)
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
        self.user = self.log_in_user(email=email)
        url = '/oauth/auth'
        query_params = {
            'client_id': TEST_CLIENT_ID,
            'redirect_uri': TEST_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'data'
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
        params = {'csrf_token': csrf_token, 'grant': 'Grant'}
        response = self.post(url, params)
        self.assertRedirects(response)
        self.assertRegexpMatches(response.headers['Location'], ur"https://localhost/\?code=.+")
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
            'scope': 'data'
        }
        response = self.post(url, params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(4, body)
        return (body['access_token'], body['refresh_token'])

    def assertMethodNotAllowed(self, response):
        error = u'Response did not return a 405 METHOD NOT ALLOWED (status code was {0})\nBody: {1}'.format(response.status_int, response.body)
        self.assertEqual(response.status_int, 405, error)

    def assertCreated(self, response):
        error = u'Response did not return a 201 CREATED (status code was {0})\nBody: {1}'.format(response.status_int, response.body)
        self.assertEqual(response.status_int, 201, error)

    def assertNoContent(self, response):
        error = u'Response did not return a 204 NO CONTENT (status code was {0})\nBody: {1}'.format(response.status_int, response.body)
        self.assertEqual(response.status_int, 204, error)

    def get(self, url, params=None, headers=None, bearer_token=None):
        if bearer_token is not None:
            if headers is None:
                headers = {}
            headers.update({'Authorization': 'Bearer ' + str(bearer_token)})
        return super(OauthTest, self).get(url, params=params, headers=headers)

    def post(self, url, params='', headers=None, upload_files=None, bearer_token=None):
        if bearer_token is not None:
            if headers is None:
                headers = {}
            headers.update({'Authorization': 'Bearer ' + str(bearer_token)})
        return super(OauthTest, self).post(url, params=params, headers=headers, upload_files=upload_files)

    def delete(self, url, headers=None, bearer_token=None):
        if bearer_token is not None:
            if headers is None:
                headers = {}
            headers.update({'Authorization': 'Bearer ' + str(bearer_token)})
        return super(OauthTest, self).delete(url, headers=headers)

    def post_json(self, url, params='', headers=None, bearer_token=None):
        if bearer_token is not None:
            if headers is None:
                headers = {}
            headers.update({'Authorization': 'Bearer ' + str(bearer_token)})
        return self.app.post_json(url, params, headers=headers, status="*", expect_errors=True)

    def put_json(self, url, params='', headers=None, bearer_token=None):
        if bearer_token is not None:
            if headers is None:
                headers = {}
            headers.update({'Authorization': 'Bearer ' + str(bearer_token)})
        return self.app.put_json(url, params, headers=headers, status="*", expect_errors=True)


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
            'response_type': 'code',
            'scope': 'data'
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
        params = {'csrf_token': csrf_token, 'grant': 'Grant'}
        response = self.post(url, params)
        self.assertRedirects(response)
        self.assertRegexpMatches(response.headers['Location'], ur"https://localhost/\?code=.+")
        self.assertEqual(1, Client.query().count())

    def test_post_deny_invalid_client(self):
        url = self.url
        query_params = {
            'client_id': 'new_client',
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
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        self.assertEqual(body['error'], 'invalid_request')

    def test_post_deny_existing_client(self):
        Client.get_or_insert('test_client', client_id=TEST_CLIENT_ID, redirect_uris=[TEST_REDIRECT_URI])
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

    def test_post_incorrect_redirect_uri(self):
        self.get_authorization_code()
        self.log_in_user()
        query_params = {
            'client_id': TEST_CLIENT_ID,
            'redirect_uri': 'invalid_redirect_uri',
            'response_type': 'code'
        }
        response = self.get(self.url, params=query_params)
        self.assertOK(response)
        csrf_string = 'name="csrf_token" type="hidden" value="'
        begin = response.body.find(csrf_string) + len(csrf_string)
        end = response.body.find('"', begin)
        csrf_token = response.body[begin:end]
        url = self.url
        if query_params:
            query_params = urlencode(query_params, doseq=True)
            if '?' in url:
                url += '&'
            else:
                url += '?'
            url += query_params
        params = {'csrf_token': csrf_token, 'grant': 'Grant'}
        response = self.post(url, params)
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        self.assertEqual(body['error'], 'invalid_request')

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
            'scope': 'data'
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
        logging.disable(logging.ERROR)
        response = self.post(self.url, params)
        logging.disable(logging.NOTSET)
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
            'scope': 'data'
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

    def test_post_invalid_secret(self):
        code = self.get_authorization_code()
        params = {
            'code': code,
            'grant_type': 'authorization_code',
            'client_id': TEST_CLIENT_ID,
            'client_secret': 'invalid_secret',
            'redirect_uri': TEST_REDIRECT_URI,
        }
        response = self.post(self.url, params)
        self.assertBadRequest(response)
        self.assertEqual(0, Token.query().count())
        body = json.loads(response.body)
        self.assertLength(1, body)
        self.assertEqual(body['error'], 'invalid_client')

    def test_post_invalid_redirect_uri(self):
        code = self.get_authorization_code()
        params = {
            'code': code,
            'grant_type': 'authorization_code',
            'client_id': TEST_CLIENT_ID,
            'client_secret': TEST_CLIENT_SECRET,
            'redirect_uri': 'http:/invalid.com',
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
            'scope': 'data'
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
            'scope': 'data'
        }
        response = self.post(self.url, params)
        self.assertBadRequest(response)
        self.assertEqual(1, Token.query().count())
        token = Token.query().get()
        self.assertEqual(token.key, old_token_key)
        body = json.loads(response.body)
        self.assertLength(1, body)
        self.assertEqual(body['error'], 'invalid_grant')


class RegistrationHandlerTest(OauthTest):
    URL = '/oauth/register'
    ALLOWED = ['POST']

    def setUp(self):
        super(RegistrationHandlerTest, self).setUp()

    def test_post(self):
        self.client.key.delete()
        self.client = None
        params = {
            'client_id': TEST_CLIENT_ID,
            'redirect_uris': [TEST_REDIRECT_URI],
            'client_name': TEST_CLIENT_NAME,
            'client_uri': TEST_CLIENT_URI,
            'logo_uri': TEST_LOGO_URI
        }
        response = self.post_json(self.url, params=params)
        self.assertCreated(response)
        self.assertEqual(Client.query().count(), 1)
        client = Client.query().get()
        self.assertTrue(client.active)
        body = json.loads(response.body)
        self.assertEqual(len(body), NUM_CLIENT_FIELDS)
        self.assertEqual(body['client_id'], TEST_CLIENT_ID)
        self.assertEqual(body['redirect_uris'], [TEST_REDIRECT_URI])
        self.assertEqual(body['client_name'], TEST_CLIENT_NAME)
        self.assertEqual(body['client_uri'], TEST_CLIENT_URI)
        self.assertEqual(body['logo_uri'], TEST_LOGO_URI)
        self.assertEqual(body['registration_client_uri'], 'https://localhost:80/oauth/client/{0}'.format(TEST_CLIENT_ID))
        self.assertEqual(body['registration_access_token'], client.registration_access_token)
        self.assertEqual(body['client_secret'], client.secret)
        self.assertEqual(body['client_secret_expires_at'], client.secret_expires_at)

    def test_post_minimum(self):
        self.client.key.delete()
        self.client = None
        params = {
            'redirect_uris': [TEST_REDIRECT_URI]
        }
        response = self.post_json(self.url, params=params)
        self.assertCreated(response)
        self.assertEqual(Client.query().count(), 1)
        client = Client.query().get()
        self.assertTrue(client.active)
        body = json.loads(response.body)
        self.assertEqual(len(body), NUM_CLIENT_FIELDS-3)
        self.assertEqual(body['client_id'], client.client_id)
        self.assertEqual(body['redirect_uris'], [TEST_REDIRECT_URI])
        self.assertEqual(body['registration_client_uri'], 'https://localhost:80/oauth/client/{0}'.format(client.client_id))
        self.assertEqual(body['registration_access_token'], client.registration_access_token)
        self.assertEqual(body['client_secret'], client.secret)
        self.assertEqual(body['client_secret_expires_at'], client.secret_expires_at)

    def test_post_invalid_request(self):
        params = {}
        logging.disable(logging.ERROR)
        response = self.post_json(self.url, params=params)
        logging.disable(logging.NOTSET)
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertEqual(body['error'], 'invalid_request')

    def test_post_duplicate_client_id(self):
        params = {
            'client_id': TEST_CLIENT_ID,
            'redirect_uris': [TEST_REDIRECT_URI],
            'client_name': TEST_CLIENT_NAME,
            'client_uri': TEST_CLIENT_URI,
            'logo_uri': TEST_LOGO_URI
        }
        response = self.post_json(self.url, params=params)
        self.assertCreated(response)
        self.assertEqual(Client.query().count(), 2)
        client = Client.query().get()
        self.assertTrue(client.active)
        body = json.loads(response.body)
        self.assertEqual(len(body), NUM_CLIENT_FIELDS)
        self.assertTrue(body['client_id'].startswith(TEST_CLIENT_ID+'-'))
        client = Client.get_by_client_id(body['client_id'])
        self.assertEqual(body['redirect_uris'], [TEST_REDIRECT_URI])
        self.assertEqual(body['client_name'], TEST_CLIENT_NAME)
        self.assertEqual(body['client_uri'], TEST_CLIENT_URI)
        self.assertEqual(body['logo_uri'], TEST_LOGO_URI)
        self.assertEqual(body['registration_client_uri'], 'https://localhost:80/oauth/client/{0}'.format(client.client_id))
        self.assertEqual(body['registration_access_token'], client.registration_access_token)
        self.assertEqual(body['client_secret'], client.secret)
        self.assertEqual(body['client_secret_expires_at'], client.secret_expires_at)


class ClientHanderTest(OauthTest):
    URL = '/oauth/client/{0}'
    ALLOWED = ['GET', 'POST', 'DELETE']

    def setUp(self):
        super(ClientHanderTest, self).setUp()
        logging.disable(logging.NOTSET)

    @property
    def url(self):
        return self.URL.format(self.client.client_id)

    def test_get(self):
        response = self.get(self.url, bearer_token=self.client.registration_access_token)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertEqual(len(body), NUM_CLIENT_FIELDS)
        self.assertEqual(body['client_id'], TEST_CLIENT_ID)
        self.assertEqual(body['redirect_uris'], [TEST_REDIRECT_URI])
        self.assertEqual(body['client_name'], TEST_CLIENT_NAME)
        self.assertEqual(body['client_uri'], TEST_CLIENT_URI)
        self.assertEqual(body['logo_uri'], TEST_LOGO_URI)
        self.assertEqual(body['registration_client_uri'], 'https://localhost:80/oauth/client/{0}'.format(TEST_CLIENT_ID))
        self.assertEqual(body['registration_access_token'], self.client.registration_access_token)
        self.assertEqual(body['client_secret'], self.client.secret)
        self.assertEqual(body['client_secret_expires_at'], self.client.secret_expires_at)

    def test_get_no_auth(self):
        response = self.get(self.url)
        self.assertUnauthorized(response)

    def test_put(self):
        params = {
            'client_id': TEST_CLIENT_ID,
            'redirect_uris': [TEST_REDIRECT_URI],
            'client_secret': TEST_CLIENT_SECRET,
            'client_name': 'new_client_name',
            'client_uri': TEST_CLIENT_URI,
            'logo_uri': TEST_LOGO_URI
        }
        response = self.put_json(self.url, params=params, bearer_token=self.client.registration_access_token)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertEqual(len(body), NUM_CLIENT_FIELDS)
        self.assertEqual(body['client_id'], TEST_CLIENT_ID)
        self.assertEqual(body['redirect_uris'], [TEST_REDIRECT_URI])
        self.assertEqual(body['client_name'], 'new_client_name')
        self.assertEqual(body['client_uri'], TEST_CLIENT_URI)
        self.assertEqual(body['logo_uri'], TEST_LOGO_URI)
        self.assertEqual(body['registration_client_uri'], 'https://localhost:80/oauth/client/{0}'.format(TEST_CLIENT_ID))
        self.assertEqual(body['registration_access_token'], self.client.registration_access_token)
        self.assertEqual(body['client_secret'], self.client.secret)
        self.assertEqual(body['client_secret_expires_at'], self.client.secret_expires_at)

    def test_put_minimum(self):
        params = {
            'client_id': TEST_CLIENT_ID,
            'redirect_uris': [TEST_REDIRECT_URI],
            'client_secret': TEST_CLIENT_SECRET
        }
        response = self.put_json(self.url, params=params, bearer_token=self.client.registration_access_token)
        self.assertOK(response)
        client = self.client.key.get()  #Reload
        body = json.loads(response.body)
        self.assertEqual(len(body), NUM_CLIENT_FIELDS-3)
        self.assertEqual(body['client_id'], TEST_CLIENT_ID)
        self.assertEqual(body['redirect_uris'], [TEST_REDIRECT_URI])
        self.assertIsNone(client.name)
        self.assertIsNone(client.uri)
        self.assertIsNone(client.logo_uri)
        self.assertEqual(body['registration_client_uri'], 'https://localhost:80/oauth/client/{0}'.format(TEST_CLIENT_ID))
        self.assertEqual(body['registration_access_token'], self.client.registration_access_token)
        self.assertEqual(body['client_secret'], self.client.secret)
        self.assertEqual(body['client_secret_expires_at'], self.client.secret_expires_at)

    def test_put_no_auth(self):
        params = {
            'client_id': TEST_CLIENT_ID,
            'redirect_uris': [TEST_REDIRECT_URI]
        }
        response = self.put_json(self.url, params=params)
        self.assertUnauthorized(response)

    def test_put_invalid_client_id(self):
        params = {
            'client_id': 'invalid_id',
            'redirect_uris': [TEST_REDIRECT_URI],
            'client_name': 'new_client_name',
            'client_uri': TEST_CLIENT_URI,
            'logo_uri': TEST_LOGO_URI
        }
        response = self.put_json(self.url, params=params, bearer_token=self.client.registration_access_token)
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertEqual(body['error'], 'invalid_client_id')

    def test_put_no_redirect_uri(self):
        params = {
            'client_id': 'invalid_id',
            'client_name': 'new_client_name',
            'client_uri': TEST_CLIENT_URI,
            'logo_uri': TEST_LOGO_URI
        }
        logging.disable(logging.ERROR)
        response = self.put_json(self.url, params=params, bearer_token=self.client.registration_access_token)
        logging.disable(logging.NOTSET)
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertEqual(body['error'], 'invalid_request')

    def test_delete(self):
        response = self.delete(self.url, bearer_token=self.client.registration_access_token)
        self.assertNoContent(response)
        self.assertEqual(Client.query().count(), 0)

    def test_delete_no_auth(self):
        response = self.delete(self.url)
        self.assertUnauthorized(response)
        self.assertEqual(Client.query().count(), 1)

    def test_delete_invalid_client_id(self):
        response = self.delete(self.URL.format('invalid_client_id'), bearer_token=self.client.registration_access_token)
        self.assertUnauthorized(response)
        self.assertEqual(Client.query().count(), 1)


class ShowAuthorizationCodeHandlerTest(OauthTest):
    URL = '/oauth/show'
    ALLOWED = ['GET']

    def test_get(self):
        code = self.get_authorization_code()
        self.assertIsNotNone(code)
        self.user = self.log_in_user()
        url = self.url + '?code={0}'.format(code)
        response = self.get(url)
        self.assertOK(response)
        self.assertIn(code, response.body)

    def test_get_not_logged_in(self):
        access_token, refresh_token = self.get_tokens()
        response = self.get(self.url)
        self.assertRedirects(response)

    def test_get_error(self):
        self.user = self.log_in_user()
        url = self.url + '?error=access_denied'
        response = self.get(url)
        self.assertOK(response)
        self.assertIn('access_denied', response.body)


class TestHandlerTest(OauthTest):
    URL = '/oauth/test'
    ALLOWED = ['GET']

    def test_get(self):
        access_token, refresh_token = self.get_tokens()
        response = self.get(self.url, bearer_token=access_token)
        self.assertOK(response)

    def test_get_no_token(self):
        access_token, refresh_token = self.get_tokens()
        response = self.get(self.url)
        self.assertUnauthorized(response)

    def test_get_invalid_token(self):
        access_token, refresh_token = self.get_tokens()
        response = self.get(self.url, bearer_token='invalid_token')
        self.assertUnauthorized(response)

    def test_expired_token(self):
        from config import coal_config
        expires_in = coal_config.OAUTH_TOKEN_EXPIRES_IN
        coal_config.OAUTH_TOKEN_EXPIRES_IN = 0
        access_token, refresh_token = self.get_tokens()
        response = self.get(self.url, bearer_token=access_token)
        self.assertUnauthorized(response)
        coal_config.OAUTH_TOKEN_EXPIRES_IN = expires_in
