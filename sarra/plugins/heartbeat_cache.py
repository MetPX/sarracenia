#!/usr/bin/python3

"""
  default on_heartbeat handler cache that it was envoke
"""

class Heartbeat_Cache(object): 

    def __init__(self,parent):
        self.last_time  = time.time()
        self.last_count = 0
          
    def perform(self,parent):
        self.logger     = parent.logger

        if not hasattr(parent,"cache") :
           self.logger.error( "heartbeat_cache with no cache" )
           return True

        if parent.cache_stat :
           count = parent.cache.count
           parent.cache.save()

           now       = time.time()
           new_count = parent.cache.count

           self.logger.info("cache was %d, but since %f sec, increased up to %d, now saved %d entries" % 
                           ( self.last_count, now-self.last_time, count, new_count))

           self.last_time  = now
           self.last_count = new_count

        else :

           parent.cache.save()
           self.logger.info("cache saved (%d)" % len(parent.cache.cache_dict))

        return True

heartbeat_cache = Heartbeat_Cache(self)

self.on_heartbeat = heartbeat_cache.perform

