import os

import webapp2

from models import Server


class ServerStatusHandler(webapp2.RequestHandler):
    def get(self):
        for server in Server.query():
            server.check_is_running()


application = webapp2.WSGIApplication(
    [
        webapp2.Route('/cron/server/status', ServerStatusHandler, name='cron_server_status'),
    ],
    debug=os.environ.get('SERVER_SOFTWARE','').startswith('Development')
)
