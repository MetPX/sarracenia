#!/usr/bin/python3

"""
  on_heartbeat handler that runs a sanity check on all processes
  This plugin was designed to be used under sr_audit only

"""

class Hb_Sanity(object): 

    def __init__(self,parent):
        parent.logger.debug( "hb_sanity initialized" )
          
    def perform(self,parent):
        parent.logger.info( "hb_sanity launched" )
        parent.run_command(['sr','sanity'])
        return True

hb_sanity = Hb_Sanity(self)
self.on_heartbeat = hb_sanity.perform
