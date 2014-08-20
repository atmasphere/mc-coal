=======
Servers
=======

.. http:get:: /api/v1/servers

  Get a :ref:`list <list>` of all servers ordered by created timestamp.

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.

  :status 200 OK: Successfully queried the servers.
  
    :Response Data:
  
      - **servers** -- The list of servers.
      - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **servers** is an object of server status information.

    .. _server_status_response_data:

    :Server Status:
  
      - **key** -- The server key.
      - **name** -- The server name.
      - **gce** -- A boolean indicating whether the server is hosted by MC-COAL on a Google Compute Engine server.
      - **running_version** -- The actual version of minecraft that was last running.
      - **address** -- The IP address (including the port, if necessary) of the server. If ``gce`` is ``false`` and the address isn't passed to the agent at startup, this field will be ``null``.
      - **status** -- A string indicating the status of the minecraft server. Possible values are ``RUNNING``, ``STOPPED``, ``QUEUED_START``, ``QUEUED_STOP``, or ``UNKNOWN``.
      - **last_ping** -- The timestamp of the last agent ping.
      - **server_day** -- An integer indicating the number of game days since the start of the level.
      - **server_time** -- An integer indicating the game time of day. 0 is sunrise, 6000 is mid day, 12000 is sunset, 18000 is mid night, 24000 is the next day's 0.
      - **is_raining** -- A boolean indicating whether it is raining. If this value is ``null`` the status is unknown.
      - **is_thundering** -- A boolean indicating whether it is thundering. If this value is ``null`` the status is unknown.
      - **created** -- The server's creation timestamp.
      - **updated** -- The server's updated timestamp.

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "servers": [
        {
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "name": "My World",
          "gce": false,
          "running_version": "1.5.1",
          "address": null,
          "last_ping": "2013-04-14 19:55:22 CDT-0500",
          "updated": "2013-04-14 19:55:22 CDT-0500",
          "status": "RUNNING",
          "created": "2013-03-04 15:05:53 CST-0600"
          "server_day": 15744,
          "server_time": 19767,
          "is_raining": true,
          "is_thundering": true
        },
        {
          "key": "IZCxIGQ2xpZW50Ig1tYy1jb2FsLWFnZW50DA",
          "name": "My PVP World",
          "gce": true,
          "running_version": "1.5.1",
          "address": "1.2.3.4:56789",
          "last_ping": "2013-04-14 19:55:43 CDT-0500",
          "updated": "2013-04-14 19:55:43 CDT-0500",
          "status": "STOPPED",
          "created": "2013-03-04 15:07:00 CST-0600",
          "server_day": 15223,
          "server_time": 14141,
          "is_raining": false,
          "is_thundering": false
        }
      ]
    }


.. http:post:: /api/v1/servers

  Create a new server. Only an authenticated administrator can call this service.

  :formparam name: The server name. (*required*)
  :formparam gce: A boolean indicating whether the server should be hosted by MC-COAL on Google Compute Engine. (*required*)

  :status 201 Created: Successfully created the server.
  
    :Response Data: See :ref:`Server status response <server_status_response_data>`

  :status 403 Forbidden: The authenticated user is not an administrator.

  **Example request**:

  .. sourcecode:: http

    POST /api/v1/servers HTTP/1.1

  .. sourcecode:: http

    name=Brave+New+World&gce=true&version=1.7.4&memory=256M

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 201 Created
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "key": "bbhd871bXB0aW9uLW1pbmVj26GhY",
      "name": "Brave New World",
      "gce": true,
      "running_version": null,
      "address": null,
      "last_ping": null,
      "updated": "2014-01-14 17:33:00 CST-0600",
      "status": "UNKNOWN",
      "created": "2014-01-13 12:00:00 CST-0600",
      "server_day": null,
      "server_time": null,
      "is_raining": null,
      "is_thundering": null
    }


.. http:get:: /api/v1/servers/(key)

  Get status information for the server (`key`).

  :arg key: The requested server's key. (*required*)

  :status 200 OK: Successfully read the server.
  
    :Response Data: See :ref:`Server status response <server_status_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/bbhd871bXB0aW9uLW1pbmVj26GhY HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "key": "bbhd871bXB0aW9uLW1pbmVj26GhY",
      "name": "Brave New World",
      "gce": true,
      "running_version": null,
      "address": null,
      "last_ping": null,
      "updated": "2014-01-14 17:33:00 CST-0600",
      "status": "UNKNOWN",
      "created": "2014-01-13 12:00:00 CST-0600",
      "server_day": null,
      "server_time": null,
      "is_raining": null,
      "is_thundering": null
    }


.. http:post:: /api/v1/servers/(key)

  Update the settings for the server (`key`). Only an authenticated administrator can call this service.

  :arg key: The requested server's key. (*required*)

  :formparam name: The server name. (*required*)

  :status 200 OK: Successfully updated the settings.

    :Response Data: See :ref:`Server status response <server_status_response_data>`

  **Example request**:

  .. sourcecode:: http

    POST /api/v1/servers/bbhd871bXB0aW9uLW1pbmVj26GhY HTTP/1.1

  .. sourcecode:: http

    name=Not+So+Brave+New+World

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 202 Accepted
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "key": "bbhd871bXB0aW9uLW1pbmVj26GhY",
      "name": "Not So Brave New World",
      "gce": true,
      "running_version": null,
      "address": null,
      "last_ping": null,
      "updated": "2014-01-16 15:00:00 CST-0600",
      "status": "UNKNOWN",
      "created": "2014-01-13 12:00:00 CST-0600",
      "server_day": null,
      "server_time": null,
      "is_raining": null,
      "is_thundering": null
    }


.. http:get:: /api/v1/servers/(key)/properties

  Get the minecraft server properties for the GCE-hosted server (`key`). If the requested server is not a GCE sever (i.e. ``gce`` is ``false``), a :http:statuscode:`404` will be returned.

  :arg key: The requested server's key. (*required*)

  :status 200 OK: Successfully read the server properties. The response will be an object with the current minecraft properties for the server.

    .. _server_properties_response_data:

    :Server Properties:
  
      - **key** -- The server key.
      - **server_port** -- The minecraft server port to use (``null`` indicates first available).
      - **version** -- The minecraft server version.
      - **memory** -- The amount of memory dedicated to the server. Possible values are ``256M``, ``512M``, ``1G``, ``2G``, ``3G``, or ``4G``.
      - **operator** -- The minecraft username of the initial operator of the server.
      - **idle_timeout** -- Number of idle minutes before the server is automatically paused (zero means never)
      - **motd** -- The message of the day.
      - **white_list** -- A boolean indicating whether the server whitelist is enabled.
      - **gamemode** -- An integer indicating the game mode. Possible values are ``0`` (Survival), ``1`` (Creative), and ``2`` (Adventure).
      - **force_gamemode** -- A boolean indicating whether players are forced to join in the default game mode.
      - **level_type** -- The type of map for the server. Possible values are ``DEFAULT``, ``FLAT``, ``LARGEBIOMES``, and ``AMPLIFIED``.
      - **level_seed** -- The seed for the server world.
      - **generator_settings** -- The settings used to customize Superflat world generation.
      - **difficulty** -- An integer indicating the server difficulty. Possible values are ``0`` (Peaceful), ``1`` (Easy), ``2`` (Normal), and ``3`` (Hard).
      - **pvp** -- A boolean indicating whether the server is PvP.
      - **hardcore** -- A boolean indicating whether the server is in hardcore mode.
      - **allow_flight** -- A boolean indicating whether users can use flight while in Survival mode.
      - **allow_nether** -- A boolean indicating whether players can travel to the Nether.
      - **max_build_height** -- The maximum height in which building is allowed (Min: 0, Max: 1024).
      - **generate_structures** -- A boolean indicating whether to generate structures.
      - **spawn_npcs** -- A boolean indicating whether to spawn villagers.
      - **spawn_animals** -- A boolean indicating whether to spawn animals.
      - **spawn_monsters** -- A boolean indicating whether to spawn monsters.
      - **view_distance** -- An integer indicating the number of chunks of world data the server sends the client (Min: 3, Max: 15).
      - **player_idle_timeout** -- An integer indicating the number of minutes before an idle player is kicked (zero means never) (Min: 0, Max: 60).
      - **max_players** -- An integer indicating the maximum number of players that can play on the server at the same time.
      - **spawn_protection** -- An integer radius of the spawn protection area (Min: 0, Max: 24).
      - **enable_command_block** -- A boolean indicating whether to enable command blocks.
      - **snooper_enabled** -- A boolean indicating whether to send snoop data regularly to snoop.minecraft.net.
      - **resource_pack** -- The URL (if any) to prompt clients to download a resource pack from.
      - **op_permission_level** -- An integer indicating the operator permission level. Possible values are ``0`` (Can bypass spawn protection), ``1`` (Can use ``/clear``, ``/difficulty``, ``/effect``, ``/gamemode``, ``/gamerule``, ``/give``, and ``/tp``, and can edit command blocks), and ``2`` (Can use ``/ban``, ``/deop``, ``/kick``, and ``/op``).

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/bbhd871bXB0aW9uLW1pbmVj26GhY/properties HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "key": "bbhd871bXB0aW9uLW1pbmVj26GhY",
      server_port: null,
      "version": "1.7.4",
      "memory": "256M",
      "operator": "gumptionthomas",
      "idle_timeout": 5,
      "motd": "It's a brave new world out there",
      "white_list": true,
      "gamemode": 0,
      "force_gamemode": false,
      "level_type": "DEFAULT",
      "level_seed": "",
      "generator_settings": "",
      "difficulty": "1",
      "pvp": false,
      "hardcore": false,
      "allow_flight": false,
      "allow_nether": true,
      "max_build_height": 256,
      "generate_structures": true,
      "spawn_npcs": true,
      "spawn_animals": true,
      "spawn_monsters": true,
      "view_distance": 10,
      "player_idle_timeout": 0,
      "max_players": 20,
      "spawn_protection": 16,
      "enable_command_block": false,
      "snooper_enabled": true,
      "resource_pack": "",
      "op_permission_level": 3
    }


.. http:post:: /api/v1/servers/(key)/properties

  Update the minecraft server properties for the GCE-hosted server (`key`). If the requested server is not a GCE sever (i.e. ``gce`` is ``false``), a :http:statuscode:`404` will be returned. Only an authenticated administrator can call this service.

  :arg key: The requested server's key. (*required*)

  :formparam server_port: The minecraft server port to use (``''`` [empty string] indicates first available).
  :formparam version: The minecraft version to use for the server.
  :formparam memory: The amount of memory to dedicate to the server. Possible values are ``256M``, ``512M``, ``1G``, ``2G``, ``3G``, or ``4G``.
  :formparam operator: The minecraft username of the initial operator for the server.
  :formparam idle_timeout: The number of idle minutes before the server is automatically paused (zero means never)
  :formparam motd: The message of the day.
  :formparam white_list: A boolean indicating whether the server whitelist should be enabled.
  :formparam gamemode: An integer indicating the game mode. Possible values are ``0`` (Survival), ``1`` (Creative), and ``2`` (Adventure).
  :formparam force_gamemode: A boolean indicating whether players should be forced to join in the default game mode.
  :formparam level_type: The type of map for the server. Possible values are ``DEFAULT``, ``FLAT``, ``LARGEBIOMES``, and ``AMPLIFIED``.
  :formparam level_seed: The seed for the server world.
  :formparam generator_settings: The settings used to customize Superflat world generation.
  :formparam difficulty: An integer indicating the server difficulty. Possible values are ``0`` (Peaceful), ``1`` (Easy), ``2`` (Normal), and ``3`` (Hard).
  :formparam pvp: A boolean indicating whether the server should be PvP.
  :formparam hardcore: A boolean indicating whether the server should be in hardcore mode.
  :formparam allow_flight: A boolean indicating whether users can use flight while in Survival mode.
  :formparam allow_nether: A boolean indicating whether players can travel to the Nether.
  :formparam max_build_height: The maximum height in which building is allowed (Min: 0, Max: 1024).
  :formparam generate_structures: A boolean indicating whether to generate structures.
  :formparam spawn_npcs: A boolean indicating whether to spawn villagers.
  :formparam spawn_animals: A boolean indicating whether to spawn animals.
  :formparam spawn_monsters: A boolean indicating whether to spawn monsters.
  :formparam view_distance: An integer indicating the number of chunks of world data the server sends the client (Min: 3, Max: 15).
  :formparam player_idle_timeout: An integer indicating the number of minutes before an idle player is kicked (zero means never) (Min: 0, Max: 60).
  :formparam max_players: An integer indicating the maximum number of players that can play on the server at the same time.
  :formparam spawn_protection: An integer radius of the spawn protection area (Min: 0, Max: 24).
  :formparam enable_command_block: A boolean indicating whether to enable command blocks.
  :formparam snooper_enabled: A boolean indicating whether to send snoop data regularly to snoop.minecraft.net.
  :formparam resource_pack: The URL (if any) to prompt clients to download a resource pack from.
  :formparam op_permission_level: An integer indicating the operator permission level. Possible values are ``0`` (Can bypass spawn protection), ``1`` (Can use ``/clear``, ``/difficulty``, ``/effect``, ``/gamemode``, ``/gamerule``, ``/give``, and ``/tp``, and can edit command blocks), and ``2`` (Can use ``/ban``, ``/deop``, ``/kick``, and ``/op``).

  :status 200 OK: Successfully updated the server properties. The response will be an object with the new minecraft properties for the server.
  
    :Response Data: See :ref:`Server properties response <server_properties_response_data>`

  **Example request**:

  .. sourcecode:: http

    POST /api/v1/servers/bbhd871bXB0aW9uLW1pbmVj26GhY/properties HTTP/1.1

  .. sourcecode:: http

    memory=1G&gamemode=1&level_type=FLAT&spawn_monsters=false&motd=Maybe+not+that+brave

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "key": "bbhd871bXB0aW9uLW1pbmVj26GhY",
      server_port: null,
      "version": "1.7.4",
      "memory": "1G",
      "operator": "gumptionthomas",
      "idle_timeout": 5,
      "motd": "Maybe not that brave",
      "white_list": true,
      "gamemode": 1,
      "force_gamemode": false,
      "level_type": "FLAT",
      "level_seed": "",
      "generator_settings": "",
      "difficulty": "1",
      "pvp": false,
      "hardcore": false,
      "allow_flight": false,
      "allow_nether": true,
      "max_build_height": 256,
      "generate_structures": true,
      "spawn_npcs": true,
      "spawn_animals": true,
      "spawn_monsters": false,
      "view_distance": 10,
      "player_idle_timeout": 0,
      "max_players": 20,
      "spawn_protection": 16,
      "enable_command_block": false,
      "snooper_enabled": true,
      "resource_pack": "",
      "op_permission_level": 3
    }


.. http:post:: /api/v1/servers/(key)/queue/play

  Place the GCE-hosted server (`key`) in the play queue. If the requested server is not a GCE sever (i.e. ``gce`` is ``false``), a :http:statuscode:`404` will be returned. Any authenticated user can call this service.

  :arg key: The requested server's key. (*required*)

  :status 200 OK: The server was already playing or queued to play. No action taken.
  :status 202 Accepted: Successfully queued the server to play.

  **Example request**:

  .. sourcecode:: http

    POST /api/v1/servers/bbhd871bXB0aW9uLW1pbmVj26GhY/queue/play HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 202 Accepted

  .. note:: To determine when the server is ready to play (i.e. for minecraft clients to connect), call :http:get:`/api/v1/servers/(key)`.  The response property ``status`` will be ``RUNNING`` and ``address`` will contain the server's IP address.


.. http:post:: /api/v1/servers/(key)/queue/pause

  Place the GCE-hosted server (`key`) in the pause queue. If the requested server is not a GCE sever (i.e. ``gce`` is ``false``), a :http:statuscode:`404` will be returned. Only an authenticated administrator can call this service.

  :arg key: The requested server's key. (*required*)

  :status 200 OK: The server was already paused or queued to pause. No action taken.
  :status 202 Accepted: Successfully queued the server to pause.

  **Example request**:

  .. sourcecode:: http

    POST /api/v1/servers/bbhd871bXB0aW9uLW1pbmVj26GhY/queue/pause HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 202 Accepted

  .. note:: To determine when the server is paused (i.e. when minecraft clients can no longer connect), call :http:get:`/api/v1/servers/(key)`.  The response property ``status`` will be ``STOPPED`` or ``UNKNOWN``.

