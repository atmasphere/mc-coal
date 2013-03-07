import os
import sys

for d in os.environ["PATH"].split(":"):
    dev_appserver_path = os.path.join(d, "dev_appserver.py")
    if os.path.isfile(dev_appserver_path):
        sdk_path = os.path.abspath(os.path.dirname(os.path.realpath(dev_appserver_path)))
        sys.path.insert(0, sdk_path)
        import dev_appserver
        dev_appserver.fix_sys_path()

import datetime

from agar.test.base_test import BaseTest
from agar.test.web_test import WebTest

from config import coal_config
import cron
import models


class StatusCheckTest(BaseTest, WebTest):
    APPLICATION = cron.application

    def setUp(self):
        super(StatusCheckTest, self).setUp()
        self.now = datetime.datetime.now()
        self.server = models.Server.global_key().get()
        self.user = models.User(email="admin@example.com", admin=True)
        self.user.put()

    def test_server_ok(self):
        self.server.is_running = True
        self.server.last_ping = self.now
        self.response = self.get("/cron/server/status")
        self.assertOK(self.response)
        server = models.Server.global_key().get()
        self.assertTrue(server.is_running)

    def test_server_unknown(self):
        self.server.is_running = True
        self.server.last_ping = self.now - datetime.timedelta(minutes=6)
        self.response = self.get("/cron/server/status")
        self.assertOK(self.response)
        server = models.Server.global_key().get()
        self.assertIsNone(server.is_running)
        self.assertEmailSent(to=self.user.email, subject="{0} server status is UNKNOWN".format(coal_config.TITLE))
