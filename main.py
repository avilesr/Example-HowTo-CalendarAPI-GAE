import webapp2
import sys
import time
import datetime
import os
import jinja2
import urllib
import httplib2

from apiclient.discovery import build
from oauth2client.appengine import OAuth2Decorator
from google.appengine.api import memcache

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions=['jinja2.ext.autoescape'],
  autoescape=True)


decorator = OAuth2Decorator(client_id='991267974420-q0om8a1s3maofh703q8ot0cdecb8lt1c.apps.googleusercontent.com',
                            client_secret='0i1tlQUQ0Jpri4SiR2yysbqO',
                            scope='https://www.googleapis.com/auth/calendar')
http = httplib2.Http(memcache)
service = build('calendar', 'v3', http=http)

class MainHandler(webapp2.RequestHandler):

   @decorator.oauth_required
   def get(self):
    # get the next 7 days of events
    epoch_time = time.time()
    start_time = epoch_time - 3600  # 1 hour ago
    end_time = epoch_time + 168 * 3600  # 7 days in the future
    tz_offset = - time.altzone / 3600
    if tz_offset < 0:
      tz_offset_str = "-%02d00" % abs(tz_offset)
    else:
      tz_offset_str = "+%02d00" % abs(tz_offset)
    start_time = datetime.datetime.fromtimestamp(start_time).strftime("%Y-%m-%dT%H:%M:%S") + tz_offset_str
    end_time = datetime.datetime.fromtimestamp(end_time).strftime("%Y-%m-%dT%H:%M:%S") + tz_offset_str
    self.response.write("Getting calendar events between: " + start_time + " and " + end_time)
    events = service.events().list(calendarId='m90kv57sr3iegrbv6qtdhsrmak@group.calendar.google.com', timeMin=start_time, timeMax=end_time, singleEvents=True).execute(
         http=decorator.http())

    employee = []
    stime = []
    etime = []

    for event in events['items']:
      employee.append(event['summary'])
      stime.append(event['start']['dateTime'])
      etime.append(event['end']['dateTime'])
    table_rows = zip(employee, stime, etime)
    variables = {
        'table_rows' : table_rows
    }
    template = JINJA_ENVIRONMENT.get_template('view.html')
    self.response.write(template.render(variables))



class AddShift(webapp2.RequestHandler): #navigates to the html form to add an event
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('add.html')
    self.response.write(template.render())

class ScheduleEmployee(webapp2.RequestHandler): #when html form is submitted, redirects to here
  @decorator.oauth_required
  def post(self):
    if decorator.has_credentials():
      action = self.request.get('action')
      if action == "add":
        event_name = self.request.get('event')
        start_time = self.request.get('start_time')
        end_time = self.request.get('end_time')
        new_shift = {
          'summary': event_name,
          'start': {
            'dateTime': start_time+':00-06:00',
            'timeZone': 'America/Chicago'
          },
          'end': {
            'dateTime': end_time+':00-06:00',
            'timeZone': 'America/Chicago'
          },
        }
        new_event = service.events().insert(calendarId='m90kv57sr3iegrbv6qtdhsrmak@group.calendar.google.com', body=new_shift).execute(
          http=decorator.http())
        self.redirect('/add')  
      else:
        self.response.write("Error: couldn't add shift")
    else:
      self.response.write("Error: Incorrect Credentials")
      

application = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/view', MainHandler),
    ('/add', AddShift),
    ('/enter', ScheduleEmployee),
    (decorator.callback_path, decorator.callback_handler()),
    ], debug=True)