import os

import webapp2

from models import Server


ON_SERVER = not os.environ.get('SERVER_SOFTWARE', 'Development').startswith('Development')


class ServerStatusHandler(webapp2.RequestHandler):
    def get(self):
        for server in Server.query_all():
            server.update_status()


application = webapp2.WSGIApplication(
    [
        webapp2.Route('/cron/server/status', ServerStatusHandler, name='cron_server_status'),
    ],
    debug=not ON_SERVER
)
