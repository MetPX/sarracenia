#!/usr/bin/python3
"""
  This plugin delays processing of messages by *message_delay* seconds


  msg_delay 30
  on_message msg_delay

  every message will be at least 30 seconds old before it is forwarded by this plugin.

"""
import logging
from sarracenia import timestr2flt, nowflt, nowstr
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)



class MessageDelay(FlowCB):
    def __init__(self, options):
        self.o = options
        logger.debug("msg_log initialized")
        self.o.add_option('msg_delay','list') #FIXME should thid be list? or int?
        
        if hasattr(self.o, 'msg_delay') and type(self.o.msg_delay) is list:
            self.o.msg_delay = int(self.o.msg_delay[0])
        elif not hasattr(self.o, 'msg_delay'):
            self.o.msg_delay = 300

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:
            if not 'delay' in message['headers']:
                message['headers']['delay'] = nowstr()
    
            # Test msg delay
            elapsedtime = nowflt() - timestr2flt(message['headers']['pubTime'])
            if 0 < elapsedtime < 1:
                logger.debug("msg_delay received msg")
            else:
                logger.info("trying msg with {:.3f}s elapsed".format(elapsedtime))
            if elapsedtime < self.o.msg_delay:
                dbg_msg = "message not old enough, sleeping for {:.3f} seconds"
                logger.debug(dbg_msg.format(elapsedtime, self.o.msg_delay - elapsedtime))
                self.o.consumer.sleep_now = self.o.consumer.sleep_min
                self.o.consumer.msg_to_retry()
                message['isRetry'] = False
                worklist.rejected.append(message)
            new_incoming.append(message)
        worklist.incoming = new_incoming

