# Stolen from: http://ikaisays.com/2011/05/26/setting-up-an-oauth-provider-on-google-app-engine/
# Requires installing python-oauth2:
#   git clone https://github.com/simplegeo/python-oauth2.git
#   cd python-oauth2
#   sudo python setup.py install

import oauth2 as oauth
import urlparse
import os
import pickle

app_id = "gumption-minecraft"
url = "https://{0}.appspot.com/api/data/oauth_test".format(
    app_id
)

consumer_key = 'coal.gumption.com'
consumer_secret = '1H7vhCSI7S8wUTQg5iVD4ZzR'

access_token_file = "token.dat"

request_token_url = "https://%s.appspot.com/_ah/OAuthGetRequestToken" % app_id
authorize_url = "https://%s.appspot.com/_ah/OAuthAuthorizeToken" % app_id
access_token_url = "https://%s.appspot.com/_ah/OAuthGetAccessToken" % app_id

consumer = oauth.Consumer(consumer_key, consumer_secret)

if not os.path.exists(access_token_file):
    client = oauth.Client(consumer)

    # Step 1: Get a request token. This is a temporary token that is used for
    # having the user authorize an access token and to sign the request to obtain
    # said access token.
    resp, content = client.request(request_token_url)
    if resp['status'] != '200':
        raise Exception("Invalid response %s." % resp['status'])

    request_token = dict(urlparse.parse_qsl(content))

    print "Request Token:"
    print "    - oauth_token        = %s" % request_token['oauth_token']
    print "    - oauth_token_secret = %s" % request_token['oauth_token_secret']
    print

    print "Go to the following link in your browser:"
    print "%s?oauth_token=%s" % (authorize_url, request_token['oauth_token'])
    print

    # Step 2: After the user has granted access to you, the consumer, the provider will
    # redirect you to whatever URL you have told them to redirect to. You can
    # usually define this in the oauth_callback argument as well.
    accepted = 'n'
    while accepted.lower() == 'n':
        accepted = raw_input('Have you authorized me? (y/n) ')

    # Step 3: Once the consumer has redirected the user back to the oauth_callback
    # URL you can request the access token the user has approved. You use the
    # request token to sign this request. After this is done you throw away the
    # request token and use the access token returned. You should store this
    # access token somewhere safe, like a database, for future use.
    token = oauth.Token(request_token['oauth_token'],
        request_token['oauth_token_secret'])
    client = oauth.Client(consumer, token)

    resp, content = client.request(access_token_url, "POST")
    access_token = dict(urlparse.parse_qsl(content))

    print "Access Token:"
    print "    - oauth_token        = %s" % access_token['oauth_token']
    print "    - oauth_token_secret = %s" % access_token['oauth_token_secret']
    print
    print "You may now access protected resources using the access tokens above."
    print

    token = oauth.Token(access_token['oauth_token'],
                access_token['oauth_token_secret'])

    #noinspection Restricted_Python_calls
    with open(access_token_file, "w") as f:
        pickle.dump(token, f)

else:
    with open(access_token_file, "r") as f:
        token = pickle.load(f)

client = oauth.Client(consumer, token)
resp, content = client.request(url)
print "Response Status Code: %s" % resp['status']
print "Response body: %s" % content
