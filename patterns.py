# [SublimeLinter flake8-max-line-length:250]
import fix_path  # noqa

UNKNOWN_TAG = 'unknown'
TIMESTAMP_TAG = 'timestamp'
CONNECTION_TAG = 'connection'
LOGIN_TAG = 'login'
LOGOUT_TAG = 'logout'
CHAT_TAG = 'chat'
SERVER_TAG = 'server'
PERFORMANCE_TAG = 'performance'
OVERLOADED_TAG = 'overloaded'
STOPPING_TAG = 'stopping'
STARTING_TAG = 'starting'
DEATH_TAG = 'death'
ACHIEVEMENT_TAG = 'achievement'
COAL_TAG = 'coal'
LOGIN_TAGS = [TIMESTAMP_TAG, CONNECTION_TAG, LOGIN_TAG]
LOGOUT_TAGS = [TIMESTAMP_TAG, CONNECTION_TAG, LOGOUT_TAG]
CHAT_TAGS = [TIMESTAMP_TAG, CHAT_TAG]
OVERLOADED_TAGS = [TIMESTAMP_TAG, SERVER_TAG, PERFORMANCE_TAG, OVERLOADED_TAG]
STOPPING_TAGS = [TIMESTAMP_TAG, SERVER_TAG, STOPPING_TAG]
STARTING_TAGS = [TIMESTAMP_TAG, SERVER_TAG, STARTING_TAG]
DEATH_TAGS = [TIMESTAMP_TAG, DEATH_TAG]
ACHIEVEMENT_TAGS = [TIMESTAMP_TAG, ACHIEVEMENT_TAG]
COAL_TAGS = [TIMESTAMP_TAG, COAL_TAG]
TIMESTAMP_TAGS = [TIMESTAMP_TAG, UNKNOWN_TAG]
CHANNEL_TAGS_SET = set(['login', 'logout', 'chat', 'death', 'achievement'])
REGEX_TAGS = [
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+)\[/(?P<ip>[\w.]+):(?P<port>\w+)\] logged in.+\((?P<location_x>-?\w.+), (?P<location_y>-?\w.+), (?P<location_z>-?\w.+)\)"
        ],
        LOGIN_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) lost connection:.+"
        ],
        LOGOUT_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] \[Server\] \<COAL\> (?P<chat>.+)",
        ],
        COAL_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] \<(?P<username>[\w\xA7]+)\> (?P<chat>.+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] \[Server\] \<(?P<username>[\w@\.\xA7]+)\> (?P<chat>.+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] \[Server\] (?P<chat>.+)"
        ],
        CHAT_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] Can't keep up! .+",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] Can't keep up! .+ Running (?P<behind>.+)ms behind, skipping (?P<ticks>.+) tick\(s\)"
        ],
        OVERLOADED_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] Stopping server"
        ],
        STOPPING_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] Starting minecraft server version (?P<server_version>[\S:]+)"
        ],
        STARTING_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was squashed by a falling anvil",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was pricked to death",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) walked into a cactus whilst trying to escape (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was shot by arrow",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) drowned whilst trying to escape (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) drowned",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) blew up",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was blown up by (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) hit the ground too hard",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) fell off a ladder",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) fell off some vines",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) fell out of the water",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) fell from a high place",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) fell into a patch of fire",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) fell into a patch of cacti",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was doomed to fall by (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was shot off some vines by (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was blown from a high place by (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) went up in flames",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) burned to death",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was burnt to a crisp whilst fighting (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) walked into a fire whilst fighting (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was slain by (?P<username_mob>[\w\xA7]+) using (?P<weapon>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was slain by (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was shot by (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was fireballed by (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was killed by magic",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was killed by (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) got finished off by (?P<username_mob>[\w\xA7]+) using (?P<weapon>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) tried to swim in lava while trying to escape (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) tried to swim in lava",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) died",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) starved to death",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) suffocated in a wall",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was killed while trying to hurt (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was pummeled by (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) fell out of the world",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) fell from a high place and fell out of the world",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) was knocked into the void by (?P<username_mob>[\w\xA7]+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) withered away",
        ],
        DEATH_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>[\w\xA7]+) has just earned the achievement \[(?P<achievement>.+)\]",
        ],
        ACHIEVEMENT_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] .+"
        ],
        TIMESTAMP_TAGS
    )
]
