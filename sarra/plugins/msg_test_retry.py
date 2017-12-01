#!/usr/bin/python3
"""
  msg_test_retry:  this change the message randomly so that it will cause
                   a download or send error.

                   when a message is being retried, it is randomly fixed

"""

import random

class Msg_test_retry():

    def __init__(self,parent):
        self.parent = parent
        self.msg_baseurl_bad     = 'ftps://retry_user:retry_passwd@retry_host'
        self.msg_baseurl_good    = None
        self.parent_details_good = None
        self.parent_details_bad  = None

    def perform(self,parent):
        l = parent.logger
        m = parent.msg

        if self.msg_baseurl_good == None :
           self.msg_baseurl_good = m.baseurl

        if self.parent_details_good == None and hasattr(self.parent,'details') :
           self.parent_details_good = parent.details
           self.parent_details_bad  = parent.credentials.get(self.msg_baseurl_bad)
           
        parent.details = self.parent_details_good
        
        if m.isRetry and random.randint(0,2) :
           m.set_notice(self.msg_baseurl_good,m.relpath,m.time)

        elif random.randint(0,2) :
           # if sarra or subscribe  break download
           if parent.program_name != 'sr_sender' :
              m.set_notice(self.msg_baseurl_bad, m.relpath,m.time)
           # if sender break destination
           else: 
              parent.details = self.parent_details_bad

        return True

msg_test_retry=Msg_test_retry(None)
self.on_message=msg_test_retry.perform
