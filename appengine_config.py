# main config

main_SECRET_KEY = 'yq92UiIxHDlBFaWdWyft'

main_TITLE = 'Minecraft'

main_DESCRIPTION = 'You know, for kids.'


# gce config

gce_BOOT_DISK_IMAGE = 'debian-7-wheezy-v20140926'


# oauth config

oauth_SECRET_KEY = main_SECRET_KEY  # Can optionally be a different secret string

oauth_TOKEN_EXPIRES_IN = 3600*24*30  # Thirty days
