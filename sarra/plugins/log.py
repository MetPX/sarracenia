#!/usr/bin/python3

"""
  implement logging at all on_* points. 
  prints a simple notice.

  should be configured with:

  on_message log

"""

class Log(object): 

    def __init__(self,parent):
        parent.logger.debug("log initialized")
          
    def on_start(self,parent):
        parent.logger.info("log start")
        return True

    def on_stop(self,parent):
        parent.logger.info("log stop")
        return True

    def on_message(self,parent):
        msg = parent.msg
        parent.logger.info("log message accepted: %s %s%s topic=%s lag=%g %s" % \
           tuple( msg.notice.split()[0:3] + [ msg.topic, msg.get_elapse(), msg.hdrstr ] ) )
        return True
          
    def on_part(self,parent):
        parent.logger.info("log part downloaded to: %s/%s" % ( parent.new_dir, parent.msg.new_file) )
        return True

    def on_file(self,parent):
        parent.logger.info("log file downloaded to: %s/%s" % ( parent.new_dir, parent.msg.new_file) )
        return True

    def on_post(self,parent):

        msg = parent.msg
        parent.logger.info("log post notice=%s %s %s headers=%s" % \
            tuple( msg.notice.split()[0:3] + [ msg.headers ] ) )
        return True

    def on_heartbeat(self,parent):
        parent.logger.info("log heartbeat. Sarracenia version is: %s \n" % sarra.__version__ )
        return True


log = Log(self)

self.on_message = log.on_message

