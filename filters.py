from pytz.gae import pytz

from config import coal_config


def datetime_filter(value, format='%A, %B %d, %Y %I:%M:%S %p'):
    utc_dt = pytz.utc.localize(value)
    timezone_dt = utc_dt.astimezone(pytz.timezone(coal_config.TIMEZONE))
    return timezone_dt.strftime(format)


FILTERS = {
    'datetimeformat': datetime_filter
}
