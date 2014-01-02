import json

from google.appengine.api import taskqueue

import gce


def queue_controller_task(payload):
    payload = json.dumps(payload)
    taskqueue.Queue('controller').add([taskqueue.Task(payload=payload, method='PULL')])


def start_server(server):
    if gce.is_setup():
        instance = gce.Instance.singleton()
        if not instance.is_running():
            instance.start()
        payload = {'event': 'START_SERVER'}
        payload['server_key'] = server.key.urlsafe()
        payload['agent_client_id'] = server.agent.client_id
        payload['agent_secret'] = server.agent.secret
        queue_controller_task(payload)


def stop_server(server):
    if gce.is_setup():
        payload = {'event': 'STOP_SERVER'}
        payload['server_key'] = server.key.urlsafe()
        queue_controller_task(payload)
