from testing_utils import fix_sys_path; fix_sys_path()

import base64
import datetime
import os

from google.appengine.ext import blobstore, testbed, deferred, ndb

import minimock

from agar.test.base_test import BaseTest

import channel
import image
import main
import models
import string
import random

IMAGE_PATH = 'static/img/coal_sprite.png'

def create_blob_info(path, image_data=None):
    if not image_data:
        image_data = open(path, 'rb').read()
    path = os.path.basename(path)
    ScreenShotTest.TESTBED.get_stub('blobstore').CreateBlob(path, image_data)
    return blobstore.BlobInfo(blobstore.BlobKey(path))


def mock_post_data(data, filename=None, mime_type=None):
    if not filename:
        filename = ''.join([random.choice(string.ascii_uppercase) for x in xrange(50)])
    blob_info = create_blob_info(filename, image_data=data)
    return blob_info.key()


class ScreenShotTest(BaseTest):
    APPLICATION = main.application

    def setUp(self):
        super(ScreenShotTest, self).setUp()
        ScreenShotTest.TESTBED = self.testbed
        minimock.mock('image.NdbImage.post_data', returns_func=mock_post_data, tracker=None)
        self.server = models.Server.create()
        self.image_data = None
        self.screen_shots = []
        blob_info = self.create_blob_info(IMAGE_PATH)
        for i in range(5):
            screen_shot = models.ScreenShot.create(None, self.server.key, blob_info=blob_info)
            self.screen_shots.append(screen_shot)
        self.assertEqual(5, models.ScreenShot.query().count())
        #For speed, don't actually generate the blurs for these images
        taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        taskqueue_stub.FlushQueue('default')

    def tearDown(self):
        super(ScreenShotTest, self).tearDown()
        ScreenShotTest.TESTBED = None
        minimock.restore()

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

    def test_random(self):
        found_keys = set()
        for i in range(20):
            found_keys.add(models.ScreenShot.random().key)
        self.assertLess(0, len(found_keys))

    def test_create_data(self):
        self.image_data = open(IMAGE_PATH, 'rb').read()
        screen_shot = models.ScreenShot.create(None, self.server.key, data=self.image_data, filename=IMAGE_PATH)
        self.assertIsNotNone(screen_shot)
        self.assertEqual(self.image_data, screen_shot.image_data)
        self.assertEqual(1, len(self.blobs))
        # Create the blurred version
        self.run_deferred()
        self.assertIsNotNone(screen_shot.blurred_image_serving_url)
        self.assertEqual(2, len(self.blobs))

    def test_create_blob(self):
        blob_info = self.create_blob_info(IMAGE_PATH)
        screen_shot = models.ScreenShot.create(None, self.server.key, blob_info=blob_info)
        self.assertIsNotNone(screen_shot)
        self.assertIsNone(screen_shot.blurred_image_serving_url)
        image_data = open(IMAGE_PATH, 'rb').read()
        self.assertEqual(image_data, screen_shot.image_data)
        self.assertEqual(1, len(self.blobs))
        # Create the blurred version
        self.run_deferred()
        self.assertIsNotNone(screen_shot.blurred_image_serving_url)
        self.assertEqual(2, len(self.blobs))

    def test_delete(self):
        blob_info = self.create_blob_info(IMAGE_PATH)
        screen_shot = models.ScreenShot.create(None, self.server.key, blob_info=blob_info)
        # Create the blurred version
        self.run_deferred()
        self.assertIsNotNone(screen_shot)
        self.assertIsNotNone(screen_shot.blurred_image_serving_url)
        self.assertEqual(6, models.ScreenShot.query().count())
        self.assertEqual(1, models.NdbImage.query().count())
        self.assertEqual(2, len(self.blobs))
        image_data = open(IMAGE_PATH, 'rb').read()
        self.assertEqual(image_data, screen_shot.image_data)
        screen_shot.key.delete()
        self.assertEqual(5, models.ScreenShot.query().count())
        self.assertEqual(0, models.NdbImage.query().count())
        self.assertEqual(0, len(self.blobs))


class ServerTest(BaseTest):
    def setUp(self):
        super(ServerTest, self).setUp()
        self.server = models.Server.create()
        self.now = datetime.datetime.now()

    def test_update_is_running(self):
        self.server.update_is_running(True, self.now)
        self.assertTrue(self.server.is_running)
        self.assertEqual(self.now, self.server.last_ping)
        ping_time = self.now + datetime.timedelta(seconds=30)
        self.server.update_is_running(True, ping_time)
        self.assertTrue(self.server.is_running)
        self.assertEqual(self.now, self.server.last_ping)
        ping_time = self.now + datetime.timedelta(seconds=61)
        self.server.update_is_running(True, ping_time)
        self.assertTrue(self.server.is_running)
        self.assertEqual(ping_time, self.server.last_ping)


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
