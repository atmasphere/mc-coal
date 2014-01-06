#!/usr/bin/env python

import base64
import fnmatch
import json
import logging
import os
import random
import shutil
import signal
import socket
import subprocess
import sys
import time
import zipfile

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload, MediaIoBaseDownload

from oauth2client import gce
import httplib2

SCOPE = 'https://www.googleapis.com/auth/taskqueue'
TQ_API_VERSION = 'v1beta2'
STORAGE_API_VERSION = 'v1beta2'
MINECRAFT_DIR = '/minecraft/'
COAL_DIR = '/coal/'
SERVERS_DIR = os.path.join(COAL_DIR, 'servers')
ARCHIVES_DIR = os.path.join(COAL_DIR, 'archives')
WORLDS_BUCKET = 'worlds'
NUM_RETRIES = 5
CHUNKSIZE = 2 * 1024 * 1024
RETRYABLE_ERRORS = (httplib2.HttpLib2Error, IOError)

#Globals
logger = None
project = None
service = None
external_ip = None


def init_external_ip():
    global external_ip
    results = json.loads(
        subprocess.Popen(
            ['gcutil', 'getinstance', '--format=json', socket.gethostname()], stdout=subprocess.PIPE
        ).stdout.read()
    )
    external_ip = results['networkInterfaces'][0]['accessConfigs'][0]['natIP']


def get_ports_in_use():
    _, port_dirs, _ = os.walk(SERVERS_DIR).next()
    ports = [port for port in port_dirs if fnmatch.fnmatch(port, '[0-9]*')]
    ports.sort()
    return ports


def get_free_port():
    ports_in_use = get_ports_in_use()
    port = 25565
    while str(port) in ports_in_use:
        port += 1
    return port


def get_server_dir(port):
    return os.path.join(SERVERS_DIR, str(port))


def read_server_key(port):
    server_key_filename = os.path.join(SERVERS_DIR, port, 'server_key')
    server_key = open(server_key_filename, 'r').read()
    return server_key


def write_server_key(port, server_key):
    server_dir = get_server_dir(port)
    server_key_filename = os.path.join(server_dir, 'server_key')
    with open(server_key_filename, 'w') as server_key_file:
        server_key_file.write(server_key)


def get_servers():
    servers = dict()
    ports = get_ports_in_use()
    for port in ports:
        server_key = read_server_key(port)
        servers[server_key] = {'port': port}
    return servers


def copy_server_properties(port, server_properties):
    default_properties = os.path.join(COAL_DIR, 'server.properties')
    server_dir = get_server_dir(port)
    new_properties = os.path.join(server_dir, 'server.properties')
    server_properties['server-port'] = port
    with open(new_properties, "w") as fout:
        with open(default_properties, "r") as fin:
            for line in fin:
                for prop in server_properties:
                    if line.startswith(prop):
                        line = "{0}={1}\n".format(prop, server_properties[prop])
                fout.write(line)


def copy_server_files(port, server_properties):
    server_dir = get_server_dir(port)
    shutil.copy2(os.path.join(MINECRAFT_DIR, 'minecraft_server.jar'), server_dir)
    shutil.copy2(os.path.join(MINECRAFT_DIR, 'log4j2.xml'), server_dir)
    copy_server_properties(port, server_properties)
    filenames = [
        'timezones.py',
        'mc_coal_agent.py'
    ]
    mc_coal_dir = os.path.join(server_dir, 'mc_coal')
    if not os.path.exists(mc_coal_dir):
        os.makedirs(mc_coal_dir)
    for fn in filenames:
        shutil.copy2(os.path.join(COAL_DIR, fn), mc_coal_dir)


def make_fifo(server_dir):
    fifo = os.path.join(server_dir, 'command-fifo')
    try:
        os.remove(fifo)
    except OSError:
        pass
    os.mkfifo(fifo, 0666)
    return fifo


def load_zip_from_gcs(server_key, server_dir):
    credentials = gce.AppAssertionCredentials(scope=SCOPE)
    http = credentials.authorize(httplib2.Http())
    service = build('storage', STORAGE_API_VERSION, http=http)
    archive_file = os.path.join(server_dir, '{0}.zip'.format(server_key))
    with file(archive_file, 'w') as f:
        name = '{0}.zip'.format(server_key)
        request = service.objects().get_media(bucket=WORLDS_BUCKET, object=name)
        media = MediaIoBaseDownload(f, request, chunksize=CHUNKSIZE)
        progressless_iters = 0
        done = False
        while not done:
            error = None
            try:
                progress, done = media.next_chunk()
                if progress:
                    logger.info('Download %d%%' % (100 * progress.progress()))
            except HttpError, err:
                error = err
                if err.resp.status < 500:
                    raise
            except RETRYABLE_ERRORS, err:
                error = err
                if error:
                    progressless_iters += 1
                    if progressless_iters > NUM_RETRIES:
                        raise error
                        sleeptime = random.random() * (2**progressless_iters)
                        logger.error('Caught exception ({0}). Sleeping for {1} seconds before retry #{2}.'.format(
                            str(error), sleeptime, progressless_iters)
                        )
                        time.sleep(sleeptime)
                    else:
                        progressless_iters = 0


def unzip_server_dir(server_key, server_dir):
    archive_file = os.path.join(server_dir, '{0}.zip'.format(server_key))
    with zipfile.ZipFile(archive_file) as zf:
        for member in zf.infolist():
            path = os.path.join(server_dir, member.filename)
            zf.extract(member, path)


def start_server(server_key, **kwargs):
    servers = get_servers()
    if server_key in servers.keys():
        return
    port = get_free_port()
    address = external_ip
    if port != 25565:
        address += ':{0}'.format(port)
    server_dir = get_server_dir(port)
    while os.path.exists(server_dir):
        if read_server_key(port) == server_key:
            break
        port = get_free_port()
        server_dir = get_server_dir(port)
    if not os.path.exists(server_dir):
        os.makedirs(server_dir)
        write_server_key(port, server_key)
        load_zip_from_gcs(server_key, server_dir)
        unzip_server_dir(server_key, server_dir)
        server_properties = kwargs.get('server_properties', {})
        copy_server_files(port, server_properties)
    try:
        fifo = make_fifo(server_dir)
        # Start Agent
        mc_coal_dir = os.path.join(server_dir, 'mc_coal')
        agent = os.path.join(mc_coal_dir, 'mc_coal_agent.py')
        args = [agent]
        args.append('--coal_host={0}.appspot.com'.format(project))
        args.append('--agent_client_id={0}'.format(kwargs['agent_client_id']))
        args.append('--agent_secret={0}'.format(kwargs['agent_secret']))
        args.append('--address={0}'.format(address))
        pid = subprocess.Popen(args, cwd=mc_coal_dir).pid
        pid_filename = os.path.join(server_dir, 'agent.pid')
        with open(pid_filename, 'w') as pid_file:
            pid_file.write(str(pid))
        # Start MC
        mc_jar = os.path.join(server_dir, 'minecraft_server.jar')
        log4j = os.path.join(server_dir, 'log4j2.xml')
        args = ['java', '-Xmx1G', '-Xms1G']
        args.append('-Dlog4j.configurationFile={0}'.format(log4j))
        args.append('-jar')
        args.append(mc_jar)
        args.append('nogui')
        with open(fifo, 'w+') as fifo_file:
            pid = subprocess.Popen(args, cwd=server_dir, stdin=fifo_file).pid
        pid_filename = os.path.join(server_dir, 'server.pid')
        with open(pid_filename, 'w') as pid_file:
            pid_file.write(str(pid))
    except Exception, e:
        logger.error(e)


def zip_server_dir(server_dir, archive_file):
    skip_dirs = [
        os.path.join(server_dir, 'mc_coal'),
        os.path.join(server_dir, 'logs'),
    ]
    skip_files = [
        'command-fifo',
        'minecraft_server.jar',
        'log4j.xml'
    ]
    abs_src = os.path.abspath(server_dir)
    with zipfile.ZipFile(archive_file, "w") as zf:
        for dirname, subdirs, files in os.walk(server_dir):
            if dirname not in skip_dirs:
                arcname = os.path.relpath(dirname, abs_src)
                zf.write(dirname, arcname)
                for filename in files:
                    if filename not in skip_files:
                        absname = os.path.abspath(os.path.join(dirname, filename))
                        arcname = os.path.relpath(absname, abs_src)
                        zf.write(absname, arcname)


def upload_zip_to_gcs(server_key, archive_file):
    credentials = gce.AppAssertionCredentials(scope=SCOPE)
    http = credentials.authorize(httplib2.Http())
    service = build('storage', STORAGE_API_VERSION, http=http)
    media = MediaFileUpload(archive_file, chunksize=CHUNKSIZE, resumable=True)
    if not media.mimetype():
        media = MediaFileUpload(archive_file, 'application/octet-stream', resumable=True)
    name = '{0}.zip'.format(server_key)
    request = service.objects().insert(bucket=WORLDS_BUCKET, name=name, media_body=media)
    progressless_iters = 0
    response = None
    while response is None:
        error = None
        try:
            progress, response = request.next_chunk()
            if progress:
                logger.info('Upload %d%%' % (100 * progress.progress()))
        except HttpError, err:
            error = err
            if err.resp.status < 500:
                raise
        except RETRYABLE_ERRORS, err:
            error = err
        if error:
            progressless_iters += 1
            if progressless_iters > NUM_RETRIES:
                raise error
            sleeptime = random.random() * (2**progressless_iters)
            logger.error('Caught exception ({0}). Sleeping for {1} seconds before retry #{2}.'.format(
                str(error), sleeptime, progressless_iters)
            )
            time.sleep(sleeptime)
        else:
            progressless_iters = 0


def stop_server(server_key, **kwargs):
    servers = get_servers()
    server = servers.get(server_key, None)
    if server is None:
        return
    port = server['port']
    server_dir = get_server_dir(port)
    # Stop MC
    fifo = os.path.join(server_dir, 'command-fifo')
    with open(fifo, 'a+') as fifo_file:
        fifo_file.write('save-all\n')
        fifo_file.write('stop\n')
    pid = open(os.path.join(server_dir, 'server.pid'), 'r').read()
    try:
        os.waitpid(int(pid), 0)
    except OSError, e:
        logger.error(e)
    # Archive server_dir
    archive_file = os.path.join(ARCHIVES_DIR, '{0}.zip'.format(server_key))
    zip_server_dir(server_dir, archive_file)
    upload_zip_to_gcs(server_key, archive_file)
    # Stop Agent
    time.sleep(10)
    pid = open(os.path.join(server_dir, 'agent.pid'), 'r').read()
    os.kill(int(pid), signal.SIGTERM)
    os.waitpid(int(pid), 0)
    shutil.rmtree(server_dir)


def complete_tasks(tasks):
    logger.info("TASKS: {0}".format(tasks))
    completed_tasks = list()
    for task in tasks:
        try:
            logging.info(task)
            payload = task['payload']
            event = payload.pop('event')
            server_key = payload.pop('server_key')
            if event == 'START_SERVER':
                start_server(server_key, **payload)
            if event == 'STOP_SERVER':
                stop_server(server_key, **payload)
            completed_tasks.append(task)
        except Exception, e:
            logger.error(
                u"Task Error {0}: {1} for task: {2}".format(
                    type(e).__name__, e, task
                )
            )
    return completed_tasks


def lease_tasks():
    tasks = []
    service_call = service.tasks().lease(
        project=project, taskqueue='controller', leaseSecs=300, numTasks=10
    )
    response = service_call.execute()
    tasks += response.get('items', [])
    for task in tasks:
        task['payload'] = json.loads(base64.b64decode(task['payloadBase64']))
    return tasks


def delete_tasks(tasks):
    for task in tasks:
        try:
            service_call = service.tasks().delete(
                project='s~{0}'.format(project),
                taskqueue='controller',
                task=task['id']
            )
            service_call.execute()
        except Exception, e:
            logger.error(
                u"Delete Task Error {0}: {1}".format(type(e).__name__, e)
            )


def init_logger(debug=False, logfile='controller.log'):
    main_logger = logging.getLogger('main')
    main_logger.setLevel(logging.DEBUG)
    main_logger.propagate = False
    formatter = logging.Formatter(
        u'%(asctime)s : %(name)-8s %(levelname)-6s %(message)s'
    )
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
    global logger
    init_logger()
    logger = logging.getLogger('main')
    init_external_ip()
    if not os.path.exists(SERVERS_DIR):
        os.makedirs(SERVERS_DIR)
    try:
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
                    logger.info(u"Completed {0} task{1}".format(
                        i, 's' if i != 1 else '')
                    )
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
