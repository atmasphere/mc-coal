============
Achievements
============
.. http:get:: /api/v1/servers/(server_key)/achievements

  Get a :ref:`list <list>` of all minecraft achievements earned on the server (`server_key`) ordered by descending timestamp.

  :arg server_key: The target server's key. (*required*)

  :query q: A search string to limit the achievement results to.
  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return achievements with a timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return achievements with a timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

  :status 200 OK: Successfully queried the achievements.

    :Response Data: - **achievements** -- The list of achievements.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **achievements** is an object of achievement information.

    .. _achievement_response_data:

    :Achievement: - **key** -- The achievement log line key.
                  - **server_key** -- The achievement log line's server key.
                  - **name** -- The achievement name.
                  - **message** -- The achievement message.
                  - **username** -- The minecraft username associated with the achievement.
                  - **player_key** -- The player key.
                  - **user_key** -- The user key. ``null`` if the player is not mapped to a user.
                  - **timestamp** -- The timestamp of the achievement. It will be reported in the agent's timezone.
                  - **line** -- The complete raw achievement log line text.
                  - **created** -- The creation timestamp.
                  - **updated** -- The updated timestamp.

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/achievements HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "achievements": [
        {
          "username": "gumptionthomas",
          "updated": "2013-11-11 20:47:04 CDT-0500",
          "key": "agtkZXZ-bWMtY29hbHInCxIGU2VydmVyGICAgICAgIAJDAsSB0xvZ0xpbmUYgICAgICAhAkM",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "timestamp": "2013-11-11 20:47:02 CDT-0500",
          "created": "2013-11-11 20:47:04 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "name": "Taking Inventory",
          "message": "has just earned the achievement [Taking Inventory]",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-11-11 14:47:02 [INFO] gumptionthomas has just earned the achievement [Taking Inventory]"
        },
        {
          "username": "gumptionthomas",
          "updated": "2013-11-10 17:19:06 CDT-0500",
          "key": "agtkZXZ-bWMtY29hbHInCxIGU2VydmVyGICAgICAgIAJDAsSB0xvZ0xpbmUYgICAgICAtAkM",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "timestamp": "2013-11-10 17:19:04 CDT-0500",
          "created": "2013-11-10 17:19:06 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "name": "Getting an Upgrade",
          "message": "has just earned the achievement [Getting an Upgrade]",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-11-10 17:19:04 [INFO] gumptionthomas has just earned the achievement [Getting an Upgrade]"
        }
      ]
    }

.. http:get:: /api/v1/servers/(server_key)/achievements/(key)

  Get the information for the achievement (`key`) on the server (`server_key`).

  :arg server_key: The target server's key. (*required*)
  :arg key: The requested achievement's log line key. (*required*)

  :status 200 OK: Successfully read the achievement.

    :Response Data: See :ref:`Achievement response data <achievement_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/achievements/bWMtY29hbHInCxIGU2VydmVyGICAgICAgIAJDAsSB0xvZ0xpbmUYgICAgICAhAkM HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "username": "gumptionthomas",
      "updated": "2013-04-19 10:32:56 CDT-0500",
      "key": "bWMtY29hbHInCxIGU2VydmVyGICAgICAgIAJDAsSB0xvZ0xpbmUYgICAgICAhAkM",
      "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
      "timestamp": "2013-11-11 20:47:02 CDT-0500",
      "created": "2013-11-11 20:47:04 CDT-0500",
      "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
      "name": "Taking Inventory",
      "message": "has just earned the achievement [Taking Inventory]",
      "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
      "line": "2013-11-11 14:47:02 [INFO] gumptionthomas has just earned the achievement [Taking Inventory]"
    }

.. http:get:: /api/v1/servers/(server_key)/players/(key_username)/achievements

  Get a :ref:`list <list>` of a player's (`key_username`) minecraft achievements earned on the server (`server_key`) ordered by descending timestamp.

  :arg server_key: The target server's key. (*required*)
  :arg key_username: The requested player's key or minecraft username. (*required*)

  :query q: A search string to limit the achievement results to.
  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return log lines with a timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return log lines with a timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

  :status 200 OK: Successfully queried the achievements.

    :Response Data: - **achievements** -- The list of the player's achievements.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **achievements** is an object of achievement information. See :ref:`Achievement response data <achievement_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/players/gumptionthomas/achievements HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "achievements": [
        {
          "username": "gumptionthomas",
          "updated": "2013-11-11 20:47:04 CDT-0500",
          "key": "agtkZXZ-bWMtY29hbHInCxIGU2VydmVyGICAgICAgIAJDAsSB0xvZ0xpbmUYgICAgICAhAkM",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "timestamp": "2013-11-11 20:47:02 CDT-0500",
          "created": "2013-11-11 20:47:04 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "name": "Taking Inventory",
          "message": "has just earned the achievement [Taking Inventory]",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-11-11 14:47:02 [INFO] gumptionthomas has just earned the achievement [Taking Inventory]"
        },
        {
          "username": "gumptionthomas",
          "updated": "2013-11-10 17:19:06 CDT-0500",
          "key": "agtkZXZ-bWMtY29hbHInCxIGU2VydmVyGICAgICAgIAJDAsSB0xvZ0xpbmUYgICAgICAtAkM",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "timestamp": "2013-11-10 17:19:04 CDT-0500",
          "created": "2013-11-10 17:19:06 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "name": "Getting an Upgrade",
          "message": "has just earned the achievement [Getting an Upgrade]",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-11-10 17:19:04 [INFO] gumptionthomas has just earned the achievement [Getting an Upgrade]"
        }
      ]
    }

