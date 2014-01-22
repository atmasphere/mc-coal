import json
import logging

from google.appengine.api import taskqueue

import gce


def queue_controller_task(payload):
    payload = json.dumps(payload)
    taskqueue.Queue('controller').add([taskqueue.Task(payload=payload, method='PULL')])


def start_server(server, reserved_ports=[]):
    try:
        instance = gce.Instance.singleton()
        instance.start()
        if instance.idle:
            instance.idle = None
            instance.put()
        payload = {'event': 'START_SERVER'}
        payload['server_key'] = server.key.urlsafe()
        payload['agent_client_id'] = server.agent.client_id
        payload['agent_secret'] = server.agent.secret
        payload['minecraft_url'] = server.minecraft_url
        payload['memory'] = server.memory
        payload['reserved_ports'] = reserved_ports
        payload['server_properties'] = server.mc_properties.server_properties
        operator = server.operator
        if operator is not None:
            payload['operator'] = operator
        queue_controller_task(payload)
    except Exception as e:
        logging.exception(e)


def stop_server(server):
    try:
        payload = {'event': 'STOP_SERVER'}
        payload['server_key'] = server.key.urlsafe()
        queue_controller_task(payload)
    except Exception as e:
        logging.exception(e)
