from apiclient import discovery
from oauth2client import gce
import httplib2

TQ_SCOPE = 'https://www.googleapis.com/auth/taskqueue'
API_VERSION = 'v1beta2'

credentials = gce.AppAssertionCredentials(scope=TQ_SCOPE)
http = credentials.authorize(httplib2.Http())
tq_service = discovery.build('taskqueue', API_VERSION, http=http)
project_id = open('/coal/project-id', 'r').read()
print "PROJECT_ID: {0}".format(project_id)
print tq_service.taskqueues().get(project=project_id, taskqueue='controller')
