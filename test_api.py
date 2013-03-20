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

LOGGING_LEVEL = logging.ERROR

TIME_ZONE = 'America/Chicago'
LOG_LINE = 'Test line'
TIME_STAMP_LOG_LINE = '2012-10-07 15:10:09 [INFO] Preparing level "world"'
SERVER_START_LOG_LINE = '2012-10-15 16:05:00 [INFO] Starting minecraft server version 1.3.2'
SERVER_STOP_LOG_LINE = '2012-10-15 16:26:11 [INFO] Stopping server'
OVERLOADED_LOG_LINE = "2012-10-21 00:01:46 [WARNING] Can't keep up! Did the system time change, or is the server overloaded?"
CHAT_LOG_LINE = '2012-10-09 20:46:06 [INFO] <vesicular> yo yo'
DISCONNECT_LOG_LINE = '2012-10-09 20:50:08 [INFO] gumptionthomas lost connection: disconnect.quitting'
DISCONNECT_LOG_LINE_2 = '2013-03-13 23:03:39 [INFO] gumptionthomas lost connection: disconnect.genericReason'
CONNECT_LOG_LINE = '2012-10-09 19:52:55 [INFO] gumptionthomas[/192.168.11.198:59659] logged in with entity id 14698 at (221.41534292614716, 68.0, 239.43154415221068)'
CONNECT_LOG_LINE_2 = '2013-03-08 21:06:34 [INFO] gumptionthomas[/192.168.11.205:50167] logged in with entity id 3583968 at (1168.5659371692745, 63.0, -779.6390153758603)'
ALL_LOG_LINES = [LOG_LINE, TIME_STAMP_LOG_LINE, SERVER_START_LOG_LINE, SERVER_STOP_LOG_LINE, OVERLOADED_LOG_LINE, CHAT_LOG_LINE, DISCONNECT_LOG_LINE, DISCONNECT_LOG_LINE_2, CONNECT_LOG_LINE, CONNECT_LOG_LINE_2]
TIMESTAMP_LOG_LINES = [TIME_STAMP_LOG_LINE, SERVER_START_LOG_LINE, SERVER_STOP_LOG_LINE, OVERLOADED_LOG_LINE, CHAT_LOG_LINE, DISCONNECT_LOG_LINE, DISCONNECT_LOG_LINE_2, CONNECT_LOG_LINE, CONNECT_LOG_LINE_2]


class ApiTest(BaseTest, WebTest):
    APPLICATION = api.application
    URL = None

    def setUp(self):
        super(ApiTest, self).setUp()
        logging.disable(LOGGING_LEVEL)

    def tearDown(self):
        super(ApiTest, self).tearDown()
        logging.disable(logging.NOTSET)

    def get_secure_url(self, url=None):
        url = url or self.URL
        return url + '?p={0}'.format(coal_config.API_PASSWORD)

    def assertCreated(self, response):
        error = u'Response did not return a 201 CREATED (status code was {0})\nBody: {1}'.format(response.status_int, response.body)
        self.assertEqual(response.status_int, 201, error)

    def test_post_no_password(self):
        if self.URL:
            response = self.post(self.URL)
            self.assertForbidden(response)


class PingTest(ApiTest):
    URL = '/api/agent/ping'

    def test_post(self):
        params = {'server_name': 'test'}
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        self.assertIsNone(body['last_line'])
        self.assertIsNone(models.Server.global_key().get().is_running)

    def test_post_no_server_name(self):
        response = self.post(self.get_secure_url())
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertEqual({u'errors': {u'server_name': [u'This field is required.']}}, body)

    def test_post_server_running(self):
        params = {'server_name': 'test', 'is_server_running': True}
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        self.assertIsNone(body['last_line'])
        self.assertTrue(models.Server.global_key().get().is_running)

    def test_post_server_not_running(self):
        params = {'server_name': 'test', 'is_server_running': False}
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        self.assertIsNone(body['last_line'])
        self.assertFalse(models.Server.global_key().get().is_running)

    def test_post_last_line(self):
        params = {'line': TIME_STAMP_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(LogLineTest.URL), params=params)
        self.assertCreated(response)
        params = {'server_name': 'test'}
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        self.assertEqual(TIME_STAMP_LOG_LINE, body['last_line'])


class LogLineTest(ApiTest):
    URL = '/api/agent/log_line'

    def test_post_missing_param(self):
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
        self.assertEqual(1, models.LogLine.query_latest_chats().count())
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
