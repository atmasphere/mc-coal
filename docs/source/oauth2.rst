.. _oauth2:

******
OAuth2
******

Clients making calls to the API on behalf of a user require a bearer access token which can be acquired via a simplified oauth2 flow as described in the `draft-ietf-oauth-v2 proposed spec <http://tools.ietf.org/html/draft-ietf-oauth-v2>`_.

[Description of oauth2 flows here]

===========
OAuth2 Test
===========

An oauth2 test resource endpoint is provided to simplify developing consumer applications:

.. http:get:: /oauth/test

  **Example request**:

  .. sourcecode:: http

    GET /oauth/test HTTP/1.1
    Authorization: Bearer 8wB8QtpULBVNuL2mqBaWdIRWX30qKtIK3E5QbOWP

  **Example response**:

  .. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/json

  .. sourcecode:: javascript

    {
      "authorization": "Bearer 8wB8QtpULBVNuL2mqBaWdIRWX30qKtIK3E5QbOWP",
      "client_id": "my-client-id",
      "user": "joe_user"
    }

===================
Client Registration
===================

Clients register with the API using an Open Registration lifecycle as described in the `draft-ietf-oauth-dyn-reg proposed spec <http://tools.ietf.org/html/draft-ietf-oauth-dyn-reg>`_.

[Description of oauth2 open registration flows here]