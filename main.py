import logging
import jinja2
import webapp2

from agar.config import Config
from agar.env import on_production_server


class PortalConfig(Config):
    _prefix = "portal"

    HOST_NAME = u'unknown'
    DEFAULT_PARTNER_SUBDOMAIN = u'unknown'
    MAJOR_VERSION = u'unknown'
    MINOR_VERSION = u'unknown'
    TINY_VERSION = u'unknown'
    ASSET_TIMESTAMP = u'unknown'
    GOOGLE_ANALYTICS_ID = u'unknown'


class JinjaHandler(webapp2.RequestHandler):
    _filters = {}
    _globals = {}

    @webapp2.cached_property
    def jinja2(self):
        return jinja2.get_jinja2(factory=self.jinja2_factory)

    def jinja2_factory(self, app):
        j = jinja2.Jinja2(app)
        j.environment.filters.update(self._filters)
        j.environment.globals.update(self._globals)
        return j

    def get_template_args(self, template_args=None):
        return template_args

    def render_template(self, filename, context={}):
        context = self.get_template_args(context)

        if not on_production_server:
            logging.info("Template values: {0}".format(context))

        self.response.write(self.jinja2.render_template(filename, **context))


class MainHandler(JinjaHandler):
    def get(self):
        self.response.write("""Hello, MINECRAFT world.""")


application = webapp2.WSGIApplication([
    ('/.*', MainHandler),
], debug=True)
