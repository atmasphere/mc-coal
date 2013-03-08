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
1. Temporarily install the Google App Engine SDK (if you don't already have it installed):

  >     [~] $ wget -q -O /tmp/gae.zip http://googleappengine.googlecode.com/files/google_appengine_1.7.5.zip
  >     [~] $ unzip /tmp/gae.zip /tmp
  >     [~] $ PATH=$PATH:/tmp/google_appengine/

2. [Create an App Engine application](https://appengine.google.com/) for your new COAL installation. Take note of the application id you select.
3. Fork this repository.
4. Clone the new forked repository into the minecraft server directory (the directory containing the `minecraft-server.jar` and `server.log` files).
5. Change `mc-coal` in the first line of `app.yaml` to the application id you registered above.
6. Edit `appengine_config.py` installation-specific settings (white-listed users, app title, etc.) as desired.
7. Deploy the application to app engine using oauth2. This is the first and only time you'll need to deploy the application yourself.

  >     [~/minecraft-server/mc-coal] $ appcfg.py --oauth2 update .

8. Find the `refresh_token` in `~/.appcfg_ouath2_tokens`. You'll need it to allow [drone.io](http://drone.io) to deploy the application for you.
9. Set up a [drone.io](http://drone.io) account.
10. Link a new [drone.io](http://drone.io) project to the mc-coal fork. See [drone.io settings](#droneio-settings) below.
11. Link a new [drone.io](http://drone.io) project deployment to your app engine application. You'll need your refresh token.
12. Test build/deploy.
13. In the `mc-coal` directory, run the agent:

  >     [~/minecraft-server/mc-coal] $ python mc_coal_agent.py
  >     2013-03-05 16:48:07,772 : main     INFO   Monitoring '../server.log' and reporting to 'my-app-id.appspot.com'...

14. Copy the `mc-start.sh` script into the minecraft server directory. Edit java configuration parameters as desired.
15. Start the minecraft server with the `mc-start.sh` script:

  >     [~/minecraft-server] $ ./mc-start.sh
  >     2013-03-05 16:49:18 [INFO] Starting minecraft server version 1.4.7

16. Go to the new COAL installation at `http://[my-app-id].appspot.com` where `[my-app-id]` is the application id.

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
