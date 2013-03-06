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
2. Set up a [drone.io](http://drone.io) account.
3. Link a new [drone.io](http://drone.io) project to your mc-coal fork. See [drone.io settings](#droneio-settings) below.
4. Create an app engine deployment for the [drone.io](http://drone.io) project. Take note of your application id that you set up on app engine.
5. Change the "`mc-coal`" in the first line of `app.yaml` to be the application id from above. Edit `appengine_config.py` as desired. Commit. Push.
6. Test build/deploy.
7. Clone (or copy) your fork into your minecraft server directory (it contains the `minecraft-server.jar` file).
8. In the `mc-coal` directory, run the agent:

>     [~/minecraft-server/mc-coal] $ python mc_coal_agent.py
>     2013-03-05 16:48:07,772 : main     INFO   Monitoring '../server.log' and reporting to 'my-app-id.appspot.com'...

9. Copy the `mc-start.sh` script into the minecraft server directory. Edit java configs as desired.
10. Start your minecraft server with the `mc-start.sh` script:

>     [~/minecraft-server] $ ./mc-start.sh
>     2013-03-05 16:49:18 [INFO] Starting minecraft server version 1.4.7

11. Go to your new COAL installation at `http://[my-app-id].appspot.com` where `[my-app-id]` is your app engine application id from above.

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
