MC COAL
=======

MineCraft Community On-line Activity Log

Prerequisites
-------------
* A Minecraft Server
* Python 2.7
* [psutil](https://code.google.com/p/psutil/) (Optional: Needed by the agent to report server status)

Installation
------------
1. Fork this repository.
2. Set up an http://drone.io account.
3. Link a new drone.io project to your mc-coal fork.
4. Create an app engine deployment for the drone.io project. Take note of your application id that you set up on app engine.
5. Change `mc-coal` the first line in `app.yaml` to be the application id from above. Edit appengine_config.py as desired. Commit. Push.
6. Test build/deploy.
7. Clone (or copy) your fork into your minecraft server directory (it contains the `minecraft-server.jar` file).
8. Copy `mc-start.sh` script into the minecraft server directory. Edit java configs as desired.
9. In the `mc-coal` directory, run the agent:
    $ [~/minecraft-server/mc-coal] $ python mc_coal_agent.py
    2013-03-05 16:48:07,772 : main     INFO   Monitoring '../server.log' and reporting to 'my-app-id.appspot.com'...

Continuous Integration Build Status
-----------------------------------
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
