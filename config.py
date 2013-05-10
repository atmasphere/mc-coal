from agar.config import Config


class COALConfig(Config):
    _prefix = "COAL"

    TITLE = "MC COAL"
    USER_WHITELIST = []
    TIMEZONE = ''
    RESULTS_PER_PAGE = 50
    API_PASSWORD = ''
    SECRET_KEY = ''
    COOKIE_MAX_AGE = None

coal_config = COALConfig.get_config()
