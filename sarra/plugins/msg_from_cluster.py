#!/usr/bin/python3

"""
  Select messages whose source is the same as the 'msg_by_source' setting.

"""

import os,stat,time

class Transformer(object): 


    def __init__(self,parent):

        if not hasattr(parent,'msg_from_cluster'):
           parent.logger.info("msg_from_cluster setting mandatory")
           return

        parent.logger.info("msg_from_cluster is %s " % parent.msg_from_cluster )

          
    def perform(self,parent):
        return ( parent.msg.headers[ 'from_cluster' ] in parent.msg_from_cluster ) 


transformer = Transformer(self)
self.on_message = transformer.perform

