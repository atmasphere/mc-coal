from testing_utils import fix_sys_path; fix_sys_path()

import json

from google.appengine.api import channel as gae_channel

from agar.test.base_test import BaseTest
from agar.test.web_test import WebTest

import minimock

import channel
import models


class ServerChannelsTest(BaseTest):
    def setUp(self):
        super(ServerChannelsTest, self).setUp()

    def test_get_numeric_client_id(self):
        server = models.Server.create()
        models.User.create_user('1234', email='bill@example.com')
        user = models.User.lookup(email='bill@example.com')
        client_id = models.ServerChannels.get_client_id(server.key, user)
        self.assertTrue(client_id.startswith('{0}.{1}'.format(server.key.id(), user.key.id())))
        self.assertEqual(server.key, models.ServerChannels.get_server_key(client_id))

    def test_get_alpha_client_id(self):
        server = models.Server.create(id='test_server')
        models.User.create_user('1234', email='bill@example.com')
        user = models.User.lookup(email='bill@example.com')
        client_id = models.ServerChannels.get_client_id(server.key, user)
        self.assertTrue(client_id.startswith('{0}.{1}'.format(server.key.id(), user.key.id())))
        self.assertEqual(server.key, models.ServerChannels.get_server_key(client_id))


class SendLogLineTest(BaseTest):
    INTERESTING_LOG_LINE = '2013-03-23 19:01:19 [INFO] <quazifene> is there anybody in there?'
    UNINTERESTING_LOG_LINE = '2013-03-21 22:27:00 [INFO] Preparing spawn area: 35%'

    def setUp(self):
        super(SendLogLineTest, self).setUp()
        self.server = models.Server.create()
        self.interesting_log_line = models.LogLine.create(self.server, self.INTERESTING_LOG_LINE, 'US/Central')
        self.uninteresting_log_line = models.LogLine.create(self.server, self.UNINTERESTING_LOG_LINE, 'US/Central')
        self.tracker = minimock.TraceTracker()
        minimock.mock('channel.ServerChannels.get_client_ids', returns=['client_id'], tracker=None)
        minimock.mock('channel.ServerChannels.send_message', tracker=self.tracker)

    def tearDown(self):
        super(SendLogLineTest, self).tearDown()
        minimock.restore()

    def test_sends_interesting_log_lines(self):
        self.interesting_log_line.send_message()
        trace = self.tracker.dump()
        self.assertTrue('Called channel.ServerChannels.send_message' in trace)

    def test_does_not_send_uninteresting_log_lines(self):
        self.uninteresting_log_line.send_message()
        trace = self.tracker.dump()
        self.assertFalse('Called channel.ServerChannels.send_message' in trace)

    def test_sends_message_to_all_connected_clients(self):
        minimock.restore()
        self.tracker = minimock.TraceTracker()
        minimock.mock('channel.ServerChannels.get_client_ids', returns=['client_1', 'client_2'], tracker=None)
        minimock.mock('gae_channel.send_message', tracker=self.tracker)
        self.interesting_log_line.send_message()
        trace = self.tracker.dump()
        self.assertTrue('client_1' in trace)
        self.assertTrue('client_2' in trace)

    def test_sends_log_line_data_as_json(self):
        minimock.restore()
        self.tracker = minimock.TraceTracker()
        minimock.mock('channel.ServerChannels.get_client_ids', returns=['client_id'], tracker=None)
        minimock.mock('gae_channel.send_message', tracker=self.tracker)
        js = '{"username": "quazifene", "chat": "is there anybody in there?", "time": "12:01am", "date": "Mar 24, 2013", "event": "chat", "death_message": null}'
        self.interesting_log_line.send_message()
        minimock.assert_same_trace(self.tracker, """Called gae_channel.send_message(
    'client_id',
    '%s')""" % js
        )
        log_line = json.loads(js)
        self.assertEqual('chat', log_line['event'])
        self.assertEqual('Mar 24, 2013', log_line['date'])
        self.assertEqual('12:01am', log_line['time'])
        self.assertEqual('quazifene', log_line['username'])
        self.assertEqual('is there anybody in there?', log_line['chat'])
        self.assertEqual(None, log_line['death_message'])


class ChannelHandlerTest(BaseTest, WebTest):
    APPLICATION = channel.application

    def tearDown(self):
        super(ChannelHandlerTest, self).tearDown()
        minimock.restore()


class ConnectedHandlerTest(ChannelHandlerTest):
    def test_returns_200_OK(self):
        response = self.post('/_ah/channel/connected/', params={'from': 'client-id'})
        self.assertOK(response)

    def test_adds_client_id_to_lookup_store(self):
        tracker = minimock.TraceTracker()
        minimock.mock('channel.ServerChannels.add_client_id', tracker=tracker)
        self.post('/_ah/channel/connected/', params={'from': 'client-id'})
        self.assertTrue(
            tracker.check("Called channel.ServerChannels.add_client_id(u'client-id')")
        )


class DisconnectedHandlerTest(ChannelHandlerTest):
    def test_returns_200_OK(self):
        response = self.post('/_ah/channel/disconnected/', params={'from': 'client-id'})
        self.assertOK(response)

    def test_removes_client_id_from_lookup_store(self):
        tracker = minimock.TraceTracker()
        minimock.mock('channel.ServerChannels.remove_client_id', tracker=tracker)
        self.post('/_ah/channel/disconnected/', params={'from': 'client-id-1'})
        self.assertTrue(
            tracker.check("Called channel.ServerChannels.remove_client_id(u'client-id-1')")
        )
