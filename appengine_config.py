# main config

main_SECRET_KEY = 'a_secret_string'

main_TITLE = 'My COAL Installation'

main_DESCRIPTION = 'This is my COAL installation. There are many like it, but this one is mine.'


# gce config

gce_BOOT_DISK_IMAGE = 'debian-7-wheezy-v20140924'


# oauth config

oauth_SECRET_KEY = main_SECRET_KEY  # Can optionally be a different secret string

oauth_TOKEN_EXPIRES_IN = 3600*24*30  # Thirty days
