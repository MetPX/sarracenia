#!/usr/bin/python3

"""
  default on_heartbeat handler to clean the cache.
  by invoking parent.cache.save() it will only write out the values that are still relevant.

"""

class Hb_Cache(object): 

    def __init__(self,parent):
        self.last_time  = time.time()
        self.last_count = 0
          
    def perform(self,parent):
        self.logger     = parent.logger

        if not hasattr(parent,"cache") :
           self.logger.info( "hb_cache: off " )
           return True

        if parent.cache_stat :
           count = parent.cache.count
           parent.cache.save()

           now       = time.time()
           new_count = parent.cache.count

           self.logger.info("hb_cache was %d, but since %5.2f sec, increased up to %d, now saved %d entries" % 
                           ( self.last_count, now-self.last_time, count, new_count))

           self.last_time  = now
           self.last_count = new_count

        else :

           parent.cache.save()
           self.logger.info("hb_cache saved (%d)" % len(parent.cache.cache_dict))

        return True

hb_cache = Hb_Cache(self)

self.on_heartbeat = hb_cache.perform

