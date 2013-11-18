=======
MC COAL
=======

MineCraft Community On-line Activity Log

************
Installation
************

-------------
Prerequisites
-------------

* A Minecraft Server
* Python 2.7
* `psutil <https://code.google.com/p/psutil/>`_ (Optional: Needed by the agent to report server status)

-----------
COAL Server
-----------
1. `Create an App Engine application <https://appengine.google.com/>`_ for your new COAL installation. Take note of the application id you select. Set up `repository push-to-deploy <https://developers.google.com/appengine/docs/push-to-deploy>`_.
2. Fork this repository.
3. Change the application name (i.e. ``mc-coal``) in the first line of `app.yaml <app.yaml>`_ to the application id you registered above.
4. Change the ``COAL_SECRET_KEY`` value in `appengine_config.py <appengine_config.py>`_ to a unique random value. You can use this `random.org link <http://www.random.org/strings/?num=1&len=20&digits=on&upperalpha=on&loweralpha=on&unique=on&format=html&rnd=new>`_ to generate a unique string value.
5. Commit. Push. Push-Deploy. `[Git instructions to go here]`
6. Browse to ``https://[my-app-id].appspot.com/admin`` where `[my-app-id]` is your application id from step 1. For bootstrapping purposes, the first user to request this page is made an administrator, so make sure to do this right away.
7. Create a server. Note the `Agent Client ID` and `Agent Secret` for that server.

----------
COAL Agent
----------
1. Clone the newly forked repository into the minecraft server directory (the directory containing the ``minecraft-server.jar`` and ``server.log`` files). `[Git instructions to go here]`
2. In the ``mc-coal`` directory, run the agent with the ``agent_client_id`` and ``agent_secret`` for your server:

::

  [~/minecraft-server/mc-coal] $ python mc_coal_agent.py --agent_client_id=mc-coal-agent-12345 --agent_secret=ow9mLT8rev1e8og5AWeN1TyBM7EXZYiCntw8dj4d
  2013-10-01 23:55:42,970 : main     INFO   Monitoring '../server.log' and reporting to '[my-app-id].appspot.com'...

3. Copy the `mc-start.sh <mc-start.sh>`_ script into the minecraft server directory. Edit the java configuration parameters within as desired.
4. For Minecraft 1.7.2 and later -- Copy the `log4j2.xml <log4j2.xml>`_ configuration file into the minecraft server directory.
5. Start the minecraft server with the start script:

::

  [~/minecraft-server] $ ./mc-start.sh
  2013-11-11 14:52:22 [INFO] Starting minecraft server version 1.7.2
  2013-11-11 14:52:22 [INFO] Loading properties
  2013-11-11 14:52:22 [INFO] Default game type: SURVIVAL
  2013-11-11 14:52:22 [INFO] Generating keypair
  2013-11-11 14:52:23 [INFO] Starting Minecraft server on *:25565
  2013-11-11 14:52:23 [INFO] Preparing level "world"
  2013-11-11 14:52:23 [INFO] Preparing start region for level 0
  2013-11-11 14:52:24 [INFO] Done (0.942s)! For help, type "help" or "?"
