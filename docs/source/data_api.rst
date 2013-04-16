========
Data API
========

--------------
Authentication
--------------
Calls to services can be authenticated via login session cookie (via a browser) or the ``COAL_API_PASSWORD`` as defined in ``mc_coal_config.py`` passed via the ``p`` query parameter.

-------------------------
Common Request Parameters
-------------------------
.. http:get:: /api/data/(service)

.. http:post:: /api/data/(service)

  :query p: The ``COAL_API_PASSWORD`` as defined in ``mc_coal_config.py``. An incorrect password will result in a :http:statuscode:`403`.

  :status 403: No or invalid authentication provided.

  **Examples**:

  .. sourcecode:: http

    GET /api/data/(service)?p=a_password HTTP/1.1

  .. sourcecode:: http

    POST /api/data/(service)?p=a_password HTTP/1.1

----------------
Common Responses
----------------

^^^^^^^^^^
Timestamps
^^^^^^^^^^

  Unless otherwise specified, all timestamps are of the form ``%Y-%m-%d %H:%M:%S %Z%z`` (see `Python strftime formatting <http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior>`_) and converted to the ``COAL_TIMEZONE`` as defined in ``mc_coal_config.py`` or UTC if not defined.

^^^^^^^^^^^^^^
Response Codes
^^^^^^^^^^^^^^

- :http:statuscode:`200`

  The body will be a JSON dictionary whose contents are service specific:

  .. sourcecode:: javascript

    {
      "key1": value1,
      "key2": value2,
      ...
    }

- :http:statuscode:`201`

  The body will be a JSON dictionary whose contents are service specific:

  .. sourcecode:: javascript

    {
      "key1": value1,
      "key2": value2,
      ...
    }

- :http:statuscode:`400`

  The body will be a JSON dictionary of the form:

  .. sourcecode:: javascript

    {
      "errors": "This was a bad request because..."
    }

  The ``errors`` string is service and error specific.

- :http:statuscode:`403` -- The body will be empty.
- :http:statuscode:`404` -- The body will be empty.
- :http:statuscode:`405` -- The body will be empty.

- :http:statuscode:`500`

  The body will be a JSON dictionary of the form:

  .. sourcecode:: javascript

    {
      "errors": "This request failed because..."
    }

  The ``errors`` string is service and error specific.

.. _list:

-------------
List Services
-------------
Some services return a list of results that can span requests. These services all take a common set of query parameters and return a common set of response data to help iterate through large lists of data.

.. http:get:: /api/data/(list_service)

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.

  :status 200: Successfully called the *list_service*.

    :Response Data:
      - **cursor** -- If more results are available, this root level response value will be the next cursor string to be passed back into this service to grab the next set of results. If no more results are available, this field will be absent.

  **Example first request**:

  .. sourcecode:: http

    GET /api/data/(list_service)?size=5 HTTP/1.1

  **Example first response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "results": ["result1", "result2", "result3", "result4", "result5"],
      "cursor": "hsajkhasjkdy8y3h3h8fhih38djhdjdj"
    }

  **Example second request**:

  .. sourcecode:: http

    GET /api/data/(list_service)?size=5&cursor=hsajkhasjkdy8y3h3h8fhih38djhdjdj HTTP/1.1

  **Example second response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "results": ["result6", "result7", "result8"]
    }


------
Server
------
.. http:get:: /api/data/server

  Get the minecraft server information.

  :status 200: Successfully queried the server information.

    .. _server_response_data:

    :Response Data: - **version** -- The minecraft server version.
                    - **is_running** -- A boolean indicating whether the minecraft server is running. If this value is ``null`` the status is unknown.
                    - **last_ping** -- The timestamp of the last agent ping.
                    - **created** -- The server's creation timestamp.
                    - **updated** -- The server's updated timestamp.

  **Example request**:

  .. sourcecode:: http

    GET /api/data/server HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "last_ping": "2013-04-14 19:55:22 CDT-0500",
      "version": "1.5.1",
      "updated": "2013-04-14 19:55:22 CDT-0500",
      "is_running": true,
      "created": "2013-03-04 15:05:53 CST-0600"
    }


----
User
----
.. http:get:: /api/data/user

  Get a :ref:`list <list>` of all users ordered by email.

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.

  :status 200: Successfully queried the users.

    :Response Data: - **users** -- The list of users.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this service to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **users** is a dictionary of the user information.

    .. _user_response_data:

    :User: - **key** -- The user key.
           - **player_key** -- The user's minecraft player key. ``null`` if the user is not mapped to a minecraft player.
           - **username** -- The user's minecraft username. Empty string if the user is not mapped to a minecraft player.
           - **email** -- The user's email.
           - **nickname** -- The user's nickname.
           - **active** -- A boolean indicating whether the user is active.
           - **admin** -- A boolean indicating whether the user is an admin.
           - **last_coal_login** -- The timestamp of the user's last COAL login.
           - **last_chat_view** -- The timestamp of the user's last chat view.
           - **created** -- The user's creation timestamp.
           - **updated** -- The user's updated timestamp.

  **Example request**:

  .. sourcecode:: http

    GET /api/data/user HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "users": [
        {
          "username": "",
          "updated": "2013-03-14 17:23:09 CDT-0500",
          "created": "2013-03-04 17:43:37 CST-0600",
          "admin": false,
          "player_key": null,
          "last_chat_view": "2013-03-14 17:23:09 CDT-0500",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchiZdQw",
          "active": true,
          "last_coal_login": null,
          "nickname": "jennifer",
          "email": "j@gmail.com"
        },
        {
          "username": "quazifene",
          "updated": "2013-04-14 18:56:59 CDT-0500",
          "created": "2013-03-04 17:53:12 CST-0600",
          "admin": true,
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIuCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIJcXVhemlmZW5lDA",
          "last_chat_view": "2013-04-14 18:48:47 CDT-0500",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchiBfQw",
          "active": true,
          "last_coal_login": "2013-04-12 14:04:39 CDT-0500",
          "nickname": "mark",
          "email": "m@gmail.com"
        },
        {
          "username": "gumptionthomas",
          "updated": "2013-04-14 18:37:35 CDT-0500",
          "created": "2013-03-04 15:05:52 CST-0600",
          "admin": true,
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "last_chat_view": "2013-04-14 18:37:35 CDT-0500",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "active": true,
          "last_coal_login": "2013-04-13 14:03:33 CDT-0500",
          "nickname": "thomas",
          "email": "t@gmail.com"
        }
      ]
    }

.. http:get:: /api/data/user/(key)

  Get the information for the user (`key`).

  :arg key: The requested user's key. (*required*)

  :status 200: Successfully read the user.

    :Response Data: See :ref:`User response data <user_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/data/user/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "username": "gumptionthomas",
      "updated": "2013-04-14 18:37:35 CDT-0500",
      "created": "2013-03-04 15:05:52 CST-0600",
      "admin": true,
      "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
      "last_chat_view": "2013-04-14 18:37:35 CDT-0500",
      "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
      "active": true,
      "last_coal_login": "2013-04-13 14:03:33 CDT-0500",
      "nickname": "thomas",
      "email": "t@gmail.com"
    }


------
Player
------
.. http:get:: /api/data/player

  Get a :ref:`list <list>` of all minecraft players ordered by username.

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.

  :status 200: Successfully queried the players.

    :Response Data: - **players** -- The list of players.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this service to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **players** is a dictionary of the player information.

    .. _player_response_data:

    :Player: - **key** -- The player key.
             - **username** -- The player's minecraft username.
             - **user_key** -- The player's user key. ``null`` if the player is not mapped to a user.
             - **last_login** -- The timestamp of the player's last minecraft login. ``null`` if the player has not logged in.
             - **last_session_duration** -- The player's last session duration in seconds. ``null`` if the player has not logged in.
             - **is_playing** -- A boolean indicating whether the player is currently logged into the minecraft server.

  **Example request**:

  .. sourcecode:: http

    GET /api/data/player HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "players": [
        {
          "username": "gumptionthomas",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "last_login": "2013-04-13 20:50:34 CDT-0500",
          "last_session_duration": 8126,
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "is_playing": false
        },
          "username": "quazifene",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchiBfQw",
          "last_login": "2013-04-13 21:21:30 CDT-0500",
          "last_session_duration": 6821,
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIuCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIJcXVhemlmZW5lDA",
          "is_playing": false
        }
      ]
    }

.. http:get:: /api/data/player/(key_username)

  Get the information for the player (`key_username`).

  :arg key_username: The requested player's key or minecraft username. (*required*)

  :status 200: Successfully read the player.

    :Response Data: See :ref:`Player response data <player_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/data/player/gumptionthomas HTTP/1.1

  **OR**

  .. sourcecode:: http

    GET /api/data/player/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "username": "gumptionthomas",
      "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
      "last_login": "2013-04-13 20:50:34 CDT-0500",
      "last_session_duration": 8126,
      "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
      "is_playing": false
    }


------------
Play Session
------------
.. http:get:: /api/data/play_session

  Get a :ref:`list <list>` of all minecraft play sessions ordered by descending login timestamp.

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return sessions with a login datetime since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return sessions with a login datetime before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

  :status 200: Successfully queried the play sessions.

    :Response Data: - **play_sessions** -- The list of play sessions.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this service to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **play_sessions** is a dictionary of the play session information.

    .. _play_session_response_data:

    :Play Session: - **key** -- The play session key.
                   - **username** -- The minecraft username associated with the play session.
                   - **player_key** -- The player key. ``null`` if the username is not mapped to a player.
                   - **user_key** -- The user key. ``null`` if the username is not mapped to a player or the player is not mapped to a user.
                   - **login_timestamp** -- The timestamp of the play session start. It will be reported in the agent's timezone.
                   - **logout_timestamp** -- The timestamp of the play session end. It will be reported in the agent's timezone.
                   - **duration** -- The length of the play session in seconds.
                   - **login_log_line_key** -- The login log line key. May be ``null``.
                   - **logout_log_line_key** -- The logout log line key. May be ``null``.
                   - **created** -- The creation timestamp.
                   - **updated** -- The updated timestamp.

  **Example request**:

  .. sourcecode:: http

    GET /api/data/play_session HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "play_sessions": [
        {
          "username": "gumptionthomas",
          "updated": "2013-04-13 23:06:01 CDT-0500",
          "logout_timestamp": "2013-04-13 23:06:00 CDT-0500",
          "login_timestamp": "2013-04-13 20:50:34 CDT-0500",
          "created": "2013-04-13 20:50:35 CDT-0500",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "login_log_line_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY9PogDA",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIsCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSC1BsYXlTZXNzaW9uGNPbIAw",
          "duration": 8126,
          "logout_log_line_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUYtMQgDA"
        },
        {
          "username": "vesicular",
          "updated": "2013-04-13 20:20:21 CDT-0500",
          "logout_timestamp": "2013-04-13 20:20:19 CDT-0500",
          "login_timestamp": "2013-04-13 19:48:28 CDT-0500",
          "created": "2013-04-13 19:48:29 CDT-0500",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchjkLww",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIuCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIJdmVzaWN1bGFyDA",
          "login_log_line_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY-NYfDA",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIsCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSC1BsYXlTZXNzaW9uGPnWHww",
          "duration": 1911,
          "logout_log_line_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUYpesgDA"
        }
      ]
    }

.. http:get:: /api/data/play_session/(key)

  Get the information for the play session (`key`).

  :arg key: The requested play session's key. (*required*)

  :status 200: Successfully read the play session.

    :Response Data: See :ref:`Play session response data <play_session_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/data/play_session/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIsCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSC1BsYXlTZXNzaW9uGNPbIAw HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "username": "gumptionthomas",
      "updated": "2013-04-13 23:06:01 CDT-0500",
      "logout_timestamp": "2013-04-13 23:06:00 CDT-0500",
      "login_timestamp": "2013-04-13 20:50:34 CDT-0500",
      "created": "2013-04-13 20:50:35 CDT-0500",
      "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
      "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
      "login_log_line_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY9PogDA",
      "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIsCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSC1BsYXlTZXNzaW9uGNPbIAw",
      "duration": 8126,
      "logout_log_line_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUYtMQgDA"
    }

.. http:get:: /api/data/player/(key_username)/session

  Get a :ref:`list <list>` of a player's minecraft play sessions ordered by descending login timestamp.

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.

  :status 200: Successfully queried the play sessions.

    :Response Data: - **play_sessions** -- The list of the player's play sessions.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this service to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **play_sessions** is a dictionary of the player's play session information. See :ref:`Play session response data <play_session_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/data/player/gumptionthomas/session HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "play_sessions": [
        {
          "username": "gumptionthomas",
          "updated": "2013-04-15 22:31:43 CDT-0500",
          "logout_timestamp": "2013-04-15 22:31:42 CDT-0500",
          "login_timestamp": "2013-04-15 22:31:18 CDT-0500",
          "created": "2013-04-15 22:31:19 CDT-0500",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "login_log_line_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUYlOIjDA",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIsCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSC1BsYXlTZXNzaW9uGIWpHAw",
          "duration": 24,
          "logout_log_line_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUYhZEkDA"
        },
        {
          "username": "gumptionthomas",
          "updated": "2013-04-13 23:06:01 CDT-0500",
          "logout_timestamp": "2013-04-13 23:06:00 CDT-0500",
          "login_timestamp": "2013-04-13 20:50:34 CDT-0500",
          "created": "2013-04-13 20:50:35 CDT-0500",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "login_log_line_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY9PogDA",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIsCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSC1BsYXlTZXNzaW9uGNPbIAw",
          "duration": 8126,
          "logout_log_line_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUYtMQgDA"
        }
      ]
    }
