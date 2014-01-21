=====
Chats
=====
.. http:get:: /api/v1/servers/(server_key)/chats

  Get a :ref:`list <list>` of all minecraft chats on the server (`server_key`) ordered by descending timestamp.

  :arg server_key: The target server's key. (*required*)

  :query q: A search string to limit the chat results to.
  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return chats with a timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return chats with a timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

  :status 200 OK: Successfully queried the chats.
  
    :Response Data:
  
      - **chats** -- The list of chats.
      - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **chats** is an object of chat information.

    .. _chat_response_data:

    :Chat:
  
      - **key** -- The chat log line key.
      - **server_key** -- The chat's server key.
      - **chat** -- The chat text. May be ``null``.
      - **username** -- The minecraft username associated with the chat. May be ``null``.
      - **player_key** -- The player key. ``null`` if the username is not mapped to a player.
      - **user_key** -- The user key. ``null`` if the username is not mapped to a player or the player is not mapped to a user.
      - **timestamp** -- The timestamp of the chat. It will be reported in the agent's timezone.
      - **line** -- The complete raw chat log line text.
      - **created** -- The creation timestamp.
      - **updated** -- The updated timestamp.

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/chats HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "chats": [
        {
          "username": "gumptionthomas",
          "updated": "2013-04-19 10:33:56 CDT-0500",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nXV",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "timestamp": "2013-04-19 10:33:55 CDT-0500",
          "created": "2013-04-19 10:33:56 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "chat": "what's up?",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-04-19 10:33:55 [INFO] <gumptionthomas> what's up?"
        },
        {
          "username": "gumptionthomas",
          "updated": "2013-04-19 10:32:56 CDT-0500",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nDA",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "timestamp": "2013-04-19 10:32:55 CDT-0500",
          "created": "2013-04-19 10:32:56 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "chat": "hey guys",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-04-19 10:32:55 [INFO] [Server] <gumptionthomas> hey guys"
        }
      ]
    }

.. http:post:: /api/v1/servers/(server_key)/chats

  Queue a new chat on the server (`server_key`) from the authenticated user. In game, the chat will appear as a "Server" chat with the user's default minecraft username in angle brackets (much like a normal chat):
  ::
  
      [Server] <gumptionthomas> Hello world...

  If the API user does not have an associated minecraft username, the user's nickname or email will be used instead:
  ::
  
      [Server] <t@gmail.com> Hello world...

  :arg server_key: The target server's key. (*required*)

  :formparam chat: The chat text.

  :status 202 Accepted: Successfully queued the chat. It will be sent to the agent on the next ping.

  **Example request**:

  .. sourcecode:: http

    POST /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/chats HTTP/1.1

  .. sourcecode:: http

    chat=Hello+world...

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 202 Accepted
    Content-Type: application/json

.. http:get:: /api/v1/servers/(server_key)/chats/(key)

  Get the information for the chat (`key`).

  :arg server_key: The target server's key. (*required*)
  :arg key: The requested chat's log line key. (*required*)

  :status 200 OK: Successfully read the chat.

    :Response Data: See :ref:`Chat response data <chat_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/chats/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nDA HTTP/1.1

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
      "chat": "hey guys",
      "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
      "line": "2013-04-19 10:32:55 [INFO] [Server] <gumptionthomas> hey guys"
    }

.. http:get:: /api/v1/servers/(server_key)/players/(key_username)/chats

  Get a :ref:`list <list>` of a player's (`key_username`) minecraft chats on the server (`server_key`) ordered by descending timestamp.

  :arg server_key: The target server's key. (*required*)
  :arg key_username: The requested player's key or minecraft username. (*required*)

  :query q: A search string to limit the chat results to.
  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return log lines with a timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return log lines with a timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

  :status 200 OK: Successfully queried the chats.
  
    :Response Data:
  
      - **chats** -- The list of the player's chats.
      - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **chats** is an object of chat information. See :ref:`Chat response data <chat_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/players/gumptionthomas/chats HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "chats": [
        {
          "username": "gumptionthomas",
          "updated": "2013-04-19 10:33:56 CDT-0500",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nXV",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "timestamp": "2013-04-19 10:33:55 CDT-0500",
          "created": "2013-04-19 10:33:56 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "chat": "what's up?",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-04-19 10:33:55 [INFO] <gumptionthomas> what's up?"
        },
        {
          "username": "gumptionthomas",
          "updated": "2013-04-19 10:32:56 CDT-0500",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIoCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSB0xvZ0xpbmUY674nDA",
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
          "timestamp": "2013-04-19 10:32:55 CDT-0500",
          "created": "2013-04-19 10:32:56 CDT-0500",
          "player_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIzCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSBlBsYXllciIOZ3VtcHRpb250aG9tYXMM",
          "chat": "hey guys",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "line": "2013-04-19 10:32:55 [INFO] [Server] <gumptionthomas> hey guys"
        }
      ]
    }

.. http:post:: /api/v1/servers/(server_key)/players/(key_username)/chats

  Queue a new chat on the server (`server_key`) for the player (`key_username`) from the authenticated user. In game, the chat will appear as a "Server" chat with the username in angle brackets (much like a normal chat):
  ::
  
      [Server] <gumptionthomas> Hello world...

  :arg server_key: The target server's key. (*required*)
  :arg key_username: The requested player's key or minecraft username. (*required*)

  :formparam chat: The chat text.

  :status 202 Accepted: Successfully queued the chat. It will be sent to the agent on the next ping.

  :status 403 Forbidden: The authenticated user has not claimed the requested player's username.

  **Example request**:

  .. sourcecode:: http

    POST /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/players/gumptionthomas/chats HTTP/1.1

  .. sourcecode:: http

    chat=Hello+world...

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 202 Accepted
    Content-Type: application/json


