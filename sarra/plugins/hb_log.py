#!/usr/bin/python3

"""
  on_heartbeat handler that just prints a log message when it is invoked.

"""

class Hb_Log(object): 

    def __init__(self,parent):
        parent.logger.debug( "hb_log initialized" )
          
    def perform(self,parent):
        parent.logger.info("heartbeat. Sarracenia version is: %s \n" % sarra.__version__ )
        return True

hb_log = Hb_Log(self)

self.on_heartbeat = hb_log.perform

