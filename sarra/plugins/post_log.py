#!/usr/bin/python3

"""
  default on_file handler logs that the file has been received.
  prints a simple notice.

"""

import os,stat,time

class Post_Log(object): 

    def __init__(self,parent):
          pass
          
    def perform(self,parent):

        msg = parent.msg
        parent.logger.info("post_log notice=%s headers=%s" % ( msg.notice, msg.headers))
        return True

post_log = Post_Log(self)

self.on_post = post_log.perform

