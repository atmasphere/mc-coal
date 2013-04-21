========
Data API
========

--------------
Authentication
--------------
Calls to services can be authenticated via a normal login session cookie (via a browser) or valid Google Account OAuth credentials. Both of these authentication schemes require calls be made using HTTPS. If your mc-coal instance is mapped to a custom domain, you'll need to make calls to your application's ``appspot.com`` domain rather than your custom domain.

Unless otherwise indicated, services don't actually require authenicating a user. In these cases, the ``COAL_API_PASSWORD`` as defined in ``mc_coal_config.py`` passed via the ``p`` query parameter can be used in lieu of the session cookie or oauth.

See these links for more information on authenticating via oauth:

* `OAuth for Python Overview <https://developers.google.com/appengine/docs/python/oauth/overview>`_
* `Setting up an OAuth provider on Google App Engine <http://ikaisays.com/2011/05/26/setting-up-an-oauth-provider-on-google-app-engine/>`_
* `StackOverflow: google app engine oauth2 provider <http://stackoverflow.com/questions/7810607/google-app-engine-oauth2-provider>`_

An oauth test endpoint is provided to simplify developing consumer applications:

.. http:get:: /api/data/oauth_test

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK

    Request:
    GET /api/data/oauth_test?oauth_body_hash=2jmj7l5rSw0yVb%2FvlWAYkK%2FYBwk%3D&oauth_nonce=49307393&oauth_timestamp=1366478308&oauth_consumer_key=my.consumer.com&oauth_signature_method=HMAC-SHA1&oauth_version=1.0&oauth_token=1%2F6UptVLjvsKTr2CAF6t5GFCwL6I8s-24pBxi4bJoIPGQ&oauth_signature=%2FbCvttoC3y82LGYX7onyjuZmNrg%3D HTTP/1.1

    Current User Nickname: thomasbohmbach
    Current User Email: t@gmail.com
    Consumer Key (from params): my.consumer.com


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

.. http:get:: /api/data/user/self

  Get the information for the current user as authenicated via session cookie or oauth. If no valid authentication credentials are provided, a :http:statuscode:`403` will result.

  :status 200: Successfully read the current user.

    :Response Data: See :ref:`User response data <user_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/data/user/self HTTP/1.1

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
  :query since: Return sessions with a login timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return sessions with a login timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

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

  :arg key_username: The requested player's key or minecraft username. (*required*)

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return sessions with a login timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return sessions with a login timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

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


--------
Log Line
--------
.. http:get:: /api/data/log_line

  Get a :ref:`list <list>` of all minecraft log lines ordered by descending timestamp.

  :query tag: A tag to limit the type of log line results.

    .. _log_line_tag_options:

    :Tag Options: - ``unknown``
                  - ``timestamp``
                  - ``connection``
                  - ``login``
                  - ``logout``
                  - ``chat``
                  - ``server``
                  - ``performance``
                  - ``overloaded``
                  - ``stopping``
                  - ``starting``

  :query q: A search string to limit the results to.
  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return log lines with a timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return log lines with a timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

  :status 200: Successfully queried the log lines.

    :Response Data: - **log_lines** -- The list of log lines.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this service to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **log_lines** is a dictionary of the log line information.

    .. _log_line_response_data:

    :Log Line: - **key** -- The log line key.
               - **line** -- The complete raw log line text.
               - **username** -- The minecraft username associated with the log line. May be ``null``.
               - **player_key** -- The player key. ``null`` if the username is not mapped to a player.
               - **user_key** -- The user key. ``null`` if the username is not mapped to a player or the player is not mapped to a user.
               - **timestamp** -- The timestamp of the log line. It will be reported in the agent's timezone.
               - **log_level** -- The log level of the log line. May be ``null``.
               - **ip** -- The ip address recorded with the log line. May be ``null``.
               - **port** -- The port recorded with the log line. May be ``null``.
               - **location** -- The location of the log line as a dictionary containing ``x``, ``y``, and ``z`` keys with float values. May be ``null``.
               - **chat** -- The chat text of the log line. May be ``null``.
               - **tags** -- A list of the log line's tags. May be an empty list.
               - **created** -- The creation timestamp.
               - **updated** -- The updated timestamp.

  **Example request**:

  .. sourcecode:: http

    GET /api/data/log_line HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "log_lines": [
        {
          "username": "gumptionthomas",
          "updated": "2013-04-19 10:32:56 CDT-0500",
          "log_level": "INFO",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nDA",
          "timestamp": "2013-04-19 10:32:55 CDT-0500",
          "tags": [
              "timestamp",
              "chat"
          ],
          "ip": null,
          "created": "2013-04-19 10:32:56 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "location": null,
          "chat": "hey guys",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-04-19 10:32:55 [INFO] [Server] <gumptionthomas> hey guys",
          "port": null
        },
        {
          "username": "gumptionthomas",
          "updated": "2013-04-19 00:26:53 CDT-0500",
          "log_level": "INFO",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUYlL4iDA",
          "timestamp": "2013-04-19 00:26:53 CDT-0500",
          "tags": [
              "timestamp",
              "connection",
              "logout"
          ],
          "ip": null,
          "created": "2013-04-19 00:26:53 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "location": null,
          "chat": null,
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-04-19 00:26:53 [INFO] gumptionthomas lost connection: disconnect.quitting",
          "port": null
        }
      ]
    }

.. http:get:: /api/data/log_line/(key)

  Get the information for the log line (`key`).

  :arg key: The requested log line's key. (*required*)

  :status 200: Successfully read the log line.

    :Response Data: See :ref:`Log line response data <log_line_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/data/log_line/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nDA HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "username": "gumptionthomas",
      "updated": "2013-04-19 10:32:56 CDT-0500",
      "log_level": "INFO",
      "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nDA",
      "timestamp": "2013-04-19 10:32:55 CDT-0500",
      "tags": [
          "timestamp",
          "chat"
      ],
      "ip": null,
      "created": "2013-04-19 10:32:56 CDT-0500",
      "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
      "location": null,
      "chat": "hey guys",
      "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
      "line": "2013-04-19 10:32:55 [INFO] [Server] <gumptionthomas> hey guys",
      "port": null
    }

.. http:get:: /api/data/player/(key_username)/log_line

  Get a :ref:`list <list>` of a player's minecraft log lines ordered by descending login timestamp.

  :arg key_username: The requested player's key or minecraft username. (*required*)

  :query tag: A tag to limit the type of log line results. For possible values see :ref:`Log line tag options <log_line_tag_options>`

  :query q: A search string to limit the results to.
  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return log lines with a timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return log lines with a timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

  :status 200: Successfully queried the log lines.

    :Response Data: - **log_lines** -- The list of the player's log lines.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this service to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **log_lines** is a dictionary of the player's log line information. See :ref:`Log line response data <log_line_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/data/player/gumptionthomas/log_line HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "log_lines": [
        {
          "username": "gumptionthomas",
          "updated": "2013-04-19 10:32:56 CDT-0500",
          "log_level": "INFO",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nDA",
          "timestamp": "2013-04-19 10:32:55 CDT-0500",
          "tags": [
              "timestamp",
              "chat"
          ],
          "ip": null,
          "created": "2013-04-19 10:32:56 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "location": null,
          "chat": "hey guys",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-04-19 10:32:55 [INFO] [Server] <gumptionthomas> hey guys",
          "port": null
        },
        {
          "username": "gumptionthomas",
          "updated": "2013-04-19 00:26:53 CDT-0500",
          "log_level": "INFO",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUYlL4iDA",
          "timestamp": "2013-04-19 00:26:53 CDT-0500",
          "tags": [
              "timestamp",
              "connection",
              "logout"
          ],
          "ip": null,
          "created": "2013-04-19 00:26:53 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "location": null,
          "chat": null,
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-04-19 00:26:53 [INFO] gumptionthomas lost connection: disconnect.quitting",
          "port": null
        },
        {
          "username": "gumptionthomas",
          "updated": "2013-04-13 08:11:27 CDT-0500",
          "log_level": "INFO",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY5dYfDA",
          "timestamp": "2013-04-13 08:11:26 CDT-0500",
          "tags": [
              "timestamp",
              "connection",
              "login"
          ],
          "ip": "192.168.0.1",
          "created": "2013-04-19 08:11:27 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "location": {
              "y": 72,
              "x": 221.3000000119209,
              "z": 240.68847388602495
          },
          "chat": null,
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-04-13 08:11:26 [INFO] gumptionthomas[/192.168.0.1:52142] logged in with entity id 1372 at (221.3000000119209, 72.0, 240.68847388602495)",
          "port": "52142"
        }
      ]
    }
