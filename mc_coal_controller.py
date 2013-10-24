from oauth2client import gce
import httplib2

TQ_SCOPE = 'https://www.googleapis.com/auth/taskqueue'
API_VERSION = 'v1beta16'

credentials = gce.AppAssertionCredentials(scope=TQ_SCOPE)
http = credentials.authorize(httplib2.Http())
tq_service = discovery.build('taskqueue', API_VERSION, http=http)
