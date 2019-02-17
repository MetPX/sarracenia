#!/usr/bin/python3

"""
  This plugin delays processing of messages by *message_delay* seconds


  msg_delay 30
  on_message msg_delay

  every message will be at least 30 seconds old before it is forwarded by this plugin.

"""
import os,time

class Msg_Delay(object): 

    def __init__(self,parent):
        parent.logger.debug("msg_log initialized")
        parent.declare_option('msg_delay')
        if hasattr(parent, 'msg_delay'):
            if type(parent.msg_delay) is list:
               parent.msg_delay=int(parent.msg_delay[0])
        else:
            parent.msg_delay=300

          
    def on_message(self,parent):
        import calendar
        from sarra.sr_util import timestr2flt

        msg = parent.msg
        msgtime=timestr2flt(msg.pubtime)
        now=time.time()

        lag=now-msgtime

        parent.logger.info("msg_delay received: %s %s%s topic=%s lag=%g %s" % \
           ( msg.pubtime, msg.baseurl, msg.relpath, msg.topic, msg.get_elapse(), msg.hdrstr ) )

        if lag < parent.msg_delay :
            parent.logger.info("msg_delay message not old enough, sleeping for %d seconds" %  (parent.msg_delay - lag) )
            time.sleep( parent.msg_delay - lag )

        return True

msg_delay = Msg_Delay(self)

self.on_message = msg_delay.on_message

