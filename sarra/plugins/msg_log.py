#!/usr/bin/python3

"""
  the default on_msg handler for sr_log.
  prints a simple notice.

"""

class Msg_Log(object): 

    def __init__(self,parent):
        parent.logger.debug("msg_log initialized")
          
    def on_message(self,parent):
        msg = parent.msg
        parent.logger.info("msg_log received: %s %s%s topic=%s lag=%g %s" % \
           ( msg.pubtime, msg.baseurl, msg.relpath, msg.topic, msg.get_elapse(), msg.hdrstr ) )
        return True

msg_log = Msg_Log(self)

self.on_message = msg_log.on_message

