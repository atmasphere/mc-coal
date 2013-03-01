import os
import sys

for d in os.environ["PATH"].split(":"):
    dev_appserver_path = os.path.join(d, "dev_appserver.py")
    if os.path.isfile(dev_appserver_path):
        sdk_path = os.path.abspath(os.path.dirname(os.path.realpath(dev_appserver_path)))
        sys.path.insert(0, sdk_path)
        import dev_appserver
        dev_appserver.fix_sys_path()

from base_test import BaseTest
from web_test import WebTest

import main


class MainTest(BaseTest, WebTest):

    APPLICATION = main.application

    def test_hello_world(self):
        response = self.get("/")
        self.assertOK(response)
