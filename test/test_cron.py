import fix_dev_path  # noqa

import datetime

from google.appengine.ext import ndb

from base_test import BaseTest
from web_test import WebTest

import cron
import models
import oauth
import time

from test_oauth import (
    TEST_CLIENT_ID, TEST_REDIRECT_URI, TEST_CLIENT_NAME, TEST_CLIENT_URI, TEST_LOGO_URI, TEST_CLIENT_SECRET,
    TEST_REGISTRATION_ACCESS_TOKEN
)


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


class BackupTest(BaseTest, WebTest):
    APPLICATION = cron.application

    def setUp(self):
        super(BackupTest, self).setUp()
        self.server = models.Server.create()
        self.user = models.User(email="admin@example.com", admin=True)
        self.user.put()

    def test_server_ok(self):
        self.response = self.get("/cron/server/backup")
        self.assertOK(self.response)


class CleanTest(BaseTest, WebTest):
    APPLICATION = cron.application

    def setUp(self):
        super(CleanTest, self).setUp()
        self.user = models.User()
        self.user.put()
        key = ndb.Key(oauth.Client, TEST_CLIENT_ID)
        data = {
            'client_id': TEST_CLIENT_ID,
            'redirect_uris': [TEST_REDIRECT_URI],
            'name': TEST_CLIENT_NAME,
            'uri': TEST_CLIENT_URI,
            'logo_uri': TEST_LOGO_URI,
            'scope': ['data'],
            'secret': TEST_CLIENT_SECRET,
            'secret_expires_at': 0,
            'registration_access_token': TEST_REGISTRATION_ACCESS_TOKEN
        }
        self.client = oauth.Client(key=key, **data)
        self.client.put()
        for i in range(0, 115):
            key = oauth.Token.get_key("token_{0}".format(i))
            access_token = "access_token_{0}".format(i)
            refresh_token = "refresh_token_{0}".format(i)
            token = oauth.Token(
                key=key, access_token=access_token, refresh_token=refresh_token, client_id=TEST_CLIENT_ID,
                user_key=self.user.key, scope=['data'], token_type='Bearer', expires_in=0
            )
            token.put()

    def test_clean(self):
        self.APPLICATION = cron.application
        self.assertEqual(115, oauth.Token.query().count())
        self.response = self.get("/cron/oauth/clean")
        self.assertOK(self.response)
        self.assertEqual(0, oauth.Token.query().count())
