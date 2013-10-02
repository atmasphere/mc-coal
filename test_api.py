from testing_utils import fix_sys_path; fix_sys_path()

import base64
import datetime
import json
import logging
import os

from google.appengine.ext import blobstore, testbed, deferred

import main
import models
from test_oauth import OauthTest


TIME_ZONE = 'America/Chicago'
LOG_LINE = 'Test line'
IMAGE_PATH = 'static/img/coal_sprite.png'

TIME_STAMP_LOG_LINE = '2012-10-07 15:10:09 [INFO] Preparing level "world"'
SERVER_START_LOG_LINE = '2012-10-15 16:05:00 [INFO] Starting minecraft server version 1.3.2'
SERVER_STOP_LOG_LINE = '2012-10-15 16:26:11 [INFO] Stopping server'
OVERLOADED_LOG_LINE = "2012-10-21 00:01:46 [WARNING] Can't keep up! Did the system time change, or is the server overloaded?"
CHAT_LOG_LINE = '2012-10-09 20:46:06 [INFO] <vesicular> yo yo'
CHAT_LOG_LINE_2 = '2013-04-03 10:27:55 [INFO] [Server] hello'
CHAT_LOG_LINE_3 = '2012-10-09 20:46:05 [INFO] [Server] <vesicular> yo yo'
CHAT_LOG_LINE_4 = '2012-10-09 20:46:05 [INFO] [Server] <t@gmail.com> yo yo'
DISCONNECT_LOG_LINE = '2012-10-09 20:50:08 [INFO] gumptionthomas lost connection: disconnect.quitting'
DISCONNECT_LOG_LINE_2 = '2013-03-13 23:03:39 [INFO] gumptionthomas lost connection: disconnect.genericReason'
CONNECT_LOG_LINE = '2012-10-09 19:52:55 [INFO] gumptionthomas[/192.168.11.198:59659] logged in with entity id 14698 at (221.41534292614716, 68.0, 239.43154415221068)'
CONNECT_LOG_LINE_2 = '2013-03-08 21:06:34 [INFO] gumptionthomas[/192.168.11.205:50167] logged in with entity id 3583968 at (1168.5659371692745, 63.0, -779.6390153758603)'
ALL_LOG_LINES = [LOG_LINE, TIME_STAMP_LOG_LINE, SERVER_START_LOG_LINE, SERVER_STOP_LOG_LINE, OVERLOADED_LOG_LINE, CHAT_LOG_LINE, CHAT_LOG_LINE_2, CHAT_LOG_LINE_3, DISCONNECT_LOG_LINE, DISCONNECT_LOG_LINE_2, CONNECT_LOG_LINE, CONNECT_LOG_LINE_2]
TIMESTAMP_LOG_LINES = [TIME_STAMP_LOG_LINE, SERVER_START_LOG_LINE, SERVER_STOP_LOG_LINE, OVERLOADED_LOG_LINE, CHAT_LOG_LINE, CHAT_LOG_LINE_2, CHAT_LOG_LINE_3, DISCONNECT_LOG_LINE, DISCONNECT_LOG_LINE_2, CONNECT_LOG_LINE, CONNECT_LOG_LINE_2]
TIMESTAMP_LOG_LINES_CRON = [CHAT_LOG_LINE_2, DISCONNECT_LOG_LINE_2, CONNECT_LOG_LINE_2, OVERLOADED_LOG_LINE, SERVER_STOP_LOG_LINE, SERVER_START_LOG_LINE, DISCONNECT_LOG_LINE, CHAT_LOG_LINE, CHAT_LOG_LINE_3, CONNECT_LOG_LINE, TIME_STAMP_LOG_LINE]
CHAT_LOG_LINES_CRON = [CHAT_LOG_LINE_2, CHAT_LOG_LINE, CHAT_LOG_LINE_3]
ANVIL_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas was squashed by a falling anvil'
PRICKED_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas was pricked to death'
CACTUS_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas walked into a cactus whilst trying to escape Skeleton'
CACTUS_DEATH_LOG_LINE_2 = '2013-04-03 10:27:55 [INFO] gumptionthomas walked into a cactus whilst trying to escape vesicular'
SHOT_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas was shot by arrow'
DROWNED_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas drowned'
DROWNED_DEATH_LOG_LINE_2 = '2013-04-03 10:27:55 [INFO] gumptionthomas drowned whilst trying to escape Skeleton'
DROWNED_DEATH_LOG_LINE_3 = '2013-04-03 10:27:55 [INFO] gumptionthomas drowned whilst trying to escape vesicular'
BLEW_UP_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas blew up'
BLEW_UP_DEATH_LOG_LINE_2 = '2013-04-03 10:27:55 [INFO] gumptionthomas was blown up by Creeper'
BLEW_UP_DEATH_LOG_LINE_3 = '2013-04-03 10:27:55 [INFO] gumptionthomas was blown up by vesicular'
FALLING_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas hit the ground too hard'
FALLING_DEATH_LOG_LINE_2 = '2013-04-03 10:27:55 [INFO] gumptionthomas fell off a ladder'
FALLING_DEATH_LOG_LINE_3 = '2013-04-03 10:27:55 [INFO] gumptionthomas fell off some vines'
FALLING_DEATH_LOG_LINE_4 = '2013-04-03 10:27:55 [INFO] gumptionthomas fell out of the water'
FALLING_DEATH_LOG_LINE_5 = '2013-04-03 10:27:55 [INFO] gumptionthomas fell from a high place'
FALLING_DEATH_LOG_LINE_6 = '2013-04-03 10:27:55 [INFO] gumptionthomas fell into a patch of fire'
FALLING_DEATH_LOG_LINE_7 = '2013-04-03 10:27:55 [INFO] gumptionthomas fell into a patch of cacti'
FALLING_DEATH_LOG_LINE_8 = '2013-04-03 10:27:55 [INFO] gumptionthomas was doomed to fall by Skeleton'
FALLING_DEATH_LOG_LINE_9 = '2013-04-03 10:27:55 [INFO] gumptionthomas was doomed to fall by vesicular'
FALLING_DEATH_LOG_LINE_10 = '2013-04-03 10:27:55 [INFO] gumptionthomas was shot off some vines by Skeleton'
FALLING_DEATH_LOG_LINE_11 = '2013-04-03 10:27:55 [INFO] gumptionthomas was shot off some vines by vesicular'
FALLING_DEATH_LOG_LINE_12 = '2013-04-03 10:27:55 [INFO] gumptionthomas was blown from a high place by Creeper'
FIRE_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas went up in flames'
FIRE_DEATH_LOG_LINE_2 = '2013-04-03 10:27:55 [INFO] gumptionthomas burned to death'
FIRE_DEATH_LOG_LINE_3 = '2013-04-03 10:27:55 [INFO] gumptionthomas was burnt to a crisp whilst fighting Skeleton'
FIRE_DEATH_LOG_LINE_4 = '2013-04-03 10:27:55 [INFO] gumptionthomas was burnt to a crisp whilst fighting vesicular'
FIRE_DEATH_LOG_LINE_5 = '2013-04-03 10:27:55 [INFO] gumptionthomas walked into a fire whilst fighting Skeleton'
FIRE_DEATH_LOG_LINE_6 = '2013-04-03 10:27:55 [INFO] gumptionthomas walked into a fire whilst fighting vesicular'
MOB_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas was slain by Skeleton'
MOB_DEATH_LOG_LINE_2 = '2013-04-03 10:27:55 [INFO] gumptionthomas was shot by Skeleton'
MOB_DEATH_LOG_LINE_3 = '2013-04-03 10:27:55 [INFO] gumptionthomas was fireballed by Ghast'
MOB_DEATH_LOG_LINE_4 = '2013-04-03 10:27:55 [INFO] gumptionthomas was killed by Whitch'
MOB_DEATH_LOG_LINE_5 = '2013-04-03 10:27:55 [INFO] gumptionthomas got finished off by Skeleton using Bow'
MOB_DEATH_LOG_LINE_6 = '2013-04-03 10:27:55 [INFO] gumptionthomas was slain by Skeleton using Bow'
LAVA_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas tried to swim in lava'
LAVA_DEATH_LOG_LINE_2 = '2013-04-03 10:27:55 [INFO] gumptionthomas tried to swim in lava while trying to escape Skeleton'
LAVA_DEATH_LOG_LINE_3 = '2013-04-03 10:27:55 [INFO] gumptionthomas tried to swim in lava while trying to escape vesicular'
OTHER_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas died'
PVP_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas got finished off by vesicular using Bow'
PVP_DEATH_LOG_LINE_2 = '2013-04-03 10:27:55 [INFO] gumptionthomas was slain by vesicular using Bow'
PVP_DEATH_LOG_LINE_3 = '2013-04-03 10:27:55 [INFO] gumptionthomas was shot by vesicular'
PVP_DEATH_LOG_LINE_4 = '2013-04-03 10:27:55 [INFO] gumptionthomas was killed by vesicular'
POTION_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas was killed by magic'
STARVATION_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas starved to death'
SUFFOCATION_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas suffocated in a wall'
THORNS_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas was killed while trying to hurt Skeleton'
THORNS_DEATH_LOG_LINE_2 = '2013-04-03 10:27:55 [INFO] gumptionthomas was killed while trying to hurt vesicular'
UNUSED_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas was pummeled by vesicular'
VOID_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas fell out of the world'
VOID_DEATH_LOG_LINE_2 = '2013-04-03 10:27:55 [INFO] gumptionthomas fell from a high place and fell out of the world'
VOID_DEATH_LOG_LINE_3 = '2013-04-03 10:27:55 [INFO] gumptionthomas was knocked into the void by Skeleton'
VOID_DEATH_LOG_LINE_4 = '2013-04-03 10:27:55 [INFO] gumptionthomas was knocked into the void by vesicular'
WITHER_DEATH_LOG_LINE = '2013-04-03 10:27:55 [INFO] gumptionthomas withered away'
DEATH_LOG_LINES_CRON = [ANVIL_DEATH_LOG_LINE, PRICKED_DEATH_LOG_LINE, CACTUS_DEATH_LOG_LINE]

DEATH_LOG_LINES = [
    (ANVIL_DEATH_LOG_LINE, "was squashed by a falling anvil", None, None),
    (PRICKED_DEATH_LOG_LINE, "was pricked to death", None, None),
    (CACTUS_DEATH_LOG_LINE, "walked into a cactus whilst trying to escape Skeleton", "Skeleton", None),
    (CACTUS_DEATH_LOG_LINE_2, "walked into a cactus whilst trying to escape vesicular", "vesicular", None),
    (SHOT_DEATH_LOG_LINE, "was shot by arrow", None, None),
    (DROWNED_DEATH_LOG_LINE, "drowned", None, None),
    (DROWNED_DEATH_LOG_LINE_2, "drowned whilst trying to escape Skeleton", "Skeleton", None),
    (DROWNED_DEATH_LOG_LINE_3, "drowned whilst trying to escape vesicular", "vesicular", None),
    (BLEW_UP_DEATH_LOG_LINE, "blew up", None, None),
    (BLEW_UP_DEATH_LOG_LINE_2, "was blown up by Creeper", "Creeper", None),
    (BLEW_UP_DEATH_LOG_LINE_3, "was blown up by vesicular", "vesicular", None),
    (FALLING_DEATH_LOG_LINE, "hit the ground too hard", None, None),
    (FALLING_DEATH_LOG_LINE_2, "fell off a ladder", None, None),
    (FALLING_DEATH_LOG_LINE_3, "fell off some vines", None, None),
    (FALLING_DEATH_LOG_LINE_4, "fell out of the water", None, None),
    (FALLING_DEATH_LOG_LINE_5, "fell from a high place", None, None),
    (FALLING_DEATH_LOG_LINE_6, "fell into a patch of fire", None, None),
    (FALLING_DEATH_LOG_LINE_7, "fell into a patch of cacti", None, None),
    (FALLING_DEATH_LOG_LINE_8, "was doomed to fall by Skeleton", "Skeleton", None),
    (FALLING_DEATH_LOG_LINE_9, "was doomed to fall by vesicular", "vesicular", None),
    (FALLING_DEATH_LOG_LINE_10, "was shot off some vines by Skeleton", "Skeleton", None),
    (FALLING_DEATH_LOG_LINE_11, "was shot off some vines by vesicular", "vesicular", None),
    (FALLING_DEATH_LOG_LINE_12, "was blown from a high place by Creeper", "Creeper", None),
    (FIRE_DEATH_LOG_LINE, "went up in flames", None, None),
    (FIRE_DEATH_LOG_LINE_2, "burned to death", None, None),
    (FIRE_DEATH_LOG_LINE_3, "was burnt to a crisp whilst fighting Skeleton", "Skeleton", None),
    (FIRE_DEATH_LOG_LINE_4, "was burnt to a crisp whilst fighting vesicular", "vesicular", None),
    (FIRE_DEATH_LOG_LINE_5, "walked into a fire whilst fighting Skeleton", "Skeleton", None),
    (FIRE_DEATH_LOG_LINE_6, "walked into a fire whilst fighting vesicular", "vesicular", None),
    (MOB_DEATH_LOG_LINE, "was slain by Skeleton", "Skeleton", None),
    (MOB_DEATH_LOG_LINE_2, "was shot by Skeleton", "Skeleton", None),
    (MOB_DEATH_LOG_LINE_3, "was fireballed by Ghast", "Ghast", None),
    (MOB_DEATH_LOG_LINE_4, "was killed by Whitch", "Whitch", None),
    (MOB_DEATH_LOG_LINE_5, "got finished off by Skeleton using Bow", "Skeleton", "Bow"),
    (MOB_DEATH_LOG_LINE_6, "was slain by Skeleton using Bow", "Skeleton", "Bow"),
    (LAVA_DEATH_LOG_LINE, "tried to swim in lava", None, None),
    (LAVA_DEATH_LOG_LINE_2, "tried to swim in lava while trying to escape Skeleton", "Skeleton", None),
    (LAVA_DEATH_LOG_LINE_3, "tried to swim in lava while trying to escape vesicular", "vesicular", None),
    (OTHER_DEATH_LOG_LINE, "died", None, None),
    (PVP_DEATH_LOG_LINE, "got finished off by vesicular using Bow", "vesicular", "Bow"),
    (PVP_DEATH_LOG_LINE_2, "was slain by vesicular using Bow", "vesicular", "Bow"),
    (PVP_DEATH_LOG_LINE_3, "was shot by vesicular", "vesicular", None),
    (PVP_DEATH_LOG_LINE_4, "was killed by vesicular", "vesicular", None),
    (POTION_DEATH_LOG_LINE, "was killed by magic", None, None),
    (STARVATION_DEATH_LOG_LINE, "starved to death", None, None),
    (SUFFOCATION_DEATH_LOG_LINE, "suffocated in a wall", None, None),
    (THORNS_DEATH_LOG_LINE, "was killed while trying to hurt Skeleton", "Skeleton", None),
    (THORNS_DEATH_LOG_LINE_2, "was killed while trying to hurt vesicular", "vesicular", None),
    (UNUSED_DEATH_LOG_LINE, "was pummeled by vesicular", "vesicular", None),
    (VOID_DEATH_LOG_LINE, "fell out of the world", None, None),
    (VOID_DEATH_LOG_LINE_2, "fell from a high place and fell out of the world", None, None),
    (VOID_DEATH_LOG_LINE_3, "was knocked into the void by Skeleton", "Skeleton", None),
    (VOID_DEATH_LOG_LINE_4, "was knocked into the void by vesicular", "vesicular", None),
    (WITHER_DEATH_LOG_LINE, "withered away", None, None),
]
TEST_USER_EMAIL = 'admin@example.com'

NUM_PLAYER_FIELDS = 6
NUM_USER_FIELDS = 9
NUM_SERVER_FIELDS =11
NUM_PLAY_SESSION_FIELDS = 11
NUM_LOG_LINE_FIELDS = 14
NUM_CHAT_FIELDS = 9
NUM_DEATH_FIELDS = 9
NUM_SCREENSHOT_FIELDS = 7


class ApiTest(OauthTest):
    APPLICATION = main.application
    URL = None
    ALLOWED = []

    @property
    def url(self):
        return self.URL

    def setUp(self):
        super(ApiTest, self).setUp()
        self.server = models.Server.create()
        self.access_token, self.refresh_token = self.get_tokens()

    def tearDown(self):
        super(ApiTest, self).tearDown()
        logging.disable(logging.NOTSET)

    def assertCreated(self, response):
        error = u'Response did not return a 201 CREATED (status code was {0})\nBody: {1}'.format(response.status_int, response.body)
        self.assertEqual(response.status_int, 201, error)

    def assertMethodNotAllowed(self, response):
        error = u'Response did not return a 405 METHOD NOT ALLOWED (status code was {0})\nBody: {1}'.format(response.status_int, response.body)
        self.assertEqual(response.status_int, 405, error)

    def get(self, url=None, params=None, headers=None, bearer_token=None):
        url = url or self.url
        return super(ApiTest, self).get(url, params=params, headers=headers, bearer_token=bearer_token or getattr(self, 'access_token', None))

    def post(self, url=None, params='', headers=None, upload_files=None, bearer_token=None):
        url = url or self.url
        return super(ApiTest, self).post(url, params=params, headers=headers, upload_files=upload_files, bearer_token=bearer_token or getattr(self, 'access_token', None))

    def test_get_no_auth(self):
        if self.url:
            self.access_token = None
            response = self.get()
            if 'GET' in self.ALLOWED:
                self.assertUnauthorized(response)
            else:
                self.assertMethodNotAllowed(response)

    def test_post_no_auth(self):
        if self.url:
            self.access_token = None
            response = self.post()
            if 'POST' in self.ALLOWED:
                self.assertUnauthorized(response)
            else:
                self.assertMethodNotAllowed(response)


class AgentApiTest(ApiTest):
    def setUp(self):
        super(AgentApiTest, self).setUp()
        self.access_token, self.refresh_token = self.get_agent_tokens()

    def get_agent_tokens(self, email=None):
        agent_client = self.server.agent
        url = '/oauth/token'
        params = {
            'code': agent_client.secret,
            'grant_type': 'authorization_code',
            'client_id': agent_client.client_id,
            'client_secret': agent_client.secret,
            'redirect_uri': '/',
            'scope': 'agent'
        }
        response = self.post(url=url, params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(4, body)
        return (body['access_token'], body['refresh_token'])

    def test_get_unauth(self):
        if self.url:
            self.access_token, self.refresh_token = self.get_tokens()
            response = self.get()
            if 'GET' in self.ALLOWED:
                self.assertUnauthorized(response)
            else:
                self.assertMethodNotAllowed(response)

    def test_post_unauth(self):
        if self.url:
            self.access_token, self.refresh_token = self.get_tokens()
            response = self.post()
            if 'POST' in self.ALLOWED:
                self.assertUnauthorized(response)
            else:
                self.assertMethodNotAllowed(response)


class PingTest(AgentApiTest):
    URL = '/api/agent/ping'
    ALLOWED = ['POST']

    def test_post(self):
        params = {'server_name': 'test'}
        response = self.post(params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        self.assertIsNone(body['last_line'])
        self.assertEmpty(body['commands'])
        self.assertIsNone(models.Server.query().get().is_running)

    def test_post_no_server_name(self):
        logging.disable(logging.ERROR)
        response = self.post()
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertEqual({u'errors': {u'server_name': [u'This field is required.']}}, body)

    def test_post_server_running(self):
        params = {'server_name': 'test', 'is_server_running': True}
        response = self.post(params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        self.assertIsNone(body['last_line'])
        self.assertEmpty(body['commands'])
        self.assertTrue(models.Server.query().get().is_running)

    def test_post_server_not_running(self):
        params = {'server_name': 'test', 'is_server_running': False}
        response = self.post(params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        self.assertIsNone(body['last_line'])
        self.assertEmpty(body['commands'])
        self.assertFalse(models.Server.query().get().is_running)

    def test_post_last_line(self):
        params = {'line': TIME_STAMP_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(url=LogLineTest.URL, params=params)
        self.assertCreated(response)
        params = {'server_name': 'test'}
        response = self.post(params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        self.assertEqual(TIME_STAMP_LOG_LINE, body['last_line'])
        self.assertEmpty(body['commands'])

    def post_level_data(self, now=None, timestamp=None, server_day=None, server_time=None):
        now = now or datetime.datetime.now()
        timestamp = timestamp or now
        params = {
            'server_name': 'test',
            'is_server_running': True,
            'server_day': 10,
            'server_time': 1000,
            'timestamp': timestamp.strftime(u"%Y-%m-%d %H:%M:%S")
        }
        response = self.post(params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        self.assertIsNone(body['last_line'])
        self.assertEmpty(body['commands'])
        return body

    def test_post_level_data(self):
        self.post_level_data()
        server = models.Server.query().get()
        self.assertTrue(server.is_running)
        self.assertEqual(10, server.last_server_day)
        self.assertEqual(1000, server.last_server_time)
        self.assertEqual(server.last_server_day, server.server_day)
        self.assertLess(abs(server.server_time - server.last_server_time), 100) #Within 5 seconds

    def test_post_level_data_past(self):
        now = datetime.datetime.now()
        self.post_level_data(now=now, timestamp=now - datetime.timedelta(seconds=20))
        server = models.Server.query().get()
        self.assertTrue(server.is_running)
        self.assertEqual(10, server.last_server_day)
        self.assertEqual(1000, server.last_server_time)
        self.assertEqual(server.last_server_day, server.server_day)
        self.assertGreaterEqual(server.server_time, 1400)

    def test_post_level_data_day_past(self):
        now = datetime.datetime.now()
        self.post_level_data(now=now, timestamp=now - datetime.timedelta(seconds=1220)) #One game day + 400 ticks
        server = models.Server.query().get()
        self.assertTrue(server.is_running)
        self.assertEqual(10, server.last_server_day)
        self.assertEqual(1000, server.last_server_time)
        self.assertEqual(server.last_server_day, server.server_day)
        self.assertGreaterEqual(server.server_time, 1400)

    def test_post_commands(self):
        commands = []
        for i in range(5):
            command = models.Command.push(self.server.key, 'gumptionthomas', '/say hello world')
            commands.append(command.to_dict)
        params = {'line': TIME_STAMP_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(url=LogLineTest.URL, params=params)
        self.assertCreated(response)
        params = {'server_name': 'test'}
        response = self.post(params=params)
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
        response = self.post(params=params)
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertEqual({u'errors': {u'line': [u'This field is required.']}}, body)
        params = {'line': LOG_LINE}
        response = self.post(params=params)
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertEqual({u'errors': {u'zone': [u'This field is required.']}}, body)
        response = self.post()
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertEqual({u'errors': {u'zone': [u'This field is required.'], u'line': [u'This field is required.']}}, body)

    def test_post_log_line(self):
        params = {'line': LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(params=params)
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
        response = self.post(params=params)
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
        response = self.post(params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual('1.3.2', models.Server.query().get().version)
        self.assertEqual(1, models.LogLine.query().count())
        log_line = models.LogLine.query().get()
        self.assertEqual(SERVER_START_LOG_LINE, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2012, 10, 15, 21, 5), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertEqual(models.STARTING_TAGS, log_line.tags)

    def test_post_server_stop_log_line(self):
        params = {'line': SERVER_STOP_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(params=params)
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
        response = self.post(params=params)
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
        response = self.post(params=params)
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
        player = models.Player.lookup(self.server.key, log_line.username)
        self.assertIsNotNone(player)

    def test_post_chat_log_line_2(self):
        params = {'line': CHAT_LOG_LINE_2, 'zone': TIME_ZONE}
        response = self.post(params=params)
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
        response = self.post(params=params)
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
        player = models.Player.lookup(self.server.key, log_line.username)
        self.assertIsNotNone(player)

    def test_post_chat_log_line_4(self):
        params = {'line': CHAT_LOG_LINE_4, 'zone': TIME_ZONE}
        response = self.post(params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())
        log_line = models.LogLine.query().get()
        self.assertEqual(CHAT_LOG_LINE_4, log_line.line)
        self.assertEqual(TIME_ZONE, log_line.zone)
        self.assertEqual(datetime.datetime(2012, 10, 10, 1, 46, 5), log_line.timestamp)
        self.assertEqual('INFO', log_line.log_level)
        self.assertEqual('t@gmail.com', log_line.username)
        self.assertEqual('yo yo', log_line.chat)
        self.assertEqual(models.CHAT_TAGS, log_line.tags)
        self.assertEqual(0, models.Player.query().count())

    def test_post_disconnect_line(self):
        params = {'line': DISCONNECT_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(params=params)
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
        play_session = models.PlaySession.current(self.server.key, 'gumptionthomas')
        self.assertIsNone(play_session)
        player = models.Player.lookup(self.server.key, log_line.username)
        self.assertIsNone(player.last_login_timestamp)
        self.assertIsNone(player.last_session_duration)
        log_line.key.delete()

        params = {'line': DISCONNECT_LOG_LINE_2, 'zone': TIME_ZONE}
        response = self.post(params=params)
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
        play_session = models.PlaySession.current(self.server.key, 'gumptionthomas')
        self.assertIsNone(play_session)
        player = models.Player.lookup(self.server.key, log_line.username)
        self.assertIsNone(player.last_login_timestamp)
        self.assertIsNone(player.last_session_duration)

    def test_post_connect_line(self):
        params = {'line': CONNECT_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(params=params)
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
        play_session = models.PlaySession.current(self.server.key, 'gumptionthomas')
        self.assertIsNotNone(play_session)
        self.assertEqual(1, models.Player.query().count())
        player = models.Player.lookup(self.server.key, log_line.username)
        self.assertIsNotNone(player)
        self.assertTrue(player.is_playing)
        self.assertEqual(datetime.datetime(2012, 10, 10, 0, 52, 55), player.last_login_timestamp)
        self.assertIsNotNone(player.last_session_duration)
        log_line.key.delete()

        params = {'line': CONNECT_LOG_LINE_2, 'zone': TIME_ZONE}
        response = self.post(params=params)
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
        play_session = models.PlaySession.current(self.server.key, 'gumptionthomas')
        self.assertIsNotNone(play_session)
        self.assertEqual(1, models.Player.query().count())
        player = models.Player.lookup(self.server.key, log_line.username)
        self.assertIsNotNone(player)
        self.assertTrue(player.is_playing)
        self.assertEqual(datetime.datetime(2013, 3, 9, 3, 6, 34), player.last_login_timestamp)
        self.assertIsNotNone(player.last_session_duration)

    def test_post_all(self):
        for line in ALL_LOG_LINES:
            params = {'line': line, 'zone': TIME_ZONE}
            response = self.post(params=params)
            self.assertCreated(response)
            body = json.loads(response.body)
            self.assertLength(0, body)
        self.assertEqual(len(ALL_LOG_LINES), models.LogLine.query().count())
        self.assertEqual(len(TIMESTAMP_LOG_LINES), models.LogLine.query_latest_with_timestamp(self.server.key).count())
        self.assertEqual(1, models.LogLine.query_by_tags(self.server.key, models.OVERLOADED_TAG).count())
        self.assertEqual(3, models.LogLine.query_latest_chats(self.server.key).count())
        self.assertEqual(2, models.LogLine.query_latest_logins(self.server.key).count())
        self.assertEqual(2, models.LogLine.query_latest_logouts(self.server.key).count())

    def test_post_log_line_twice(self):
        params = {'line': LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(params=params)
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())
        response = self.post(params=params)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(0, body)
        self.assertEqual(1, models.LogLine.query().count())

    def test_login_logout(self):
        params = {'line': CONNECT_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(params=params)
        self.assertCreated(response)
        self.assertEqual(1, models.PlaySession.query().count())
        play_session = models.PlaySession.current(self.server.key, 'gumptionthomas')
        self.assertIsNotNone(play_session)
        params = {'line': DISCONNECT_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(params=params)
        self.assertCreated(response)
        self.assertEqual(1, models.PlaySession.query().count())
        play_session = models.PlaySession.current(self.server.key, 'gumptionthomas')
        self.assertIsNone(play_session)

    def test_login_server_stop(self):
        params = {'line': CONNECT_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(params=params)
        self.assertCreated(response)
        self.assertEqual(1, models.PlaySession.query().count())
        play_session = models.PlaySession.current(self.server.key, 'gumptionthomas')
        self.assertIsNotNone(play_session)
        params = {'line': SERVER_STOP_LOG_LINE, 'zone': TIME_ZONE}
        response = self.post(params=params)
        self.assertCreated(response)
        self.assertEqual(1, models.PlaySession.query().count())
        play_session = models.PlaySession.current(self.server.key, 'gumptionthomas')
        self.assertIsNone(play_session)


class DeathLogLineTest(AgentApiTest):
    URL = '/api/agent/log_line'
    ALLOWED = ['POST']

    def test_all_deaths(self):
        for (line, death_message, username_mob, weapon) in DEATH_LOG_LINES:
            params = {'line': line, 'zone': TIME_ZONE}
            response = self.post(params=params)
            self.assertCreated(response)
            self.assertEqual(1, models.LogLine.query().count())
            log_line = models.LogLine.query().get()
            self.assertEqual(line, log_line.line)
            self.assertEqual(TIME_ZONE, log_line.zone)
            self.assertEqual(datetime.datetime(2013, 4, 3, 15, 27, 55), log_line.timestamp)
            self.assertEqual('INFO', log_line.log_level)
            self.assertEqual('gumptionthomas', log_line.username, msg="Incorrect death username: '{0}' [{1}]".format(log_line.username, log_line.line))
            self.assertEqual(death_message, log_line.death_message, msg="Incorrect death message: '{0}' [{1}]".format(log_line.death_message, log_line.line))
            self.assertEqual(username_mob, log_line.username_mob, msg="Incorrect username/mob: '{0}' [{1}]".format(log_line.username_mob, log_line.line))
            self.assertEqual(weapon, log_line.weapon)
            self.assertEqual(models.DEATH_TAGS, log_line.tags)
            self.assertEqual(1, models.Player.query().count())
            player = models.Player.lookup(self.server.key, log_line.username)
            self.assertIsNotNone(player)
            log_line.key.delete()


class MultiPageApiTest(ApiTest):
    def test_get_invalid_cursor(self):
        if self.URL:
            logging.disable(logging.ERROR)
            response = self.get(url='{0}?cursor={1}'.format(self.URL, 'invalid_cursor_xxx'))
            logging.disable(logging.NOTSET)
            self.assertBadRequest(response)
            body = json.loads(response.body)
            errors = body['errors']
            self.assertEqual({'cursor': 'Invalid cursor invalid_cursor_xxx. Details: Incorrect padding'}, errors)

    def test_get_invalid_size(self):
        if self.URL:
            logging.disable(logging.ERROR)
            response = self.get(url='{0}?size={1}'.format(self.URL, 0))
            logging.disable(logging.NOTSET)
            self.assertBadRequest(response)
            body = json.loads(response.body)
            errors = body['errors']
            self.assertEqual({'size': ['Number must be between 1 and 50.']}, errors)

    def test_get_empty_size(self):
        if self.URL:
            logging.disable(logging.ERROR)
            response = self.get(url='{0}?size={1}'.format(self.URL, ''))
            logging.disable(logging.NOTSET)
            self.assertBadRequest(response)
            body = json.loads(response.body)
            errors = body['errors']
            self.assertEqual({'size': ['Not a valid integer value', 'Number must be between 1 and 50.']}, errors)


class KeyApiTest(ApiTest):
    def test_get_invalid_key(self):
        if self.URL:
            url = "{0}/{1}".format(self.URL, 'invalid_key')
            response = self.get(url=url)
            self.assertNotFound(response)


class ServersTest(MultiPageApiTest):
    URL = '/api/v1/data/servers'
    ALLOWED = ['GET']

    def setUp(self):
        super(ServersTest, self).setUp()
        self.servers = [self.server]
        for i in range(4):
            self.servers.append(models.Server.create(name='world {0}'.format(i)))

    def test_get(self):
        response = self.get()
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        reponse_servers = body['servers']
        self.assertLength(len(self.servers), reponse_servers)
        for i, server in enumerate(reponse_servers):
            self.assertEqual(NUM_SERVER_FIELDS, len(server))
            self.assertFalse(server['is_running'])


class ServerKeyTest(KeyApiTest):
    URL = '/api/v1/data/servers'
    ALLOWED = ['GET']

    @property
    def url(self):
        return "{0}/{1}".format(self.URL, self.server.key.urlsafe())

    def setUp(self):
        super(ServerKeyTest, self).setUp()

    def test_get(self):
        response = self.get()
        self.assertOK(response)
        server = json.loads(response.body)
        self.assertEqual(NUM_SERVER_FIELDS, len(server))
        self.assertEqual(self.server.key.urlsafe(), server['key'])
        self.assertEqual(self.server.name, server['name'])
        self.assertFalse(server['is_running'])


class UsersTest(MultiPageApiTest):
    URL = '/api/v1/data/users'
    ALLOWED = ['GET']

    def setUp(self):
        super(UsersTest, self).setUp()
        self.users = [models.User.query().get()]
        for i in range(9):
            user = self.log_in_user(email="user_{0}@test.com".format(i))
            self.log_out_user()
            self.users.append(user)

    def test_get(self):
        response = self.get()
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
    URL = '/api/v1/data/users'
    ALLOWED = ['GET']

    @property
    def url(self):
        return "{0}/{1}".format(self.URL, self.user.key.urlsafe())

    def setUp(self):
        super(UserKeyTest, self).setUp()
        self.user = self.log_in_user("user@test.com")
        self.user.last_login = datetime.datetime.now()
        self.user.put()
        self.log_out_user()

    def test_get(self):
        response = self.get()
        self.assertOK(response)
        user = json.loads(response.body)
        self.assertEqual(NUM_USER_FIELDS, len(user))
        self.assertEqual(self.user.key.urlsafe(), user['key'])
        self.assertEqual(self.user.username, user['username'])
        self.assertIsNotNone(user['last_coal_login'])

    def test_get_self(self):
        self.access_token, self.refresh_token = self.get_tokens(email="user@test.com")
        url = "{0}/{1}".format(self.URL, 'self')
        response = self.get(url=url)
        self.assertOK(response)
        response_user = json.loads(response.body)
        self.assertEqual(NUM_USER_FIELDS, len(response_user))
        self.assertEqual(self.user.key.urlsafe(), response_user['key'])
        self.assertIsNotNone(response_user['last_coal_login'])


class PlayersTest(MultiPageApiTest):
    URL = '/api/v1/data/players'
    ALLOWED = ['GET']

    def setUp(self):
        super(PlayersTest, self).setUp()
        self.players = []
        for i in range(10):
            self.players.append(models.Player.get_or_create(self.server.key, "Player_{0}".format(i)))
            self.players[i].last_login_timestamp = datetime.datetime.now()

    def test_get(self):
        response = self.get()
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
    URL = '/api/v1/data/players'
    ALLOWED = ['GET']

    @property
    def url(self):
        return "{0}/{1}".format(self.URL, self.player.key.urlsafe())

    def setUp(self):
        super(PlayerKeyTest, self).setUp()
        self.player = models.Player.get_or_create(self.server.key, "Test_Player")
        self.player.last_login_timestamp = datetime.datetime.now()

    def test_get(self):
        response = self.get()
        self.assertOK(response)
        player = json.loads(response.body)
        self.assertEqual(NUM_PLAYER_FIELDS, len(player))
        self.assertEqual(self.player.username, player['username'])
        self.assertIsNotNone(player['last_login'])


class PlayerUsernameTest(KeyApiTest):
    URL = '/api/v1/data/players'
    ALLOWED = ['GET']

    @property
    def url(self):
        return "{0}/{1}".format(self.URL, self.player.username)

    def setUp(self):
        super(PlayerUsernameTest, self).setUp()
        self.player = models.Player.get_or_create(self.server.key, "Test_Player")
        self.player.last_login_timestamp = datetime.datetime.now()

    def test_get(self):
        response = self.get()
        self.assertOK(response)
        player = json.loads(response.body)
        self.assertEqual(NUM_PLAYER_FIELDS, len(player))
        self.assertEqual(self.player.username, player['username'])
        self.assertIsNotNone(player['last_login'])


class PlaySessionsTest(MultiPageApiTest):
    URL = '/api/v1/data/sessions'
    ALLOWED = ['GET']

    def setUp(self):
        super(PlaySessionsTest, self).setUp()
        self.now = datetime.datetime.now()
        self.players = []
        for i in range(2):
            self.players.append(models.Player.get_or_create(self.server.key, "Player_{0}".format(i)))
            self.players[i].last_login_timestamp = datetime.datetime.now()
        self.play_sessions = []
        for i in range(10):
            player = self.players[i % 2]
            play_session = models.PlaySession.create(self.server.key, player.username, self.now - datetime.timedelta(seconds=10*i), TIME_ZONE, None)
            self.play_sessions.append(play_session)

    def test_get(self):
        response = self.get()
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        play_sessions = body['sessions']
        self.assertLength(len(self.play_sessions), play_sessions)
        for i, play_session in enumerate(play_sessions):
            self.assertEqual(NUM_PLAY_SESSION_FIELDS, len(play_session))
            self.assertEqual(self.play_sessions[i].username, play_session['username'])
            self.assertIsNotNone(play_session['login_timestamp'])

    def test_get_username(self):
        username = self.players[0].username
        url = "/api/v1/data/players/{0}/sessions".format(username)
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        play_sessions = body['sessions']
        self.assertLength(len(self.play_sessions) / 2, play_sessions)
        for i, play_session in enumerate(play_sessions):
            self.assertEqual(NUM_PLAY_SESSION_FIELDS, len(play_session))
            self.assertEqual(username, play_session['username'])

    def test_get_since_before(self):
        url = "{0}?since={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        play_sessions = body['sessions']
        self.assertLength(1, play_sessions)
        for i, play_session in enumerate(play_sessions):
            self.assertEqual(NUM_PLAY_SESSION_FIELDS, len(play_session))
            self.assertEqual(self.play_sessions[i].username, play_session['username'])
            self.assertIsNotNone(play_session['login_timestamp'])
        url = "{0}?before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        play_sessions = body['sessions']
        self.assertLength(9, play_sessions)
        for i, play_session in enumerate(play_sessions):
            self.assertEqual(NUM_PLAY_SESSION_FIELDS, len(play_session))
            self.assertEqual(self.play_sessions[i+1].username, play_session['username'])
            self.assertIsNotNone(play_session['login_timestamp'])
        url = "{0}?since={1}&before={2}".format(self.URL, self.play_sessions[9].login_timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        play_sessions = body['sessions']
        self.assertLength(9, play_sessions)
        for i, play_session in enumerate(play_sessions):
            self.assertEqual(NUM_PLAY_SESSION_FIELDS, len(play_session))
            self.assertEqual(self.play_sessions[i+1].username, play_session['username'])
            self.assertIsNotNone(play_session['login_timestamp'])
        url = "{0}?since={1}&before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        play_sessions = body['sessions']
        self.assertLength(0, play_sessions)


class PlaySessionKeyTest(KeyApiTest):
    URL = '/api/v1/data/sessions'
    ALLOWED = ['GET']

    @property
    def url(self):
        return "{0}/{1}".format(self.URL, self.play_session.key.urlsafe())

    def setUp(self):
        super(PlaySessionKeyTest, self).setUp()
        self.player = models.Player.get_or_create(self.server.key, "Test_Player")
        self.player.last_login_timestamp = datetime.datetime.now()
        self.play_session = models.PlaySession.create(self.server.key, self.player.username, datetime.datetime.now(), TIME_ZONE, None)

    def test_get(self):
        response = self.get()
        self.assertOK(response)
        play_session = json.loads(response.body)
        self.assertEqual(NUM_PLAY_SESSION_FIELDS, len(play_session))
        self.assertEqual(self.play_session.username, play_session['username'])
        self.assertIsNotNone(play_session['login_timestamp'])


class ChatTest(MultiPageApiTest):
    URL = '/api/v1/data/chats'
    ALLOWED = ['GET', 'POST']

    def setUp(self):
        super(ChatTest, self).setUp()
        self.now = datetime.datetime.now()
        self.players = []
        self.players.append(models.Player.get_or_create(self.server.key, "gumptionthomas"))
        self.players.append(models.Player.get_or_create(self.server.key, "vesicular"))
        self.log_lines = []
        for i in range(len(CHAT_LOG_LINES_CRON)):
            log_line = models.LogLine.create(self.server, CHAT_LOG_LINES_CRON[i], TIME_ZONE)
            self.log_lines.append(log_line)
        log_line = models.LogLine.create(self.server, TIME_STAMP_LOG_LINE, TIME_ZONE)

    def test_get(self):
        response = self.get(url='{0}?size={1}'.format(self.URL, 50))
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
        url = "/api/v1/data/players/{0}/chats".format(username)
        response = self.get(url=url)
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
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
        url = "{0}?before={1}".format(self.URL, self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(len(self.log_lines)-2, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
        url = "{0}?since={1}&before={2}".format(self.URL, self.log_lines[2].timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
        url = "{0}?since={1}&before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(0, log_lines)

    def test_post(self):
        username = "gumptionthomas"
        self.player = models.Player.get_or_create(self.server.key, username)
        self.user.usernames = [username]
        self.user.put()
        chat = u'Hello world...'
        params = {'chat': chat}
        response = self.post(params=params)
        self.assertCreated(response)
        self.assertEqual(1, models.Command.query().count())
        command = models.Command.query().get()
        self.assertEqual(username, command.username)
        self.assertEqual(u'/say {0}'.format(chat), command.command)

    def test_post_no_player(self):
        play_name = self.user.play_name
        nickname = self.user.nickname
        chat = u'Hello world...'
        params = {'chat': chat}
        response = self.post(params=params)
        self.assertCreated(response)
        self.assertEqual(1, models.Command.query().count())
        command = models.Command.query().get()
        self.assertEqual('*{0}'.format(nickname), play_name)
        self.assertEqual(play_name, command.username)
        self.assertEqual(u'/say {0}'.format(chat), command.command)

    def test_post_no_player_no_nickname(self):
        self.user.nickname = None
        self.user.put()
        play_name = self.user.play_name
        email = self.user.email
        chat = u'Hello world...'
        params = {'chat': chat}
        response = self.post(params=params)
        self.assertCreated(response)
        self.assertEqual(1, models.Command.query().count())
        command = models.Command.query().get()
        self.assertEqual(email, play_name)
        self.assertEqual(play_name, command.username)
        self.assertEqual(u'/say {0}'.format(chat), command.command)

    def test_post_no_access_token(self):
        self.access_token = None
        response = self.post(params={'chat': u"Hello world..."})
        self.assertUnauthorized(response)

    def test_post_invalid_access_token(self):
        self.access_token = 'invalid_token'
        response = self.post(params={'chat': u"Hello world..."})
        self.assertUnauthorized(response)


class ChatQueryTest(ChatTest):
    def setUp(self):
        super(ChatQueryTest, self).setUp()
        self.now = datetime.datetime.now()
        self.log_lines = []
        for i in range(25):
            dt = self.now - datetime.timedelta(minutes=i)
            chat_log_line = '{0} [INFO] <gumptionthomas> foobar {1}'.format(dt.strftime("%Y-%m-%d %H:%M:%S"), i)
            log_line = models.LogLine.create(self.server, chat_log_line, TIME_ZONE)
            self.log_lines.append(log_line)

    def test_get(self):
        response = self.get(url='{0}?q={1}'.format(self.URL, 'yo'))
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
        url = "/api/v1/data/players/gumptionthomas/chats?q=foobar"
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        log_lines = body['chats']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])

    def test_get_multi(self):
        response = self.get(url='{0}?q={1}'.format(self.URL, 'foobar'))
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
        response = self.get(url='{0}?q={1}&cursor={2}'.format(self.URL, 'foobar', next_cursor))
        body = json.loads(response.body)
        self.assertLength(2, body)
        next_cursor = body['cursor']
        log_lines = body['chats']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])
            self.assertEqual('foobar {0}'.format(i+10), log_line['chat'])
        response = self.get(url='{0}?q={1}&cursor={2}'.format(self.URL, 'foobar', next_cursor))
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
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
        url = "{0}?q=foobar&before={1}&size=50".format(self.URL, self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(len(self.log_lines)-2, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
        url = "{0}?q=foobar&since={1}&before={2}".format(self.URL, self.log_lines[4].timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(3, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
        url = "{0}?q=foobar&since={1}&before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['chats']
        self.assertLength(0, log_lines)


class ChatKeyTest(KeyApiTest):
    URL = '/api/v1/data/chats'
    ALLOWED = ['GET']

    def setUp(self):
        super(ChatKeyTest, self).setUp()
        self.player = models.Player.get_or_create(self.server.key, "vesicular")
        self.log_line = models.LogLine.create(self.server, CHAT_LOG_LINE, TIME_ZONE)

    @property
    def url(self):
        return "{0}/{1}".format(self.URL, self.log_line.key.urlsafe())

    def test_get(self):
        response = self.get()
        self.assertOK(response)
        log_line = json.loads(response.body)
        self.assertEqual(NUM_CHAT_FIELDS, len(log_line))
        self.assertEqual(self.log_line.key.urlsafe(), log_line['key'])
        self.assertEqual(self.log_line.username, log_line['username'])


class DeathTest(MultiPageApiTest):
    URL = '/api/v1/data/deaths'
    ALLOWED = ['GET']

    def setUp(self):
        super(DeathTest, self).setUp()
        self.now = datetime.datetime.now()
        self.players = []
        self.players.append(models.Player.get_or_create(self.server.key, "gumptionthomas"))
        self.players.append(models.Player.get_or_create(self.server.key, "vesicular"))
        self.log_lines = []
        for i in range(len(DEATH_LOG_LINES_CRON)):
            log_line = models.LogLine.create(self.server, DEATH_LOG_LINES_CRON[i], TIME_ZONE)
            self.log_lines.append(log_line)
        log_line = models.LogLine.create(self.server, TIME_STAMP_LOG_LINE, TIME_ZONE)
        death_log_line = '{0} [INFO] vesicular tried to swim in lava'.format(self.now.strftime("%Y-%m-%d %H:%M:%S"))
        log_line = models.LogLine.create(self.server, death_log_line, TIME_ZONE)
        self.log_lines.insert(0, log_line)

    def test_get(self):
        response = self.get(url='{0}?size={1}'.format(self.URL, 50))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['deaths']
        self.assertLength(len(self.log_lines), log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_DEATH_FIELDS, len(log_line))
            self.assertEqual(self.log_lines[i].death_message, log_line['message'])
            self.assertEqual(self.log_lines[i].username, log_line['username'])
            self.assertIsNotNone(log_line['timestamp'])

    def test_get_username(self):
        username = "gumptionthomas"
        url = "/api/v1/data/players/{0}/deaths".format(username)
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['deaths']
        self.assertLength(3, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_DEATH_FIELDS, len(log_line))
            self.assertEqual(username, log_line['username'])

    def test_get_since_before(self):
        url = "{0}?since={1}".format(self.URL, self.log_lines[0].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['deaths']
        self.assertLength(1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_DEATH_FIELDS, len(log_line))
        url = "{0}?before={1}".format(self.URL, self.log_lines[0].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['deaths']
        self.assertLength(len(self.log_lines)-1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_DEATH_FIELDS, len(log_line))
        url = "{0}?since={1}&before={2}".format(self.URL, self.log_lines[2].timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.log_lines[0].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['deaths']
        self.assertLength(3, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_DEATH_FIELDS, len(log_line))
        url = "{0}?since={1}&before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['deaths']
        self.assertLength(0, log_lines)


class DeathQueryTest(DeathTest):
    def setUp(self):
        super(DeathQueryTest, self).setUp()
        self.now = datetime.datetime.now()
        self.log_lines = []
        for i in range(25):
            dt = self.now - datetime.timedelta(minutes=i)
            death_log_line = '{0} [INFO] gumptionthomas was squashed by a falling anvil'.format(dt.strftime("%Y-%m-%d %H:%M:%S"))
            log_line = models.LogLine.create(self.server, death_log_line, TIME_ZONE)
            self.log_lines.append(log_line)

    def test_get(self):
        response = self.get(url='{0}?q={1}'.format(self.URL, 'cactus'))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['deaths']
        self.assertLength(1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_DEATH_FIELDS, len(log_line))
            self.assertIn('cactus', log_line['line'])
            self.assertIsNotNone(log_line['timestamp'])

    def test_get_username(self):
        url = "/api/v1/data/players/gumptionthomas/deaths?q=anvil"
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        log_lines = body['deaths']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_DEATH_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])

    def test_get_multi(self):
        response = self.get(url='{0}?q={1}'.format(self.URL, 'anvil'))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        next_cursor = body['cursor']
        log_lines = body['deaths']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_DEATH_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])
        response = self.get(url='{0}?q={1}&cursor={2}'.format(self.URL, 'anvil', next_cursor))
        body = json.loads(response.body)
        self.assertLength(2, body)
        next_cursor = body['cursor']
        log_lines = body['deaths']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_DEATH_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])
        response = self.get(url='{0}?q={1}&cursor={2}'.format(self.URL, 'anvil', next_cursor))
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['deaths']
        self.assertLength(6, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_DEATH_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])

    def test_get_since_before(self):
        url = "{0}?q=anvil&since={1}".format(self.URL, self.log_lines[0].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['deaths']
        self.assertLength(1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_DEATH_FIELDS, len(log_line))
        url = "{0}?q=anvil&before={1}&size=50".format(self.URL, self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['deaths']
        self.assertLength(len(self.log_lines)-1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_DEATH_FIELDS, len(log_line))
        url = "{0}?q=anvil&since={1}&before={2}".format(self.URL, self.log_lines[4].timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['deaths']
        self.assertLength(3, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_DEATH_FIELDS, len(log_line))
        url = "{0}?q=anvil&since={1}&before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['deaths']
        self.assertLength(0, log_lines)


class DeathKeyTest(KeyApiTest):
    URL = '/api/v1/data/deaths'
    ALLOWED = ['GET']

    @property
    def url(self):
        return "{0}/{1}".format(self.URL, self.log_line.key.urlsafe())

    def setUp(self):
        super(DeathKeyTest, self).setUp()
        self.player = models.Player.get_or_create(self.server.key, "gumptionthomas")
        self.log_line = models.LogLine.create(self.server, SHOT_DEATH_LOG_LINE, TIME_ZONE)

    def test_get(self):
        response = self.get()
        self.assertOK(response)
        log_line = json.loads(response.body)
        self.assertEqual(NUM_DEATH_FIELDS, len(log_line))
        self.assertEqual(self.log_line.key.urlsafe(), log_line['key'])
        self.assertEqual(self.log_line.username, log_line['username'])


class LogLineDataTest(MultiPageApiTest):
    URL = '/api/v1/data/loglines'
    ALLOWED = ['GET']

    def setUp(self):
        super(LogLineDataTest, self).setUp()
        self.now = datetime.datetime.now()
        self.players = []
        self.players.append(models.Player.get_or_create(self.server.key, "gumptionthomas"))
        self.players.append(models.Player.get_or_create(self.server.key, "vesicular"))
        self.log_lines = []
        for i in range(len(TIMESTAMP_LOG_LINES_CRON)):
            log_line = models.LogLine.create(self.server, TIMESTAMP_LOG_LINES_CRON[i], TIME_ZONE)
            self.log_lines.append(log_line)

    def test_get(self):
        response = self.get(url='{0}?size={1}'.format(self.URL, 50))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['loglines']
        self.assertLength(len(self.log_lines), log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertEqual(self.log_lines[i].line, log_line['line'])
            self.assertIsNotNone(log_line['timestamp'])

    def test_get_username(self):
        username = "gumptionthomas"
        url = "/api/v1/data/players/{0}/loglines".format(username)
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['loglines']
        self.assertLength(4, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertEqual(username, log_line['username'])

    def test_get_since_before(self):
        url = "{0}?since={1}".format(self.URL, self.log_lines[0].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['loglines']
        self.assertLength(1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
        url = "{0}?before={1}".format(self.URL, self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['loglines']
        self.assertLength(len(self.log_lines)-2, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
        url = "{0}?since={1}&before={2}".format(self.URL, self.log_lines[4].timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['loglines']
        self.assertLength(3, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
        url = "{0}?since={1}&before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['loglines']
        self.assertLength(0, log_lines)

    def test_get_chats(self):
        url = "{0}?tag={1}".format(self.URL, 'chat')
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['loglines']
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
            log_line = models.LogLine.create(self.server, chat_log_line, TIME_ZONE)
            self.log_lines.append(log_line)

    def test_get(self):
        response = self.get(url='{0}?q={1}'.format(self.URL, 'yo'))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['loglines']
        self.assertLength(2, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertIn('yo', log_line['line'])
            self.assertIsNotNone(log_line['timestamp'])

    def test_get_username(self):
        url = "/api/v1/data/players/gumptionthomas/loglines?q=foobar"
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        log_lines = body['loglines']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])

    def test_get_multi(self):
        response = self.get('{0}?q={1}&tag=chat'.format(self.URL, 'foobar'))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        next_cursor = body['cursor']
        log_lines = body['loglines']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])
            self.assertEqual('foobar {0}'.format(i), log_line['chat'])
        response = self.get(url='{0}?q={1}&tag=chat&cursor={2}'.format(self.URL, 'foobar', next_cursor))
        body = json.loads(response.body)
        self.assertLength(2, body)
        next_cursor = body['cursor']
        log_lines = body['loglines']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])
            self.assertEqual('foobar {0}'.format(i+10), log_line['chat'])
        response = self.get(url='{0}?q={1}&tag=chat&cursor={2}'.format(self.URL, 'foobar', next_cursor))
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['loglines']
        self.assertLength(5, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])
            self.assertEqual('foobar {0}'.format(i+20), log_line['chat'])

    def test_get_chats(self):
        url = "/api/v1/data/loglines?q=foobar&tag=chat"
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(2, body)
        log_lines = body['loglines']
        self.assertLength(10, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
            self.assertEqual('gumptionthomas', log_line['username'])

    def test_get_since_before(self):
        url = "{0}?q=foobar&since={1}".format(self.URL, self.log_lines[0].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['loglines']
        self.assertLength(1, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
        url = "{0}?q=foobar&before={1}&size=50".format(self.URL, self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['loglines']
        self.assertLength(len(self.log_lines)-2, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
        url = "{0}?q=foobar&since={1}&before={2}".format(self.URL, self.log_lines[4].timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.log_lines[1].timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['loglines']
        self.assertLength(3, log_lines)
        for i, log_line in enumerate(log_lines):
            self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
        url = "{0}?q=foobar&since={1}&before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        log_lines = body['loglines']
        self.assertLength(0, log_lines)


class LogLineKeyDataTest(KeyApiTest):
    URL = '/api/v1/data/loglines'
    ALLOWED = ['GET']

    @property
    def url(self):
        return "{0}/{1}".format(self.URL, self.log_line.key.urlsafe())

    def setUp(self):
        super(LogLineKeyDataTest, self).setUp()
        self.player = models.Player.get_or_create(self.server.key, "gumptionthomas")
        self.log_line = models.LogLine.create(self.server, CONNECT_LOG_LINE, TIME_ZONE)

    def test_get(self):
        response = self.get()
        self.assertOK(response)
        log_line = json.loads(response.body)
        self.assertEqual(NUM_LOG_LINE_FIELDS, len(log_line))
        self.assertEqual(self.log_line.key.urlsafe(), log_line['key'])
        self.assertEqual(self.log_line.username, log_line['username'])


class ScreenShotTest(MultiPageApiTest):
    URL = '/api/v1/data/screenshots'
    ALLOWED = ['GET']

    def setUp(self):
        super(ScreenShotTest, self).setUp()
        self.user.usernames = ['gumptionthomas']
        self.user.put()
        self.now = datetime.datetime.now()
        self.players = []
        self.players.append(models.Player.get_or_create(self.server.key, "gumptionthomas"))
        self.players.append(models.Player.get_or_create(self.server.key, "vesicular"))
        self.screenshots = []
        self.blob_info = self.create_blob_info(IMAGE_PATH)
        for i in range(5):
            screen_shot = models.ScreenShot.create(self.server.key, self.user, blob_info=self.blob_info)
            self.screenshots.insert(0, screen_shot)
        self.assertEqual(5, models.ScreenShot.query().count())
        #For speed, don't actually generate the blurs for these images
        taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        taskqueue_stub.FlushQueue('default')

    @property
    def blobs(self):
        return self.testbed.get_stub('blobstore').storage._blobs

    def run_deferred(self, expected_tasks=1):
        taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        tasks = taskqueue_stub.GetTasks('default')
        self.assertEqual(expected_tasks, len(tasks), "Incorrect number of tasks: was {0}, should be {1}".format(repr(tasks), expected_tasks))
        for task in tasks:
            deferred.run(base64.b64decode(task['body']))

    def create_blob_info(self, path, image_data=None):
        if not image_data:
            image_data = open(path, 'rb').read()
        path = os.path.basename(path)
        self.testbed.get_stub('blobstore').CreateBlob(path, image_data)
        return blobstore.BlobInfo(blobstore.BlobKey(path))

    def test_get(self):
        for i in range(5):
            screen_shot = models.ScreenShot.create(self.server.key, self.user, blob_info=self.blob_info, created=self.now - datetime.timedelta(minutes=1))
            self.screenshots.append(screen_shot)
        self.assertEqual(10, models.ScreenShot.query().count())
        # self.run_deferred(5)
        response = self.get(url='{0}?size={1}'.format(self.URL, 50))
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        screenshots = body['screenshots']
        self.assertLength(len(self.screenshots), screenshots)
        for i, screenshot in enumerate(screenshots):
            self.assertEqual(NUM_SCREENSHOT_FIELDS, len(screenshot))
            self.assertEqual(self.screenshots[i].get_serving_url(), screenshot['original_url'])
            # self.assertEqual(self.screenshots[i].blurred_image_serving_url, screenshot['blurred_url'])
            self.assertEqual(self.screenshots[i].user_key.urlsafe(), screenshot['user_key'])

    def test_get_user(self):
        url = "/api/v1/data/users/{0}/screenshots".format(self.user.key.urlsafe())
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        screenshots = body['screenshots']
        self.assertLength(5, screenshots)
        for i, screenshot in enumerate(screenshots):
            self.assertEqual(NUM_SCREENSHOT_FIELDS, len(screenshot))
            self.assertEqual(self.screenshots[i].get_serving_url(), screenshot['original_url'])
            self.assertEqual(self.screenshots[i].blurred_image_serving_url, screenshot['blurred_url'])
            self.assertEqual(self.screenshots[i].user_key.urlsafe(), screenshot['user_key'])

    def test_get_since_before(self):
        for screen_shot in self.screenshots:
            screen_shot.key.delete()
        import time
        self.screenshots = []
        for i in range(5):
            screen_shot = models.ScreenShot.create(self.server.key, self.user, blob_info=self.blob_info)
            self.screenshots.insert(0, screen_shot)
            time.sleep(1)
        url = "{0}?since={1}".format(self.URL, self.screenshots[0].created.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        screenshots = body['screenshots']
        self.assertLength(1, screenshots)
        for i, screenshot in enumerate(screenshots):
            self.assertEqual(NUM_SCREENSHOT_FIELDS, len(screenshot))
        url = "{0}?before={1}".format(self.URL, self.screenshots[1].created.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        screenshots = body['screenshots']
        self.assertLength(len(self.screenshots)-2, screenshots)
        for i, screenshot in enumerate(screenshots):
            self.assertEqual(NUM_SCREENSHOT_FIELDS, len(screenshot))
        url = "{0}?since={1}&before={2}".format(self.URL, self.screenshots[4].created.strftime("%Y-%m-%d %H:%M:%S"), self.screenshots[1].created.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        screenshots = body['screenshots']
        self.assertLength(3, screenshots)
        for i, screenshot in enumerate(screenshots):
            self.assertEqual(NUM_SCREENSHOT_FIELDS, len(screenshot))
        url = "{0}?since={1}&before={1}".format(self.URL, self.now.strftime("%Y-%m-%d %H:%M:%S"), self.now.strftime("%Y-%m-%d %H:%M:%S"))
        response = self.get(url=url)
        self.assertOK(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        screenshots = body['screenshots']
        self.assertLength(0, screenshots)


class ScreenShotKeyTest(KeyApiTest):
    URL = '/api/v1/data/screenshots'
    ALLOWED = ['GET']

    @property
    def url(self):
        return "{0}/{1}".format(self.URL, self.screenshot.key.urlsafe())

    def setUp(self):
        super(ScreenShotKeyTest, self).setUp()
        self.user.usernames = ['gumptionthomas']
        self.user.put()
        self.now = datetime.datetime.now()
        self.blob_info = self.create_blob_info(IMAGE_PATH)
        self.player = models.Player.get_or_create(self.server.key, "gumptionthomas")
        self.screenshot = models.ScreenShot.create(self.server.key, self.user, blob_info=self.blob_info, created=self.now - datetime.timedelta(minutes=1))
        # self.run_deferred()

    @property
    def blobs(self):
        return self.testbed.get_stub('blobstore').storage._blobs

    def run_deferred(self, expected_tasks=1):
        taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        tasks = taskqueue_stub.GetTasks('default')
        self.assertEqual(expected_tasks, len(tasks), "Incorrect number of tasks: was {0}, should be {1}".format(repr(tasks), expected_tasks))
        for task in tasks:
            deferred.run(base64.b64decode(task['body']))

    def create_blob_info(self, path, image_data=None):
        if not image_data:
            image_data = open(path, 'rb').read()
        path = os.path.basename(path)
        self.testbed.get_stub('blobstore').CreateBlob(path, image_data)
        return blobstore.BlobInfo(blobstore.BlobKey(path))

    def test_get(self):
        response = self.get()
        self.assertOK(response)
        screenshot = json.loads(response.body)
        self.assertEqual(NUM_SCREENSHOT_FIELDS, len(screenshot))
        self.assertEqual(self.screenshot.get_serving_url(), screenshot['original_url'])
        self.assertEqual(self.screenshot.blurred_image_serving_url, screenshot['blurred_url'])
        self.assertEqual(self.screenshot.user.key.urlsafe(), screenshot['user_key'])
