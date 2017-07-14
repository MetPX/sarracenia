#!/usr/bin/python3

"""
  the default on_watch handler for sr_watch 
  when sr_watch wakes up... run this plugin

"""

class Watch_Log(object): 

    def __init__(self,parent):
        parent.logger.debug("watch_log initialized " )
          
    def perform(self,parent):
        parent.logger.info("watch_log iteration" )
        return True

watch_log = Watch_Log(self)

self.on_watch = watch_log.perform

