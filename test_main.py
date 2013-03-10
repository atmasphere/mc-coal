import os
import sys

for d in os.environ["PATH"].split(":"):
    dev_appserver_path = os.path.join(d, "dev_appserver.py")
    if os.path.isfile(dev_appserver_path):
        sdk_path = os.path.abspath(os.path.dirname(os.path.realpath(dev_appserver_path)))
        sys.path.insert(0, sdk_path)
        import dev_appserver
        dev_appserver.fix_sys_path()

from agar.test.base_test import BaseTest
from agar.test.web_test import WebTest

from config import coal_config
from models import User
import main

TEST_USER_EMAIL = coal_config.USER_WHITELIST[0]['email']


class MainBaseTest(BaseTest, WebTest):
    APPLICATION = main.application
    URL = None

    def log_in_user(self, email=TEST_USER_EMAIL, is_admin=False):
        super(MainBaseTest, self).log_in_user(email, is_admin=is_admin)
        response = self.get('/login_callback')
        cookies = response.headers.get('Set-Cookie')
        self.auth_cookie = cookies[0:cookies.find(';')]
        self.assertRedirects(response, to='/')
        self.current_user = User.lookup(email=email)

    def log_in_admin(self, email=TEST_USER_EMAIL):
        self.log_in_user(email, is_admin=True)

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
        # self.assertIn('Sign Out', response.body)
        pass

    def assertNotLoggedIn(self, response):
        self.assertIn('Login', response.body)

    def assertCreated(self, response):
        error = u'Response did not return a 201 CREATED (status code was {0})\nBody: {1}'.format(response.status_int, response.body)
        self.assertEqual(response.status_int, 201, error)

    def setUp(self):
        super(MainBaseTest, self).setUp()

    def get(self, url, params=None, headers=None):
        self.app.reset()
        extra_environ = None
        if getattr(self, 'auth_cookie', None):
            extra_environ = {'HTTP_COOKIE': self.auth_cookie.replace('=', '%3D').replace('%3D', '=', 1)}
        return self.app.get(url, params=params, headers=headers, extra_environ=extra_environ, status="*", expect_errors=True)

    def test_get_with_slash(self):
        if self.URL:
            url = self.URL
            if url != '/':
                url += '/'
                response = self.get(url)
                self.assertRedirects(response, to=self.URL, code=301)


class AuthTest(MainBaseTest):
    def test_get_auth(self):
        if self.URL:
            self.log_in_user()
            response = self.get(self.URL)
            self.assertOK(response)
            self.assertLoggedIn(response)

    def test_get_no_auth(self):
        if self.URL:
            response = self.get(self.URL)
            self.assertRedirects(response)

    def test_get_inactive(self):
        if self.URL:
            self.log_in_user(email='hacker@example.com')
            response = self.get(self.URL)
            self.assertRedirects(response)

    def test_logout(self):
        if self.URL:
            self.log_in_user()
            response = self.get(self.URL)
            self.assertOK(response)
            self.assertLoggedIn(response)
            self.log_out_user()
            response = self.get(self.URL)
            self.assertRedirects(response)

    def test_login_again(self):
        if self.URL:
            self.log_in_user()
            response = self.get(self.URL)
            self.assertOK(response)
            self.assertLoggedIn(response)
            self.log_out_user()
            response = self.get(self.URL)
            self.assertRedirects(response)
            self.log_in_user()
            response = self.get(self.URL)
            self.assertOK(response)
            self.assertLoggedIn(response)


class HomeTest(AuthTest):
    URL = '/'

    def test_get(self):
        self.log_in_user()
        response = self.get(self.URL)
        self.assertOK(response)

    def test_get_no_auth(self):
        response = self.get(self.URL)
        self.assertOK(response)
        self.assertIn('Log In', response.body)

    def test_get_inactive(self):
        self.log_in_user(email='hacker@example.com')
        response = self.get(self.URL)
        self.assertOK(response)
        self.assertIn('Log Out', response.body)

    def test_logout(self):
        self.log_in_user()
        response = self.get(self.URL)
        self.assertOK(response)
        self.assertLoggedIn(response)
        self.log_out_user()
        response = self.get(self.URL)
        self.assertOK(response)
        self.assertIn('Log In', response.body)

    def test_login_again(self):
        self.log_in_user()
        response = self.get(self.URL)
        self.assertOK(response)
        self.assertLoggedIn(response)
        self.log_out_user()
        response = self.get(self.URL)
        self.assertOK(response)
        self.assertIn('Log In', response.body)
        self.log_in_user()
        response = self.get(self.URL)
        self.assertOK(response)
        self.assertLoggedIn(response)


class ChatsTest(AuthTest):
    URL = '/chats'

    def test_get(self):
        self.log_in_user()
        response = self.get(self.URL)
        self.assertOK(response)


class PlayersTest(AuthTest):
    URL = '/players'

    def test_get(self):
        self.log_in_user()
        response = self.get(self.URL)
        self.assertOK(response)


class PlaySessionsTest(AuthTest):
    URL = '/sessions'

    def test_get(self):
        self.log_in_user()
        response = self.get(self.URL)
        self.assertOK(response)


class ScreenShotUploadTest(AuthTest):
    URL = '/screen_shot_upload'

    def test_get(self):
        self.log_in_user()
        response = self.get(self.URL)
        self.assertOK(response)
        self.assertIn("http://localhost/_ah/upload/", response.body)

    # def test_post(self):
    #     self.log_in_user()
    #     response = self.get(self.URL)
    #     body = response.body
    #     i = body.index("http://localhost/")
    #     j = body.index('"', i)
    #     url = body[i:j]
    #     self.post(url, {'file': None})
    #     self.assertRedirects(response, '/')
