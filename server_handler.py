import fix_path  # noqa

from google.appengine.ext import ndb

import webapp2

from models import Server, ScreenShot
from user_auth import UserHandler


class ServerHandlerBase(UserHandler):
    def get_template_context(self, context=None):
        template_context = super(ServerHandlerBase, self).get_template_context(context=context)
        server = template_context['server'] = template_context.get('server', None) or getattr(self.request, 'server', None)  # noqa
        if server is not None:
            bg_img = ScreenShot.random(server.key)
            if bg_img is not None:
                template_context['bg_img'] = bg_img.blurred_image_serving_url
        return template_context

    def redirect_to_server(self, route_name):
        servers = Server.query_all().fetch(2)
        if servers and len(servers) == 1:
            self.redirect(webapp2.uri_for(route_name, server_key=servers[0].url_key))
        else:
            self.redirect(webapp2.uri_for('main'))

    def get_server_by_key(self, key, abort=True):
        if key:
            try:
                server_key = ndb.Key(urlsafe=key)
                server = server_key.get()
            except Exception:
                server = Server.get_by_short_name(key)
        else:
            server = None
        if server is not None and not server.active:
            server = None
        if abort and not server:
            self.abort(404)
        self.request.server = server
        return self.request.server

    def head(self):
        self.get()
        self.response.clear()


class PagingHandler(ServerHandlerBase):
    def get_results_with_cursors(self, query, reverse_query, size):
        cursor = self.request.get('cursor', None)
        if cursor:
            try:
                cursor = ndb.Cursor.from_websafe_string(cursor)
            except:
                cursor = None
        next_cursor = previous_cursor = None
        if cursor is not None:
            reverse_cursor = cursor.reversed()
            reverse_results, reverse_next_cursor, reverse_more = reverse_query.fetch_page(
                size, start_cursor=reverse_cursor
            )
            if reverse_more:
                previous_cursor = reverse_next_cursor.reversed()
                previous_cursor = previous_cursor.to_websafe_string()
            else:
                previous_cursor = 'START'
        results, next_cursor, more = query.fetch_page(size, start_cursor=cursor)
        if more:
            next_cursor = next_cursor.to_websafe_string()
        else:
            next_cursor = None
        return results, previous_cursor, next_cursor
