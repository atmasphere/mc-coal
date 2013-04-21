import datetime
import json
import logging
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
import api
import models

TIME_ZONE = 'America/Chicago'
LOG_LINE = 'Test line'
TIME_STAMP_LOG_LINE = '2012-10-07 15:10:09 [INFO] Preparing level "world"'
SERVER_START_LOG_LINE = '2012-10-15 16:05:00 [INFO] Starting minecraft server version 1.3.2'
SERVER_STOP_LOG_LINE = '2012-10-15 16:26:11 [INFO] Stopping server'
OVERLOADED_LOG_LINE = "2012-10-21 00:01:46 [WARNING] Can't keep up! Did the system time change, or is the server overloaded?"
CHAT_LOG_LINE = '2012-10-09 20:46:06 [INFO] <vesicular> yo yo'
CHAT_LOG_LINE_2 = '2013-04-03 10:27:55 [INFO] [Server] hello'
CHAT_LOG_LINE_3 = '2012-10-09 20:46:05 [INFO] [Server] <vesicular> yo yo'
DISCONNECT_LOG_LINE = '2012-10-09 20:50:08 [INFO] gumptionthomas lost connection: disconnect.quitting'
DISCONNECT_LOG_LINE_2 = '2013-03-13 23:03:39 [INFO] gumptionthomas lost connection: disconnect.genericReason'
CONNECT_LOG_LINE = '2012-10-09 19:52:55 [INFO] gumptionthomas[/192.168.11.198:59659] logged in with entity id 14698 at (221.41534292614716, 68.0, 239.43154415221068)'
CONNECT_LOG_LINE_2 = '2013-03-08 21:06:34 [INFO] gumptionthomas[/192.168.11.205:50167] logged in with entity id 3583968 at (1168.5659371692745, 63.0, -779.6390153758603)'
ALL_LOG_LINES = [LOG_LINE, TIME_STAMP_LOG_LINE, SERVER_START_LOG_LINE, SERVER_STOP_LOG_LINE, OVERLOADED_LOG_LINE, CHAT_LOG_LINE, CHAT_LOG_LINE_2, CHAT_LOG_LINE_3, DISCONNECT_LOG_LINE, DISCONNECT_LOG_LINE_2, CONNECT_LOG_LINE, CONNECT_LOG_LINE_2]
TIMESTAMP_LOG_LINES = [TIME_STAMP_LOG_LINE, SERVER_START_LOG_LINE, SERVER_STOP_LOG_LINE, OVERLOADED_LOG_LINE, CHAT_LOG_LINE, CHAT_LOG_LINE_2, CHAT_LOG_LINE_3, DISCONNECT_LOG_LINE, DISCONNECT_LOG_LINE_2, CONNECT_LOG_LINE, CONNECT_LOG_LINE_2]
TIMESTAMP_LOG_LINES_CRON = [CHAT_LOG_LINE_2, DISCONNECT_LOG_LINE_2, CONNECT_LOG_LINE_2, OVERLOADED_LOG_LINE, SERVER_STOP_LOG_LINE, SERVER_START_LOG_LINE, DISCONNECT_LOG_LINE, CHAT_LOG_LINE, CHAT_LOG_LINE_3, CONNECT_LOG_LINE, TIME_STAMP_LOG_LINE]
CHAT_LOG_LINES_CRON = [CHAT_LOG_LINE_2, CHAT_LOG_LINE, CHAT_LOG_LINE_3]

TEST_USER_EMAIL = 'admin@example.com'

NUM_PLAYER_FIELDS = 6
NUM_USER_FIELDS = 11
NUM_SERVER_FIELDS = 5
NUM_PLAY_SESSION_FIELDS = 11
NUM_LOG_LINE_FIELDS = 14
NUM_CHAT_FIELDS = 9


class ApiTest(BaseTest, WebTest):
    APPLICATION = api.application
    URL = None
    ALLOWED = []

    def setUp(self):
        super(ApiTest, self).setUp()

    def tearDown(self):
        super(ApiTest, self).tearDown()
        logging.disable(logging.NOTSET)

    def get_secure_url(self, url=None):
        url = url or self.URL
        sep = '?'
        if '?' in url:
            sep = '&'
        return url + '{0}p={1}'.format(sep, coal_config.API_PASSWORD)

    def log_in_user(self, email=TEST_USER_EMAIL, is_active=True, is_admin=False):
        super(ApiTest, self).log_in_user(email, is_admin=is_admin)
        response = self.get('/login_callback')
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
        response = self.get('/logout')
        self.auth_cookie = None

    def assertCreated(self, response):
        error = u'Response did not return a 201 CREATED (status code was {0})\nBody: {1}'.format(response.status_int, response.body)
        self.assertEqual(response.status_int, 201, error)

    def assertMethodNotAllowed(self, response):
        error = u'Response did not return a 405 METHOD NOT ALLOWED (status code was {0})\nBody: {1}'.format(response.status_int, response.body)
        self.assertEqual(response.status_int, 405, error)

    def test_get_no_auth(self):
        if self.URL:
            self.log_out_user()
            url = getattr(self, 'url', None) or self.URL
            response = self.get(url)
            if 'GET' in self.ALLOWED:
                self.assertForbidden(response)
            else:
                self.assertMethodNotAllowed(response)

    def test_get_no_password(self):
        if self.URL:
            self.log_in_user()
            url = getattr(self, 'url', None) or self.URL
            response = self.get(url)
            if 'GET' in self.ALLOWED:
                self.assertOK(response)
            else:
                self.assertMethodNotAllowed(response)

    def test_post_no_auth(self):
        if self.URL:
            self.log_out_user()
            url = getattr(self, 'url', None) or self.URL
            response = self.post(url)
            if 'POST' in self.ALLOWED:
                self.assertForbidden(response)
            else:
                self.assertMethodNotAllowed(response)

    def test_post_no_password(self):
        if self.URL:
            self.log_in_user()
            url = getattr(self, 'url', None) or self.URL
            response = self.post(url)
            if 'POST' in self.ALLOWED:
                self.assertOK(response)
            else:
                self.assertMethodNotAllowed(response)


class AgentApiTest(ApiTest):
    def test_post_no_password(self):
        if self.URL:
            self.log_in_user()
            url = getattr(self, 'url', None) or self.URL
            response = self.post(url)
            self.assertForbidden(response)


class PingTest(AgentApiTest):
    URL = '/api/agent/ping'
    ALLOWED = ['POST']

    def test_post(self):
        params = {'server_name': 'test'}
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        self.assertIsNone(body['last_line'])
        self.assertEmpty(body['commands'])
        self.assertIsNone(models.Server.global_key().get().is_running)

    def test_post_no_server_name(self):
        logging.disable(logging.ERROR)
        response = self.post(self.get_secure_url())
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertEqual({u'errors': {u'server_name': [u'This field is required.']}}, body)

    def test_post_server_running(self):
        params = {'server_name': 'test', 'is_server_running': True}
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        self.assertIsNone(body['last_line'])
        self.assertEmpty(body['commands'])
        self.assertTrue(models.Server.global_key().get().is_running)

    def test_post_server_not_running(self):
        params = {'server_name': 'test', 'is_server_running': False}
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        self.assertIsNone(body['last_line'])
        self.assertEmpty(body['commands'])
        self.assertFalse(models.Server.global_key().get().is_running)

    def test_post_last_line(self):
        params = {'line': TIME_STAMP_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(LogLineTest.URL), params=params)
        self.assertCreated(response)
        params = {'server_name': 'test'}
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        self.assertEqual(TIME_STAMP_LOG_LINE, body['last_line'])
        self.assertEmpty(body['commands'])

    def test_post_commands(self):
        commands = []
        for i in range(5):
            command = models.Command.push('gumptionthomas', '/say hello world')
            commands.append(command.to_dict)
        params = {'line': TIME_STAMP_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(LogLineTest.URL), params=params)
        self.assertCreated(response)
        params = {'server_name': 'test'}
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        self.assertEqual(TIME_STAMP_LOG_LINE, body['last_line'])
        self.assertEqual(body['commands'], commands)


class LogLineTest(AgentApiTest):
    URL = '/api/agent/log_line'
    ALLOWED = ['POST']

    def test_post_missing_param(self):
        logging.disable(logging.ERROR)
        params = {'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertEqual({u'errors': {u'line': [u'This field is required.']}}, body)
        params = {'line': LOG_LINE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertEqual({u'errors': {u'zone': [u'This field is required.']}}, body)
        response = self.post(self.get_secure_url())
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertEqual({u'errors': {u'zone': [u'This field is required.'], u'line': [u'This field is required.']}}, body)

    def test_post_log_line(self):
        params = {'line': LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())
        log_line = models.LogLine.query().get()
        self.assertEqual(LOG_LINE, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual([u'unknown'], log_line.tags)

    def test_post_time_stamp_log_line(self):
        params = {'line': TIME_STAMP_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())
        log_line = models.LogLine.query().get()
        self.assertEqual(TIME_STAMP_LOG_LINE, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2012, 10, 7, 20, 10, 9), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertEqual([u'timestamp', u'unknown'], log_line.tags)

    def test_post_server_start_log_line(self):
        params = {'line': SERVER_START_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual('1.3.2', models.Server.global_key().get().version)
        self.assertEqual(1, models.LogLine.query().count())
        log_line = models.LogLine.query().get()
        self.assertEqual(SERVER_START_LOG_LINE, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2012, 10, 15, 21, 5), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertEqual(models.STARTING_TAGS, log_line.tags)

    def test_post_server_stop_log_line(self):
        params = {'line': SERVER_STOP_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())
        log_line = models.LogLine.query().get()
        self.assertEqual(SERVER_STOP_LOG_LINE, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2012, 10, 15, 21, 26, 11), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertEqual(models.STOPPING_TAGS, log_line.tags)

    def test_post_overloaded_log_line(self):
        params = {'line': OVERLOADED_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())
        log_line = models.LogLine.query().get()
        self.assertEqual(OVERLOADED_LOG_LINE, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2012, 10, 21, 5, 1, 46), log_line.timestamp)
        self.assertEqual('WARNING', log_line.log_level)
        self.assertEqual(models.OVERLOADED_TAGS, log_line.tags)

    def test_post_chat_log_line(self):
        params = {'line': CHAT_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())
        log_line = models.LogLine.query().get()
        self.assertEqual(CHAT_LOG_LINE, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2012, 10, 10, 1, 46, 6), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertEqual('vesicular', log_line.username)
        self.assertEqual('yo yo', log_line.chat)
        self.assertEqual(models.CHAT_TAGS, log_line.tags)
        self.assertEqual(1, models.Player.query().count())
        player = models.Player.lookup(log_line.username)
        self.assertIsNotNone(player)

    def test_post_chat_log_line_2(self):
        params = {'line': CHAT_LOG_LINE_2, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())
        log_line = models.LogLine.query().get()
        self.assertEqual(CHAT_LOG_LINE_2, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2013, 4, 3, 15, 27, 55), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertIsNone(log_line.username)
        self.assertEqual('hello', log_line.chat)
        self.assertEqual(models.CHAT_TAGS, log_line.tags)
        self.assertEqual(0, models.Player.query().count())

    def test_post_chat_log_line_3(self):
        params = {'line': CHAT_LOG_LINE_3, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())
        log_line = models.LogLine.query().get()
        self.assertEqual(CHAT_LOG_LINE_3, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2012, 10, 10, 1, 46, 5), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertEqual('vesicular', log_line.username)
        self.assertEqual('yo yo', log_line.chat)
        self.assertEqual(models.CHAT_TAGS, log_line.tags)
        self.assertEqual(1, models.Player.query().count())
        player = models.Player.lookup(log_line.username)
        self.assertIsNotNone(player)

    def test_post_disconnect_line(self):
        params = {'line': DISCONNECT_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())
        log_line = models.LogLine.query().get()
        self.assertEqual(DISCONNECT_LOG_LINE, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2012, 10, 10, 1, 50, 8), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertEqual('gumptionthomas', log_line.username)
        self.assertEqual(models.LOGOUT_TAGS, log_line.tags)
        self.assertEqual(0, models.PlaySession.query().count())
        play_session = models.PlaySession.current('gumptionthomas')
        self.assertIsNone(play_session)
        player = models.Player.lookup(log_line.username)
        self.assertIsNone(player.last_login_timestamp)
        self.assertIsNone(player.last_session_duration)
        log_line.key.delete()

        params = {'line': DISCONNECT_LOG_LINE_2, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())
        log_line = models.LogLine.query().get()
        self.assertEqual(DISCONNECT_LOG_LINE_2, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2013, 3, 14, 4, 3, 39), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertEqual('gumptionthomas', log_line.username)
        self.assertEqual(models.LOGOUT_TAGS, log_line.tags)
        self.assertEqual(0, models.PlaySession.query().count())
        play_session = models.PlaySession.current('gumptionthomas')
        self.assertIsNone(play_session)
        player = models.Player.lookup(log_line.username)
        self.assertIsNone(player.last_login_timestamp)
        self.assertIsNone(player.last_session_duration)

    def test_post_connect_line(self):
        params = {'line': CONNECT_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())
        log_line = models.LogLine.query().get()
        self.assertEqual(CONNECT_LOG_LINE, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2012, 10, 10, 0, 52, 55), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertEqual('gumptionthomas', log_line.username)
        self.assertEqual(models.LOGIN_TAGS, log_line.tags)
        self.assertEqual(1, models.PlaySession.query().count())
        play_session = models.PlaySession.current('gumptionthomas')
        self.assertIsNotNone(play_session)
        self.assertEqual(1, models.Player.query().count())
        player = models.Player.lookup(log_line.username)
        self.assertIsNotNone(player)
        self.assertTrue(player.is_playing)
        self.assertEqual(datetime.datetime(2012, 10, 10, 0, 52, 55), player.last_login_timestamp)
        self.assertIsNotNone(player.last_session_duration)
        log_line.key.delete()

        params = {'line': CONNECT_LOG_LINE_2, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())
        log_line = models.LogLine.query().get()
        self.assertEqual(CONNECT_LOG_LINE_2, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2013, 3, 9, 3, 6, 34), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertEqual('gumptionthomas', log_line.username)
        self.assertEqual(models.LOGIN_TAGS, log_line.tags)
        self.assertEqual(2, models.PlaySession.query().count())
        play_session = models.PlaySession.current('gumptionthomas')
        self.assertIsNotNone(play_session)
        self.assertEqual(1, models.Player.query().count())
        player = models.Player.lookup(log_line.username)
        self.assertIsNotNone(player)
        self.assertTrue(player.is_playing)
        self.assertEqual(datetime.datetime(2013, 3, 9, 3, 6, 34), player.last_login_timestamp)
        self.assertIsNotNone(player.last_session_duration)

    def test_post_all(self):
        for line in ALL_LOG_LINES:
            params = {'line': line, 'zone': TIME_ZONE}
            response = self.post(self.get_secure_url(), params=params)
            self.assertCreated(response)
            body = json.loads(response.body)
            self.assertLength(0, body)
        self.assertEqual(len(ALL_LOG_LINES), models.LogLine.query().count())
        self.assertEqual(len(TIMESTAMP_LOG_LINES), models.LogLine.query_latest_with_timestamp().count())
        self.assertEqual(1, models.LogLine.query_by_tags(models.OVERLOADED_TAG).count())
        self.assertEqual(3, models.LogLine.query_latest_chats().count())
        self.assertEqual(2, models.LogLine.query_latest_logins().count())
        self.assertEqual(2, models.LogLine.query_latest_logouts().count())

    def test_post_log_line_twice(self):
        params = {'line': LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())

    def test_login_logout(self):
        params = {'line': CONNECT_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        self.assertEqual(1, models.PlaySession.query().count())
        play_session = models.PlaySession.current('gumptionthomas')
        self.assertIsNotNone(play_session)
        params = {'line': DISCONNECT_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        self.assertEqual(1, models.PlaySession.query().count())
        play_session = models.PlaySession.current('gumptionthomas')
        self.assertIsNone(play_session)

    def test_login_server_stop(self):
        params = {'line': CONNECT_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        self.assertEqual(1, models.PlaySession.query().count())
        play_session = models.PlaySession.current('gumptionthomas')
        self.assertIsNotNone(play_session)
        params = {'line': SERVER_STOP_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        self.assertEqual(1, models.PlaySession.query().count())
        play_session = models.PlaySession.current('gumptionthomas')
        self.assertIsNone(play_session)


class OAuthTestTest(ApiTest):
    def test_get(self):
        response = self.get("/api/data/oauth_test")
        self.assertOK(response)
        self.assertIn('Consumer Key', response)


class MultiPageApiTest(ApiTest):
    def test_get_invalid_cursor(self):
        if self.URL:
            logging.disable(logging.ERROR)
            response = self.get(self.get_secure_url('{0}?cursor={1}'.format(self.URL, 'invalid_cursor_xxx')))
            logging.disable(logging.NOTSET)
            self.assertBadRequest(response)
            body = json.loads(response.body)
            errors = body['errors']
            self.assertEqual({'cursor': 'Invalid cursor invalid_cursor_xxx. Details: Incorrect padding'}, errors)

    def test_get_invalid_size(self):
        if self.URL:
            logging.disable(logging.ERROR)
            response = self.get(self.get_secure_url('{0}?size={1}'.format(self.URL, 0)))
            logging.disable(logging.NOTSET)
            self.assertBadRequest(response)
            body = json.loads(response.body)
            errors = body['errors']
            self.assertEqual({'size': ['Number must be between 1 and 50.']}, errors)

    def test_get_empty_size(self):
        if self.URL:
            logging.disable(logging.ERROR)
            response = self.get(self.get_secure_url('{0}?size={1}'.format(self.URL, '')))
            logging.disable(logging.NOTSET)
            self.assertBadRequest(response)
            body = json.loads(response.body)
            errors = body['errors']
            self.assertEqual({'size': ['Not a valid integer value', 'Number must be between 1 and 50.']}, errors)


class KeyApiTest(ApiTest):
    def test_get_invalid_key(self):
        if self.URL:
            self.url = "{0}/{1}".format(self.URL, 'invalid_key')
            response = self.get(self.get_secure_url(url=self.url))
            self.assertNotFound(response)


class ServerTest(ApiTest):
    URL = '/api/data/server'
    ALLOWED = ['GET']

    def setUp(self):
        super(ServerTest, self).setUp()

    def test_get(self):
        response = self.get(self.get_secure_url(url=self.URL))
        self.assertOK(response)
        server = json.loads(response.body)
        self.assertEqual(NUM_SERVER_FIELDS, len(server))
        self.assertFalse(server['is_running'])


class UsersTest(MultiPageApiTest):
    URL = '/api/data/user'
    ALLOWED = ['GET']

    def setUp(self):
        super(UsersTest, self).setUp()
        self.users = []
        for i in range(10):
            user = self.log_in_user(email="user_{0}@test.com".format(i))
            self.log_out_user()
            self.users.append(user)

    def test_get(self):
        response = self.get(self.get_secure_url())
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        reponse_users = body['users']
        self.assertLength(len(self.users), reponse_users)
        for i, user in enumerate(reponse_users):
            self.assertEqual(NUM_USER_FIELDS, len(user))
            self.assertEqual(self.users[i].username, user['username'])
            self.assertIsNotNone(user['last_coal_login'])


class UserKeyTest(KeyApiTest):
    URL = '/api/data/user'
    ALLOWED = ['GET']

    def setUp(self):
        super(UserKeyTest, self).setUp()
        self.user = self.log_in_user("user@test.com")
        self.user.last_login = datetime.datetime.now()
        self.user.put()
        self.url = "{0}/{1}".format(self.URL, self.user.key.urlsafe())

    def test_get(self):
        response = self.get(self.get_secure_url(url=self.url))
        self.assertOK(response)
        user = json.loads(response.body)
        self.assertEqual(NUM_USER_FIELDS, len(user))
        self.assertEqual(self.user.key.urlsafe(), user['key'])
        self.assertEqual(self.user.username, user['username'])
        self.assertIsNotNone(user['last_coal_login'])

    def test_get_self(self):
        self.log_out_user()
        self.user = self.log_in_user("example@example.com")
        self.url = "{0}/{1}".format(self.URL, 'self')
        response = self.get(url=self.url)
        self.assertOK(response)
        user = json.loads(response.body)
        self.assertEqual(NUM_USER_FIELDS, len(user))
        self.assertEqual(self.user.key.urlsafe(), user['key'])
        self.assertIsNotNone(user['last_coal_login'])


class PlayersTest(MultiPageApiTest):
    URL = '/api/data/player'
    ALLOWED = ['GET']

    def setUp(self):
        super(PlayersTest, self).setUp()
        self.players = []
        for i in range(10):
            self.players.append(models.Player.get_or_create("Player_{0}".format(i)))
            self.players[i].last_login_timestamp = datetime.datetime.now()

    def test_get(self):
        response = self.get(self.get_secure_url())
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        players = body['players']
        self.assertLength(len(self.players), players)
        for i, player in enumerate(players):
            self.assertEqual(NUM_PLAYER_FIELDS, len(player))
            self.assertEqual(self.players[i].username, player['username'])
            self.assertIsNotNone(player['last_login'])


class PlayerKeyTest(KeyApiTest):
    URL = '/api/data/player'
    ALLOWED = ['GET']

    def setUp(self):
        super(PlayerKeyTest, self).setUp()
        self.player = models.Player.get_or_create("Test_Player")
        self.player.last_login_timestamp = datetime.datetime.now()
        self.url = "{0}/{1}".format(self.URL, self.player.key.urlsafe())

    def test_get(self):
        response = self.get(self.get_secure_url(url=self.url))
        self.assertOK(response)
        player = json.loads(response.body)
        self.assertEqual(NUM_PLAYER_FIELDS, len(player))
        self.assertEqual(self.player.username, player['username'])
        self.assertIsNotNone(player['last_login'])


class PlayerUsernameTest(KeyApiTest):
    URL = '/api/data/player'
    ALLOWED = ['GET']

    def setUp(self):
        super(PlayerUsernameTest, self).setUp()
        self.player = models.Player.get_or_create("Test_Player")
        self.player.last_login_timestamp = datetime.datetime.now()
        self.url = "{0}/{1}".format(self.URL, self.player.username)

    def test_get(self):
        response = self.get(self.get_secure_url(url=self.url))
        self.assertOK(response)
        player = json.loads(response.body)
        self.assertEqual(NUM_PLAYER_FIELDS, len(player))
        self.assertEqual(self.player.username, player['username'])
        self.assertIsNotNone(player['last_login'])


class PlaySessionsTest(MultiPageApiTest):
    URL = '/api/data/play_session'
    ALLOWED = ['GET']

    def setUp(self):
        super(PlaySessionsTest, self).setUp()
        self.now = datetime.datetime.now()
        self.players = []
        for i in range(2):
            self.players.append(models.Player.get_or_create("Player_{0}".format(i)))
            self.players[i].last_login_timestamp = datetime.datetime.now()
        self.play_sessions = []
        for i in range(10):
            player = self.players[i % 2]
            play_session = models.PlaySession.create(player.username, self.now - datetime.timedelta(seconds=10*i), TIME_ZONE, None)
            self.play_sessions.append(play_session)

    def test_get(self):
        response = self.get(self.get_secure_url())
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        play_sessions = body['play_sessions']
        self.assertLength(len(self.play_sessions), play_sessions)
        for i, play_session in enumerate(play_sessions):
            self.assertEqual(NUM_PLAY_SESSION_FIELDS, len(play_session))
            self.assertEqual(self.play_sessions[i].username, play_session['username'])
            self.assertIsNotNone(play_session['login_timestamp'])

    def test_get_username(self):
        username = self.players[0].username
        url = "/api/data/player/{0}/session".format(username)
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        play_sessions = body['play_sessions']
        self.assertLength(len(self.play_sessions) / 2, play_sessions)
        for i, play_session in enumerate(play_sessions):
            self.assertEqual(NUM_PLAY_SESSION_FIELDS, len(play_session))
            self.assertEqual(username, play_session['username'])

    def test_get_since_before(self):
        url = "{0}?since={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        play_sessions = body['play_sessions']
        self.assertLength(1, play_sessions)
        for i, play_session in enumerate(play_sessions):
            self.assertEqual(NUM_PLAY_SESSION_FIELDS, len(play_session))
            self.assertEqual(self.play_sessions[i].username, play_session['username'])
            self.assertIsNotNone(play_session['login_timestamp'])
        url = "{0}?before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        play_sessions = body['play_sessions']
        self.assertLength(9, play_sessions)
        for i, play_session in enumerate(play_sessions):
            self.assertEqual(NUM_PLAY_SESSION_FIELDS, len(play_session))
            self.assertEqual(self.play_sessions[i+1].username, play_session['username'])
            self.assertIsNotNone(play_session['login_timestamp'])
        url = "{0}?since={1}&before={2}".format(self.URL, self.play_sessions[9].login_timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        play_sessions = body['play_sessions']
        self.assertLength(9, play_sessions)
        for i, play_session in enumerate(play_sessions):
            self.assertEqual(NUM_PLAY_SESSION_FIELDS, len(play_session))
            self.assertEqual(self.play_sessions[i+1].username, play_session['username'])
            self.assertIsNotNone(play_session['login_timestamp'])
        url = "{0}?since={1}&before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        play_sessions = body['play_sessions']
        self.assertLength(0, play_sessions)


class PlaySessionKeyTest(KeyApiTest):
    URL = '/api/data/play_session'
    ALLOWED = ['GET']

    def setUp(self):
        super(PlaySessionKeyTest, self).setUp()
        self.player = models.Player.get_or_create("Test_Player")
        self.player.last_login_timestamp = datetime.datetime.now()
        self.play_session = models.PlaySession.create(self.player.username, datetime.datetime.now(), TIME_ZONE, None)
        self.url = "{0}/{1}".format(self.URL, self.play_session.key.urlsafe())

    def test_get(self):
        response = self.get(self.get_secure_url(url=self.url))
        self.assertOK(response)
        play_session = json.loads(response.body)
        self.assertEqual(NUM_PLAY_SESSION_FIELDS, len(play_session))
        self.assertEqual(self.play_session.username, play_session['username'])
        self.assertIsNotNone(play_session['login_timestamp'])


class ChatTest(MultiPageApiTest):
    URL = '/api/data/chat'
    ALLOWED = ['GET', 'POST']

    def setUp(self):
        super(ChatTest, self).setUp()
        self.now = datetime.datetime.now()
        self.players = []
        self.players.append(models.Player.get_or_create("gumptionthomas"))
        self.players.append(models.Player.get_or_create("vesicular"))
        self.log_lines = []
        for i in range(len(CHAT_LOG_LINES_CRON)):
            log_line = models.LogLine.create(CHAT_LOG_LINES_CRON[i], TIME_ZONE)
            self.log_lines.append(log_line)
        log_line = models.LogLine.create(TIME_STAMP_LOG_LINE, TIME_ZONE)

    def test_get(self):
        response = self.get(self.get_secure_url('{0}?size={1}'.format(self.URL, 50)))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(len(self.log_lines), log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
            self.assertEqual(self.log_lines[i].chat, log_line['chat'])
            self.assertEqual(self.log_lines[i].username, log_line['username'])
            self.assertIsNotNone(log_line['timestamp'])

    def test_get_username(self):
        username = "vesicular"
        url = "/api/data/player/{0}/chat".format(username)
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(2, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
            self.assertEqual(username, log_line['username'])

    def test_get_since_before(self):
        url = "{0}?since={1}".format(self.URL, self.log_lines[0].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
        url = "{0}?before={1}".format(self.URL, self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(len(self.log_lines)-2, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
        url = "{0}?since={1}&before={2}".format(self.URL, self.log_lines[2].timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
        url = "{0}?since={1}&before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(0, log_lines)

    def test_post(self):
        user = self.log_in_user()
        username = "gumptionthomas"
        self.player = models.Player.get_or_create(username)
        user.username = username
        user.put()
        chat = u'Hello world...'
        params = {'chat': chat}
        response = self.post(self.URL, params=params)
        self.assertCreated(response)
        self.assertEqual(1, models.Command.query().count())
        command = models.Command.query().get()
        self.assertEqual(username, command.username)
        self.assertEqual(u'/say {0}'.format(chat), command.command)

    def test_post_no_player(self):
        user = self.log_in_user()
        chat = u'Hello world...'
        params = {'chat': chat}
        response = self.post(self.URL, params=params)
        self.assertCreated(response)
        self.assertEqual(1, models.Command.query().count())
        command = models.Command.query().get()
        self.assertEqual(user.email, command.username)
        self.assertEqual(u'/say {0}'.format(chat), command.command)

    def test_post_no_password(self):
            self.log_in_user()
            url = getattr(self, 'url', None) or self.URL
            response = self.post(url, {'chat': u"Hello world..."})
            if 'POST' in self.ALLOWED:
                self.assertCreated(response)
            else:
                self.assertMethodNotAllowed(response)


class ChatQueryTest(ChatTest):
    def setUp(self):
        super(ChatQueryTest, self).setUp()
        self.now = datetime.datetime.now()
        self.log_lines = []
        for i in range(25):
            dt = self.now - datetime.timedelta(minutes=i)
            chat_log_line = '{0} [INFO] <gumptionthomas> foobar {1}'.format(dt.strftime("%Y-%m-%d %H:%M:%S"), i)
            log_line = models.LogLine.create(chat_log_line, TIME_ZONE)
            self.log_lines.append(log_line)

    def test_get(self):
        response = self.get(self.get_secure_url('{0}?q={1}'.format(self.URL, 'yo')))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(2, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
            self.assertIn('yo', log_line['line'])
            self.assertIsNotNone(log_line['timestamp'])

    def test_get_username(self):
        url = "/api/data/player/gumptionthomas/chat?q=foobar"
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        log_lines = body['chats']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])

    def test_get_multi(self):
        response = self.get(self.get_secure_url('{0}?q={1}'.format(self.URL, 'foobar')))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        next_cursor = body['cursor']
        log_lines = body['chats']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])
            self.assertEqual('foobar {0}'.format(i), log_line['chat'])
        response = self.get(self.get_secure_url('{0}?q={1}&cursor={2}'.format(self.URL, 'foobar', next_cursor)))
        body = json.loads(response.body)
        self.assertLength(2, body)
        next_cursor = body['cursor']
        log_lines = body['chats']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])
            self.assertEqual('foobar {0}'.format(i+10), log_line['chat'])
        response = self.get(self.get_secure_url('{0}?q={1}&cursor={2}'.format(self.URL, 'foobar', next_cursor)))
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(5, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])
            self.assertEqual('foobar {0}'.format(i+20), log_line['chat'])

    def test_get_since_before(self):
        url = "{0}?q=foobar&since={1}".format(self.URL, self.log_lines[0].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
        url = "{0}?q=foobar&before={1}&size=50".format(self.URL, self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(len(self.log_lines)-2, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
        url = "{0}?q=foobar&since={1}&before={2}".format(self.URL, self.log_lines[4].timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(3, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
        url = "{0}?q=foobar&since={1}&before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(0, log_lines)


class ChatKeyTest(KeyApiTest):
    URL = '/api/data/chat'
    ALLOWED = ['GET']

    def setUp(self):
        super(ChatKeyTest, self).setUp()
        self.player = models.Player.get_or_create("vesicular")
        self.log_line = models.LogLine.create(CHAT_LOG_LINE, TIME_ZONE)
        self.url = "{0}/{1}".format(self.URL, self.log_line.key.urlsafe())

    def test_get(self):
        response = self.get(self.get_secure_url(url=self.url))
        self.assertOK(response)
        log_line = json.loads(response.body)
        self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
        self.assertEqual(self.log_line.key.urlsafe(), log_line['key'])
        self.assertEqual(self.log_line.username, log_line['username'])


class LogLineDataTest(MultiPageApiTest):
    URL = '/api/data/log_line'
    ALLOWED = ['GET']

    def setUp(self):
        super(LogLineDataTest, self).setUp()
        self.now = datetime.datetime.now()
        self.players = []
        self.players.append(models.Player.get_or_create("gumptionthomas"))
        self.players.append(models.Player.get_or_create("vesicular"))
        self.log_lines = []
        for i in range(len(TIMESTAMP_LOG_LINES_CRON)):
            log_line = models.LogLine.create(TIMESTAMP_LOG_LINES_CRON[i], TIME_ZONE)
            self.log_lines.append(log_line)

    def test_get(self):
        response = self.get(self.get_secure_url('{0}?size={1}'.format(self.URL, 50)))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['log_lines']
        self.assertLength(len(self.log_lines), log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertEqual(self.log_lines[i].line, log_line['line'])
            self.assertIsNotNone(log_line['timestamp'])

    def test_get_username(self):
        username = "gumptionthomas"
        url = "/api/data/player/{0}/log_line".format(username)
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['log_lines']
        self.assertLength(4, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertEqual(username, log_line['username'])

    def test_get_since_before(self):
        url = "{0}?since={1}".format(self.URL, self.log_lines[0].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['log_lines']
        self.assertLength(1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
        url = "{0}?before={1}".format(self.URL, self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['log_lines']
        self.assertLength(len(self.log_lines)-2, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
        url = "{0}?since={1}&before={2}".format(self.URL, self.log_lines[4].timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['log_lines']
        self.assertLength(3, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
        url = "{0}?since={1}&before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['log_lines']
        self.assertLength(0, log_lines)

    def test_get_chats(self):
        url = "{0}?tag={1}".format(self.URL, 'chat')
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['log_lines']
        self.assertLength(3, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertIn('chat', log_line['tags'])


class LogLineDataQueryTest(LogLineDataTest):
    def setUp(self):
        super(LogLineDataQueryTest, self).setUp()
        self.now = datetime.datetime.now()
        self.log_lines = []
        for i in range(25):
            dt = self.now - datetime.timedelta(minutes=i)
            chat_log_line = '{0} [INFO] <gumptionthomas> foobar {1}'.format(dt.strftime("%Y-%m-%d %H:%M:%S"), i)
            log_line = models.LogLine.create(chat_log_line, TIME_ZONE)
            self.log_lines.append(log_line)

    def test_get(self):
        response = self.get(self.get_secure_url('{0}?q={1}'.format(self.URL, 'yo')))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['log_lines']
        self.assertLength(2, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertIn('yo', log_line['line'])
            self.assertIsNotNone(log_line['timestamp'])

    def test_get_username(self):
        url = "/api/data/player/gumptionthomas/log_line?q=foobar"
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        log_lines = body['log_lines']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])

    def test_get_multi(self):
        response = self.get(self.get_secure_url('{0}?q={1}&tag=chat'.format(self.URL, 'foobar')))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        next_cursor = body['cursor']
        log_lines = body['log_lines']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])
            self.assertEqual('foobar {0}'.format(i), log_line['chat'])
        response = self.get(self.get_secure_url('{0}?q={1}&tag=chat&cursor={2}'.format(self.URL, 'foobar', next_cursor)))
        body = json.loads(response.body)
        self.assertLength(2, body)
        next_cursor = body['cursor']
        log_lines = body['log_lines']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])
            self.assertEqual('foobar {0}'.format(i+10), log_line['chat'])
        response = self.get(self.get_secure_url('{0}?q={1}&tag=chat&cursor={2}'.format(self.URL, 'foobar', next_cursor)))
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['log_lines']
        self.assertLength(5, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])
            self.assertEqual('foobar {0}'.format(i+20), log_line['chat'])

    def test_get_chats(self):
        url = "/api/data/log_line?q=foobar&tag=chat"
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        log_lines = body['log_lines']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])

    def test_get_since_before(self):
        url = "{0}?q=foobar&since={1}".format(self.URL, self.log_lines[0].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['log_lines']
        self.assertLength(1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
        url = "{0}?q=foobar&before={1}&size=50".format(self.URL, self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['log_lines']
        self.assertLength(len(self.log_lines)-2, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
        url = "{0}?q=foobar&since={1}&before={2}".format(self.URL, self.log_lines[4].timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['log_lines']
        self.assertLength(3, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
        url = "{0}?q=foobar&since={1}&before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(self.get_secure_url(url=url))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['log_lines']
        self.assertLength(0, log_lines)


class LogLineKeyDataTest(KeyApiTest):
    URL = '/api/data/log_line'
    ALLOWED = ['GET']

    def setUp(self):
        super(LogLineKeyDataTest, self).setUp()
        self.player = models.Player.get_or_create("gumptionthomas")
        self.log_line = models.LogLine.create(CONNECT_LOG_LINE, TIME_ZONE)
        self.url = "{0}/{1}".format(self.URL, self.log_line.key.urlsafe())

    def test_get(self):
        response = self.get(self.get_secure_url(url=self.url))
        self.assertOK(response)
        log_line = json.loads(response.body)
        self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
        self.assertEqual(self.log_line.key.urlsafe(), log_line['key'])
        self.assertEqual(self.log_line.username, log_line['username'])
