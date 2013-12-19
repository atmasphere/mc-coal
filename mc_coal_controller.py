#!/usr/bin/env python

import fnmatch
import logging
import os
import sys
import time

from apiclient.discovery import build
from oauth2client import gce
import httplib2

SCOPE = 'https://www.googleapis.com/auth/taskqueue'
TQ_API_VERSION = 'v1beta2'

SERVERS_DIR = '/coal/servers/'

#Globals
servers = {}
project = None
service = None


def lease_tasks():
    tasks = []
    service_call = service.tasks().lease(
        project=project, taskqueue='controller', leaseSecs=300, numTasks=10
    )
    response = service_call.execute()
    tasks += response.get('items', [])
    return tasks

def complete_tasks(tasks):
    global servers
    for task in tasks:
        logging.info(task)

def delete_tasks(tasks):
    for task in tasks:
        service_call = service.tasks().delete(project=project, taskqueue=task.queueName, task=task.id)
        service_call.execute()

def get_servers():
    if not os.path.exists(SERVERS_DIR):
        os.makedirs(SERVERS_DIR)
    _, port_dirs, _ = os.walk(SERVERS_DIR).next()
    ports = [port for port in port_dirs if fnmatch.fnmatch(port, '[0-9]*')]

def init_loggers(debug=False, logfile='controller.log'):
    main_logger = logging.getLogger('main')
    main_logger.setLevel(logging.DEBUG)
    main_logger.propagate = False
    formatter = logging.Formatter(u'%(asctime)s : %(name)-8s %(levelname)-6s %(message)s')
    if logfile:
        fh = logging.FileHandler(logfile)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        main_logger.addHandler(fh)
    ch = logging.StreamHandler()
    if debug:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    main_logger.addHandler(ch)

def main(argv):
    global project
    global service
    try:
        init_loggers()
        logger = logging.getLogger('main')
        project = open('/coal/project_id', 'r').read()
        credentials = gce.AppAssertionCredentials(scope=SCOPE)
        http = credentials.authorize(httplib2.Http())
        service = build('taskqueue', TQ_API_VERSION, http=http)
        while True:
            tasks = lease_tasks()
            if tasks:
                completed_tasks = []
                try:
                    completed_tasks = complete_tasks(tasks)
                finally:
                    i = len(completed_tasks) if completed_tasks else 0
                    server = completed_tasks[0].tag if completed_tasks else None
                    m = u"Completed {0} task{1} for server {2}".format(i, 's' if i != 1 else '', server)
                    logger.info(m)
                    delete_tasks(completed_tasks)
            time.sleep(1.0)
    except KeyboardInterrupt:
        logger.info(u"Canceled")
    except SystemExit:
        logger.info(u"System Exit")
    except Exception, e:
        logger.error(u"Unexpected {0}: {1}".format(type(e).__name__, e))
    logger.info(u"Shutting down... Goodbye.")


if __name__ == "__main__":
    main(sys.argv[1:])
