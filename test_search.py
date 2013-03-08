import os
import sys

for d in os.environ["PATH"].split(":"):
    dev_appserver_path = os.path.join(d, "dev_appserver.py")
    if os.path.isfile(dev_appserver_path):
        sdk_path = os.path.abspath(os.path.dirname(os.path.realpath(dev_appserver_path)))
        sys.path.insert(0, sdk_path)
        import dev_appserver
        dev_appserver.fix_sys_path()

from pytz.gae import pytz

from agar.test.base_test import BaseTest

import api
import main
import models
import search

from test_api import ALL_LOG_LINES


class SearchTest(BaseTest):
    APPLICATION = main.application

    def setUp(self):
        super(SearchTest, self).setUp()
        self.log_lines = []
        tz = pytz.timezone('America/Chicago')
        for line in ALL_LOG_LINES:
            self.log_lines.append(api.handle_new_line(line, tz))

    def test_search_log_lines(self):
        results, number_found = search.search_log_lines('gumptionthomas')
        self.assertEqual(2, len(results))
        self.assertEqual(2, number_found)
        results, number_found = search.search_log_lines('info')
        self.assertEqual(6, len(results))
        self.assertEqual(6, number_found)
        results, number_found = search.search_log_lines('vesicular')
        self.assertEqual(1, len(results))
        self.assertEqual(1, number_found)
        results, number_found = search.search_log_lines('yo')
        self.assertEqual(1, len(results))
        self.assertEqual(1, number_found)
        results, number_found = search.search_log_lines(models.CONNECTION_TAG)
        self.assertEqual(2, len(results))
        self.assertEqual(2, number_found)
        results, number_found = search.search_log_lines(models.SERVER_TAG)
        self.assertEqual(3, len(results))
        self.assertEqual(3, number_found)
        results, number_found = search.search_log_lines('2012-10-15')
        self.assertEqual(2, len(results))
        self.assertEqual(2, number_found)
        results, number_found = search.search_log_lines('username:gumptionthomas tags:{0}'.format(models.LOGIN_TAG))
        self.assertEqual(1, len(results))
        self.assertEqual(1, number_found)

    def test_remove_log_lines(self):
        results, number_found = search.search_log_lines('info')
        self.assertEqual(6, len(results))
        self.assertEqual(6, number_found)
        for result in results:
            result.key.delete()
        results, number_found = search.search_log_lines('info')
        self.assertEqual(0, len(results))
        self.assertEqual(0, number_found)

    def test_search_players(self):
        results, number_found = search.search_players('gumptionthomas')
        self.assertEqual(1, len(results))
        self.assertEqual(1, number_found)
        results, number_found = search.search_players('vesicular')
        self.assertEqual(1, len(results))
        self.assertEqual(1, number_found)

    def test_remove_players(self):
        results, number_found = search.search_players('gumptionthomas')
        self.assertEqual(1, len(results))
        self.assertEqual(1, number_found)
        for result in results:
            result.key.delete()
        results, number_found = search.search_players('gumptionthomas')
        self.assertEqual(0, len(results))
        self.assertEqual(0, number_found)
