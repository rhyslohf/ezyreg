import tornado.httpserver
import tornado.websocket
import tornado.ioloop
from tornado.concurrent import return_future
from tornado.gen import coroutine
from tornado.httputil import HTTPHeaders
import tornado.web
import socket
import json

import os
import sys
from bs4 import BeautifulSoup
import requests

def scan_ezyreg(reg):
    #create session
    s = requests.Session()

    #login
    url = "https://www.ecom.transport.sa.gov.au/et/checkRegistrationExpiryDate.do"
    r = s.get(url)

    #query
    url = "https://www.ecom.transport.sa.gov.au/et/cred_registration_details.do"
    data = {"plateNumber": reg.upper()}
    r = s.post(url, data)
    soup = BeautifulSoup(r.text, 'html.parser')

    #get data
    def clean(str):
        return str.encode('utf-8').replace('\xc2\xa0', '_').lower().strip()
    domData = dict(zip(soup.find_all('td', {'class':'fieldTitle'}),soup.find_all('td', {'class':'fieldSpace'})))
    data = {clean(k.text):clean(v.text) for (k,v) in domData.iteritems()}
    
    if "please_enter_a_south_australian_plate_number" in data:
        return None

    #use data
    return data

class RESTHandler(tornado.web.RequestHandler):
    def initialize(self, **kwargs):
        pass
      
    def options(self, *args):
        allowedMethods = list(["OPTIONS", "GET"])
        self.set_header("Access-Control-Allow-Methods", ",".join(allowedMethods))
        self.finish()
      
    @coroutine
    def get(self, reg):
        regData = scan_ezyreg(reg)
        if regData:
            self.set_status(200)
            self.finish(regData)
        else:
            self.set_status(404)
            self.finish()
            
def main():
    application = tornado.web.Application([
        (r'/reg/(.*)', RESTHandler),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": '.', "default_filename": "index.html"})
    ])
    http_server = tornado.httpserver.HTTPServer(application)
    port = int(os.environ.get("PORT", 5000))
    http_server.listen(port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()