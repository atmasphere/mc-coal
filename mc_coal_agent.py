import argparse
import httplib
import json
import logging
import os
import pytz
import re
import sys
import time
import urllib

import timezones
import yaml


DEFAULT_AGENT_LOGFILE = 'agent.log'
DEFAULT_MC_LOGFILE = '../server.log'


class AgentException(Exception):
    pass


class NoHostException(AgentException):
    pass


class NoPasswordException(AgentException):
    pass


class NoPingException(AgentException):
    pass


def ping_host(host, password):
    logger = logging.getLogger('ping')
    try:
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "text/plain"
        }
        params = urllib.urlencode({'server_name': host})
        conn = httplib.HTTPConnection(host)
        conn.request("POST", "/api/ping?p={0}".format(password), params, headers)
        response = conn.getresponse()
        if response.status == 200:
            body = json.loads(response.read())
            last_line = body['last_line']
            return last_line
        else:
            logger.error("UNEXPECTED RESPONSE: {0} {1}".format(response.status, response.reason))
            logger.debug("{0}".format(response.read()))
    except Exception, e:
        logger.error("{0}".format(str(e)))
    raise NoPingException()


def is_moved_wrongly_warning(line):
    return re.search(ur"([\w-]+) ([\w:]+) \[WARNING\] (.+) moved wrongly!", line)


def is_overloaded_warning(line):
    return re.search(ur"([\w-]+) ([\w:]+) \[WARNING\] Can't keep up! Did the system time change, or is the server overloaded\?", line)


def is_chat(line):
    return re.search(ur"([\w-]+) ([\w:]+) \[(\w+)\] \<(\w+)\> (.+)", line)


def post_line(host, line, password, zone, skip_chat):
    logger = logging.getLogger('log_line')
    if is_moved_wrongly_warning(line):
        logger.debug(u"SKIPPING '{0}'".format(line))
        return
    if is_overloaded_warning(line):
        logger.debug(u"SKIPPING '{0}'".format(line))
        return
    if skip_chat and is_chat(line):
        logger.debug(u"SKIPPING '{0}'".format(line))
        return
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"
    }
    params = urllib.urlencode({'line': line, 'zone': zone})
    tries = 0
    while True:
        tries = tries - 1
        try:
            conn = httplib.HTTPConnection(host)
            conn.request("POST", "/api/log_line?p={0}".format(password), params, headers)
            response = conn.getresponse()
            if response.status == 201 or response.status == 200:
                logger.debug(u"REPORTED '{0}'".format(line))
                break
            else:
                logger.error(u"UNEXPECTED RESPONSE: {0} {1}".format(response.status, response.reason))
                logger.debug(u"{0}".format(response.read()))
        except Exception, e:
            logger.error(u"{0}".format(str(e)))
        timeout = 10 if tries < 10 else 30
        logger.info(u"SLEEPING FOR {0} SECONDS...".format(timeout))
        time.sleep(timeout)


def line_reader(logfile):
    while True:
        where = logfile.tell()
        raw_line = logfile.readline()
        line = raw_line.decode('ISO-8859-2', errors='ignore')
        line = line.strip()
        if not line:
            logfile.seek(where)
            time.sleep(1.0)
        else:
            yield line


def tail(host, filename, password, zone, parse_history, skip_chat, last_line):
    logger = logging.getLogger('main')
    with open(filename, 'r') as logfile:
        st_results = os.stat(filename)
        st_size = st_results[6]
        if parse_history:
            read_last_line = False if last_line is not None else True
            if last_line is not None:
                logger.debug(u"Skipping ahead to line '{0}'".format(last_line))
        else:
            st_results = os.stat(filename)
            st_size = st_results[6]
            logfile.seek(st_size)
            read_last_line = True
        for line in line_reader(logfile):
            if read_last_line:
                post_line(host, line, password, zone, skip_chat)
                if skip_chat:
                    where = logfile.tell()
                    if where >= st_size:
                        skip_chat = False
            elif line == last_line:
                read_last_line = True
            else:
                where = logfile.tell()
                if where >= st_size:
                    read_last_line = True
                    skip_chat = False


def get_application_host():
    try:
        with open('app.yaml') as appcfg:
            data = yaml.safe_load(appcfg)
            if data:
                application = data.get('application', None)
                if application:
                    return "{0}.appspot.com".format(application)
    except:
        pass
    return None


def get_password():
    try:
        from appengine_config import COAL_API_PASSWORD
    except ImportError:
        return None
    return COAL_API_PASSWORD


def get_local_zone():
    try:
        return timezones.localtz().zone
    except:
        pass
    return None


def init_loggers(debug=False, logfile='agent.log'):
    main_logger = logging.getLogger('main')
    ping_logger = logging.getLogger('ping')
    log_line_logger = logging.getLogger('log_line')
    main_logger.setLevel(logging.DEBUG)
    main_logger.propagate = False
    ping_logger.setLevel(logging.DEBUG)
    ping_logger.propagate = False
    log_line_logger.setLevel(logging.DEBUG)
    log_line_logger.propagate = False
    formatter = logging.Formatter('%(asctime)s : %(name)-8s %(levelname)-6s %(message)s')
    if logfile:
        fh = logging.FileHandler(logfile)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        main_logger.addHandler(fh)
        ping_logger.addHandler(fh)
        log_line_logger.addHandler(fh)
    ch = logging.StreamHandler()
    if debug:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    main_logger.addHandler(ch)
    ping_logger.addHandler(ch)
    log_line_logger.addHandler(ch)


def main(argv):
    parser = argparse.ArgumentParser(description="The MC COAL minecraft server log monitoring and reporting agent.")
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help="Log DEBUG info to the console"
    )
    parser.add_argument(
        '--agent_logfile',
        default=DEFAULT_AGENT_LOGFILE,
        help="The MC COAL agent log filename (default: '{0}'). Set to blank (i.e. '--agent-logfile=') to supress file logging.".format(DEFAULT_AGENT_LOGFILE)
    )
    coal_host = get_application_host()
    parser.add_argument(
        '--coal_host',
        default=coal_host,
        help="The MC COAL server host name (default: {0})".format("'{0}'".format(coal_host) if coal_host else '<No default found in app.yaml>')
    )
    parser.add_argument(
        '--coal_password',
        help="The MC COAL server API password. The default value is pulled from 'appengine_config.py'"
    )
    parser.add_argument(
        '--mc_logfile',
        default=DEFAULT_MC_LOGFILE,
        help="The Minecraft server log filename (default: '{0}')".format(DEFAULT_MC_LOGFILE)
    )
    parser.add_argument(
        '--parse_mc_history',
        action='store_true',
        help="Set this flag to parse and report on the Minecraft server log from the beginning rather than just new entries."
    )
    parser.add_argument(
        '--skip_chat_history',
        action='store_true',
        help="Set this flag to skip reporting the Minecraft server log chat history. New chats will still be reported."
    )
    mc_timezone = get_local_zone()
    parser.add_argument(
        '--mc_timezone',
        default=mc_timezone,
        help="The Minecraft server timezone name (default: {0})".format("'{0}'".format(mc_timezone) if mc_timezone else '<No default local timezone>')
    )
    args = parser.parse_args()
    try:
        init_loggers(debug=args.verbose, logfile=args.agent_logfile)
        logger = logging.getLogger('main')
        coal_host = args.coal_host
        if not coal_host:
            raise NoHostException()
        coal_password = args.coal_password or get_password()
        if not coal_password:
            raise NoPasswordException()
        mc_logfile = args.mc_logfile
        parse_mc_history = args.parse_mc_history
        skip_chat_history = args.skip_chat_history
        mc_timezone = args.mc_timezone
        tz = pytz.timezone(mc_timezone)
        last_line = ping_host(coal_host, coal_password)
        logger.info("Monitoring '{0}' and reporting to '{1}'...".format(mc_logfile, coal_host))
        tail(coal_host, mc_logfile, coal_password, tz.zone, parse_mc_history, skip_chat_history, last_line)
    except NoPingException:
        logger.error("Unable to ping '{0}'".format(coal_host))
    except pytz.UnknownTimeZoneError:
        logger.error("Invalid timezone: '{0}'".format(mc_timezone))
    except NoHostException:
        logger.error("No MC COAL server host name provided.")
    except NoPasswordException:
        logger.error("No MC COAL server API password provided.")
    except KeyboardInterrupt:
        logger.info("Cancelled")
    except SystemExit:
        logger.info("System Exit")
    except Exception, e:
        logger.error("Unexpected {0}: {1}".format(type(e).__name__, e))
    logger.info("Shutting down... Goodbye.")

if __name__ == "__main__":
    main(sys.argv[1:])
