#!/usr/bin/python3

"""
  This plugin delays processing of messages by *message_delay* seconds


  msg_fdelay 30
  on_message msg_fdelay

  every message will be at least 30 seconds old before it is forwarded by this plugin.

"""
import os,time

class Msg_FDelay(object): 

    def __init__(self,parent):
        parent.logger.debug("msg_log initialized")
        parent.declare_option('msg_fdelay')
        if hasattr(parent, 'msg_fdelay'):
            if type(parent.msg_fdelay) is list:
               parent.msg_fdelay=int(parent.msg_fdelay[0])
        else:
            parent.msg_fdelay=300

          
    def on_message(self,parent):
        import calendar,os,stat

        msg = parent.msg

        # dont need to wait or clean 'R' message
        if msg.sumflg == 'R' : return False

        parent.logger.info( "%s %s %s" % (msg.pubtime, msg.baseurl, msg.relpath) )
        lag = msg.get_elapse()

        parent.logger.info("msg_fdelay received: %s %s%s topic=%s lag=%g %s" % \
           ( msg.pubtime, msg.baseurl, msg.relpath, msg.topic, lag, msg.hdrstr ) )

        if lag < parent.msg_fdelay :
            parent.logger.info("msg_fdelay message not old enough, sleeping for %d seconds" %  (parent.msg_fdelay - lag) )
            time.sleep( parent.msg_fdelay - lag )

        
        f= "%s/%s" % ( msg.new_dir, msg.new_file )
        if not os.path.exists(f):
           return True

        filetime=os.stat( f )[stat.ST_MTIME]
        now=time.time()
        lag=now-filetime
        if lag < parent.msg_fdelay :
            parent.logger.info("msg_fdelay file not old enough, sleeping for %d seconds" %  (parent.msg_fdelay - lag) )
            time.sleep( parent.msg_fdelay - lag )

        return True

msg_fdelay = Msg_FDelay(self)

self.on_message = msg_fdelay.on_message

