from testing_utils import fix_sys_path
fix_sys_path()

import json

from google.appengine.api import channel

from agar.test.base_test import BaseTest
from agar.test.web_test import WebTest

import minimock

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
        minimock.mock('models.Lookup.channelers', returns=['client_id'], tracker=None)
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
        minimock.mock('models.Lookup.channelers', returns=['client_1', 'client_2'], tracker=None)
        coal_channel.send_log_line(self.interesting_log_line)
        trace = self.tracker.dump()
        self.assertTrue('client_1' in trace)
        self.assertTrue('client_2' in trace)

    def test_sends_log_line_data_as_json(self):
        js = '{"username": "quazifene", "chat": "is there anybody in there?", "time": "07:01pm", "date": "Mar 23, 2013", "event": "chat", "death_message": null}'
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
        self.assertEqual(None, log_line['death_message'])


class ChannelHandlerTest(BaseTest, WebTest):

    APPLICATION = coal_channel.application

    def tearDown(self):
        super(ChannelHandlerTest, self).tearDown()
        minimock.restore()


class ConnectedHandlerTest(ChannelHandlerTest):

    def test_returns_200_OK(self):
        response = self.post('/_ah/channel/connected/', params={'from': 'client-id'})
        self.assertOK(response)

    def test_adds_client_id_to_lookup_store(self):
        tracker = minimock.TraceTracker()
        minimock.mock('models.Lookup.add_channeler', tracker=tracker)
        self.post('/_ah/channel/connected/', params={'from': 'client-id'})
        self.assertTrue(
            tracker.check("Called models.Lookup.add_channeler(u'client-id')")
        )


class DisconnectedHandlerTest(ChannelHandlerTest):

    def test_returns_200_OK(self):
        response = self.post('/_ah/channel/disconnected/', params={'from': 'client-id'})
        self.assertOK(response)

    def test_removes_client_id_from_lookup_store(self):
        tracker = minimock.TraceTracker()
        minimock.mock('models.Lookup.remove_channeler', tracker=tracker)
        self.post('/_ah/channel/disconnected/', params={'from': 'client-id-1'})
        self.assertTrue(
            tracker.check("Called models.Lookup.remove_channeler(u'client-id-1')")
        )
