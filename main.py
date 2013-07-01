import httplib2
import logging
import os
import pickle
import json

from datetime import date, timedelta

from apiclient.discovery import build
from oauth2client.appengine import oauth2decorator_from_clientsecrets
from oauth2client.client import AccessTokenRefreshError
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import webapp2
import jinja2

ROOT_DIR = os.path.dirname(__file__)
CLIENT_SECRETS = os.path.join(ROOT_DIR, 'client_secrets.json')
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(ROOT_DIR, 'templates')),
    extensions=['jinja2.ext.autoescape'])

http = httplib2.Http(memcache)
service = build("analytics", "v3", http=http)

decorator = oauth2decorator_from_clientsecrets(
    CLIENT_SECRETS,
    scope=[
      'https://www.googleapis.com/auth/analytics',
      'https://www.googleapis.com/auth/analytics.readonly',
    ],
    message="")

def dtos(date):
  return date.strftime("%Y-%m-%d")

class MainHandler(webapp2.RequestHandler):

  @decorator.oauth_required
  def get(self):
    req = service.management().profiles().list(accountId="~all", webPropertyId="~all")
    resp = req.execute(http=decorator.http())
    d = json.dumps(resp)
    template = jinja_env.get_template('home.html')
    self.response.out.write(template.render(resp))
    # self.response.out.write(template.render({"d": d}))

class DetailHandler(webapp2.RequestHandler):

  @decorator.oauth_required
  def get(self, app_id):
    today = date.today()
    tminus1m = today - timedelta(days=30)
    req = service.data().ga().get(
      ids="ga:%s" % app_id, 
      end_date=dtos(today),
      start_date=dtos(tminus1m), 
      metrics="ga:visits",
      dimensions="ga:day")
    resp = req.execute(http=decorator.http())
    template = jinja_env.get_template('detail.html')
    d = json.dumps(resp)
    self.response.out.write(template.render({"d": d}))
  

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    (r'/detail/(\d+)', DetailHandler),
    (decorator.callback_path, decorator.callback_handler()),
], debug=True)
