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
        destinationBucket=bucket,
        destinationObject=object,
        sourceGeneration=generation,
        body={}
    )
    try:
        request.execute()
    except HttpError as e:
        if e.resp.status != 404 and e.resp.status != 401:
            logging.error("Error ({0}) calling {1}".format(e.resp, getattr(e, 'operationType', None)))
        raise


def verify_bucket(num_versions=10):
    service = get_gcs_service()
    bucket = get_default_bucket_name()
    body = {
        'versioning': {'enabled': True},
        'lifecycle': {
            'rule': [
                {
                    'action': {'type': 'Delete'},
                    'condition': {
                        'isLive': False,
                        'numNewerVersions': num_versions
                    }
                }
            ]
        }
    }
    try:
        request = service.buckets().get(bucket=bucket)
        response = request.execute()
        versioning = response.get('versioning', {}).get('enabled', False)
        num_newer_versions = 0
        lifecycle_rules = response.get('lifecycle', {}).get('rule', [])
        if lifecycle_rules:
            num_newer_versions = lifecycle_rules[0].get('condition', {}).get('numNewerVersions', 0)
        if not (versioning and num_versions == num_newer_versions):
            request = service.buckets().patch(bucket=bucket, body=body)
            request.execute()
    except HttpError as err:
        if err.resp.status == 404:
            try:
                body['name'] = bucket
                request = service.buckets().insert(project=get_project_id(), body=body)
                request.execute()
            except HttpError as err2:
                logging.error("Error ({0}) creating bucket".format(err2))
                raise
        else:
            logging.error("Error ({0}) verifying bucket".format(err))
            raise


def get_gcs_service():
    credentials = AppAssertionCredentials(scope=STORAGE_API_SCOPE)
    http = credentials.authorize(httplib2.Http(memcache, 30))
    return discovery.build('storage', STORAGE_API_VERSION, http=http)
