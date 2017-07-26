#!/usr/bin/python3

"""
  default on_heartbeat handler logs that it was envoke
"""

class Heartbeat_Log(object): 

    def __init__(self,parent):
        parent.logger.debug( "heartbeat_log initialized" )
          
    def perform(self,parent):
        parent.logger.info("heartbeat")
        return True

heartbeat_log = Heartbeat_Log(self)

self.on_heartbeat = heartbeat_log.perform

