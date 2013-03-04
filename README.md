MC COAL
=======

MineCraft Community Online Activity Log

[![Build Status](https://drone.io/github.com/gumptionthomas/mc-coal/status.png)](https://drone.io/github.com/gumptionthomas/mc-coal/latest)

drone.io settings
-----------------
Environment Variables

    PATH=$PATH:/tmp/google_appengine/

Commands

    GAE=1.7.5
    wget -q -O /tmp/gae.zip http://googleappengine.googlecode.com/files/google_appengine_${GAE}.zip
    unzip -q /tmp/gae.zip -d /tmp
    python -m unittest discover
