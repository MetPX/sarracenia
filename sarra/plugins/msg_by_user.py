#!/usr/bin/python3

"""
  Select messages posted by user that is the same as the 'msg_by_user' setting.

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

