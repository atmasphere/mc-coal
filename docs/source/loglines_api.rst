=========
Log Lines
=========
.. http:get:: /api/v1/servers/(server_key)/loglines

  Get a :ref:`list <list>` of all minecraft log lines on the server (`server_key`) ordered by descending timestamp.

  :arg server_key: The target server's key. (*required*)

  :query tag: A tag to limit the type of log line results.

    .. _logline_tag_options:

    :Tag Options: - ``unknown``
                  - ``timestamp``
                  - ``connection``
                  - ``login``
                  - ``logout``
                  - ``chat``
                  - ``death``
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

  :status 200 OK: Successfully queried the log lines.

    :Response Data: - **loglines** -- The list of log lines.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **loglines** is an object of log line information.

    .. _logline_response_data:

    :Log Line: - **key** -- The log line key.
               - **server_key** -- The log line's server key.
               - **line** -- The complete raw log line text.
               - **username** -- The minecraft username associated with the log line. May be ``null``.
               - **player_key** -- The player key. ``null`` if the username is not mapped to a player.
               - **user_key** -- The user key. ``null`` if the username is not mapped to a player or the player is not mapped to a user.
               - **timestamp** -- The timestamp of the log line. It will be reported in the agent's timezone.
               - **log_level** -- The log level of the log line. May be ``null``.
               - **ip** -- The ip address recorded with the log line. May be ``null``.
               - **port** -- The port recorded with the log line. May be ``null``.
               - **location** -- The location of the log line as an object containing ``x``, ``y``, and ``z`` keys with float values. May be ``null``.
               - **chat** -- The chat text of the log line. May be ``null``.
               - **tags** -- A list of the log line's tags. May be an empty list.
               - **created** -- The creation timestamp.
               - **updated** -- The updated timestamp.

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/loglines HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "loglines": [
        {
          "username": "gumptionthomas",
          "updated": "2013-04-19 10:32:56 CDT-0500",
          "log_level": "INFO",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nDA",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
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
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
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

.. http:get:: /api/v1/servers/(server_key)/loglines/(key)

  Get the information for the log line (`key`).

  :arg server_key: The target server's key. (*required*)
  :arg key: The requested log line's key. (*required*)

  :status 200 OK: Successfully read the log line.

    :Response Data: See :ref:`Log line response data <logline_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/loglines/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nDA HTTP/1.1

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
      "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
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

.. http:get:: /api/v1/servers/(server_key)/players/(key_username)/loglines

  Get a :ref:`list <list>` of a player's (`key_username`) minecraft log lines on the server (`server_key`) ordered by descending timestamp.

  :arg server_key: The target server's key. (*required*)
  :arg key_username: The requested player's key or minecraft username. (*required*)

  :query tag: A tag to limit the type of log line results. For possible values see :ref:`Log line tag options <logline_tag_options>`

  :query q: A search string to limit the results to.
  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return log lines with a timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return log lines with a timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

  :status 200 OK: Successfully queried the log lines.

    :Response Data: - **loglines** -- The list of the player's log lines.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **loglines** is an object of log line information. See :ref:`Log line response data <logline_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/players/gumptionthomas/loglines HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "loglines": [
        {
          "username": "gumptionthomas",
          "updated": "2013-04-19 10:32:56 CDT-0500",
          "log_level": "INFO",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nDA",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
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
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
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
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
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


