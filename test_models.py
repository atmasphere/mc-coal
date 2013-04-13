import base64
import os
import sys
import minimock

for d in os.environ["PATH"].split(":"):
    dev_appserver_path = os.path.join(d, "dev_appserver.py")
    if os.path.isfile(dev_appserver_path):
        sdk_path = os.path.abspath(os.path.dirname(os.path.realpath(dev_appserver_path)))
        sys.path.insert(0, sdk_path)
        import dev_appserver
        dev_appserver.fix_sys_path()

from google.appengine.ext import blobstore, testbed, deferred, ndb

from agar.test.base_test import BaseTest

import channel
import main
import models

IMAGE_PATH = 'static/img/coal_sprite.png'

try:
    from PIL import Image
except ImportError:
    Image = None

if Image is not None:
    class ScreenShotTest(BaseTest):
        APPLICATION = main.application

        def setUp(self):
            super(ScreenShotTest, self).setUp()
            self.screen_shots = []
            blob_info = self.create_blob_info(IMAGE_PATH)
            for i in range(5):
                screen_shot = models.ScreenShot.create(username='bill', blob_info=blob_info)
                self.screen_shots.append(screen_shot)
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

        def test_random(self):
            found_keys = set()
            for i in range(20):
                found_keys.add(models.ScreenShot.random().key)
            self.assertLess(0, len(found_keys))

        def create_blob_info(self, path, image_data=None):
            if not image_data:
                image_data = open(path, 'rb').read()
            path = os.path.basename(path)
            self.testbed.get_stub('blobstore').CreateBlob(path, image_data)
            return blobstore.BlobInfo(blobstore.BlobKey(path))

        def test_create_data(self):
            image_data = open(IMAGE_PATH, 'rb').read()
            screen_shot = models.ScreenShot.create('bill', data=image_data, filename=IMAGE_PATH)
            self.assertIsNotNone(screen_shot)
            self.assertIsNone(screen_shot.blurred_image_serving_url)
            self.assertEqual(image_data, screen_shot.image_data)
            self.run_deferred()
            self.assertIsNotNone(screen_shot.blurred_image_serving_url)

        def test_create_blob(self):
            blob_info = self.create_blob_info(IMAGE_PATH)
            image = models.ScreenShot.create('bill', blob_info=blob_info)
            self.assertIsNotNone(image)
            self.assertIsNone(image.blurred_image_serving_url)
            image_data = open(IMAGE_PATH, 'rb').read()
            self.assertEqual(image_data, image.image_data)
            self.assertEqual(1, len(self.blobs))    # Just IMAGE_PATH
            self.run_deferred()
            self.assertIsNotNone(image.blurred_image_serving_url)
            self.assertEqual(2, len(self.blobs))    # IMAGE_PATH & blur

        def test_delete(self):
            image_data = open(IMAGE_PATH, 'rb').read()
            screen_shot = models.ScreenShot.create('bill', data=image_data, filename=IMAGE_PATH)
            self.run_deferred()
            self.assertIsNotNone(screen_shot)
            self.assertIsNotNone(screen_shot.blurred_image_serving_url)
            self.assertEqual(6, models.ScreenShot.query().count())
            self.assertEqual(1, models.AgarImage.query().count())
            self.assertEqual(image_data, screen_shot.image_data)
            screen_shot.key.delete()
            self.assertEqual(5, models.ScreenShot.query().count())
            self.assertEqual(0, models.AgarImage.query().count())


class LogLineTest(BaseTest):

    def cleanUp(self):
        super(LogLineTest, self).cleanUp()
        minimock.restore()

    def test_post_put_hook_sends_log_line_to_channel(self):
        tracker = minimock.TraceTracker()
        minimock.mock('channel.send_log_line', tracker=tracker)
        models.LogLine(key=ndb.Key('LogLine', 'line'), line='my line', zone='my zone').put()
        trace = tracker.dump()
        self.assertTrue("""Called channel.send_log_line(
    LogLine(key=Key('LogLine', 'line'), created=""" in trace)
        self.assertTrue("line=u'my line'" in trace)


class LookupChannelersTest(BaseTest):

    def test_returns_emtpy_list_if_no_entity(self):
        self.assertEqual([], models.Lookup.channelers())


class LookupAddChannelerTest(BaseTest):

    def test_adds_client_id_to_lookup_store_despite_missing_lookup_entity(self):
        models.Lookup.add_channeler('client-id')
        self.assertEqual(['client-id'], models.Lookup.channelers())

    def test_adds_client_id_to_existing_lookup_store(self):
        models.Lookup.add_channeler('client-id-1')
        models.Lookup.add_channeler('client-id-2')
        self.assertEqual(['client-id-1', 'client-id-2'], models.Lookup.channelers())

    def test_does_not_add_client_id_to_lookup_store_if_already_exists_there(self):
        models.Lookup.add_channeler('client-id')
        models.Lookup.add_channeler('client-id')
        self.assertEqual(['client-id'], models.Lookup.channelers())


class LookupRemoveChannelerTest(BaseTest):

    def test_removes_client_id_from_lookup_store(self):
        models.Lookup.add_channeler('client-id-1')
        models.Lookup.add_channeler('client-id-2')
        models.Lookup.remove_channeler('client-id-1')
        self.assertEqual(['client-id-2'], models.Lookup.channelers())

    def test_no_ops_if_missing_lookup_entity(self):
        models.Lookup.remove_channeler('client-id')
        self.assertEqual([], models.Lookup.channelers())

    def test_no_ops_if_client_id_is_not_in_lookup_store(self):
        models.Lookup.add_channeler('client-id-1')
        models.Lookup.remove_channeler('client-id-2')
        self.assertEqual(['client-id-1'], models.Lookup.channelers())
