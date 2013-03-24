import os
import sys
import minimock
import json

for d in os.environ["PATH"].split(":"):
    dev_appserver_path = os.path.join(d, "dev_appserver.py")
    if os.path.isfile(dev_appserver_path):
        sdk_path = os.path.abspath(os.path.dirname(os.path.realpath(dev_appserver_path)))
        sys.path.insert(0, sdk_path)
        import dev_appserver
        dev_appserver.fix_sys_path()

from google.appengine.api import channel
from google.appengine.api import memcache
from agar.test.base_test import BaseTest
from agar.test.web_test import WebTest

import channel as coal_channel
import models


class SendLogLineTest(BaseTest):

    INTERESTING_LOG_LINE = '2013-03-23 19:01:19 [INFO] <quazifene> is there anybody in there?'
    UNINTERESTING_LOG_LINE = '2013-03-21 22:27:00 [INFO] Preparing spawn area: 35%'

    def setUp(self):
        super(SendLogLineTest, self).setUp()
        self.interesting_log_line = models.LogLine.create(self.INTERESTING_LOG_LINE, 'US/Central')
        self.uninteresting_log_line = models.LogLine.create(self.UNINTERESTING_LOG_LINE, 'US/Central')
        self.tracker = minimock.TraceTracker()
        minimock.mock('memcache.get', returns=['client_id'], tracker=None)
        minimock.mock('channel.send_message', tracker=self.tracker)

    def tearDown(self):
        super(SendLogLineTest, self).tearDown()
        minimock.restore()

    def test_sends_interesting_log_lines(self):
        coal_channel.send_log_line(self.interesting_log_line)
        trace = self.tracker.dump()
        self.assertTrue('Called channel.send_message' in trace)

    def test_does_not_send_uninteresting_log_lines(self):
        coal_channel.send_log_line(self.uninteresting_log_line)
        trace = self.tracker.dump()
        self.assertTrue('Called channel.send_message' not in trace)

    def test_sends_message_to_all_connected_clients(self):
        minimock.mock('memcache.get', returns=['client_1', 'client_2'], tracker=None)
        coal_channel.send_log_line(self.interesting_log_line)
        trace = self.tracker.dump()
        self.assertTrue('client_1' in trace)
        self.assertTrue('client_2' in trace)

    def test_sends_log_line_data_as_json(self):
        js = '{"date": "Mar 23, 2013", "username": "quazifene", "event": "chat", "chat": "is there anybody in there?", "time": "07:01pm"}'
        coal_channel.send_log_line(self.interesting_log_line)
        self.assertTrue(
            self.tracker.check("""Called channel.send_message(
    'client_id',
    '%s')""" % js)
        )
        log_line = json.loads(js)
        self.assertEqual('chat', log_line['event'])
        self.assertEqual('Mar 23, 2013', log_line['date'])
        self.assertEqual('07:01pm', log_line['time'])
        self.assertEqual('quazifene', log_line['username'])
        self.assertEqual('is there anybody in there?', log_line['chat'])


class ChannelHandlerTest(BaseTest, WebTest):

    APPLICATION = coal_channel.application


class ConnectedHandlerTest(ChannelHandlerTest):

    def test_returns_200_OK(self):
        response = self.post('/_ah/channel/connected/', params={'from': 'client-id'})
        self.assertOK(response)

    def test_saves_client_id_in_memcache_despite_missing_memcache_key(self):
        memcache.delete('channelers')
        self.post('/_ah/channel/connected/', params={'from': 'client-id'})
        self.assertEqual(['client-id'], memcache.get('channelers'))

    def test_saves_client_id_in_memcache(self):
        memcache.set('channelers', ['client-id-1'])
        self.post('/_ah/channel/connected/', params={'from': 'client-id-2'})
        self.assertEqual(['client-id-1', 'client-id-2'], memcache.get('channelers'))

    def test_does_not_save_client_id_in_memcache_if_already_exists_there(self):
        memcache.set('channelers', ['client-id-1', 'client-id-2'])
        self.post('/_ah/channel/connected/', params={'from': 'client-id-2'})
        self.assertEqual(['client-id-1', 'client-id-2'], memcache.get('channelers'))


class DisconnectedHandlerTest(ChannelHandlerTest):

    def setUp(self):
        super(DisconnectedHandlerTest, self).setUp()

    def test_returns_200_OK(self):
        response = self.post('/_ah/channel/disconnected/', params={'from': 'client-id'})
        self.assertOK(response)

    def test_removes_client_id_from_memcache(self):
        memcache.set('channelers', ['client-id-1', 'client-id-2'])
        self.post('/_ah/channel/disconnected/', params={'from': 'client-id-1'})
        self.assertEqual(['client-id-2'], memcache.get('channelers'))

    def test_no_ops_if_memcache_key_is_missing(self):
        memcache.delete('channelers')
        self.post('/_ah/channel/disconnected/', params={'from': 'client-id-1'})
        self.assertIsNone(memcache.get('channelers'))

    def test_no_ops_if_client_id_is_not_in_memcache(self):
        memcache.set('channelers', ['client-id-1'])
        self.post('/_ah/channel/disconnected/', params={'from': 'client-id-2'})
        self.assertEqual(['client-id-1'], memcache.get('channelers'))
