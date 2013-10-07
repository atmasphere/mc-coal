# Default COAL Configuration

COAL_USER_WHITELIST = []

COAL_SECRET_KEY = 'a_secret_string'

COAL_COOKIE_MAX_AGE = 2592000  # 30 days

COAL_OAUTH_TOKEN_EXPIRES_IN = 3600 # 1 hour

try:
    from mc_coal_config import *
except ImportError, e:
    pass
