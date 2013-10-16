import httplib2
import logging

from apiclient.discovery import build

from google.appengine.api import app_identity, memcache
from google.appengine.ext import ndb

from oauth2client.appengine import AppAssertionCredentials

from restler.decorators import ae_ndb_serializer


GCE_SCOPE = 'https://www.googleapis.com/auth/compute'
API_VERSION = 'v1beta16'
GCE_URL = 'https://www.googleapis.com/compute/%s/projects/' % (API_VERSION)
DEFAULT_ZONE = 'us-central1-a'



@ae_ndb_serializer
class MinecraftServer(ndb.Model):
    running = ndb.BooleanProperty(default=False)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)


def get_instances():
    credentials = AppAssertionCredentials(scope=GCE_SCOPE)
    http = credentials.authorize(httplib2.Http(memcache))

    # Build the service
    project_id = app_identity.get_application_id()
    gce_service = build('compute', API_VERSION, http=http)
    project_url = '%s%s' % (GCE_URL, project_id)

    # List instances
    try:
        request = gce_service.instances().list(project=project_id, filter=None, zone=DEFAULT_ZONE)
        response = request.execute()
        if response and 'items' in response:
            return response['items']
    except Exception, e:
        logging.error(repr(e))
    return None
