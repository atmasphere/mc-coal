from testing_utils import fix_sys_path; fix_sys_path()

import datetime

from google.appengine.ext import ndb

from base_test import BaseTest
from web_test import WebTest

import cron
import models


class StatusCheckTest(BaseTest, WebTest):
    APPLICATION = cron.application

    def setUp(self):
        super(StatusCheckTest, self).setUp()
        self.now = datetime.datetime.utcnow()
        self.server = models.Server.create()
        self.user = models.User(email="admin@example.com", admin=True)
        self.user.put()

    def test_server_ok(self):
        self.server.status = models.SERVER_RUNNING
        self.server.last_ping = self.now
        self.response = self.get("/cron/server/status")
        self.assertOK(self.response)
        server = models.Server.query().get()
        self.assertEqual(models.SERVER_RUNNING, server.status)

    def test_server_unknown(self):
        self.server.status = models.SERVER_RUNNING
        self.server.last_ping = self.now - datetime.timedelta(minutes=6)
        self.response = self.get("/cron/server/status")
        self.assertOK(self.response)
        server = models.Server.query().get()
        self.assertEqual(models.SERVER_UNKNOWN, server.status)
        self.assertEmailSent(to=self.user.email, subject="{0} server status is UNKNOWN".format(self.server.name))
