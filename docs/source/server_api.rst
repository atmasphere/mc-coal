=======
Servers
=======
.. http:get:: /api/v1/servers

  Get a :ref:`list <list>` of all servers ordered by created timestamp.

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.

  :status 200 OK: Successfully queried the servers.

    :Response Data: - **servers** -- The list of servers.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **servers** is a dictionary of server information.

    .. _server_response_data:

    :Response Data: - **key** -- The server key.
                    - **name** -- The server name.
                    - **version** -- The minecraft server version.
                    - **status** -- A string indicating the status of the minecraft server. Possible values are ``RUNNING``, ``STOPPED``, ``QUEUED``, or ``UNKNOWN`.
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
          "name": "My World"
          "last_ping": "2013-04-14 19:55:22 CDT-0500",
          "version": "1.5.1",
          "updated": "2013-04-14 19:55:22 CDT-0500",
          "status": "RUNNING",
          "created": "2013-03-04 15:05:53 CST-0600"
          "server_day": 15744
          "server_time": 19767
          "is_raining": true,
          "is_thundering": true
        },
        {
          "key": "IZCxIGQ2xpZW50Ig1tYy1jb2FsLWFnZW50DA",
          "name": "My PVP World"
          "last_ping": "2013-04-14 19:55:43 CDT-0500",
          "version": "1.5.1",
          "updated": "2013-04-14 19:55:43 CDT-0500",
          "status": "STOPPED",
          "created": "2013-03-04 15:07:00 CST-0600"
          "server_day": 15223
          "server_time": 14141
          "is_raining": fale,
          "is_thundering": false
        }
      ]
    }


.. http:get:: /api/v1/servers/(key)

  Get the information for the server (`key`).

  :arg key: The requested server's key. (*required*)

  :status 200 OK: Successfully read the server.

    :Response Data: See :ref:`Server response data <server_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH",
      "name": "My World"
      "last_ping": "2013-04-14 19:55:22 CDT-0500",
      "version": "1.5.1",
      "updated": "2013-04-14 19:55:22 CDT-0500",
      "status": "RUNNING",
      "created": "2013-03-04 15:05:53 CST-0600"
      "server_day": 15744
      "server_time": 19767
      "is_raining": true,
      "is_thundering": true
    }


