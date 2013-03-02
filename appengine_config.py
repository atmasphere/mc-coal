"""
The configuration file used by :py:mod:`agar.config` implementations and other libraries using the
`google.appengine.api.lib_config`_ configuration library. Configuration overrides go in this file.
"""

COAL_USER_WHITELIST = [
    {
        'email': 'admin@example.com',
        'username': 'steve',
        'admin': True
    },
    {
        'email': 'test@example.com',
        'username': 'bill',
        'admin': False
    }
]

COAL_API_PASSWORD = 'thespire'

#########################
# WEBAPP2_EXTRAS SETTINGS
#########################
webapp2_extras_sessions_secret_key = 'a_secret_string'
