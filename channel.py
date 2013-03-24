import logging
import random
import time
from webapp2 import WSGIApplication, RequestHandler, Route
from webapp2_extras.json import json
from google.appengine.api import channel
from google.appengine.api import memcache
from filters import datetime_filter

CHANNELERS_KEY = 'channelers'
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

    channelers = memcache.get(CHANNELERS_KEY)
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

        memcache_client = memcache.Client()
        while True:
            channelers = memcache_client.gets(CHANNELERS_KEY)
            if channelers is None:
                ## memcache.Client.cas() always fails and returns False when
                ## trying to set a key that didn't previously exist in
                ## memcache...so I guess I just have to hope I don't
                ## overwrite it if someone else sneaks one in right before
                ## me...?? (Or is that a bug in dev_appserver?)
                memcache_client.set(CHANNELERS_KEY, [channeler_id])
                break

            if channeler_id in channelers:
                break

            channelers.append(channeler_id)
            if memcache_client.cas(CHANNELERS_KEY, channelers):
                break


class DisconnectedHandler(RequestHandler):

    def post(self):
        channeler_id = self.request.get('from')
        logging.info(u'channel client %s disconnected!' % channeler_id)

        memcache_client = memcache.Client()
        while True:
            channelers = memcache_client.gets(CHANNELERS_KEY)
            if channelers is None:
                break
            if channeler_id not in channelers:
                break
            channelers.remove(channeler_id)
            if memcache_client.cas(CHANNELERS_KEY, channelers):
                break


application = WSGIApplication(
    [
        Route('/_ah/channel/connected/', ConnectedHandler),
        Route('/_ah/channel/disconnected/', DisconnectedHandler),
    ],
    debug=False
)
