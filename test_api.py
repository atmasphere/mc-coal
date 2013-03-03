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

import api
from models import LogLine, TimeStampLogLine, ConnectLine, DisconnectLine, ChatLine

TIME_ZONE = 'America/Chicago'
LOG_LINE = 'Test line'
TIME_STAMP_LOG_LINE = '2012-10-07 15:10:09 [INFO] Preparing level "world"'
CHAT_LINE = '2012-10-09 20:46:06 [INFO] <vesicular> yo yo'
DISCONNECT_LINE = '2012-10-09 20:50:08 [INFO] gumptionthomas lost connection: disconnect.quitting'
CONNECT_LINE = '2012-10-09 19:52:55 [INFO] gumptionthomas[/192.168.11.198:59659] logged in with entity id 14698 at (221.41534292614716, 68.0, 239.43154415221068)'


class ApiTest(BaseTest, WebTest):
    APPLICATION = api.application
    URL = None

    def setUp(self):
        super(ApiTest, self).setUp()
        logging.disable(logging.ERROR)

    def tearDown(self):
        super(ApiTest, self).tearDown()
        logging.disable(logging.NOTSET)

    def get_secure_url(self, url=None):
        url = url or self.URL
        return url + '?p={0}'.format(api.config.API_PASSWORD)

    def assertCreated(self, response):
        error = u'Response did not return a 201 CREATED (status code was {0})\nBody: {1}'.format(response.status_int, response.body)
        self.assertEqual(response.status_int, 201, error)

    def test_post_no_password(self):
        if self.URL:
            response = self.post(self.URL)
            self.assertForbidden(response)


class PingTest(ApiTest):
    URL = '/api/ping'

    def test_post(self):
        params = {'server_name': 'test'}
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        self.assertIsNone(body['last_line'])

    def test_post_no_server_name(self):
        response = self.post(self.get_secure_url())
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertEqual({u'errors': {u'server_name': [u'This field is required.']}}, body)

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
    URL = '/api/log_line'

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
        self.assertEqual(1, LogLine.query().count())
        log_line = LogLine.query().get()
        self.assertEqual(LOG_LINE, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)

    def test_post_time_stamp_log_line(self):
        params = {'line': TIME_STAMP_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, TimeStampLogLine.query().count())
        log_line = TimeStampLogLine.query().get()
        self.assertEqual(TIME_STAMP_LOG_LINE, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2012, 10, 7, 20, 10, 9), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)

    def test_post_chat_log_line(self):
        params = {'line': CHAT_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, ChatLine.query().count())
        log_line = ChatLine.query().get()
        self.assertEqual(CHAT_LINE, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2012, 10, 10, 1, 46, 6), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertEqual('vesicular', log_line.username)
        self.assertEqual('yo yo', log_line.chat)

    def test_post_disconnect_line(self):
        params = {'line': DISCONNECT_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, DisconnectLine.query().count())
        log_line = DisconnectLine.query().get()
        self.assertEqual(DISCONNECT_LINE, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2012, 10, 10, 1, 50, 8), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertEqual('gumptionthomas', log_line.username)

    def test_post_connect_line(self):
        params = {'line': CONNECT_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, ConnectLine.query().count())
        log_line = ConnectLine.query().get()
        self.assertEqual(CONNECT_LINE, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2012, 10, 10, 0, 52, 55), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertEqual('gumptionthomas', log_line.username)

    def test_post_log_line_twice(self):
        params = {'line': LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, LogLine.query().count())
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, LogLine.query().count())

    def test_post_time_stamp_log_line_twice(self):
        params = {'line': TIME_STAMP_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, TimeStampLogLine.query().count())
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, TimeStampLogLine.query().count())

    def test_post_chat_log_line_twice(self):
        params = {'line': CHAT_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, ChatLine.query().count())
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, ChatLine.query().count())

    def test_post_disconnect_line_twice(self):
        params = {'line': DISCONNECT_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, DisconnectLine.query().count())
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, DisconnectLine.query().count())

    def test_post_connect_line_twice(self):
        params = {'line': CONNECT_LINE, 'zone': TIME_ZONE}
        response = self.post(self.get_secure_url(), params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, ConnectLine.query().count())
        response = self.post(self.get_secure_url(), params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, ConnectLine.query().count())
