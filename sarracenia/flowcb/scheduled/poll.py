import logging
import requests
import base64

import datetime
import os
import sys
import time

from datetime import date

import sarracenia
from sarracenia.flowcb.scheduled import Scheduled

logger = logging.getLogger(__name__)




class Poll(Scheduled):
    """
      
    """

    def gather(self,messageCountMax): # placeholder
        """

           This gather aborts further gathers if the next interval has not yet arrived.

        """
        logger.info( f"waiting for next poll")
        self.wait_until_next()

        return  not (self.stop_requested or self.housekeeping_needed), [] 


if __name__ == '__main__':

    import sarracenia.config
    import types
    import sarracenia.flow

    options = sarracenia.config.default_config()
    flow = sarracenia.flow.Flow(options)
    flow.o.scheduled_interval= 5
    flow.o.pollUrl = "https://dd.weather.gc.ca/bulletins/alphanumeric/"
    if sys.platform.startswith( "win" ):
        flow.o.directory = "C:\\temp\poll"
    else:
        flow.o.directory = "/tmp/scheduled_poll/${%Y%m%d}"
    logging.basicConfig(level=logging.DEBUG)

    me = Poll(flow.o)
    me.gather(flow.o.batch)
    logger.info("first done")
    me.gather(flow.o.batch)
    logger.info("Second Done")
