#!/usr/bin/python3
"""
  msg_test_retry:  this change the message randomly so that it will cause
                   a download or send error.

                   when a message is being retried, it is randomly fixed
"""

import random

try :    from sr_credentials       import *
except : from sarra.sr_credentials import *

class Msg_test_retry():

    def __init__(self,parent):
        self.destination      = None
        self.msg_baseurl_good = None
        self.details_bad      = None
        self.msg_baseurl_bad  = 'sftp://ruser:rpass@retryhost'

    def on_message(self,parent):

        l = parent.logger
        m = parent.msg

        l.debug("msg_test_retry")

        if self.destination      == None: self.destination = parent.destination

        if self.msg_baseurl_good == None: self.msg_baseurl_good = m.baseurl

        # retry message : recover it
        if m.isRetry :
           parent.destination = self.destination
           ok, parent.details = parent.credentials.get(self.destination)
           m.set_notice(self.msg_baseurl_good,m.relpath,m.pubtime)

        # original message :  50% chance of breakage
        elif random.randint(0,2) :

           # if sarra or subscribe  break download
           if parent.program_name != 'sr_sender' :
              l.debug("making it bad 1")
              ok, parent.details = parent.credentials.get(self.destination)
              m.set_notice(self.msg_baseurl_bad, m.relpath,m.pubtime)

           # if sender break destination
           else: 
              l.debug("making it bad 2")
              parent.sleep_connect_try_interval_max = 1.0
              parent.destination = self.msg_baseurl_bad
              parent.credentials.parse(self.msg_baseurl_bad)
              ok, parent.details = parent.credentials.get(self.msg_baseurl_bad)

        l.debug("return from msg_test_retry")
        return True

msg_test_retry=Msg_test_retry(None)
self.on_message=msg_test_retry.on_message
