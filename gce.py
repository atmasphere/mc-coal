import httplib2
import logging

from apiclient.discovery import build

from google.appengine.api import app_identity, memcache
from google.appengine.ext import ndb

from oauth2client.appengine import AppAssertionCredentials


GCE_SCOPE = 'https://www.googleapis.com/auth/compute'
API_VERSION = 'v1beta16'
GCE_URL = 'https://www.googleapis.com/compute/%s/projects/' % (API_VERSION)


class Instance(ndb.Model):
    name = ndb.StringProperty(required=True)
    zone = ndb.StringProperty(required=True)
    running = ndb.BooleanProperty(default=False)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def start(cls, zone):
        pass

    def stop(cls, zone):
        pass

    @classmethod
    def get_gce_instances(cls, zone):
        credentials = AppAssertionCredentials(scope=GCE_SCOPE)
        http = credentials.authorize(httplib2.Http(memcache))

        # Build the service
        gce_service = build('compute', API_VERSION, http=http)

        # List instances
        try:
            request = gce_service.instances().list(project=get_project_id(), zone=zone)
            response = request.execute()
            if response and 'items' in response:
                return [instance['name'] for instance in response['items']]
        except Exception as e:
            logging.error("{0} -- {1}".format(e.__class__, repr(e)))
        return None


def get_project_id():
    return app_identity.get_application_id()


def get_zones():
    credentials = AppAssertionCredentials(scope=GCE_SCOPE)
    http = credentials.authorize(httplib2.Http(memcache))

    # Build the service
    gce_service = build('compute', API_VERSION, http=http)

    # List zones
    try:
        request = gce_service.zones().list(project=get_project_id())
        response = request.execute()
        if response and 'items' in response:
            return [zone['name'] for zone in response['items']]
    except Exception as e:
        logging.error("{0} -- {1}".format(e.__class__, repr(e)))
    return None
