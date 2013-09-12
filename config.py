from agar.config import Config


class COALConfig(Config):
    _prefix = "COAL"

    TITLE = "MC COAL"
    USER_WHITELIST = []
    TIMEZONE = ''
    RESULTS_PER_PAGE = 50
    SECRET_KEY = ''
    COOKIE_MAX_AGE = None
    OAUTH_TOKEN_EXPIRES_IN = 3600

coal_config = COALConfig.get_config()
