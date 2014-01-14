import json

from google.appengine.api import taskqueue

import gce


def queue_controller_task(payload):
    payload = json.dumps(payload)
    taskqueue.Queue('controller').add([taskqueue.Task(payload=payload, method='PULL')])


def start_server(server):
    instance = gce.Instance.singleton()
    if not instance.is_running():
        instance.start()
    payload = {'event': 'START_SERVER'}
    payload['server_key'] = server.key.urlsafe()
    payload['agent_client_id'] = server.agent.client_id
    payload['agent_secret'] = server.agent.secret
    payload['minecraft_url'] = 'https://s3.amazonaws.com/Minecraft.Download/versions/1.7.4/minecraft_server.1.7.4.jar'
    payload['memory'] = server.memory
    payload['server_properties'] = server.mc_properties.server_properties
    operator = server.operator
    if operator is not None:
        payload['operator'] = operator
    queue_controller_task(payload)


def stop_server(server):
    payload = {'event': 'STOP_SERVER'}
    payload['server_key'] = server.key.urlsafe()
    queue_controller_task(payload)
