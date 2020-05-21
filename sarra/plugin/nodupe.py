#!/usr/bin/python3

"""
  default on_housekeeping handler to clean the duplicate suppression memory.
  by invoking parent.cache.save() it will only write out the values that are still relevant.

"""
import logging
from sarra.sr_util import nowflt
from sarra.plugin import Plugin

logger = logging.getLogger( __name__ )


class NoDupe(Plugin):

    def __init__(self,options):
        self.last_time  = nowflt()
        self.last_count = 0
        self.o = options
        
          
    def on_housekeeping(self):

        if not hasattr(parent,"suppress_duplicates") :
           logger.info( "suppress_duplicates: off " )
           return True

        if self.o.cache_stat :
           count = self.o.noDupes.count
           self.o.noDupes.save()

           now       = nowflt()
           new_count = self.o.cache.count

           logger.info("hb_cache was %d, but since %5.2f sec, increased up to %d, now saved %d entries" % 
                           ( self.last_count, now-self.last_time, count, new_count))

           self.last_time  = now
           self.last_count = new_count

        else :

           self.o.cache.save()
           logger.info("hb_cache saved (%d)" % len(self.o.cache.cache_dict))

        return True

