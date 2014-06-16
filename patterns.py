# [SublimeLinter flake8-max-line-length:160]
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
CLAIM_TAG = 'claim'
COAL_TAG = 'coal'
LOGIN_TAGS = [TIMESTAMP_TAG, CONNECTION_TAG, LOGIN_TAG]
LOGOUT_TAGS = [TIMESTAMP_TAG, CONNECTION_TAG, LOGOUT_TAG]
CHAT_TAGS = [TIMESTAMP_TAG, CHAT_TAG]
OVERLOADED_TAGS = [TIMESTAMP_TAG, SERVER_TAG, PERFORMANCE_TAG, OVERLOADED_TAG]
STOPPING_TAGS = [TIMESTAMP_TAG, SERVER_TAG, STOPPING_TAG]
STARTING_TAGS = [TIMESTAMP_TAG, SERVER_TAG, STARTING_TAG]
DEATH_TAGS = [TIMESTAMP_TAG, DEATH_TAG]
ACHIEVEMENT_TAGS = [TIMESTAMP_TAG, ACHIEVEMENT_TAG]
CLAIM_TAGS = [TIMESTAMP_TAG, CLAIM_TAG]
COAL_TAGS = [TIMESTAMP_TAG, COAL_TAG]
TIMESTAMP_TAGS = [TIMESTAMP_TAG, UNKNOWN_TAG]
CHANNEL_TAGS_SET = set(['login', 'logout', 'chat', 'death', 'achievement'])
REGEX_TAGS = [
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+)\[/(?P<ip>[\w.]+):(?P<port>\w+)\] logged in.+\((?P<location_x>-?\w.+), (?P<location_y>-?\w.+), (?P<location_z>-?\w.+)\)"  # noqa
        ],
        LOGIN_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) left the game"
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
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] \<(?P<username>\w+)\> coal:claim:(?P<code>.+)",
        ],
        CLAIM_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] \<(?P<username>\w+)\> (?P<chat>.+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] \[Server\] \<(?P<username>[\w@\.]+)\> (?P<chat>.+)",
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
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was squashed by a falling anvil",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was pricked to death",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) walked into a cactus whilst trying to escape (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was shot by arrow",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) drowned whilst trying to escape (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) drowned",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) blew up",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was blown up by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) hit the ground too hard",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell off a ladder",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell off some vines",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell out of the water",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell from a high place",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell into a patch of fire",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell into a patch of cacti",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was doomed to fall by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was shot off some vines by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was blown from a high place by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) went up in flames",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) burned to death",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was burnt to a crisp whilst fighting (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) walked into a fire whilst fighting (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was slain by (?P<username_mob>\w+) using (?P<weapon>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was slain by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was shot by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was fireballed by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was killed by magic",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was killed by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) got finished off by (?P<username_mob>\w+) using (?P<weapon>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) tried to swim in lava while trying to escape (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) tried to swim in lava",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) died",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) starved to death",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) suffocated in a wall",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was killed while trying to hurt (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was pummeled by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell out of the world",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) fell from a high place and fell out of the world",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) was knocked into the void by (?P<username_mob>\w+)",
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) withered away",
        ],
        DEATH_TAGS
    ),
    (
        [
            ur"(?P<date>[\w-]+) (?P<time>[\w:]+) \[(?P<log_level>\w+)\] (?P<username>\w+) has just earned the achievement \[(?P<achievement>.+)\]",
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
