import datetime
import itertools
import os

from google.appengine.ext import ndb

import webapp2

from gce import Instance
from models import Server
from oauth import Token


ON_SERVER = not os.environ.get('SERVER_SOFTWARE', 'Development').startswith('Development')


class ServerStatusHandler(webapp2.RequestHandler):
    def get(self):
        instance = Instance.singleton()
        gce_server_running = False
        servers = Server.query_all()
        for server in servers:
            server.update_status()
            if server.is_gce:
                if server.is_running and not server.idle and not server.has_open_play_session:
                    server.idle = datetime.datetime.utcnow()
                    server.put()
                server.stop_if_idle()
                if server.is_queued or server.is_running:
                    gce_server_running = True
                    if instance.idle:
                        instance.idle = None
                        instance.put()
        if instance.is_running() and not gce_server_running and not instance.idle:
            instance.idle = datetime.datetime.utcnow()
            instance.put()
        instance.stop_if_idle()


class ServerBackupHandler(webapp2.RequestHandler):
    def get(self):
        servers = Server.query_running()
        for server in servers:
            server.backup()


def grouper(n, iterable):
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


class DeleteExpiredTokens(webapp2.RequestHandler):
    @ndb.toplevel
    def get(self):
        now = datetime.datetime.utcnow()
        token_query = Token.query_expired(now)
        for keys in grouper(50, token_query.iter(keys_only=True)):
            ndb.delete_multi_async(keys)


application = webapp2.WSGIApplication(
    [
        webapp2.Route('/cron/server/status', ServerStatusHandler, name='cron_server_status'),
        webapp2.Route('/cron/server/backup', ServerBackupHandler, name='cron_server_backup'),
        webapp2.Route('/cron/oauth/clean', DeleteExpiredTokens, name='cron_oauth_clean')
    ],
    debug=not ON_SERVER
)
