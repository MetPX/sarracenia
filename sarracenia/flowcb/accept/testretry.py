"""
Plugin testretry.py:
    This changes the message randomly so that it will cause
    a download or send an error.
    When a message is being retried, it is randomly fixed

Usage:
    flowcb sarracenia.flowcb.accept.testretry.TestRetry
"""

import logging
import random
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class TestRetry(FlowCB):
    def __init__(self, options):
        super().__init__(options,logger)
        self.sendTo = None
        self.msg_baseUrl_good = None
        self.details_bad = None
        self.msg_baseUrl_bad = 'sftp://ruser:rpass@retryhost'

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:
            logger.debug("testretry after_accept")

            if self.sendTo == None:
                self.sendTo = self.o.sendTo
            if self.msg_baseUrl_good == None:
                self.msg_baseUrl_good = message['baseUrl']

            # retry message : recover it
            # update: this is set somewhere as true in /diskqueue.py, should think about initializing first so we
            # dont have to test for existence
            # 2022-06-10: isRetry was removed. Maybe can check if the message has msg_baseUrl_bad?
            #             see issues #466 and #527.
            if 'isRetry' in message and message['isRetry']:
                self.o.sendTo = self.sendTo
                ok, self.o.details = self.o.credentials.get(self.sendTo)

                ## # FIXME dont see 'set_notice' as an entry in the message dictionary, could cause an error
                ## #message['set_notice'](self.msg_baseUrl_good, message['relPath'], message['pubTime'])
                # Fixed missing message.set_notice method; now just set baseUrl
                message['baseUrl'] = self.msg_baseUrl_good

            # original message :  50% chance of breakage
            elif random.randint(0, 2):

                # if sarra or subscribe break download
                if self.o.component != 'sender':
                    logger.debug("making it bad 1")
                    ok, self.o.details = self.o.credentials.get(self.sendTo)

                    ## # FIXME dont see 'set_notice' as an entry in the message dictionary, could cause an error
                    ## #message['set_notice'](self.msg_baseUrl_bad, message['relpath'], message['pubTime'])
                    # Fixed missing message.set_notice method; now just set baseUrl
                    message['baseUrl'] = self.msg_baseUrl_bad

                # if sender break destination
                else:
                    logger.debug("making it bad 2")
                    self.o.sleep_connect_try_interval_max = 1.0
                    self.o.sendTo = self.msg_baseUrl_bad
                    self.o.credentials._parse(self.msg_baseUrl_bad)
                    ok, self.o.details = self.o.credentials.get(self.msg_baseUrl_bad)

            logger.debug("return from testretry after_accept")
            # TODO not sure where to add to new_incoming. as of now not appending to new_incoming or worklist.rejected
        worklist.incoming = new_incoming
