from agar.config import Config


class COALConfig(Config):
    _prefix = "COAL"

    USER_WHITELIST = []
    TIMEZONE = ''
    SECRET_KEY = ''
    COOKIE_MAX_AGE = None
    OAUTH_TOKEN_EXPIRES_IN = 3600

coal_config = COALConfig.get_config()
