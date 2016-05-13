#!/usr/bin/python3

"""
  the default on_msg handler for sr_log.
  prints a simple notice.

"""

class Post_Log(object): 

    def __init__(self,parent):
          pass
          
    def perform(self,parent):
        msg = parent.msg
        parent.logger.info("msg_log received: %s topic=%s lag=%g %s" % \
           ( msg.notice, msg.topic, msg.get_elapse(), msg.hdrstr ) )
        return True

post_log = Post_Log(self)

self.on_post = post_log.perform

