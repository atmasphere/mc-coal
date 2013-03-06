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
1. Create an app engine application for the COAL installation. Take note of the application id you select.
2. Fork this repository.
3. Clone (or copy) the fork into the minecraft server directory (the directory containing the `minecraft-server.jar` and `server.log` files).
4. Change `mc-coal` in the first line of `app.yaml` to the application id from above.
5. Edit `appengine_config.py` installation-specific settings (whitelisted users, app title, etc.) as desired.
6. Deploy the application to app engine using oauth2. This is the first and only time you'll need to deploy the application theself.

  >    [~/minecraft-server/mc-coal] $ appcfg.py --oauth2 update .

7. Find the `refresh_token` in `~/.appcfg_ouath2_tokens`. You'll need it to allow [drone.io](http://drone.io) to deploy the application for you.
8. Set up a [drone.io](http://drone.io) account.
9. Link a new [drone.io](http://drone.io) project to the mc-coal fork. See [drone.io settings](#droneio-settings) below.
10. Link a new [drone.io](http://drone.io) project deployment to your app engine application. You'll need your refresh token.
11. Test build/deploy.
12. In the `mc-coal` directory, run the agent:

  >     [~/minecraft-server/mc-coal] $ python mc_coal_agent.py
  >     2013-03-05 16:48:07,772 : main     INFO   Monitoring '../server.log' and reporting to 'my-app-id.appspot.com'...

13. Copy the `mc-start.sh` script into the minecraft server directory. Edit java configs as desired.
14. Start the minecraft server with the `mc-start.sh` script:

  >     [~/minecraft-server] $ ./mc-start.sh
  >     2013-03-05 16:49:18 [INFO] Starting minecraft server version 1.4.7

15. Go to the new COAL installation at `http://[my-app-id].appspot.com` where `[my-app-id]` is the application id.

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
