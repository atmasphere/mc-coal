# Install-specific COAL Configuration

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

COAL_SECRET_KEY = 'a_secret_string'

COAL_COOKIE_MAX_AGE = None

COAL_OAUTH_TOKEN_EXPIRES_IN = 3600
