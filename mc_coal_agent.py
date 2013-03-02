import argparse
import httplib
import logging
import os
import sys
import time
import urllib
import timezones
import yaml


def ping_host(host):
    logger = logging.getLogger('ping')
    tries = 5
    while tries >= 0:
        tries = tries - 1
        try:
            headers = {
                "Content-type": "application/x-www-form-urlencoded",
                "Accept": "text/plain"
            }
            params = urllib.urlencode({'server_name': host})
            conn = httplib.HTTPConnection(host)
            conn.request("POST", "/api/ping", params, headers)
            response = conn.getresponse()
            if response.status == 200:
                return True
            else:
                logger.error("UNEXPECTED RESPONSE: {0} {1}".format(response.status, response.reason))
                logger.debug("{0}".format(response.read()))
        except Exception, e:
            logger.error("{0}".format(str(e)))
        timeout = 10 if tries > 2 else 30
        logger.info("SLEEPING FOR {0} SECONDS".format(timeout))
        time.sleep(timeout)
    return False


def post_line(host, line):
    logger = logging.getLogger('log_line')
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"
    }
    params = urllib.urlencode({'line': line, 'tz_name': timezones.localtz()})
    tries = 10
    while tries >= 0:
        tries = tries - 1
        try:
            conn = httplib.HTTPConnection(host)
            conn.request("POST", "/api/log_line", params, headers)
            response = conn.getresponse()
            if response.status == 201:
                break
            else:
                logger.error("UNEXPECTED RESPONSE: {0} {1}".format(response.status, response.reason))
                logger.debug("{0}".format(response.read()))
        except Exception, e:
            logger.error("{0}".format(str(e)))
        timeout = 10 if tries > 4 else 60
        logger.info("SLEEPING FOR {0} SECONDS".format(timeout))
        time.sleep(timeout)


def line_reader(logfile):
    while True:
        where = logfile.tell()
        line = logfile.readline()
        if not line:
            logfile.seek(where)
        else:
            yield line


def tail(host, filename):
    with open(filename, 'r') as logfile:
        st_results = os.stat(filename)
        st_size = st_results[6]
        logfile.seek(st_size)
        for line in line_reader(logfile):
            post_line(host, line)


def get_application_host():
    host = None
    with open('app.yaml') as appcfg:
        data = yaml.safe_load(appcfg)
        if data:
            application = data.get('application', None)
            if application:
                host = "{0}.appspot.com".format(application)
    return host


def init_loggers():
    main_logger = logging.getLogger('main')
    ping_logger = logging.getLogger('ping')
    log_line_logger = logging.getLogger('log_line')
    main_logger.setLevel(logging.DEBUG)
    ping_logger.setLevel(logging.DEBUG)
    log_line_logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('mc-coal-agent.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s : %(name)-8s %(levelname)-6s %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    main_logger.addHandler(fh)
    ping_logger.addHandler(fh)
    log_line_logger.addHandler(fh)
    main_logger.addHandler(ch)
    ping_logger.addHandler(ch)
    log_line_logger.addHandler(ch)


def main(argv):
    init_loggers()
    host = get_application_host()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--host',
        help="The MC COAL server host name (default: '{0}')".format(host)
    )
    parser.add_argument(
        '--filename',
        default='server.log',
        help="The server log filename (default: 'server.log')"
    )
    args = parser.parse_args()
    host = args.host or host
    if ping_host(host):
        tail(host, args.filename)

if __name__ == "__main__":
    main(sys.argv[1:])
