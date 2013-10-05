===========
Screenshots
===========
.. http:get:: /api/v1/servers/(server_key)/screenshots

  Get a :ref:`list <list>` of all screenshots on the server (`server_key`) ordered by descending create timestamp.

  :arg server_key: The target server's key. (*required*)

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return screenshots with a create timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return screenshots with a create timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

  :status 200 OK: Successfully queried the screenshot.

    :Response Data: - **screenshots** -- The list of screenshots.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **screenshots** is a dictionary of screenshot information.

    .. _screenshot_response_data:

    :Screenshot: - **key** -- The screenshot key.
                 - **server_key** -- The screenshot's server key.
                 - **user_key** -- The user's key that uploaded the screenshot.
                 - **random_id** -- A random float attached to the screenshot at creation time.
                 - **original_url** -- The URL of the original screenshot.
                 - **blurred_url** -- The URL of the blurred version of the screenshot. ``null`` if the blurred version isn't ready.
                 - **created** -- The creation timestamp.
                 - **updated** -- The updated timestamp.

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/screenshots HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "screenshots": [
        {
          "updated": "2013-04-13 11:12:20 CDT-0500",
          "created": "2013-04-13 11:12:05 CDT-0500",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchiBfQw",
          "original_url": "http://lh5.ggpht.com/AMWDO-e5cK153ejlWn0ExDv1DuUACRpyM0kYEgAJKqTjs8a65v055NapS9EFwzMNwijA290_ABNgnDdi5WI2UCycKOnrLkHw9A",
          "random_id": 0.23893109322623773,
          "blurred_url": "http://lh4.ggpht.com/j8qNAEjoxIubBdRNZgjj629-2vjFOzWfSgkGPOmvR8VHiIBYTLjlrHfDMmu2-_tm1-6T86eokuXxqugWSDyx-IZjQtFQMCrs3A",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIrCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSClNjcmVlblNob3QYxrQgDA"
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH"
        },
        {
          "updated": "2013-04-07 01:52:11 CDT-0500",
          "created": "2013-04-07 01:50:57 CDT-0500",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "original_url": "http://lh3.ggpht.com/IFQVCSjpctTvNkJQhqj-j7anoaApZmawMe-Qy1LVqV2GKS9k_AkyaG0I8z-Ri2gDQFIxRL3NanEonqX4LK2mfjEpRUPvj7RKwA",
          "random_id": 0.6780209099707669,
          "blurred_url": "http://lh6.ggpht.com/x0BKS8tbI88RRkhUX6vJ7MmzjhBaZShbKf51Th5oghUYtezZbD94SHu4nYQjYQhoAyJVcgThprqvZSmKE1M5uqf5JQLu0miL",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIrCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSClNjcmVlblNob3QYyPkWDA"
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH"
        }
      ]
    }

.. http:get:: /api/v1/servers/(server_key)/screenshots/(key)

  Get the information for the screenshot (`key`).

  :arg server_key: The target server's key. (*required*)
  :arg key: The requested screenshot's key. (*required*)

  :status 200 OK: Successfully read the screenshot.

    :Response Data: See :ref:`Screenshot response data <screenshot_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/screenshots/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIrCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSClNjcmVlblNob3QYyPkWDA HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "updated": "2013-04-07 01:52:11 CDT-0500",
      "created": "2013-04-07 01:50:57 CDT-0500",
      "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
      "original_url": "http://lh3.ggpht.com/IFQVCSjpctTvNkJQhqj-j7anoaApZmawMe-Qy1LVqV2GKS9k_AkyaG0I8z-Ri2gDQFIxRL3NanEonqX4LK2mfjEpRUPvj7RKwA",
      "random_id": 0.6780209099707669,
      "blurred_url": "http://lh6.ggpht.com/x0BKS8tbI88RRkhUX6vJ7MmzjhBaZShbKf51Th5oghUYtezZbD94SHu4nYQjYQhoAyJVcgThprqvZSmKE1M5uqf5JQLu0miL",
      "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIrCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSClNjcmVlblNob3QYyPkWDA"
      "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH"
    }

.. http:get:: /api/v1/servers/(server_key)/users/(key)/screenshots

  Get a :ref:`list <list>` of a user (`key`) uploaded screenshots on the server (`server_key`) ordered by descending create timestamp.

  :arg server_key: The target server's key. (*required*)
  :arg key: The requested user's key. (*required*) To reference the authenticated user, use ``self``.

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.
  :query since: Return log lines with a create timestamp since the given datetime (inclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.
  :query before: Return log lines with a create timestamp before this datetime (exclusive). This parameter should be of the form ``YYYY-MM-DD HH:MM:SS`` and is assumed to be UTC.

  :status 200 OK: Successfully queried the screenshots.

    :Response Data: - **screenshots** -- The list of the user's uploaded screenshots.
                    - **cursor** -- If more results are available, this value will be the string to be passed back into this resource to query the next set of results. If no more results are available, this field will be absent.

    Each entry in **screenshots** is a dictionary of the user's uploaded screenshot information. See :ref:`Screen shot response data <screenshot_response_data>`

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/users/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw/screenshots HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "screenshots": [
        {
          "updated": "2013-04-07 01:52:11 CDT-0500",
          "created": "2013-04-07 01:50:57 CDT-0500",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "original_url": "http://lh3.ggpht.com/IFQVCSjpctTvNkJQhqj-j7anoaApZmawMe-Qy1LVqV2GKS9k_AkyaG0I8z-Ri2gDQFIxRL3NanEonqX4LK2mfjEpRUPvj7RKwA",
          "random_id": 0.6780209099707669,
          "blurred_url": "http://lh6.ggpht.com/x0BKS8tbI88RRkhUX6vJ7MmzjhBaZShbKf51Th5oghUYtezZbD94SHu4nYQjYQhoAyJVcgThprqvZSmKE1M5uqf5JQLu0miL",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIrCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSClNjcmVlblNob3QYyPkWDA"
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH"
        },
        {
          "updated": "2013-03-25 18:39:36 CDT-0500",
          "created": "2013-03-25 18:39:22 CDT-0500",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "original_url": "http://lh6.ggpht.com/TFqVUT4hZwgz0sImwFMI9J7rJ-AXCqwM9-K5s66v9UnXy_iwPBpBEpzASVKla6xf6mnO486085NtzZOP1qrROPpkrxdw1D30-A",
          "random_id": 0.07680268292837988,
          "blurred_url": "http://lh5.ggpht.com/B-pQmMTlp6vZ7ke48-19e7YdUclpRUE30y4L_DS45a9dUt9QjJIiniONIKB_-P80RL54YM0Qk4-zqHB9SEpEG52Wlkfjkak",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIrCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSClNjcmVlblNob3QY8MAPDA"
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH"
        }
      ]
    }

  **Example request**:

  .. sourcecode:: http

    GET /api/v1/servers/ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH/users/self/screenshots HTTP/1.1

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "screenshots": [
        {
          "updated": "2013-04-07 01:52:11 CDT-0500",
          "created": "2013-04-07 01:50:57 CDT-0500",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "original_url": "http://lh3.ggpht.com/IFQVCSjpctTvNkJQhqj-j7anoaApZmawMe-Qy1LVqV2GKS9k_AkyaG0I8z-Ri2gDQFIxRL3NanEonqX4LK2mfjEpRUPvj7RKwA",
          "random_id": 0.6780209099707669,
          "blurred_url": "http://lh6.ggpht.com/x0BKS8tbI88RRkhUX6vJ7MmzjhBaZShbKf51Th5oghUYtezZbD94SHu4nYQjYQhoAyJVcgThprqvZSmKE1M5uqf5JQLu0miL",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIrCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSClNjcmVlblNob3QYyPkWDA"
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH"
        },
        {
          "updated": "2013-03-25 18:39:36 CDT-0500",
          "created": "2013-03-25 18:39:22 CDT-0500",
          "user_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHILCxIEVXNlchivbgw",
          "original_url": "http://lh6.ggpht.com/TFqVUT4hZwgz0sImwFMI9J7rJ-AXCqwM9-K5s66v9UnXy_iwPBpBEpzASVKla6xf6mnO486085NtzZOP1qrROPpkrxdw1D30-A",
          "random_id": 0.07680268292837988,
          "blurred_url": "http://lh5.ggpht.com/B-pQmMTlp6vZ7ke48-19e7YdUclpRUE30y4L_DS45a9dUt9QjJIiniONIKB_-P80RL54YM0Qk4-zqHB9SEpEG52Wlkfjkak",
          "key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdHIrCxIGU2VydmVyIg1nbG9iYWxfc2VydmVyDAsSClNjcmVlblNob3QY8MAPDA"
          "server_key": "ahRzfmd1bXB0aW9uLW1pbmVjcmFmdH"
        }
      ]
    }
