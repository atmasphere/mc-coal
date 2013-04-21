import logging

from google.appengine.api import search
from google.appengine.ext import ndb


log_line_index = search.Index(name='log_line_search')
player_index = search.Index(name='player_search')


def add_to_index(index, key, fields):
    doc = search.Document(doc_id=key.urlsafe(), fields=fields)
    retries = 0
    while True:
        try:
            index.put(doc)
            break
        except Exception, e:
            if retries > 10:
                logging.error(u"Couldn't add doc_id '{0}' to the search index: {1}".format(key.urlsafe(), e))
                raise e
            retries += 1
    return doc


def add_log_line(log_line):
    fields = [search.TextField(name='line', value=log_line.line)]
    if log_line.timestamp is not None:
        fields.append(search.DateField(name='timestamp', value=log_line.timestamp.date()))
        fields.append(search.TextField(name='timestamp_string', value=log_line.timestamp.strftime('%Y-%m-%d %H:%M:%S')))
    if log_line.log_level:
        fields.append(search.TextField(name='log_level', value=log_line.log_level))
    if log_line.username:
        fields.append(search.TextField(name='username', value=log_line.username))
    if log_line.location:
        fields += [
            search.NumberField(name='location_x', value=log_line.location.x if log_line.location else None),
            search.NumberField(name='location_y', value=log_line.location.y if log_line.location else None),
            search.NumberField(name='location_z', value=log_line.location.z if log_line.location else None)
        ]
    if log_line.chat:
        fields.append(search.TextField(name='chat', value=log_line.chat))
    if log_line.tags:
        fields.append(search.TextField(name='tags', value=' '.join(log_line.tags) if log_line.tags else ''))
    return add_to_index(log_line_index, log_line.key, fields)


def add_player(player):
    fields = [search.TextField(name='username', value=player.username)]
    if player.last_login_timestamp is not None:
        fields.append(search.DateField(name='last_login_timestamp', value=player.last_login_timestamp.date()))
    return add_to_index(player_index, player.key, fields)


def remove_from_index(index, key):
    retries = 0
    while True:
        try:
            index.delete(key.urlsafe())
            break
        except Exception, e:
            if retries > 10:
                logging.error(u"Couldn't remove doc_id '{0}' from the search index: {1}".format(key.urlsafe(), e))
                raise e
            retries += 1


def remove_log_line(log_line_key):
    remove_from_index(log_line_index, log_line_key)


def remove_player(player_key):
    remove_from_index(player_index, player_key)


def search_index(index, query_string, sort_options=None, limit=1000, offset=None, cursor=None):
    query_string = query_string.strip()
    options = search.QueryOptions(
        limit=limit,
        offset=offset,
        cursor=search.Cursor(web_safe_string=cursor) if cursor is not None else search.Cursor(),
        sort_options=sort_options
    )
    query = search.Query(query_string=query_string, options=options)
    retries = 0
    instances = None
    while True:
        try:
            results = index.search(query)
            keys = [ndb.Key(urlsafe=result.doc_id) for result in results]
            instances = ndb.get_multi(keys)
            break
        except Exception, e:
            if retries > 10:
                logging.error(u"Couldn't search index: {0}".format(e))
                raise e
            retries += 1
    next_cursor = results.cursor.web_safe_string if results.cursor else None
    return instances, results.number_found, next_cursor


def search_log_lines(query_string, limit=1000, offset=None, cursor=None):
    timestamp_desc = search.SortExpression(
        expression='timestamp_string',
        direction=search.SortExpression.DESCENDING,
        default_value=''
    )
    sort_options = search.SortOptions(expressions=[timestamp_desc], limit=limit)
    return search_index(log_line_index, query_string, sort_options=sort_options, limit=limit, offset=offset, cursor=cursor)


def search_players(query_string, limit=1000, offset=None):
    return search_index(player_index, query_string, limit=limit, offset=offset)
