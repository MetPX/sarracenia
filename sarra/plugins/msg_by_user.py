#!/usr/bin/python3

"""
  Select messages posted by user that is the same as the 'msg_by_user' setting.

  msg_by_user 'anonymous'
  msg_by_user 'alice'

  on_message msg_by_user

  will select all messages consumed by alice or anonymous.

"""

import os,stat,time

class Transformer(object): 


    def __init__(self,parent):

        if not hasattr(parent,'msg_by_user'):
           parent.logger.info("msg_by_user setting mandatory")
           return

        parent.logger.info("msg_by_user is %s " % parent.msg_by_user )

          
    def perform(self,parent):
        return ( parent.msg.headers[ 'user' ] in parent.msg_by_user ) 


transformer = Transformer(self)
self.on_message = transformer.perform

