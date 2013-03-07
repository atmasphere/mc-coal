import base64
import datetime
import hashlib
import os

from google.appengine.api import users
from google.appengine.ext import testbed, deferred

from agar.test import BaseTest, WebTest

import cron
import models


class StatusCheckTest(BaseTest, WebTest):
    APPLICATION = cron.application

    def setUp(self):
        super(StatusCheckTest, self).setUp()
        self.now = datetime.datetime.now()
        self.server = models.Server.global_key().get()
        self.log_in_admin('admin@test.com')

    def run_deferred(self, expected_tasks=1):
        taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        tasks = taskqueue_stub.GetTasks('default')
        self.assertEqual(
            expected_tasks,
            len(tasks),
            "Incorrect number of tasks: was {0}, should be {1}".format(repr(tasks), expected_tasks)
        )
        for task in tasks:
            deferred.run(base64.b64decode(task['body']))

    def log_in_admin(self, email):
        # stolen from dev_appserver_login
        user_id_digest = hashlib.md5(email.lower()).digest()
        user_id = '1' + ''.join(['%02d' % ord(x) for x in user_id_digest])[:20]
        os.environ['USER_EMAIL'] = email
        os.environ['USER_ID'] = user_id
        os.environ['USER_IS_ADMIN'] = '1'
        return users.User(email=email, _user_id=user_id)

    def test_server_ok(self):
        self.server.is_running = True
        self.server.last_ping = self.now
        self.response = self.get("/cron/server/status")
        self.assertOK(self.response)
        server = models.Server.global_key().get()
        self.assertTrue(server.is_running)

    def test_server_unknown(self):
        self.server.is_running = True
        self.server.last_ping = self.now - datetime.timedelta(minutes=3)
        self.response = self.get("/cron/server/status")
        self.assertOK(self.response)
        server = models.Server.global_key().get()
        self.assertIsNone(server.is_running)
