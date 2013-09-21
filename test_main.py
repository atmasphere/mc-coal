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

from models import User
import main

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

    def assertCreated(self, response):
        error = u'Response did not return a 201 CREATED (status code was {0})\nBody: {1}'.format(response.status_int, response.body)
        self.assertEqual(response.status_int, 201, error)

    def setUp(self):
        super(MainBaseTest, self).setUp()

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

    def test_get_inactive(self):
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


class HomeTest(AuthTest):
    URL = '/'

    def test_get(self):
        self.log_in_user()
        response = self.get()
        self.assertOK(response)

    def test_get_no_auth(self):
        response = self.get()
        self.assertOK(response)
        self.assertIn('Log In', response.body)

    def test_get_inactive(self):
        self.log_in_user(email='hacker@example.com', is_active=False)
        response = self.get()
        self.assertOK(response)
        self.assertIn('Log Out', response.body)

    def test_get_logout(self):
        self.log_in_user()
        response = self.get()
        self.assertOK(response)
        self.assertLoggedIn(response)
        self.log_out_user()
        response = self.get()
        self.assertOK(response)
        self.assertIn('Log In', response.body)

    def test_get_login_again(self):
        self.log_in_user()
        response = self.get()
        self.assertOK(response)
        self.assertLoggedIn(response)
        self.log_out_user()
        response = self.get()
        self.assertOK(response)
        self.assertIn('Log In', response.body)
        self.log_in_user()
        response = self.get()
        self.assertOK(response)
        self.assertLoggedIn(response)


class UserProfileTest(AuthTest):
    URL = '/profile'

    def test_get(self):
        self.log_in_user()
        response = self.get()
        self.assertOK(response)


class UsernameClaimTest(AuthTest):
    URL = '/players/claim'
    ALLOWED = ['POST']

    def __init__(self, *args, **kwargs):
        super(UsernameClaimTest, self).__init__(*args, **kwargs)
        self.params = {'username': 'steve'}

    def test_post_auth(self):
        self.log_in_user()
        response = self.post(params=self.params)
        self.assertRedirects(response)
        self.assertLoggedIn(response)

    def test_post_no_auth(self):
        response = self.post(params=self.params)
        self.assertRedirects(response)

    def test_post_inactive(self):
        self.log_in_user(email='hacker@example.com', is_active=False)
        response = self.post(params=self.params)
        self.assertRedirects(response)

    def test_post_logout(self):
        self.log_in_user()
        response = self.post(params=self.params)
        self.assertRedirects(response)
        self.assertLoggedIn(response)
        self.log_out_user()
        response = self.post(params=self.params)
        self.assertRedirects(response)

    def test_post_login_again(self):
        self.log_in_user()
        response = self.post()
        self.assertRedirects(response)
        self.assertLoggedIn(response)
        self.log_out_user()
        response = self.post()
        self.assertRedirects(response)
        self.log_in_user()
        response = self.post()
        self.assertRedirects(response)
        self.assertLoggedIn(response)

    def test_post(self):
        self.log_in_user()
        response = self.post(params=self.params)
        self.assertRedirects(response)


class ChatsTest(AuthTest):
    URL = '/chats'

    def test_get(self):
        self.log_in_user()
        response = self.get()
        self.assertOK(response)

    def test_returns_html_content(self):
        self.log_in_user()
        response = self.get()
        self.assertEqual('text/html', response.content_type)


class ChatsInfiniteScrollTest(AuthTest):
    URL = '/chats'

    def test_returns_status_OK(self):
        self.log_in_user()
        response = self.get(headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertOK(response)

    def test_returns_javascript_content(self):
        self.log_in_user()
        response = self.get(headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual('text/javascript', response.content_type)

    def test_response_appends_event_rows(self):
        self.log_in_user()
        response = self.get(headers={'X-Requested-With': 'XMLHttpRequest'})
        response.mustcontain("""$('#live_events').append""")


class PlayersTest(AuthTest):
    URL = '/players'

    def test_get(self):
        self.log_in_user()
        response = self.get()
        self.assertOK(response)


class PlaySessionsTest(AuthTest):
    URL = '/sessions'

    def test_get(self):
        self.log_in_user()
        response = self.get()
        self.assertOK(response)


class ScreenShotUploadTest(AuthTest):
    URL = '/screen_shot_upload'

    def test_get(self):
        self.log_in_user()
        response = self.get()
        self.assertOK(response)
        self.assertIn("http://localhost/_ah/upload/", response.body)

    # def test_post(self):
    #     self.log_in_user()
    #     response = self.get()
    #     body = response.body
    #     i = body.index("http://localhost/")
    #     j = body.index('"', i)
    #     url = body[i:j]
    #     self.post(url, {'file': None})
    #     self.assertRedirects(response, '/')


class AdminTest(AuthTest):
    URL = '/admin'

    def test_get_auth(self):
        self.log_in_admin()
        response = self.get()
        self.assertOK(response)
        self.assertLoggedIn(response)

    def test_get_inactive(self):
        self.log_in_user(email="admin@example.com", is_admin=True)
        self.log_out_user()
        super(AdminTest, self).test_get_inactive()

    def test_get_login_again(self):
        self.log_in_admin()
        response = self.get()
        self.assertOK(response)
        self.assertLoggedIn(response)
        self.log_out_user()
        response = self.get()
        self.assertRedirects(response)
        self.log_in_admin()
        response = self.get()
        self.assertOK(response)
        self.assertLoggedIn(response)

    def test_get_logout(self):
        self.log_in_admin()
        response = self.get()
        self.assertOK(response)
        self.assertLoggedIn(response)
        self.log_out_user()
        response = self.get()
        self.assertRedirects(response)

    def test_get_not_admin(self):
        self.log_in_user(email="admin@example.com", is_admin=True)
        self.log_out_user()
        self.log_in_user()
        response = self.get()
        self.assertRedirects(response)

    def test_get_first_user(self):
        self.log_in_user()
        self.assertFalse(self.current_user.admin)
        response = self.get()
        self.assertOK(response)
        self.assertLoggedIn(response)
        self.assertTrue(self.current_user.admin)


class UsersTest(AuthTest):
    URL = '/admin/users'

    def test_get_auth(self):
        self.log_in_admin()
        response = self.get()
        self.assertOK(response)
        self.assertLoggedIn(response)

    def test_get_inactive(self):
        self.log_in_user(email="admin@example.com", is_admin=True)
        self.log_out_user()
        super(UsersTest, self).test_get_inactive()

    def test_get_login_again(self):
        self.log_in_admin()
        response = self.get()
        self.assertOK(response)
        self.assertLoggedIn(response)
        self.log_out_user()
        response = self.get()
        self.assertRedirects(response)
        self.log_in_admin()
        response = self.get()
        self.assertOK(response)
        self.assertLoggedIn(response)

    def test_get_logout(self):
        self.log_in_admin()
        response = self.get()
        self.assertOK(response)
        self.assertLoggedIn(response)
        self.log_out_user()
        response = self.get()
        self.assertRedirects(response)

    def test_get_not_admin(self):
        self.log_in_user(email="admin@example.com", is_admin=True)
        self.log_out_user()
        self.log_in_user()
        response = self.get()
        self.assertRedirects(response)
