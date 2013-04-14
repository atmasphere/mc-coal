import logging
import random
import time
from webapp2 import WSGIApplication, RequestHandler, Route
from webapp2_extras.json import json
from google.appengine.api import channel
from filters import datetime_filter
import models


INTERESTING_TAGS = ['login', 'logout', 'chat']


def token_for_user(user):
    return channel.create_channel(
        '{0}.{1}.{2}'.format(
            user.email,
            int(time.time()),
            random.randrange(999999)
        )
    )


def send_log_line(log_line):
    tags_set = set(log_line.tags)
    interesting_tags_set = set(INTERESTING_TAGS)

    if tags_set.isdisjoint(interesting_tags_set):
        return

    channelers = models.Lookup.channelers()
    if channelers is not None and len(channelers) > 0:
        tag = list(tags_set.intersection(interesting_tags_set))[0]
        message_data = {
            'event': tag,
            'date': datetime_filter(log_line.timestamp, '%b %d, %Y'),
            'time': datetime_filter(log_line.timestamp, '%I:%M%p'),
            'username': log_line.username,
            'chat': log_line.chat,
        }
        message_json = json.dumps(message_data)

        for channeler_id in channelers:
            channel.send_message(channeler_id, message_json)


class ConnectedHandler(RequestHandler):

    def post(self):
        channeler_id = self.request.get('from')
        logging.info(u'channel client %s connected!' % channeler_id)
        models.Lookup.add_channeler(channeler_id)


class DisconnectedHandler(RequestHandler):

    def post(self):
        channeler_id = self.request.get('from')
        logging.info(u'channel client %s disconnected!' % channeler_id)
        models.Lookup.remove_channeler(channeler_id)


application = WSGIApplication(
    [
        Route('/_ah/channel/connected/', ConnectedHandler),
        Route('/_ah/channel/disconnected/', DisconnectedHandler),
    ],
    debug=False
)
