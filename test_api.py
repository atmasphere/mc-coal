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


class ApiTest(BaseTest, WebTest):
    APPLICATION = api.application
    URL = None

    def setUp(self):
        logging.disable(logging.ERROR)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def get_secure_url(self):
        return self.URL + '?p={0}'.format(api.config.API_PASSWORD)

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
        response = self.post(self.get_secure_url(), params={'server_name': 'test'})
        self.assertCreated(response)
        body = json.loads(response.body)
        self.assertLength(1, body)
        self.assertEqual('test', body['server_name'])

    def test_post_no_serial(self):
        response = self.post(self.get_secure_url())
        self.assertBadRequest(response)
        body = json.loads(response.body)
        self.assertEqual({u'errors': {u'server_name': [u'This field is required.']}}, body)
