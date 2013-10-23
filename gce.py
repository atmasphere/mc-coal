import httplib2
import logging

from apiclient import discovery
from apiclient.errors import HttpError

from google.appengine.api import app_identity, memcache
from google.appengine.ext import ndb

from oauth2client.appengine import AppAssertionCredentials


GCE_SCOPE = 'https://www.googleapis.com/auth/compute'
API_VERSION = 'v1beta16'
GCE_URL = 'https://www.googleapis.com/compute/%s/projects/' % (API_VERSION)


class Instance(ndb.Model):
    name = ndb.StringProperty(required=False, default='coal-instance')
    zone = ndb.StringProperty(required=False, default='us-central1-a')
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def start(self):
        pass

    def stop(self):
        pass

    def running(self):
        return self.status() == "RUNNING"

    def status(self):
        gce_instance = self.get_gce_instance()
        if gce_instance is None:
            return 'UNPROVISIONED'
        return gce_instance['status']

    def status_message(self):
        gce_instance = self.get_gce_instance()
        if gce_instance is None:
            return 'Unprovisioned'
        return gce_instance['statusMessage']

    def get_gce_instance(self):
        instance = None
        try:
            gce_service = get_gce_service()
            instance = execute_request(gce_service.instances().get(instance=self.name, project=get_project_id(), zone=self.zone))
        except HttpError as e:
            if e.resp.status != 404 and e.resp.status != 401:
                raise
        return instance

    @classmethod
    def singleton(cls):
        return cls.get_or_insert('coal-instance-singleton')


def get_project_id():
    return app_identity.get_application_id()


def get_gce_service():
    credentials = AppAssertionCredentials(scope=GCE_SCOPE)
    http = credentials.authorize(httplib2.Http(memcache))
    return discovery.build('compute', API_VERSION, http=http)


def execute_request(request):
    try:
        response = request.execute()
    except HttpError as e:
        if e.resp.status != 404 and e.resp.status != 401:
            logging.error(repr(e))
        raise
    return response


def get_zones():
    try:
        gce_service = get_gce_service()
        request = gce_service.zones().list(project=get_project_id())
        response = request.execute()
        if response and 'items' in response:
            return [zone['name'] for zone in response['items']]
    except HttpError as e:
        if e.resp.status != 404 and e.resp.status != 401:
            raise
    return None


def is_setup():
    setup = False
    try:
        gce_service = get_gce_service()
        request = gce_service.zones().list(project=get_project_id())
        request.execute()
        setup = True
    except HttpError as e:
        if e.resp.status != 404 and e.resp.status != 401:
            raise
    return setup
