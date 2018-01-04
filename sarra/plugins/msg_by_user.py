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

        parent.declare_option('msg_by_user')

        if not hasattr(parent,'msg_by_user'):
           parent.logger.info("msg_by_user setting mandatory")
           return

        parent.logger.info("msg_by_user is %s " % parent.msg_by_user )

          
    def on_message(self,parent):

        # MG  FIX ME  checking for report user I guess
        if parent.topic_prefix == 'v02.report' :
           return ( parent.msg.report_user in parent.msg_by_user ) 

        # checking for regular user
        return ( parent.msg.headers[ 'user' ] in parent.msg_by_user ) 


transformer = Transformer(self)
self.on_message = transformer.on_message

