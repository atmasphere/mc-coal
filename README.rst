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
1. `Create a Google Cloud Project <https://cloud.google.com/console/project>`_ for your new COAL installation. Take note of the Project ID you select.
2. In ``APIs``, make sure that ``Google Cloud Storage`` and ``Google Cloud Storage JSON API`` are ``ON``. If you intend to host your worlds on Google Compute Engine enable ``Google Compute Engine``. Note that this will force you to enable billing.
3. Optionally, in ``Settings``, enable billing if you didn't already as part of step 2. If you host your own small world elsewhere, you may be able to run COAL under the free quota and setting up billing won't be required.
4. In ``Cloud Development/Push-to-deploy`` make note of the ``Repository URL``.
5. In ``Permissions`` make note of the Google Compute Engine service account email address. This should be of the form ``[project number]@developer.gserviceaccount.com`` or ``[project number]@project.gserviceaccount.com``. Also, make sure there is an entry for ``[my-project-id]@appspot.gserviceaccount.com``. If it isn't there, add it as a owner member.
6. Fork this repository. Make sure the new fork is a private repository as it will contain sensitive information (like the ``COAL_SECRET_KEY``).
7. Change the application name (i.e. ``mc-coal``) in the first line of `app.yaml <app.yaml>`_ to the Project ID you created above. Commit your change.
8. Change the ``COAL_SECRET_KEY`` value in `appengine_config.py <appengine_config.py>`_ to a unique random value. You can use this `random.org link <http://www.random.org/strings/?num=1&len=20&digits=on&upperalpha=on&loweralpha=on&unique=on&format=html&rnd=new>`_ to generate a unique string value. Commit your change.
9. Add the Google Compute Engine service account email address from step 5 to the ``acl`` section of `queue.yaml <queue.yaml>`_. When finished, the file should look something like this

  ::
    
    queue:
    - name: default
      rate: 5/s

    - name: controller
      mode: pull
      acl:
      - user_email: 1234567890@developer.gserviceaccount.com

  Commit your change.

10. Push your forked repository to the ``Push-to-deploy`` repository noted in step 4.

  .. note:: Due to a `bug in Google's push-to-deploy feature <https://code.google.com/p/googleappengine/issues/detail?id=10139>`_, if you are planning on hosting your worlds on Google Compute Engine you must also update your application's task queue configuration by using the App Engine developer tool ``appcfg``. See `The Development Environment <https://developers.google.com/appengine/docs/python/gettingstartedpython27/devenvironment>`_ for information on how to download and install the developer tools and `Updating Task Queue Configuration <https://developers.google.com/appengine/docs/python/tools/uploadinganapp#Python_Updating_Task_Queue_configuration>`_ for information on running ``appcfg`` to update the configuration.

11. Browse to ``https://[my-project-id].appspot.com/admin`` where `[my-project-id]` is your Project ID from step 1.

  .. warning:: For bootstrapping purposes, the first user to request this page is made an administrator, so make sure to do this right away.

=============
World Hosting
=============

Next, you'll set up your minecraft world(s). There are two options: let COAL host your world on Google Compute Engine (easy!) or host your world elsewhere (more work for you!). You can mix both kinds of hosted worlds on a single COAL instance.

----------------------------------------
Hosting Worlds On Google Compute Engine
----------------------------------------

1. Create a new world by clicking the ``Admin/Create New GCE-Hosted Server`` link to set up a new world and then hit the play button to start the server. This can take a few minutes if a GCE instance has to be started up for the first time.
2. When the world status is "Playing" the IP address of the server will be shown. Use this IP address to connect your minecraft client to the new world.
3. Play! No additional infrastructure set up needed.

---------------------------------------------------
Hosting Worlds Elesewhere (UNIX-based servers only)
---------------------------------------------------

^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Hosting Server Prerequisites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following libraries are required to be installed on the server that is hosting your world.

* Python 2.7
* `pytz <http://pytz.sourceforge.net/>`_
* `pyyaml <http://pyyaml.org/>`_
* `requests <http://docs.python-requests.org/>`_
* `NBT <https://github.com/twoolie/NBT>`_
* `psutil <https://code.google.com/p/psutil/>`_ (Optional: Needed by the agent to report server status)

^^^^^^^^^^^^^^^^^^
Agent Installation
^^^^^^^^^^^^^^^^^^

1. Create a new directory called ``mc-coal`` in your minecraft server's directory (the one with ``server.properties``).
2. Download the following files from your COAL installation into the new ``mc-coal`` directory (assuming your project ID is ``my-project-id``)

  ::
    
    wget https://my-project-id.appspot.com/mc/timezones.py -o timezones.py
    wget https://my-project-id.appspot.com/mc/mc_coal_agent.py -o mc_coal_agent.py

#. Download the following files from your COAL installation into your minecraft server's directory

  ::
    
    wget https://my-project-id.appspot.com/mc/log4j2.xml -o log4j2.xml
    wget https://my-project-id.appspot.com/mc/mc-start.sh -o mc-start.sh
    wget https://my-project-id.appspot.com/mc/mc-stop.sh -o mc-stop.sh

^^^^^^^^^
Run Agent
^^^^^^^^^

1. Create a new world by clicking the ``Admin/Create New Server`` link to set up a new world and note the ``Agent Client ID`` and ``Agent Secret`` for that server.
2. In the ``mc-coal`` directory, run the agent with the ``agent_client_id`` and ``agent_secret`` for your server:

  ::
    
    [~/minecraft-server/mc-coal] $ python mc_coal_agent.py --agent_client_id=mc-coal-agent-12345 --agent_secret=ow9mLT8rev1e8og5AWeN1TyBM7EXZYiCntw8dj4d
    2014-01-01 23:00:01 : main     INFO   Monitoring '../server.log' and reporting to '[my-project-id].appspot.com'...

3. Edit the java configuration parameters within the `mc-start.sh <mc-start.sh>`_ script as desired.
4. Start the minecraft server with the ``mc-start.sh`` script:

  ::

    [~/minecraft-server] $ ./mc-start.sh
    2014-01-21 22:15:09,540 DEBUG Generated plugins in 0.000023000 seconds
    2014-01-21 22:15:09,575 DEBUG Calling createLayout on class org.apache.logging.log4j.core.layout.PatternLayout for element PatternLayout with params(pattern="%d{yyyy-MM-dd HH:mm:ss} [%level] %msg%n", Configuration(/Users/_minecraft/minecraft_server/log4j2.xml), null, charset="null", alwaysWriteExceptions="null")
    2014-01-21 22:15:09,576 DEBUG Generated plugins in 0.000029000 seconds
    2014-01-21 22:15:09,580 DEBUG Calling createAppender on class org.apache.logging.log4j.core.appender.FileAppender for element File with params(fileName="server.log", append="null", locking="null", name="legacy_server_log", immediateFlush="null", ignoreExceptions="null", bufferedIO="null", PatternLayout(%d{yyyy-MM-dd HH:mm:ss} [%level] %msg%n), null, advertise="null", advertiseURI="null", Configuration(/Users/_minecraft/minecraft_server/log4j2.xml))
    2014-01-21 22:15:09,582 DEBUG Starting FileManager server.log
    2014-01-21 22:15:09,582 DEBUG Calling createAppenders on class org.apache.logging.log4j.core.config.plugins.AppendersPlugin for element Appenders with params(Appenders={legacy_server_log})
    2014-01-21 22:15:09,583 DEBUG Generated plugins in 0.000012000 seconds
    2014-01-21 22:15:09,584 DEBUG Calling createAppenderRef on class org.apache.logging.log4j.core.config.AppenderRef for element AppenderRef with params(ref="legacy_server_log", level="null", null)
    2014-01-21 22:15:09,586 DEBUG Calling createLogger on class org.apache.logging.log4j.core.config.LoggerConfig$RootLogger for element Root with params(additivity="null", level="info", includeLocation="null", AppenderRef={legacy_server_log}, Properties={}, Configuration(log4j2.xml), null)
    2014-01-21 22:15:09,588 DEBUG Calling createLoggers on class org.apache.logging.log4j.core.config.plugins.LoggersPlugin for element Loggers with params(Loggers={root})
    2014-01-21 22:15:09,588 DEBUG Shutting down OutputStreamManager SYSTEM_OUT
    2014-01-21 22:15:09,588 DEBUG Reconfiguration completed

5. To stop the minecraft server later, use the ``mc-stop.sh`` script:

  ::
  
    [~/minecraft_server] $ ./mc-stop.sh
    Stopping MineCraft Server PID=5989
    2014-01-22 22:12:19,540 DEBUG ServletContext not present - WebLookup not added
    2014-01-22 22:12:19,541 DEBUG Shutting down FileManager server.log
    MineCraft shutdown complete.
