#!/usr/bin/env python

import argparse
import datetime
import errno
import logging
import os
import pytz
import re
import signal
import sys
import time

from nbt import nbt
import requests
import timezones
import yaml


DEFAULT_AGENT_LOGFILE = 'agent.log'
DEFAULT_MC_LOGFILE = '../server.log'
DEFAULT_MC_LEVELFILE = '../world/level.dat'
DEFAULT_MC_PIDFILE = '../server.pid'
DEFAULT_MC_COMMAND_FIFO = '../command-fifo'

#Globals
client = None
mc_pidfile = None
mc_logfile = None
mc_levelfile = None
mc_commandfile = None
tz = None
zone = None
parse_mc_history = False
skip_chat_history = False
address = None
overloads = []


class AgentException(Exception):
    pass


class NoHostException(AgentException):
    pass


class NoClientException(AgentException):
    pass


class NoSecretException(AgentException):
    pass


class NoPingException(AgentException):
    pass


class AgentClient(object):
    def __init__(self, host, client_id, secret, access_token=None, refresh_token=None, *args, **kwargs):
        self.host = host
        self.scheme = 'https'
        if self.host == 'localhost:8080':
            self.scheme = 'http'
        self.client_id = client_id
        self.secret = secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        super(AgentClient, self).__init__(*args, **kwargs)

    @property
    def headers(self):
        if self.access_token:
            return {
                'Authorization': 'Bearer {0}'.format(self.access_token)
            }
        return None

    def request_tokens(self):
        url = "{0}://{1}/oauth/v1/token".format(self.scheme, self.host)
        data = {
            'client_id': self.client_id,
            'client_secret': self.secret,
            'scope': 'agent'
        }
        if self.refresh_token is None:
            data['grant_type'] = 'authorization_code'
            data['code'] = self.secret
            data['redirect_uri'] = '/'
        else:
            data['grant_type'] = 'refresh_token'
            data['refresh_token'] = self.refresh_token
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            token_response = response.json()
            self.access_token = token_response['access_token']
            self.refresh_token = token_response['refresh_token']
        except requests.exceptions.RequestException:
            self.access_token = None
            self.refresh_token = None
            raise

    def get(self, url, params=None):
        url = "{0}://{1}{2}".format(self.scheme, self.host, url)
        response = requests.get(url, data=params, headers=self.headers)
        if response.status_code == 401:
            self.request_tokens()
            response = requests.get(url, data=params, headers=self.headers)
        response.raise_for_status()
        return response

    def post(self, url, params):
        url = "{0}://{1}{2}".format(self.scheme, self.host, url)
        response = requests.post(url, data=params, headers=self.headers)
        if response.status_code == 401:
            self.request_tokens()
            response = requests.post(url, data=params, headers=self.headers)
        response.raise_for_status()
        return response


def read_level(levelfile):
    logger = logging.getLogger('ping')
    t = dt = raining = thundering = None
    try:
        n = nbt.NBTFile(levelfile)
        if n is not None:
            try:
                t = n[0]["Time"].value
                t /= 24000
            except:
                t = None
            try:
                dt = n[0]["DayTime"].value
                dt %= 24000
            except:
                dt = None
            try:
                raining = bool(n[0]["raining"].value)
            except:
                raining = None
            try:
                thundering = bool(n[0]["thundering"].value)
            except:
                thundering = None
    except Exception, e:
        logger.error(e)
    return t, dt, raining, thundering


def read_pid(pidfile):
    logger = logging.getLogger('ping')
    try:
        with open(pidfile, 'r') as pidfile:
            pid = pidfile.read()
            if pid:
                return pid.strip()
    except IOError, e:
        logger.warn("Can't read the PID file '{0}': {1}".format(e.filename, e.strerror))
    return None


def pid_exists(pid):
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            return False
    return True


def is_server_running(pidfile):
    is_running = False
    pid = read_pid(pidfile)
    if pid:
        is_running = pid_exists(int(pid))
    return is_running


def execute_commands(commandfile, commands):
    with open(commandfile, "a") as command_fifo:
        for command in commands:
            c = command.get('command', None)
            u = command.get('username', None)
            if c and c.startswith(u'/say '):
                if len(c) <= 5:
                    c = None
                elif u:
                    c = u"/say <{0}> {1}".format(u, c[5:])
            if c:
                c += u'\n'
                command_fifo.write(c.encode('ISO-8859-2', errors='ignore'))


def ping_host(running, server_day, server_time, raining, thundering):
    logger = logging.getLogger('ping')
    try:
        params = {'server_name': client.host}
        if running is not None:
            params['is_server_running'] = running
        if server_day is not None and server_time is not None:
            params['server_day'] = server_day
            params['server_time'] = server_time
        params['is_raining'] = raining
        params['is_thundering'] = thundering
        recent_overloads = calculate_overloaded()
        params['num_overloads'] = recent_overloads[0]
        params['ms_behind'] = recent_overloads[1]
        params['skipped_ticks'] = recent_overloads[2]
        if address:
            params['address'] = address

        response_json = client.post("/api/v1/agents/ping", params=params).json()
        commands = response_json['commands']
        if commands:
            execute_commands(mc_commandfile, commands)
    except requests.exceptions.RequestException as e:
        logger.error(u"UNEXPECTED RESPONSE {0}".format(e))


def is_moved_wrongly_warning(line):
    return re.search(ur"([\w-]+) ([\w:]+) \[(?P<log_level>\w+)\] (.+) moved wrongly!", line)


def record_overloaded_warning(line):
    global overloads
    overloaded = re.match(
        ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] Can't keep up! .+ Running (?P<behind>.+)ms behind, skipping (?P<ticks>.+) tick\(s\)",
        line
    )
    if overloaded is None:
        overloaded = re.match(
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] Can't keep up! .+",
            line
        )
    if overloaded is not None:
        gd = overloaded.groupdict()
        d = gd.get('date', None)
        t = gd.get('time', None)
        if d and t:
            dts = "{0} {1}".format(d, t)
            dt = datetime.datetime.strptime(dts, "%Y-%m-%d %H:%M:%S")
            dt = tz.localize(dt) if tz else pytz.utc.localize(dt)
            dt = dt.astimezone(pytz.utc).replace(tzinfo=None)
            overload = (dt, gd.get('behind', None), gd.get('ticks', None))
            overloads.append(overload)
    return overloaded is not None


def calculate_overloaded():
    global overloads
    now = datetime.datetime.utcnow()
    cutoff = now - datetime.timedelta(minutes=5)
    for i, overload in overloads:
        dt = overload[0]
        if dt > cutoff:
            break
    del overloads[0:i]
    behind = 0
    ticks = 0
    for overload in overloads:
        if overload[1]:
            behind += int(overload[1])
        if overload[2]:
            ticks += int(overload[2])
    return (len(overloads), behind, ticks)


def is_chat(line):
    return re.search(ur"([\w-]+) ([\w:]+) \[(\w+)\] \<(\w+)\> (.+)", line)


def post_line(line, skip_chat):
    logger = logging.getLogger('log_line')
    if is_moved_wrongly_warning(line):
        logger.debug(u"SKIPPING '{0}'".format(line))
        return
    if record_overloaded_warning(line):
        logger.debug(u"RECORDING OVERLOAD '{0}'".format(line))
        return
    if skip_chat and is_chat(line):
        logger.debug(u"SKIPPING '{0}'".format(line))
        return
    params = {'line': line.encode('utf-8', errors='ignore'), 'zone': zone}
    tries = 0
    while True:
        tries = tries + 1
        try:
            response = client.post("/api/v1/agents/logline", params)
            logger.debug(u"REPORTED ({0}): {1}".format(response.status_code, line))
            break
        except requests.exceptions.RequestException as e:
            logger.error(u"UNEXPECTED RESPONSE {0}".format(e))
        timeout = 10 if tries < 10 else 30
        logger.info(u"SLEEPING FOR {0} SECONDS...".format(timeout))
        time.sleep(timeout)


def get_lastline():
    logger = logging.getLogger('log_line')
    try:
        response_json = client.get("/api/v1/agents/lastline").json()
        lastline = response_json['lastline']
        return lastline
    except requests.exceptions.RequestException as e:
        logger.error(u"UNEXPECTED RESPONSE {0}".format(e))
        raise NoPingException()


def line_reader(logfile, last_ping, last_time):
    while True:
        if datetime.datetime.now() > last_ping + datetime.timedelta(seconds=5):
            running = is_server_running(mc_pidfile)
            server_day, server_time, raining, thundering = read_level(mc_levelfile)
            last_time = datetime.datetime.now()
            num, behind, ticks = calculate_overloaded()
            ping_host(running, server_day, server_time, raining, thundering)
            last_ping = datetime.datetime.now()
        where = logfile.tell()
        raw_line = logfile.readline()
        line = raw_line.decode('ISO-8859-2', errors='ignore')
        line = line.strip()
        if not line:
            logfile.seek(where)
            time.sleep(1.0)
        else:
            yield line, last_ping, last_time


def tail(last_line, last_ping, last_time):
    logger = logging.getLogger('main')
    skip_chat = skip_chat_history
    while True:
        try:
            with open(mc_logfile, 'r') as logfile:
                st_results = os.stat(mc_logfile)
                st_size = st_results[6]
                if parse_mc_history:
                    read_last_line = False if last_line is not None else True
                    if last_line is not None:
                        logger.debug(u"Skipping ahead to line '{0}'".format(last_line))
                else:
                    st_results = os.stat(mc_logfile)
                    st_size = st_results[6]
                    logfile.seek(st_size)
                    read_last_line = True
                for line, last_ping, last_time in line_reader(logfile, last_ping, last_time):
                    if read_last_line:
                        post_line(line, skip_chat)
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
        except IOError, e:
            logger.error(e)
            time.sleep(5)


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
    formatter = logging.Formatter(u'%(asctime)s : %(name)-8s %(levelname)-6s %(message)s')
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


def shutdown_handler(signum=None, frame=None):
    logger = logging.getLogger('main')
    logger.info('Shutdown handler called with signal {0}'.format(signum))
    params = {'server_name': client.host}
    params['is_server_running'] = is_server_running(mc_pidfile)
    if address:
        params['address'] = address
    client.post("/api/v1/agents/ping", params=params).json()
    sys.exit(0)


def main(argv):
    global client
    global mc_pidfile
    global mc_logfile
    global mc_levelfile
    global mc_commandfile
    global tz
    global zone
    global parse_mc_history
    global skip_chat_history
    global address

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
        help="The MC COAL agent log filename (default: '{0}'). Set to blank (i.e. '--agent-logfile=') to suppress file logging.".format(DEFAULT_AGENT_LOGFILE)
    )
    coal_host = get_application_host()
    parser.add_argument(
        '--coal_host',
        default=coal_host,
        help="The MC COAL server host name (default: {0})".format(
            "'{0}'".format(coal_host) if coal_host else '<No default found in app.yaml>'
        )
    )
    parser.add_argument(
        '--agent_client_id',
        help="The MC COAL agent client ID."
    )
    parser.add_argument(
        '--agent_secret',
        help="The MC COAL agent API secret."
    )
    parser.add_argument(
        '--mc_logfile',
        default=DEFAULT_MC_LOGFILE,
        help="The Minecraft server log filename (default: '{0}')".format(DEFAULT_MC_LOGFILE)
    )
    parser.add_argument(
        '--mc_levelfile',
        default=DEFAULT_MC_LEVELFILE,
        help="The Minecraft level.dat filename (default: '{0}')".format(DEFAULT_MC_LEVELFILE)
    )
    parser.add_argument(
        '--mc_pidfile',
        default=DEFAULT_MC_PIDFILE,
        help="The Minecraft server PID filename (default: '{0}')".format(DEFAULT_MC_PIDFILE)
    )
    parser.add_argument(
        '--mc_commandfifo',
        default=DEFAULT_MC_COMMAND_FIFO,
        help="The Minecraft server command fifo filename (default: '{0}')".format(DEFAULT_MC_COMMAND_FIFO)
    )
    parser.add_argument(
        '--parse_mc_history',
        action='store_true',
        help="Set this flag to parse and report on the Minecraft server log from the beginning (or where parsing left off last time) rather than just new entries."
    )
    parser.add_argument(
        '--parse_all',
        action='store_true',
        help="Set this flag to parse and report on the Minecraft server log from the beginning even if parsing has been partially completed."
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
        help="The Minecraft server timezone name (default: {0})".format(
            "'{0}'".format(mc_timezone) if mc_timezone else '<No default local timezone>'
        )
    )
    parser.add_argument(
        '--address',
        help="The Minecraft server IP address and (optional) port"
    )
    args = parser.parse_args()
    init_loggers(debug=args.verbose, logfile=args.agent_logfile)
    logger = logging.getLogger('main')
    try:
        for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
            signal.signal(sig, shutdown_handler)
        coal_host = args.coal_host
        if not coal_host:
            raise NoHostException()
        agent_client_id = args.agent_client_id
        if not agent_client_id:
            raise NoClientException()
        agent_secret = args.agent_secret
        if not agent_secret:
            raise NoSecretException()
        mc_logfile = args.mc_logfile
        mc_levelfile = args.mc_levelfile
        mc_pidfile = args.mc_pidfile
        mc_commandfile = args.mc_commandfifo
        parse_mc_history = args.parse_mc_history
        skip_chat_history = args.skip_chat_history
        mc_timezone = args.mc_timezone
        tz = pytz.timezone(mc_timezone)
        zone = tz.zone
        client = AgentClient(coal_host, agent_client_id, agent_secret)
        last_line = get_lastline()
        parse_all = args.parse_all
        if parse_all:
            last_line = None
        address = args.address
        last_ping = datetime.datetime.now()
        last_time = datetime.datetime.now()
        logger.info(u"Monitoring '{0}' and reporting to '{1}'...".format(mc_logfile, coal_host))
        tail(last_line, last_ping, last_time)
    except NoPingException:
        logger.error(u"Unable to ping '{0}'".format(coal_host))
    except pytz.UnknownTimeZoneError:
        logger.error(u"Invalid timezone: '{0}'".format(mc_timezone))
    except NoHostException:
        logger.error(u"No MC COAL server host name provided.")
    except NoClientException:
        logger.error(u"No agent client ID provided.")
    except NoSecretException:
        logger.error(u"No agent secret provided.")
    except KeyboardInterrupt:
        logger.info(u"Canceled")
    except SystemExit:
        logger.info(u"System Exit")
    except Exception, e:
        logger.error(u"Unexpected {0}: {1}".format(type(e).__name__, e))
    logger.info(u"Shutting down... Goodbye.")


if __name__ == "__main__":
    main(sys.argv[1:])
