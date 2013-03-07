import datetime
import hashlib
import os

from google.appengine.api.users import User

from agar.test.base_test import BaseTest
from agar.test.web_test import WebTest

import cron
from models import Server


class StatusCheckTest(BaseTest, WebTest):
    APPLICATION = cron.application

    def setUp(self):
        super(StatusCheckTest, self).setUp()
        self.now = datetime.datetime.now()
        self.server = Server.global_key().get()
        self.log_in_admin('admin@test.com')

    def log_in_admin(self, email):
        # stolen from dev_appserver_login
        user_id_digest = hashlib.md5(email.lower()).digest()
        user_id = '1' + ''.join(['%02d' % ord(x) for x in user_id_digest])[:20]
        os.environ['USER_EMAIL'] = email
        os.environ['USER_ID'] = user_id
        os.environ['USER_IS_ADMIN'] = '1'
        return User(email=email, _user_id=user_id)

    def test_server_ok(self):
        self.server.is_running = True
        self.server.last_ping = self.now
        self.response = self.get("/cron/server/status")
        self.assertOK(self.response)
        server = Server.global_key().get()
        self.assertTrue(server.is_running)

    def test_server_unknown(self):
        self.server.is_running = True
        self.server.last_ping = self.now - datetime.timedelta(minutes=3)
        self.response = self.get("/cron/server/status")
        self.assertOK(self.response)
        server = Server.global_key().get()
        self.assertIsNone(server.is_running)
