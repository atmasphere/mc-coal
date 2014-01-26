import os

import webapp2
from webapp2_extras import jinja2

from filters import FILTERS


ON_SERVER = not os.environ.get('SERVER_SOFTWARE', 'Development').startswith('Development')


def uri_for_pagination(name, server_key=None, cursor=None):
    if server_key is None:
        uri = webapp2.uri_for(name)
    else:
        uri = webapp2.uri_for(name, server_key=server_key)
    if cursor is not None and cursor != 'START':
        if cursor.startswith('PAGE_0'):
            uri = u"{0}{1}{2}".format(uri, '&' if '?' in uri else '?', cursor[7:])
        else:
            uri = u"{0}{1}cursor={2}".format(uri, '&' if '?' in uri else '?', cursor)
    return uri


class JinjaHandler(webapp2.RequestHandler):
    _filters = FILTERS
    _globals = {
        'uri_for': webapp2.uri_for,
        'uri_for_pagination': uri_for_pagination,
        'ON_SERVER': ON_SERVER
    }

    @webapp2.cached_property
    def jinja2(self):
        return jinja2.get_jinja2(factory=self.jinja2_factory)

    def jinja2_factory(self, app):
        j = jinja2.Jinja2(app)
        j.environment.filters.update(self._filters)
        j.environment.globals.update(self._globals)
        return j

    def get_template_context(self, context=None):
        return context

    def render_template(self, filename, context={}):
        context = self.get_template_context(context)
        self.response.write(self.jinja2.render_template(filename, **context))
