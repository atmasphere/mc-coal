MC COAL
=======

MineCraft Community On-line Activity Log

Prerequisites
-------------
* A Minecraft Server
* Python 2.7
* [psutil](https://code.google.com/p/psutil/) (Optional: Needed by the agent to report server status)

COAL Server
-----------
1. [Create an App Engine application](https://appengine.google.com/) for your new COAL installation. Take note of the application id you select. Set up repository deploys.
2. Fork this repository.
3. Change `mc-coal` in the first line of `app.yaml` to the application id you registered above. Commit. Deploy.

COAL Agent
----------
1. Clone the new forked repository into the minecraft server directory (the directory containing the `minecraft-server.jar` and `server.log` files).
2. In the `mc-coal` directory, run the agent:

  >     [~/minecraft-server/mc-coal] $ python mc_coal_agent.py
  >     2013-03-05 16:48:07,772 : main     INFO   Monitoring '../server.log' and reporting to 'my-app-id.appspot.com'...

3. Copy the `mc-start.sh` script into the minecraft server directory. Edit java configuration parameters as desired.
4. Start the minecraft server with the `mc-start.sh` script:

  >     [~/minecraft-server] $ ./mc-start.sh
  >     2013-03-05 16:49:18 [INFO] Starting minecraft server version 1.4.7

Test
----
Go to the new COAL installation at `http://[my-app-id].appspot.com` where `[my-app-id]` is your application id.
