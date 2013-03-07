import logging

import webapp2

from agar.env import on_production_server

from models import Server


class ServerStatusHandler(webapp2.RequestHandler):
    def get(self):
        logging.info("Starting server status check...")
        server = Server.global_key().get()
        server.update_is_running()
        logging.info("Finishing server status check.")


application = webapp2.WSGIApplication(
    [
        webapp2.Route('/cron/server/status', ServerStatusHandler, name='cron_server_status'),
    ],
    debug=not on_production_server
)
