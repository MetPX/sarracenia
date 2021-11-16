#!/usr/bin/python3
"""
  msg_test_retry:  this change the message randomly so that it will cause
                   a download or send error.

                   when a message is being retried, it is randomly fixed
"""

import random
import logging
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class Msg_test_retry(FlowCB):
    def __init__(self, options):
        self.o = options
        self.destination = None
        self.msg_baseurl_good = None
        self.details_bad = None
        self.msg_baseurl_bad = 'sftp://ruser:rpass@retryhost'

    def  after_accept(self,worklist):
        new_incoming = []
        for message in worlist.incoming:
            logger.debug("msg_test_retry")

            if self.destination == None:
                self.destination = self.o.destination
            if self.msg_baseurl_good == None:
                self.msg_baseurl_good = message['baseUrl']

            # retry message : recover it
            # FIXME dont see 'isRetry' as an entry in the message dictionary, could cause an error
            if message['isRetry']:
                self.o.destination = self.destination
                ok, self.o.details = self.o.credentials.get(self.destination)

                # FIXME dont see 'set_notice' as an entry in the message dictionary, could cause an error
                message['set_notice'](self.msg_baseurl_good, message['relpath'], message['pubtime'])

            # original message :  50% chance of breakage
            elif random.randint(0, 2):

                # if sarra or subscribe break download
                if self.o.program_name != 'sr_sender':
                    logger.debug("making it bad 1")
                    ok, self.o.details = self.o.credentials.get(self.destination)

                    # FIXME dont see 'set_notice' as an entry in the message dictionary, could cause an error
                    message['set_notice'](self.msg_baseurl_bad, message['relpath'], message['pubtime'])

                # if sender break destination
                else:
                    logger.debug("making it bad 2")
                    self.o.sleep_connect_try_interval_max = 1.0
                    self.o.destination = self.msg_baseurl_bad
                    self.o.credentials.parse(self.msg_baseurl_bad)
                    ok, self.o.details = self.o.credentials.get(self.msg_baseurl_bad)

            logger.debug("return from msg_test_retry")
            # TODO not sure where to add to new_incoming. as of now not appending to new_incoming or worklist.rejected
        worklist.incoming = new_incoming


