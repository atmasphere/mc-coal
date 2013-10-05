=====
Users
=====
.. http:get:: /api/v1/users

  Get a :ref:`list <list>` of all users ordered by created timestamp.

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.

  :status 200 OK: Successfully queried the users.

    :Response Data: - **users** -- The list of users.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **users** is a dictionary of user information.

    .. _user_response_data:

    :User: - **key** -- The user key.
           - **usernames** -- The user's minecraft usernames. Empty list if the user has not claimed a minecraft username.
           - **email** -- The user's email.
           - **nickname** -- The user's nickname.
           - **active** -- A boolean indicating whether the user is active.
           - **admin** -- A boolean indicating whether the user is an admin.
           - **last_coal_login** -- The timestamp of the user's last COAL login.
           - **created** -- The user's creation timestamp.
           - **updated** -- The user's updated timestamp.

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/users HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "users": [
        {
          "usernames": ["gumptionthomas"],
          "updated": "2013-04-14 18:37:35 CDT-0500",
          "created": "2013-03-04 15:05:52 CST-0600",
          "admin": true,
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "active": true,
          "last_coal_login": "2013-04-13 14:03:33 CDT-0500",
          "nickname": "thomas",
          "email": "t@gmail.com"
        },
        {
          "usernames": "[]",
          "updated": "2013-03-14 17:23:09 CDT-0500",
          "created": "2013-03-04 17:43:37 CST-0600",
          "admin": false,
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchiZdQw",
          "active": true,
          "last_coal_login": null,
          "nickname": "jennifer",
          "email": "j@gmail.com"
        },
        {
          "usernames": ["quazifene"],
          "updated": "2013-04-14 18:56:59 CDT-0500",
          "created": "2013-03-04 17:53:12 CST-0600",
          "admin": true,
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchiBfQw",
          "active": true,
          "last_coal_login": "2013-04-12 14:04:39 CDT-0500",
          "nickname": "mark",
          "email": "m@gmail.com"
        }
      ]
    }

.. http:get:: /api/v1/users/(key)

  Get the information for the user (`key`).

  :arg key: The requested user's key. (*required*) To reference the authenticated user, use ``self``.

  :status 200 OK: Successfully read the user.

    :Response Data: See :ref:`User response data <user_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/users/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "username": ["gumptionthomas"],
      "updated": "2013-04-14 18:37:35 CDT-0500",
      "created": "2013-03-04 15:05:52 CST-0600",
      "admin": true,
      "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
      "active": true,
      "last_coal_login": "2013-04-13 14:03:33 CDT-0500",
      "nickname": "thomas",
      "email": "t@gmail.com"
    }

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/users/self HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "username": ["gumptionthomas"],
      "updated": "2013-04-14 18:37:35 CDT-0500",
      "created": "2013-03-04 15:05:52 CST-0600",
      "admin": true,
      "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
      "active": true,
      "last_coal_login": "2013-04-13 14:03:33 CDT-0500",
      "nickname": "thomas",
      "email": "t@gmail.com"
    }
