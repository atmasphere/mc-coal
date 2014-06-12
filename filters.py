import json
import pytz


def datetime_filter(value, format='%A, %B %d, %Y %I:%M:%S %p', timezone=None):
    tf = format
    if '%P' in format:
        tf = format.replace('%P', '%p')
    if timezone is None:
        timezone = pytz.utc
    if value:
        utc_dt = pytz.utc.localize(value)
        timezone_dt = utc_dt.astimezone(timezone)
        ts = timezone_dt.strftime(tf)
        if '%p' in format:
            ts = ts.replace('AM', 'am').replace('PM', 'pm')
        return ts
    return ''


def username_pronoun_filter(username, user):
    return "YOU" if user.is_username(username) else username


def escape_javascript_filter(value):
    return json.dumps(value).replace("</", "<\\/")


FILTERS = {
    'datetimeformat': datetime_filter,
    'username_pronoun': username_pronoun_filter,
    'escapejs': escape_javascript_filter,
}
