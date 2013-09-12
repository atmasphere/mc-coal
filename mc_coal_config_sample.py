# Install-specific COAL Configuration

COAL_TITLE = "My Minecraft Community"

COAL_USER_WHITELIST = [
    {
        'email': 'steve@example.com',
        'username': 'steve',
        'admin': True
    },
    {
        'email': 'bill@example.com',
        'username': 'bill',
        'admin': False
    }
]

COAL_TIMEZONE = 'US/Central'

COAL_SECRET_KEY = 'a_secret_string'

COAL_COOKIE_MAX_AGE = None

COAL_RESULTS_PER_PAGE = 50

COAL_OAUTH_TOKEN_EXPIRES_IN = 3600
