=======
Players
=======
.. http:get:: /api/v1/servers/(server_key)/players

  Get a :ref:`list <list>` of all minecraft players on the server (`server_key`). Results are ordered by username.

  :arg server_key: The target server's key. (*required*)

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.

  :status 200 OK: Successfully queried the players.

    :Response Data: - **players** -- The list of players.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **players** is an object of player information.

    .. _player_response_data:

    :Player: - **key** -- The player key.
             - **server_key** -- The player's server key.
             - **username** -- The player's minecraft username.
             - **user_key** -- The player's user key. ``null`` if the player is not mapped to a user.
             - **last_login** -- The timestamp of the player's last minecraft login. ``null`` if the player has not logged in.
             - **last_session_duration** -- The player's last session duration in seconds. ``null`` if the player has not logged in.
             - **is_playing** -- A boolean indicating whether the player is currently logged into the minecraft server.

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/players HTTP/1.1

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
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "is_playing": false
        },
          "username": "quazifene",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchiBfQw",
          "last_login": "2013-04-13 21:21:30 CDT-0500",
          "last_session_duration": 6821,
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIuCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIJcXVhemlmZW5lDA",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "is_playing": false
        }
      ]
    }

.. http:get:: /api/v1/servers/(server_key)/players/(key_username)

  Get the information for the player (`key_username`) on the server (`server_key`).

  :arg server_key: The target server's key. (*required*)
  :arg key_username: The requested player's key or minecraft username. (*required*)

  :status 200 OK: Successfully read the player.

    :Response Data: See :ref:`Player response data <player_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/players/gumptionthomas HTTP/1.1

  **OR**

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/players/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM HTTP/1.1

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
      "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
      "is_playing": false
    }


