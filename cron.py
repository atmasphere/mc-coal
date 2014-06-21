import datetime
import os

import webapp2

from gce import Instance
from models import Server


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
                if server.is_running or server.is_queued_start:
                    gce_server_running = True
                    if instance.idle:
                        instance.idle = None
                        instance.put()
        if instance.is_running() and not gce_server_running and not instance.idle:
            instance.idle = datetime.datetime.utcnow()
            instance.put()
        instance.stop_if_idle()


application = webapp2.WSGIApplication(
    [
        webapp2.Route('/cron/server/status', ServerStatusHandler, name='cron_server_status'),
    ],
    debug=not ON_SERVER
)
