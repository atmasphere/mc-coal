from agar.config import Config


class COALConfig(Config):
    _prefix = "COAL"

    USER_WHITELIST = []
    TIMEZONE = ''
    RESULTS_PER_PAGE = 50
    API_PASSWORD = ''
    SECRET_KEY = ''

config = COALConfig.get_config()
