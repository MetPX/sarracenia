#!/usr/bin/python3

"""
Poll Rate Limit Plugin
=====================================================================================

Limits how frequenty a poll accesses a remote server. 

Once ``pollRateLimit_count`` requests\* to the remote server have been made within ``pollRateLimit_period``, wait
for the remaining amount of time before making the next request(s).

Example: count=10, period=60s. 10 requests are made between 10:00:00 and 10:00:10. This plugin will wait 50s
before allowing the next request(s) to be made.

\*This limits the number of lsdir requests made to the server. If the poll that you want to rate limit doesn't
call ``sarracenia.flowcb.poll.Poll.poll_directory``, then it won't work.
  
Configurable Options:
----------------------

``pollRateLimit_count``:
^^^^^^^^^^^^^^^^^^^^^^^^^

    How many requests can be made within ``pollRateLimit_period``.

``pollRateLimit_period``:
^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    This is a duration option. It will accept a floating point number, or a floating point number suffixed with
    a unit. 

How to set up your poll config:
--------------------------------
 
    Use ``callback poll.rate_limit`` and set the above options.

Change log:
-----------

    - 2024-01: First attempt.
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

        self.o.add_option('pollRateLimit_count', kind='count', default_value=1)
        self.o.add_option('pollRateLimit_period', kind='duration', default_value=10)

        self._lsdir_count = 0
        self._last_limit = datetime.datetime.utcnow()
    
    def poll_directory(self, pdir):
        if self._lsdir_count >= self.o.pollRateLimit_count:
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
        return super().poll_directory(pdir)
