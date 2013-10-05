======
Deaths
======
.. http:get:: /api/v1/servers/(server_key)/deaths

  Get a :ref:`list <list>` of all minecraft deaths on the server (`server_key`) ordered by descending timestamp.

  :arg server_key: The target server's key. (*required*)

  :query q: A search string to limit the death results to.
  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return deaths with a timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return deaths with a timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

  :status 200 OK: Successfully queried the deaths.

    :Response Data: - **deaths** -- The list of deaths.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **deaths** is a dictionary of death information.

    .. _death_response_data:

    :Death: - **key** -- The death log line key.
            - **server_key** -- The death log line's server key.
            - **message** -- The death message. May be ``null``.
            - **username** -- The minecraft username associated with the death.
            - **player_key** -- The player key.
            - **user_key** -- The user key. ``null`` if the player is not mapped to a user.
            - **timestamp** -- The timestamp of the death. It will be reported in the agent's timezone.
            - **line** -- The complete raw death log line text.
            - **created** -- The creation timestamp.
            - **updated** -- The updated timestamp.

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/deaths HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "deaths": [
        {
          "username": "gumptionthomas",
          "updated": "2013-04-19 10:33:56 CDT-0500",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nXV",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "timestamp": "2013-04-19 10:33:55 CDT-0500",
          "created": "2013-04-19 10:33:56 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "message": "was squashed by a falling anvil",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-04-19 10:33:55 [INFO] gumptionthomas was squashed by a falling anvil"
        },
        {
          "username": "gumptionthomas",
          "updated": "2013-04-19 10:32:56 CDT-0500",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nDA",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "timestamp": "2013-04-19 10:32:55 CDT-0500",
          "created": "2013-04-19 10:32:56 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "message": "was shot by arrow",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-04-19 10:32:55 [INFO] gumptionthomas was shot by arrow"
        }
      ]
    }

.. http:get:: /api/v1/servers/(server_key)/deaths/(key)

  Get the information for the death (`key`) on the server (`server_key`).

  :arg server_key: The target server's key. (*required*)
  :arg key: The requested death's log line key. (*required*)

  :status 200 OK: Successfully read the death.

    :Response Data: See :ref:`Death response data <death_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/deaths/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nDA HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "username": "gumptionthomas",
      "updated": "2013-04-19 10:32:56 CDT-0500",
      "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nDA",
      "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
      "timestamp": "2013-04-19 10:32:55 CDT-0500",
      "created": "2013-04-19 10:32:56 CDT-0500",
      "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
      "message": "was shot by arrow",
      "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
      "line": "2013-04-19 10:32:55 [INFO] gumptionthomas was shot by arrow"
    }

.. http:get:: /api/v1/servers/(server_key)/players/(key_username)/deaths

  Get a :ref:`list <list>` of a player's (`key_username`) minecraft deaths on the server (`server_key`) ordered by descending timestamp.

  :arg server_key: The target server's key. (*required*)
  :arg key_username: The requested player's key or minecraft username. (*required*)

  :query q: A search string to limit the death results to.
  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return log lines with a timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return log lines with a timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

  :status 200 OK: Successfully queried the deaths.

    :Response Data: - **deaths** -- The list of the player's deaths.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **deaths** is a dictionary of death information. See :ref:`Death response data <death_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/players/gumptionthomas/deaths HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "deaths": [
        {
          "username": "gumptionthomas",
          "updated": "2013-04-19 10:33:56 CDT-0500",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nXV",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "timestamp": "2013-04-19 10:33:55 CDT-0500",
          "created": "2013-04-19 10:33:56 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "message": "was squashed by a falling anvil",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-04-19 10:33:55 [INFO] gumptionthomas was squashed by a falling anvil"
        },
        {
          "username": "gumptionthomas",
          "updated": "2013-04-19 10:32:56 CDT-0500",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nDA",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "timestamp": "2013-04-19 10:32:55 CDT-0500",
          "created": "2013-04-19 10:32:56 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "message": "was shot by arrow",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-04-19 10:32:55 [INFO] gumptionthomas was shot by arrow"
        }
      ]
    }


