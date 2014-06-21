import fix_path  # noqa

import httplib2
import logging

from google.appengine.api import app_identity, memcache

from apiclient import discovery
from apiclient.errors import HttpError

from oauth2client.appengine import AppAssertionCredentials


STORAGE_API_SCOPE = 'https://www.googleapis.com/auth/devstorage.full_control'
STORAGE_API_VERSION = 'v1'


def get_project_id():
    return app_identity.get_application_id()


def get_default_bucket_name():
    return app_identity.get_default_gcs_bucket_name()


def get_gcs_archive_name(server_key):
    return 'worlds/{0}.zip'.format(server_key)


def get_versions(server_key):
    versions = []
    service = get_gcs_service()
    request = service.objects().list(
        bucket=get_default_bucket_name(),
        versions=True,
        prefix=get_gcs_archive_name(server_key)
    )
    try:
        result = request.execute()
        items = result.get('items', [])
        versions = sorted(items, key=lambda k: k['updated'], reverse=True)
        logging.info("Versions: {0}".format(versions))
    except HttpError as e:
        if e.resp.status != 404 and e.resp.status != 401:
            logging.error("Error ({0}) calling {1}".format(e.resp, getattr(e, 'operationType', None)))
        raise
    return versions


def restore_generation(server_key, generation):
    service = get_gcs_service()
    bucket = get_default_bucket_name()
    object = get_gcs_archive_name(server_key)
    request = service.objects().copy(
        sourceBucket=bucket,
        sourceObject=object,
        destionationBucket=bucket,
        destinationObject=object,
        sourceGeneration=generation
    )
    try:
        request.execute()
    except HttpError as e:
        if e.resp.status != 404 and e.resp.status != 401:
            logging.error("Error ({0}) calling {1}".format(e.resp, getattr(e, 'operationType', None)))
        raise


def get_gcs_service():
    credentials = AppAssertionCredentials(scope=STORAGE_API_SCOPE)
    http = credentials.authorize(httplib2.Http(memcache, 30))
    return discovery.build('storage', STORAGE_API_VERSION, http=http)
