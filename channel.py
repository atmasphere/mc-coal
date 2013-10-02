import logging
import random
import time

from google.appengine.api import channel
from google.appengine.ext import ndb

from webapp2 import WSGIApplication, RequestHandler, Route
from webapp2_extras.json import json

from filters import datetime_filter


KEY_NAME = 'channels'

class ServerChannels(ndb.Model):
    client_ids = ndb.StringProperty(repeated=True)

    @classmethod
    def get_client_id(cls, server_key, user):
        string_id = server_key.string_id() or '{0}'.format(server_key.integer_id())
        return '{0}.{1}.{2}.{3}'.format(
            string_id,
            user.key.id(),
            int(time.time()),
            random.randrange(999)
        )
    @classmethod
    def get_server_key(cls, client_id):
        key_id = client_id[:client_id.find('.')]
        try:
            key_id = int(key_id)
        except ValueError:
            pass
        return ndb.Key('Server', key_id)

    @classmethod
    def get_key(cls, server_key):
        return ndb.Key(cls, KEY_NAME, parent=server_key)

    @classmethod
    def get_client_ids(cls, server_key):
        server_channels = cls.get_key(server_key).get()
        if server_channels is not None:
            return server_channels.client_ids
        return []

    @classmethod
    def create_channel(cls, server_key, user):
        return channel.create_channel(cls.get_client_id(server_key, user))

    @classmethod
    def send_message(cls, log_line, event):
        message = {
            'event': event,
            'date': datetime_filter(log_line.timestamp, '%b %d, %Y'),
            'time': datetime_filter(log_line.timestamp, '%I:%M%p'),
            'username': log_line.username,
            'chat': log_line.chat,
            'death_message': log_line.death_message
        }
        client_ids = cls.get_client_ids(log_line.server_key)
        if client_ids:
            message_json = json.dumps(message)
            for client_id in client_ids:
                try:
                    channel.send_message(client_id, message_json)
                except:
                    pass

    @classmethod
    def add_client_id(cls, client_id):
        server_key = cls.get_server_key(client_id)
        server_channels = cls.get_or_insert(KEY_NAME, parent=server_key)
        if server_channels is not None and client_id not in server_channels.client_ids:
            server_channels.client_ids.append(client_id)
            server_channels.put()

    @classmethod
    def remove_client_id(cls, client_id):
        server_key = cls.get_server_key(client_id)
        server_channels = cls.get_key(server_key).get()
        if server_channels is not None:
            try:
                server_channels.client_ids.remove(client_id)
                server_channels.put()
            except ValueError:
                pass


class ConnectedHandler(RequestHandler):
    def post(self):
        client_id = self.request.get('from')
        logging.info(u'channel client %s connected!' % client_id)
        ServerChannels.add_client_id(client_id)


class DisconnectedHandler(RequestHandler):
    def post(self):
        client_id = self.request.get('from')
        logging.info(u'channel client %s disconnected!' % client_id)
        ServerChannels.remove_client_id(client_id)


application = WSGIApplication(
    [
        Route('/_ah/channel/connected/', ConnectedHandler),
        Route('/_ah/channel/disconnected/', DisconnectedHandler),
    ],
    debug=False
)
