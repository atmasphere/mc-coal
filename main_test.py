import os

from base_test import BaseTest
from web_test import WebTest

import main
from models import User, Server


TEST_USER_EMAIL = 'test@example.com'


class MainBaseTest(BaseTest, WebTest):
    APPLICATION = main.application
    URL = None
    ALLOWED = ['GET']

    @property
    def url(self):
        return self.URL

    @property
    def extra_environ(self):
        extra_environ = None
        if getattr(self, 'auth_cookie', None):
            extra_environ = {'HTTP_COOKIE': self.auth_cookie.replace('=', '%3D').replace('%3D', '=', 1)}
        return extra_environ

    def log_in_user(self, email=TEST_USER_EMAIL, is_active=True, is_admin=False):
        super(MainBaseTest, self).log_in_user(email, is_admin=is_admin)
        response = self.get('/gae_login_callback')
        cookies = response.headers.get('Set-Cookie')
        self.auth_cookie = cookies[0:cookies.find(';')] if cookies else None
        self.assertRedirects(response)
        self.current_user = User.lookup(email=email)
        self.current_user.active = is_active
        self.current_user.put()

    def log_in_admin(self, email=TEST_USER_EMAIL):
        self.log_in_user(email=email, is_admin=True)

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
        response = self.get('/logout')
        self.auth_cookie = None
        self.assertRedirects(response)

    def assertLoggedIn(self, response):
        pass

    def assertNotLoggedIn(self, response):
        self.assertIn('Login', response.body)

    def assertMethodNotAllowed(self, response):
        error = u'Response did not return a 405 METHOD NOT ALLOWED (status code was {0})\nBody: {1}'.format(response.status_int, response.body)
        self.assertEqual(response.status_int, 405, error)

    def assertCreated(self, response):
        error = u'Response did not return a 201 CREATED (status code was {0})\nBody: {1}'.format(response.status_int, response.body)
        self.assertEqual(response.status_int, 201, error)

    def setUp(self):
        super(MainBaseTest, self).setUp()
        self.server = Server.create()

    def get(self, url=None, params=None, headers=None):
        url = url or self.url
        self.app.reset()
        return self.app.get(url, params=params, headers=headers, extra_environ=self.extra_environ, status="*", expect_errors=True)

    def post(self, url=None, params='', headers=None, upload_files=None):
        url = url or self.url
        self.app.reset()
        return self.app.post(url, params=params, headers=headers, extra_environ=self.extra_environ, status="*", upload_files=upload_files, expect_errors=True)

    def test_get_with_slash(self):
        if 'GET' in self.ALLOWED and self.url:
            url = self.url
            if url != '/':
                url += '/'
                response = self.get(url)
                self.assertRedirects(response, to=self.url, code=301)


class AuthTest(MainBaseTest):
    def test_get_auth(self):
        if 'GET' in self.ALLOWED and self.url:
            self.log_in_user()
            response = self.get()
            self.assertOK(response)
            self.assertLoggedIn(response)

    def test_get_no_auth(self):
        if 'GET' in self.ALLOWED and self.url:
            response = self.get()
            self.assertRedirects(response)

    def test_get_inactive_user(self):
        if 'GET' in self.ALLOWED and self.url:
            self.log_in_user(email='hacker@example.com', is_active=False)
            response = self.get()
            self.assertRedirects(response)

    def test_get_logout(self):
        if 'GET' in self.ALLOWED and self.url:
            self.log_in_user()
            response = self.get()
            self.assertOK(response)
            self.assertLoggedIn(response)
            self.log_out_user()
            response = self.get()
            self.assertRedirects(response)

    def test_get_login_again(self):
        if 'GET' in self.ALLOWED and self.url:
            self.log_in_user()
            response = self.get()
            self.assertOK(response)
            self.assertLoggedIn(response)
            self.log_out_user()
            response = self.get()
            self.assertRedirects(response)
            self.log_in_user()
            response = self.get()
            self.assertOK(response)
            self.assertLoggedIn(response)

    def test_post_auth(self):
        if 'POST' in self.ALLOWED and self.url:
            self.log_in_user()
            response = self.post()
            self.assertOK(response)
            self.assertLoggedIn(response)

    def test_post_no_auth(self):
        if 'POST' in self.ALLOWED and self.url:
            response = self.post()
            self.assertRedirects(response)

    def test_post_inactive(self):
        if 'POST' in self.ALLOWED and self.url:
            self.log_in_user(email='hacker@example.com', is_active=False)
            response = self.post()
            self.assertRedirects(response)

    def test_post_logout(self):
        if 'POST' in self.ALLOWED and self.url:
            self.log_in_user()
            response = self.post()
            self.assertOK(response)
            self.assertLoggedIn(response)
            self.log_out_user()
            response = self.post()
            self.assertRedirects(response)

    def test_post_login_again(self):
        if 'POST' in self.ALLOWED and self.url:
            self.log_in_user()
            response = self.post()
            self.assertOK(response)
            self.assertLoggedIn(response)
            self.log_out_user()
            response = self.post()
            self.assertRedirects(response)
            self.log_in_user()
            response = self.post()
            self.assertOK(response)
            self.assertLoggedIn(response)

    def test_get_inactive_server(self):
        if self.url:
            self.log_in_user()
            self.server.active = False
            self.server.put()
            response = self.get()
            if 'GET' in self.ALLOWED:
                self.assertOK(response)
            else:
                self.assertMethodNotAllowed(response)


class ServerAuthTest(AuthTest):
    def test_get_inactive_server(self):
        if self.url:
            self.log_in_user()
            self.server.active = False
            self.server.put()
            response = self.get()
            if 'GET' in self.ALLOWED:
                self.assertRedirects(response)
            else:
                self.assertMethodNotAllowed(response)
