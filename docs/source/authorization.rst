.. _authorization:

*************
Authorization
*************

Clients making calls to the :ref:`API <api>` on behalf of a user require an :ref:`access token <access_token>` which can be acquired via the following (simplified) `OAuth 2.0 <http://tools.ietf.org/html/draft-ietf-oauth-v2-31>`_ flow.

1. :ref:`Register <client_regististration>` the client via :http:post:`/oauth/v1/register` and record the :ref:`client configuration <client_configuration>` contained in the response. These :ref:`client configuration <client_configuration>` values should be kept secure.
2. :ref:`Redirect <authorization_code>` the user's browser to :http:get:`/oauth/v1/auth` with the required :ref:`client configuration <client_configuration>` values in the query parameters, including a ``redirect_uri``. If the user grants the authorization to the client, the user's browser will be redirected to the ``redirect_uri`` with an :ref:`authorization code <authorization_code>`.
3. :ref:`Request <access_token>` :http:post:`/oauth/v1/token` with the :ref:`authorization code <authorization_code>` plus other :ref:`client configuration <client_configuration>` values and record the :ref:`access token <access_token>` and :ref:`refresh token <refresh_token>` contained in the response.
4. :ref:`Refresh <refresh_token>` the :ref:`access token <access_token>` if it expires or otherwise becomes invalid using the :ref:`refresh token <refresh_token>`.


.. _client_regististration:

===================
Client Registration
===================

Clients `register <http://tools.ietf.org/html/draft-ietf-oauth-dyn-reg-14#section-3>`_ with the API using an `open registration lifecycle <http://tools.ietf.org/html/draft-ietf-oauth-dyn-reg-14#appendix-B.1>`_.

.. _client_configuration:

Most client registration and configuration endpoints (:http:post:`/oauth/v1/register`, :http:get:`/oauth/v1/clients/(client_id)`, and :http:put:`/oauth/v1/clients/(client_id)`) return an ``application/json`` response body that is an object with the client configuration as top-level members:

  :Client Configuration:
    - **client_id** -- The client id.
    - **redirect_uris** -- A list of redirect URIs (strings) for use in other oauth flows. Specifically, one of these URIs must always be used whenever a ``redirect_uri`` is required.
    - **scope** -- A space separated list of scope values that the client can use when requesting access tokens.
    - **client_secret** -- The client secret for use in other oauth flows.
    - **client_secret_expires_at** -- Time at which the ``client_secret`` will expire or 0 if it will not expire. The time is represented as the number of seconds from ``1970-01-01T0:0:0Z`` as measured in UTC until the date/time.
    - **registration_access_token** -- The access token that is used at the client configuration endpoint to perform subsequent operations upon the client registration through the client configuration enpdoints (:http:get:`/oauth/v1/clients/(client_id)`, :http:put:`/oauth/v1/clients/(client_id)`, and :http:delete:`/oauth/v1/clients/(client_id)`).
    - **registration_client_uri** -- The fully qualified URL of the client configuration endpoint for this client.  The client MUST use this URL as given when communicating with the client configuration endpoint.
    - **client_name** -- (*optional*) -- The human-readable name of the client to be presented to the user.
    - **client_uri** -- (*optional*) -- The URL of the homepage of the client.
    - **logo_uri** -- (*optional*) -- The URL that references a logo for the client.


.. http:post:: /oauth/v1/register

  :json string_array redirect_uris: An array of redirect URIs for use in other oauth flows.
  :json string client_id: (*optional*) -- A requested client id. If a client is already registered with the same client id, a unique client id based on the requested one will be created instead. If this parameter is omitted, a completely random client id will be created.
  :json string client_name: (*optional*) -- The human-readable name of the client to be presented to the user.
  :json string client_uri: (*optional*) -- The URL of the homepage of the client.
  :json string logo_uri: (*optional*) -- The URL that references a logo for the client.
  :json string scope: (*optional*) -- A space separated list of scope values that the client can use when requesting access tokens. Currently, the only valid value is ``"data"``.

  :status 201 Created: Successfully created a new client. The ``application/json`` response body will be an object with the :ref:`client configuration <client_configuration>` as top-level members.

  :status 400 Bad Request: The ``application/json`` response body will be an object with the error information as top-level members:

    :Response Data:
      - **error** -- The error. Possible values are ``invalid_request`` and ``server_error``.

  **Example request**:

  .. sourcecode:: http

    POST /oauth/v1/register HTTP/1.1

  .. sourcecode:: javascript

    {
      "redirect_uris": ["http://example.com/callback"],
      "client_id": "my_example_app",
      "client_name": "My Example Application",
      "client_uri": "http://example.com",
      "logo_uri": "http://example.com/logo.png",
      "scope": "data"
    }

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 201 Created
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "client_id": "my_example_app",
      "redirect_uris": ["http://example.com/callback"],
      "scope": "data",
      "client_secret": "bdv8HtrspbJh5F5KOlAUkDOl8KAyYcfsDQoTk1au",
      "client_secret_expires_at": 0,
      "registration_access_token": "VlhLNF2vifRsppohNr7gBcbcOO5khEqADalHlPYE",
      "registration_client_uri": "https://my-coal.org/oauth/v1/clients/my_example_app",
      "client_name": "My Example Application",
      "client_uri": "http://example.com",
      "logo_uri": "http://example.com/logo.png"
    }

====================
Client Configuration
====================

The client configuration endpoint is a protected resource that is provisioned by the server to facilitate viewing, updating, and deleting a client's registered information. If a client ever forgets its :ref:`client configuration <client_configuration>` values, they can be retreived via :http:get:`/oauth/v1/clients/(client_id)` as long as the client knows its ``registration_client_uri`` and ``registration_access_token``.

The location of this endpoint is communicated to the client through the ``registration_client_uri`` member of the :http:post:`/oauth/v1/register` response. Authorization for this endpoint requires that the client's ``registration_access_token`` be set in the request ``Authorization`` header field using the "Bearer" scheme as specified in `RFC6750: Authorization Request Header Field <http://tools.ietf.org/html/rfc6750#section-2.1>`_.


.. http:get:: /oauth/v1/clients/(client_id)

  Read the current configuration of the client (`client_id`).

  :reqheader Authorization: The client's ``registration_access_token`` using the "Bearer" scheme as specified in `RFC6750: Authorization Request Header Field <http://tools.ietf.org/html/rfc6750#section-2.1>`_.
  :resheader WWW-Authenticate: If there is a problem with authorization, the value will be ``Bearer error="invalid_token"`` as specified in `RFC6750: WWW-Authenticate Response Header Field <http://tools.ietf.org/html/rfc6750#section-3>`_.

  :status 200 OK: Successfully returned the client configuration. The ``application/json`` response body will be an object with the :ref:`client configuration <client_configuration>` as top-level members. Some of these values, including the ``client_secret``, ``client_secret_expires_at``, and ``registration_access_token``, may be different from those in the initial :http:post:`/oauth/v1/register` response.  If there is a new client secret and/or registration access token in the response, the client must immediately discard its previous client secret and/or registration access token.  The value of the ``client_id`` will not change from the initial :http:post:`/oauth/v1/register` response.

  :status 401 Unauthorized: Invalid or no ``Authorization`` request header provided. The ``WWW-Authenticate`` response header will contain the error.

  **Example request**:

  .. sourcecode:: http

    GET /oauth/v1/clients/my_example_app HTTP/1.1
    Authorization: Bearer VlhLNF2vifRsppohNr7gBcbcOO5khEqADalHlPYE

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "client_id": "my_example_app",
      "redirect_uris": ["http://example.com/callback"],
      "scope": "data",
      "client_secret": "bdv8HtrspbJh5F5KOlAUkDOl8KAyYcfsDQoTk1au",
      "client_secret_expires_at": 0,
      "registration_access_token": "VlhLNF2vifRsppohNr7gBcbcOO5khEqADalHlPYE",
      "registration_client_uri": "https://my-coal.org/oauth/v1/clients/my_example_app",
      "client_name": "My Example Application",
      "client_uri": "http://example.com",
      "logo_uri": "http://example.com/logo.png"
    }


.. http:put:: /oauth/v1/clients/(client_id)

  Update the configuration of the client (`client_id`).

  :reqheader Authorization: The client's ``registration_access_token`` using the "Bearer" scheme as specified in `RFC6750: Authorization Request Header Field <http://tools.ietf.org/html/rfc6750#section-2.1>`_.
  :resheader WWW-Authenticate: If there is a problem with authorization, the value will be ``Bearer error="invalid_token"`` as specified in `RFC6750: WWW-Authenticate Response Header Field <http://tools.ietf.org/html/rfc6750#section-3>`_.

  :json string client_id: The client id. If not correct, a :http:statuscode:`400` ``invalid_client_id`` response will result.
  :json string_array redirect_uris: The new client redirect URIs.
  :json string client_secret: The client secret. If this value does not match the current client secret, a :http:statuscode:`400` ``invalid_request`` response will result.
  :json string scope: (*optional*) -- A space separated list of scope values. If there are new values that are not part of the current scope, a :http:statuscode:`400` ``invalid_request`` response will result. Note that this means a client can remove scope values, but can never add them. If not present, the client scope will be unmodified.
  :json string client_name: (*optional*) -- The new human-readable name of the client. If not present, the client name will be set to ``null``.
  :json string client_uri: (*optional*) -- The new URL of the homepage of the client. If not present, the homepage URL will be set to ``null``.
  :json string logo_uri: (*optional*) -- The new URL that references a logo for the client. If not present, the logo URL will be set to ``null``.

  :status 200 OK: Successfully updated the client configuration. The ``application/json`` response body will be an object with the new :ref:`client configuration <client_configuration>` as top-level members. Some of these values, including the ``client_secret``, ``client_secret_expires_at``, and ``registration_access_token``, may be different from those in the initial :http:post:`/oauth/v1/register` response.  If there is a new client secret and/or registration access token in the response, the client must immediately discard its previous client secret and/or registration access token.  The value of the ``client_id`` will not change from the initial :http:post:`/oauth/v1/register` response.

  :status 400 Bad Request: The ``application/json`` response body will be an object with the error information as top-level members:

    :Response Data:
      - **error** -- The error. Possible values are ``invalid_request``, ``invalid_client_id``, and ``server_error``.

  :status 401 Unauthorized: Invalid or no ``Authorization`` request header provided. The ``WWW-Authenticate`` response header may be set and contain the error.

  **Example request**:

  .. sourcecode:: http

    PUT /oauth/v1/clients/my_example_app HTTP/1.1
    Authorization: Bearer VlhLNF2vifRsppohNr7gBcbcOO5khEqADalHlPYE

  .. sourcecode:: javascript

    {
      "client_id": "my_example_app",
      "redirect_uris": ["http://example.com/v2/callback"],
      "client_secret": "bdv8HtrspbJh5F5KOlAUkDOl8KAyYcfsDQoTk1au",
      "scope": "data",
      "client_name": "My Example Application v2",
      "client_uri": "http://example.com/v2",
      "logo_uri": "http://example.com/logo_v2.png",
    }

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "client_id": "my_example_app",
      "redirect_uris": ["http://example.com/v2/callback"],
      "scope": "data",
      "client_secret": "bdv8HtrspbJh5F5KOlAUkDOl8KAyYcfsDQoTk1au",
      "client_secret_expires_at": 0,
      "registration_access_token": "VlhLNF2vifRsppohNr7gBcbcOO5khEqADalHlPYE",
      "registration_client_uri": "https://my-coal.org/oauth/v1/clients/my_example_app",
      "client_name": "My Example Application v2",
      "client_uri": "http://example.com/v2",
      "logo_uri": "http://example.com/logo_v2.png"
    }

.. http:delete:: /oauth/v1/clients/(client_id)

  Remove the client and all grants and tokens associated with it (`client_id`).

  :reqheader Authorization: The client's ``registration_access_token`` using the "Bearer" scheme as specified in `RFC6750: Authorization Request Header Field <http://tools.ietf.org/html/rfc6750#section-2.1>`_.
  :resheader WWW-Authenticate: If there is a problem with authorization, the value will be ``Bearer error="invalid_token"`` as specified in `RFC6750: WWW-Authenticate Response Header Field <http://tools.ietf.org/html/rfc6750#section-3>`_.

  :status 204 No Content: Successfully deprovisioned the client.

  :status 401 Unauthorized: Invalid or no ``Authorization`` request header provided. The ``WWW-Authenticate`` response header may be set and contain the error.

  **Example request**:

  .. sourcecode:: http

    DELETE /oauth/v1/clients/my_example_app HTTP/1.1
    Authorization: Bearer VlhLNF2vifRsppohNr7gBcbcOO5khEqADalHlPYE

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 204 No Content


.. _authorization_code:

==================
Authorization Code
==================

Clients are granted a unique, one-time-use authorization code in response to an explicit, web-based authorization grant from a logged-in user.

.. http:get:: /oauth/v1/auth

  A user-facing web UI to prompt the user to grant or deny OAuth access for a client.

  :query client_id: The client id to authorize.
  :query redirect_uri: The fully qualified URL that the user's browser will redirect to with the access code or error. This must be one of the URIs in the client's configuration ``redirect_uris``.
  :query response_type: This should always be ``code`` when requesting an access code.
  :query scope: The scope for the authorization code request. Must always be ``data``.

  :status 302 Found: If the user grants authorization, the user's browser will redirect to the ``redirect_uri`` with the authorization code passed via the ``code`` query parameter.
  :status 302 Found: If the user denys authorization or an error occurs, the user's browser will redirect to the ``redirect_uri`` with the error passed via the ``error`` query parameter.

  **Example (user browser) request**:

  .. sourcecode:: http

    GET /oauth/v1/auth?client_id=my_example_app&redirect_uri=http://example.com/callback&response_type=code&scope=data HTTP/1.1

  **Example (user browser) response**:

    .. image:: images/grant_auth.png

    If the user grants authorization to the client, a :http:statuscode:`302` response is returned to the user's browser. The ``Location`` header in the response is set to the ``redirect_uri`` with the ``code`` query parameter set to the authorization code:

    .. sourcecode:: http

      HTTP/1.1 302 Found
      Location: http://example.com/callback?code=YEhb6FWOcPgnTUWtHwPcgBEojQjhU619YfshnqVd

    If the user denys authorization to the client, a :http:statuscode:`302` response is returned to the user's browser. The ``Location`` header in the response is set to the ``redirect_uri`` with the ``error`` query parameter set:

    .. sourcecode:: http

      HTTP/1.1 302 Found
      Location: http://example.com/callback?error=access_denied


.. _access_token:

============
Access Token
============

Clients use an :ref:`authorization code <authorization_code>` to acquire an :ref:`access token <access_token>` and a :ref:`refresh token <refresh_token>`. These tokens are unique and tied to both the client and the user that granted the authorization code. Authorization for :ref:`secured Data APIs <secured_resources>` requires that a valid access token be set in the request ``Authorization`` header field using the "Bearer" scheme as specified in `RFC6750: Authorization Request Header Field <http://tools.ietf.org/html/rfc6750#section-2.1>`_.

.. http:post:: /oauth/v1/token

  The client acquires tokens by making a request to the token endpoint, posting the following parameters in the request body using the ``application/x-www-form-urlencoded`` or ``application/json`` formats with a character encoding of ``UTF-8``.

  :formparam client_id: The client id.
  :formparam client_secret: The current client secret.
  :formparam grant_type: Should be ``authorization_code`` to convert an autorization code into an access token.
  :formparam code: The authorization code.
  :formparam redirect_uri: The fully qualified redirect URL. This must be one of the URIs in the client's configuration ``redirect_uris``.
  :formparam scope: The scope for the access token. Must always be ``data``.

  :status 200 OK: Successfully converted the authorization code into access and refresh tokens. The ``application/json`` response body will be an object with the token information as top-level members:

    :Response Data:
      - **access_token** -- The access token.
      - **refresh_token** -- The refresh token.
      - **expires_in** -- The lifetime in seconds of the access token.
      - **token_type** -- Will always be ``Bearer``

  :status 400 Bad Request: The ``application/json`` response body will be an object with the error information as top-level members:

    :Response Data:

      - **error** -- The error. Possible values are:

        - ``invalid_request`` -- Missing parameters.
        - ``unsupported_grant_type`` -- Incorrect grant type.
        - ``invalid_grant`` -- Incorrect access code or redirect URI.
        - ``invalid_client`` -- Incorrect client id or client secret.
        - ``invalid_scope`` -- Incorrect scope.
        - ``server_error`` -- Generic server error.

  **Example request**

  .. sourcecode:: http

    POST /oauth/v1/token HTTP/1.1
    Content-Type: application/x-www-form-urlencoded

    client_id=my_example_app&
    client_secret=bdv8HtrspbJh5F5KOlAUkDOl8KAyYcfsDQoTk1au&
    grant_type=authorization_code&
    code=YEhb6FWOcPgnTUWtHwPcgBEojQjhU619YfshnqVd&
    redirect_uri=http%3A%2F%2Fexample.com%2Fcallback&
    scope=data

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
        "access_token": "wIt7U1cpa5B4Rqbbvie6Mye1sWiwAjZ7H7kAXIjK",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "PuFZ2Hyu6R6eIAxVG9Y4j4kFRYsCapISTR0n3AUM"
    }


.. _refresh_token:

=============
Refresh Token
=============

When an access token expires, or otherwise becomes invalid, a one-time-use refresh token can be used to generate a new set of tokens (access and refresh).

.. http:post:: /oauth/v1/token

  The client acquires tokens by making a request to the token endpoint, posting the following parameters in the request body using the ``application/x-www-form-urlencoded`` or ``application/json`` formats with a character encoding of ``UTF-8``.

  :formparam client_id: The client id.
  :formparam client_secret: The current client secret.
  :formparam grant_type: Should be ``refresh_token`` to generate a new set of tokens.
  :formparam refresh_token: The refresh token.
  :formparam scope: The scope for the access token. Must always be ``data``.

  :status 200 OK: Successfully generated a new set of access and refresh tokens. The ``application/json`` response body will be an object with the token information as top-level members:

    :Response Data:
      - **access_token** -- The access token.
      - **refresh_token** -- The refresh token.
      - **expires_in** -- The lifetime in seconds of the access token.
      - **token_type** -- Will always be ``Bearer``

  :status 400 Bad Request: The ``application/json`` response body will be an object with the error information as top-level members:

    :Response Data:

      - **error** -- The error. Possible values are:

        - ``invalid_request`` -- Missing parameters.
        - ``unsupported_grant_type`` -- Incorrect grant type.
        - ``invalid_grant`` -- Incorrect refresh token.
        - ``invalid_client`` -- Incorrect client id or client secret.
        - ``invalid_scope`` -- Incorrect scope.
        - ``server_error`` -- Generic server error.

  **Example request**

  .. sourcecode:: http

    POST /oauth/v1/token HTTP/1.1
    Content-Type: application/x-www-form-urlencoded

    client_id=my_example_app&
    client_secret=bdv8HtrspbJh5F5KOlAUkDOl8KAyYcfsDQoTk1au&
    grant_type=refresh_token&
    refresh_token=PuFZ2Hyu6R6eIAxVG9Y4j4kFRYsCapISTR0n3AUM&
    scope=data

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
        "access_token": "vByKXlrmJzAOtD9t27B9Gf9szoA55JYBuMkvbs8f",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "9e97DujgPxnpnlr4OkYn8QSr9QdhSQXwED96BRZs"
    }

