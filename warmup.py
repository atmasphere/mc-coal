from webapp2 import WSGIApplication, RequestHandler, Route


class WarmupHandler(RequestHandler):
    def get(self):
        self.response.out.write("Warmed Up")


application = WSGIApplication(
    [
        Route('/_ah/warmup', WarmupHandler, name='warmup'),
    ],
    debug=False
)
