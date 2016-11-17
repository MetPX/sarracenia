#!/usr/bin/python3

"""
  Select messages whose source is the same as the 'msg_by_source' setting.

"""

import os,stat,time

class Transformer(object): 


    def __init__(self,parent):

        if not hasattr(parent,'msg_by_source'):
           parent.logger.info("msg_by_source setting mandatory")
           return

        parent.logger.info("msg_by_source is %s " % parent.msg_by_source )

          
    def perform(self,parent):
        return ( parent.msg.headers[ 'source' ] in  parent.msg_by_source ) 


transformer = Transformer(self)
self.on_message = transformer.perform

