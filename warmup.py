from webapp2 import WSGIApplication, RequestHandler, Route

from models import Server


class WarmupHandler(RequestHandler):
    def get(self):
        Server.global_key()
        self.response.out.write("Warmed Up")


application = WSGIApplication(
    [
        Route('/_ah/warmup', WarmupHandler, name='warmup'),
    ],
    debug=False
)
