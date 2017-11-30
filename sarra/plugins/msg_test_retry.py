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
        self.url_bad  = 'sftp://toto@titi'
        self.url_good = None

    def perform(self,parent):
        l = parent.logger
        m = parent.msg

        if self.url_good == None :
           self.url_good= m.baseurl
        
        if m.isRetry and random.randint(0,2) :
           m.baseurl = self.url_good

        elif random.randint(0,2) :
           m.baseurl = self.url_bad

        return True

msg_test_retry=Msg_test_retry(None)
self.on_message=msg_test_retry.perform
