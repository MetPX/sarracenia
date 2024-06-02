#!/usr/bin/python3

"""
Poll Rate Limit Plugin
=====================================================================================

Limits how frequenty a poll accesses a remote server. 

\\*This limits the number of lsdir requests made to the server. If the poll that you want to rate limit doesn't
call ``sarracenia.flowcb.poll.Poll.poll_directory``, then it won't work.
  
Configurable Options:
----------------------

You should either set ``pollLsdirRateMax`` to define a maximum rate of requests per second **or** use both of 
``pollRateLimit_count`` and ``pollRateLimit_period`` instead, to define a maximum number of requests that are
allowed within an arbitrary time period (e.g. 120 requests [count] allowed per minute [period]).

When using ``pollLsdirRateMax``, ``pollRateLimit_count = 1`` and ``pollRateLimit_period = 1 / pollLsdirRateMax``.

``pollLsdirRateMax``:
^^^^^^^^^^^^^^^^^^^^^^

    Maximum number of (remote server) directory listings per second. Floating point number.

    E.g. 1.0 = <= 1 lsdir/sec, 0.25 = <= 1 lsdir every 4 seconds.

``pollRateLimit_count``:
^^^^^^^^^^^^^^^^^^^^^^^^^

    How many requests can be made within ``pollRateLimit_period`` before waiting.

``pollRateLimit_period``:
^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    This is a duration option. It will accept a floating point number, or a floating point number suffixed with
    a unit (s = seconds, m = minutes, h = hours, etc.). 

Change log:
-----------

    - 2024-01: First attempt.
    - 2024-01-04: Changed to use a rate.
"""

import datetime
import logging
import sarracenia
import time

logger = logging.getLogger(__name__)

class Rate_limit(sarracenia.flowcb.poll.Poll):
    def __init__(self, options):
        super().__init__(options,logger)

        # Allow setting a logLevel *only* for this plugin in the config file:
        # set poll.rate_limit.logLevel debug
        if hasattr(self.o, 'logLevel'):
            logger.setLevel(self.o.logLevel.upper())

        self.o.add_option('pollRateLimit_count', kind='count', default_value=0)
        self.o.add_option('pollRateLimit_period', kind='duration', default_value=0)
        self.o.add_option('pollLsdirRateMax', kind='float', default_value=0.0)

        if self.o.pollLsdirRateMax != 0.0:
            logger.debug(f"Setting pollRateLimit_count and pollRateLimit_period using pollLsdirRateMax")
            if self.o.pollRateLimit_count != 0 or self.o.pollRateLimit_period != 0:
                logger.warning("Using pollLsdirRateMax, ignoring pollRateLimit_count and pollRateLimit_period")
            self.o.pollRateLimit_count = 1
            self.o.pollRateLimit_period = 1/self.o.pollLsdirRateMax
        else:
            self.o.pollLsDirRateMax = self.o.pollRateLimit_count/self.o.pollRateLimit_period

        self._lsdir_count = 0
        self._last_limit = datetime.datetime.utcnow()
        self._lsdir_total = 0
    
    def poll(self):
        self._lsdir_total = 0 # total # of lsdirs since the poll started
        start_time = datetime.datetime.utcnow()
        msgs = super().poll()
        end_time = datetime.datetime.utcnow()
        rate = self._lsdir_total/((end_time - start_time).seconds)
        logger.info(f"Actual rate: {rate:.4f} lsdir/sec, pollLsdirRateMax: {self.o.pollLsdirRateMax:.4f} lsdir/sec")
        return msgs
    
    def poll_directory(self, pdir):
        if self.o.pollRateLimit_count and self._lsdir_count >= self.o.pollRateLimit_count:
            logger.debug(f"{self._lsdir_count} requests have been made since {self._last_limit}")
            time_to_sleep = int(self.o.pollRateLimit_period - (datetime.datetime.utcnow() - self._last_limit).seconds)
            if time_to_sleep > 0:
                logger.info(f"poll rate limit reached, need to sleep for {time_to_sleep} seconds")
                # it would be better to also check for housekeeping interval like
                # sarracenia.flowcb.scheduled.Scheduled.wait_seconds does
                while (time_to_sleep > 0) and not self.stop_requested:
                    time.sleep(min(5, time_to_sleep))
                    time_to_sleep -= 5
            else:
                logger.debug(f"not sleeping, time_to_sleep={time_to_sleep} <= 0")
            self._lsdir_count = 0
            self._last_limit = datetime.datetime.utcnow()
        
        self._lsdir_count += 1
        self._lsdir_total += 1
        return super().poll_directory(pdir)
    
