======
Common
======

.. _secured_resources:

-----------------
Secured Resources
-----------------

Clients making calls to the API on behalf of a user require a bearer access token which can be acquired via a simple :ref:`authorization <authorization>` flow.

.. http:get:: /api/v1/(resource)

  :requestheader Authorization: An :ref:`access token <access_token>` using the "Bearer" scheme as specified in `RFC6750: Authorization Request Header Field <http://tools.ietf.org/html/rfc6750#section-2.1>`_. The user that granted authorization for the access token will be considered the "authenticated user" for resources that expect one.

  :status 401 Unauthorized: Invalid or no ``Authorization`` request header provided.
  :status 403 Forbidden: The authorization was not granted by an active user.

  **Example**:

  .. sourcecode:: http

    GET /api/v1/(resource) HTTP/1.1
    Authorization: Bearer 8wB8QtpULBVNuL2mqBaWdIRWX30qKtIK3E5QbOWP

.. http:post:: /api/v1/(resource)

  :requestheader Authorization: An :ref:`access token <access_token>` using the "Bearer" scheme as specified in `RFC6750: Authorization Request Header Field <http://tools.ietf.org/html/rfc6750#section-2.1>`_. The user that granted authorization for the access token will be considered the "authenticated user" for resources that expect one.

  :status 401 Unauthorized: Invalid or no ``Authorization`` request header provided.
  :status 403 Forbidden: The authorization was not granted by an active user.

  **Example**:

  .. sourcecode:: http

    POST /api/v1/(resource) HTTP/1.1
    Authorization: Bearer 8wB8QtpULBVNuL2mqBaWdIRWX30qKtIK3E5QbOWP


------------
Status Codes
------------

- :http:statuscode:`200`

  The body will be a JSON dictionary whose contents are resource specific:

  .. sourcecode:: javascript

    {
      "key1": value1,
      "key2": value2,
      ...
    }

- :http:statuscode:`201`

  The body will be a JSON dictionary whose contents are resource specific:

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

  The ``errors`` string is resource and error specific.

- :http:statuscode:`403` -- The body will be empty.
- :http:statuscode:`404` -- The body will be empty.
- :http:statuscode:`405` -- The body will be empty.

- :http:statuscode:`500`

  The body will be a JSON dictionary of the form:

  .. sourcecode:: javascript

    {
      "errors": "This request failed because..."
    }

  The ``errors`` string is resource and error specific.

----------
Timestamps
----------

  Unless otherwise specified, all timestamps are of the form ``%Y-%m-%d %H:%M:%S %Z-%z`` (see `Python strftime formatting <http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior>`_) and returned as UTC unless otherwise noted.

  **Example timestamp**:

  .. sourcecode:: http

    "2013-04-14 19:55:22 UTC-0000"

.. _list:

--------------
List Resources
--------------
Some resources return a list of results that can span requests. These resources all take a common set of query parameters and return a common set of response data to help iterate through large lists of data.

.. http:get:: /api/v1/(list_resource)

  :query size: The number of results to return per call (Default: 10. Maximum: 50).
  :query cursor: The cursor string signifying where to start the results.

  :status 200 OK: Successfully called the *list_resource*.

    :Response Data:
      - **cursor** -- If more results are available, this root level response value will be the next cursor string to be passed back into this resource to grab the next set of results. If no more results are available, this field will be absent.

  **Example first request**:

  .. sourcecode:: http

    GET /api/v1/(list_resource)?size=5 HTTP/1.1

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

    GET /api/v1/(list_resource)?size=5&cursor=hsajkhasjkdy8y3h3h8fhih38djhdjdj HTTP/1.1

  **Example second response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "results": ["result6", "result7", "result8"]
    }
