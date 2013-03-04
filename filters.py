from pytz.gae import pytz

from webapp2 import uri_for

from config import coal_config


def datetime_filter(value, format='%A, %B %d, %Y %I:%M:%S %p'):
    utc_dt = pytz.utc.localize(value)
    timezone_dt = utc_dt.astimezone(pytz.timezone(coal_config.TIMEZONE))
    return timezone_dt.strftime(format)


def next_page_filter(name, cursor=None):
    if cursor == 'START':
        return uri_for(name)
    elif cursor is not None:
        return "{0}?cursor={1}".format(uri_for(name), cursor)
    return uri_for(name)


FILTERS = {
    'datetimeformat': datetime_filter,
    'nextpageurl': next_page_filter
}
