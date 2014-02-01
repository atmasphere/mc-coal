=================================================
MC COAL - Minecraft Community Online Activity Log
=================================================

`MC COAL <http://mc-coal.org/>`_ is an open-source project aimed at helping to build and maintain community around multi-player `Minecraft <http://minecraft.net>`_ worlds. It can also optionally provide powerful and simple Minecraft multi-player server hosting and management.

`COAL <https://github.com/gumptionthomas/mc-coal>`_ is a web application. It is written in python and runs on the `Google Cloud Platform <https://cloud.google.com/>`_. It is licensed under the `GNU AFFERO GENERAL PUBLIC LICENSE Version 3 <https://github.com/gumptionthomas/mc-coal/blob/master/LICENSE.txt>`_

--------
Features
--------
  * Server status display including in-game time, weather, and currently logged in players
  * Live chat and searchable chat history
  * Chat into the game from the web
  * Player session information
  * Share screen shots
  * Detailed and well-documented API
  * Easily host and manage powerful multi-player servers on Google Compute Engine
  * Works with vanilla Minecraft multi-player servers


=================
COAL Installation
=================

-------------
Prerequisites
-------------

* A free `Google Cloud Platform <https://cloud.google.com/>`_ account.

-------------------------
Deploy and Configure COAL
-------------------------
1. `Create a Google Cloud Project <https://cloud.google.com/console/project>`_ for your new COAL installation. Take note of the Project ID you select (e.g. `[my-project-id]`).
2. Optionally, in ``Settings``, enable billing. COAL should be able to run comfortably under the daily free App Engine quota for most relatively small, lightly-populated worlds.
3. Clone, fork, or download the `MC COAL code repository <https://github.com/gumptionthomas/mc-coal>`_. Make sure any new clone or fork is a private repository as it will contain sensitive information (like the ``COAL_SECRET_KEY``).
4. Change the application name (i.e. ``mc-coal``) in the first line of `app.yaml <app.yaml>`_ to the Project ID you created above.
5. Change the ``COAL_SECRET_KEY`` value in `appengine_config.py <appengine_config.py>`_ to a unique random value. You can use this `random.org link <http://www.random.org/strings/?num=1&len=20&digits=on&upperalpha=on&loweralpha=on&unique=on&format=html&rnd=new>`_ to generate a unique string value.
6. Complete the sub-steps below if you intend to host worlds on Google Compute Engine:
  a. In ``Settings`` enable billing if you haven't already. There is no daily free Google Compute Engine quota.
  b. In ``APIs``, make sure that ``Google Compute Engine``, ``Google Cloud Storage`` and ``Google Cloud Storage JSON API`` are ``ON``.
  c. In ``Permissions`` make note of the Google Compute Engine service account email address. This should be of the form ``[project number]@developer.gserviceaccount.com`` or ``[project number]@project.gserviceaccount.com``. Also, make sure there is an entry for ``[my-project-id]@appspot.gserviceaccount.com``. If it isn't there, add it as a owner member.
  d. Add the Google Compute Engine service account email address to the ``acl`` section of `queue.yaml <queue.yaml>`_. When finished, the file should look something like this

    ::
      
      queue:
      - name: default
        rate: 5/s

      - name: controller
        mode: pull
        acl:
        - user_email: 1234567890@developer.gserviceaccount.com

7. Deploy your modified code in either of two ways:
  * Use the `App Engine python developer tools <https://developers.google.com/appengine/docs/python/tools/uploadinganapp>`_
  * Use the new `Push-to-deploy <https://developers.google.com/appengine/docs/push-to-deploy>`_

    .. note:: Due to a `bug in Google's push-to-deploy feature <https://code.google.com/p/googleappengine/issues/detail?id=10139>`_, if you are planning on hosting your worlds on Google Compute Engine you must also update your application's task queue configuration by using the App Engine developer tool ``appcfg``. See `The Development Environment <https://developers.google.com/appengine/docs/python/gettingstartedpython27/devenvironment>`_ for information on how to download and install the developer tools and `Updating Task Queue Configuration <https://developers.google.com/appengine/docs/python/tools/uploadinganapp#Python_Updating_Task_Queue_configuration>`_ for information on running ``appcfg`` to update the configuration.

8. Browse to your COAL administrator page at ``https://[my-project-id].appspot.com/admin``.

  .. warning:: For bootstrapping purposes, the first user to request this page is made an administrator, so make sure to do this right away.

=============
World Hosting
=============

Next, you'll set up your minecraft world(s). There are two options: let your COAL host your world on Google Compute Engine (easy!) or host your world elsewhere (more work for you!). You can mix both kinds of hosted worlds on a single COAL install.

----------------------------------------
Hosting Worlds On Google Compute Engine
----------------------------------------

1. Create a new server by clicking your COAL ``Admin/Create GCE-Hosted World`` link to set up a new world and then hit the play button to start the server. This can take a few minutes if a GCE instance has to be started up for the first time.
2. When the world status is "Playing" the IP address of the server will be shown. Use this IP address to connect your minecraft client to the new world.
3. Play! No additional infrastructure set up needed.

-------------------------------
Hosting Worlds On Other Servers
-------------------------------

If you already have a Minecraft multi-player world running on a UNIX-based server you can connect it to your COAL.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Hosting Server Prerequisites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following libraries are required to be installed on the server that is hosting your world.

* Python 2.7
* `pytz <http://pytz.sourceforge.net/>`_
* `pyyaml <http://pyyaml.org/>`_
* `requests <http://docs.python-requests.org/>`_
* `NBT <https://github.com/twoolie/NBT>`_

^^^^^^^^^^^^^^^^^^
Agent Installation
^^^^^^^^^^^^^^^^^^

1. Create a new directory called ``mc-coal`` in your minecraft server's directory (the one with ``server.properties``).
2. Download the following files from your COAL into the new ``mc-coal`` directory:

  ::
    
    wget https://[my-project-id].appspot.com/mc/timezones.py -o timezones.py
    wget https://[my-project-id].appspot.com/mc/mc_coal_agent.py -o mc_coal_agent.py

3. Download the following files from your COAL into your minecraft server's directory

  ::
    
    wget https://[my-project-id].appspot.com/mc/log4j2.xml -o log4j2.xml
    wget https://[my-project-id].appspot.com/mc/mc-start.sh -o mc-start.sh
    wget https://[my-project-id].appspot.com/mc/mc-stop.sh -o mc-stop.sh

^^^^^^^^^
Run Agent
^^^^^^^^^

1. Create a new COAL world by clicking the ``Admin/Create External-Server-Hosted World`` and note the ``Agent Client ID`` and ``Agent Secret``.
2. On your Minecraft server host, in the ``mc-coal`` directory, run ``mc_coal_agent.py`` with the ``coal_host``, ``agent_client_id``, and ``agent_secret`` for your server:

  ::
    
    [~/minecraft-server/mc-coal] $ python mc_coal_agent.py --coal_host=[my-project-id].appspot.com --agent_client_id=mc-coal-agent-12345 --agent_secret=ow9mLT8rev1e8og5AWeN1TyBM7EXZYiCntw8dj4d
    2014-01-01 23:00:01 : main     INFO   Monitoring '../server.log' and reporting to '[my-project-id].appspot.com'...

3. Edit the java configuration parameters within the `mc-start.sh <mc-start.sh>`_ script as desired.
4. Start the minecraft server with the ``mc-start.sh`` script:

  ::

    [~/minecraft-server] $ ./mc-start.sh
    2014-01-21 22:15:09,540 DEBUG Generated plugins in 0.000023000 seconds
    ...
    2014-01-21 22:15:09,588 DEBUG Shutting down OutputStreamManager SYSTEM_OUT
    2014-01-21 22:15:09,588 DEBUG Reconfiguration completed

5. To stop the minecraft server later, use the ``mc-stop.sh`` script:

  ::
  
    [~/minecraft_server] $ ./mc-stop.sh
    Stopping MineCraft Server PID=5989
    2014-01-22 22:12:19,540 DEBUG ServletContext not present - WebLookup not added
    2014-01-22 22:12:19,541 DEBUG Shutting down FileManager server.log
    MineCraft shutdown complete.
