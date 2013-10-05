========
Sessions
========
.. http:get:: /api/v1/servers/(server_key)/sessions

  Get a :ref:`list <list>` of all minecraft play sessions on the server (`server_key`) ordered by descending login timestamp.

  :arg server_key: The target server's key. (*required*)

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return sessions with a login timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return sessions with a login timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

  :status 200 OK: Successfully queried the play sessions.

    :Response Data: - **sessions** -- The list of play sessions.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **sessions** is a dictionary of play session information.

    .. _session_response_data:

    :Session: - **key** -- The play session key.
              - **server_key** -- The play session's server key.
              - **username** -- The minecraft username associated with the play session.
              - **player_key** -- The player key. ``null`` if the username is not mapped to a player.
              - **user_key** -- The user key. ``null`` if the username is not mapped to a player or the player is not mapped to a user.
              - **login_timestamp** -- The timestamp of the play session start. It will be reported in the agent's timezone.
              - **logout_timestamp** -- The timestamp of the play session end. It will be reported in the agent's timezone.
              - **duration** -- The length of the play session in seconds.
              - **login_logline_key** -- The login log line key. May be ``null``.
              - **logout_logline_key** -- The logout log line key. May be ``null``.
              - **created** -- The creation timestamp.
              - **updated** -- The updated timestamp.

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/sessions HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "sessions": [
        {
          "username": "gumptionthomas",
          "updated": "2013-04-13 23:06:01 CDT-0500",
          "logout_timestamp": "2013-04-13 23:06:00 CDT-0500",
          "login_timestamp": "2013-04-13 20:50:34 CDT-0500",
          "created": "2013-04-13 20:50:35 CDT-0500",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "login_logline_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY9PogDA",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIsCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSC1BsYXlTZXNzaW9uGNPbIAw",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "duration": 8126,
          "logout_logline_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUYtMQgDA"
        },
        {
          "username": "vesicular",
          "updated": "2013-04-13 20:20:21 CDT-0500",
          "logout_timestamp": "2013-04-13 20:20:19 CDT-0500",
          "login_timestamp": "2013-04-13 19:48:28 CDT-0500",
          "created": "2013-04-13 19:48:29 CDT-0500",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchjkLww",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIuCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIJdmVzaWN1bGFyDA",
          "login_logline_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY-NYfDA",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIsCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSC1BsYXlTZXNzaW9uGPnWHww",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "duration": 1911,
          "logout_logline_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUYpesgDA"
        }
      ]
    }

.. http:get:: /api/v1/servers/(server_key)/sessions/(key)

  Get the information for the play session (`key`) on the server (`server_key`).

  :arg server_key: The target server's key. (*required*)
  :arg key: The requested play session's key. (*required*)

  :status 200 OK: Successfully read the play session.

    :Response Data: See :ref:`Play session response data <session_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/sessions/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIsCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSC1BsYXlTZXNzaW9uGNPbIAw HTTP/1.1

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
      "login_logline_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY9PogDA",
      "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIsCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSC1BsYXlTZXNzaW9uGNPbIAw",
      "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
      "duration": 8126,
      "logout_logline_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUYtMQgDA"
    }

.. http:get:: /api/v1/servers/(server_key)/players/(key_username)/sessions

  Get a :ref:`list <list>` of a player's (`key_username`) minecraft play sessions on the server (`server_key`) ordered by descending login timestamp.

  :arg server_key: The target server's key. (*required*)
  :arg key_username: The requested player's key or minecraft username. (*required*)

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return sessions with a login timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return sessions with a login timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

  :status 200 OK: Successfully queried the play sessions.

    :Response Data: - **sessions** -- The list of the player's play sessions.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **sessions** is a dictionary of play session information. See :ref:`Play session response data <session_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/players/gumptionthomas/session HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "sessions": [
        {
          "username": "gumptionthomas",
          "updated": "2013-04-15 22:31:43 CDT-0500",
          "logout_timestamp": "2013-04-15 22:31:42 CDT-0500",
          "login_timestamp": "2013-04-15 22:31:18 CDT-0500",
          "created": "2013-04-15 22:31:19 CDT-0500",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "login_logline_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUYlOIjDA",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIsCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSC1BsYXlTZXNzaW9uGIWpHAw",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "duration": 24,
          "logout_logline_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUYhZEkDA"
        },
        {
          "username": "gumptionthomas",
          "updated": "2013-04-13 23:06:01 CDT-0500",
          "logout_timestamp": "2013-04-13 23:06:00 CDT-0500",
          "login_timestamp": "2013-04-13 20:50:34 CDT-0500",
          "created": "2013-04-13 20:50:35 CDT-0500",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "login_logline_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY9PogDA",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIsCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSC1BsYXlTZXNzaW9uGNPbIAw",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "duration": 8126,
          "logout_logline_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUYtMQgDA"
        }
      ]
    }


