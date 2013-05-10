# Default COAL Configuration

COAL_TITLE = "MC COAL"

COAL_USER_WHITELIST = []

COAL_TIMEZONE = 'US/Central'

COAL_RESULTS_PER_PAGE = 50

COAL_API_PASSWORD = 'a_password'

COAL_SECRET_KEY = 'a_secret_string'

COAL_COOKIE_MAX_AGE = 2592000  # 30 days

try:
    from mc_coal_config import *
except ImportError, e:
    pass
