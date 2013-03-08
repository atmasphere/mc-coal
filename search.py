from google.appengine.api import search
from google.appengine.ext import ndb


log_line_index = search.Index(name='log_line_search')
player_index = search.Index(name='player_search')


def add_to_index(index, key, fields):
    doc = search.Document(doc_id=key.urlsafe(), fields=fields)
    index.put(doc)
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
    index.delete(key.urlsafe())


def remove_log_line(log_line_key):
    remove_from_index(log_line_index, log_line_key)


def remove_player(player_key):
    remove_from_index(player_index, player_key)


def search_index(index, query_string, sort_options=None, limit=1000, offset=0):
    query_string = query_string.strip()
    options = search.QueryOptions(
        limit=limit,
        offset=offset,
        sort_options=sort_options
    )
    query = search.Query(query_string=query_string, options=options)
    results = index.search(query)
    keys = [ndb.Key(urlsafe=result.doc_id) for result in results]
    return ndb.get_multi(keys), results.number_found


def search_log_lines(query_string, limit=1000, offset=0):
    chat_desc = search.SortExpression(
        expression='timestamp_string',
        direction=search.SortExpression.DESCENDING,
        default_value=''
    )
    sort_options = search.SortOptions(expressions=[chat_desc], limit=limit)
    return search_index(log_line_index, query_string, sort_options=sort_options, limit=limit, offset=offset)


def search_players(query_string, limit=1000, offset=0):
    return search_index(player_index, query_string, limit=limit, offset=offset)
