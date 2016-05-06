#!/usr/bin/python3

"""
  the default on_msg handler for sr_log.
  prints a simple notice.

"""

import os,stat,time

class Msg_Log(object): 

    def __init__(self,parent):
          pass
          
    def perform(self,parent):

        parent.logger.info("msg_log received: %s" % parent.msg.notice)
        return True

msg_log = Msg_Log(self)

self.on_message = msg_log.perform

