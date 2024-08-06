#!/usr/bin/python3

"""
Scheduled flow for new BC Trans API
=====================================================================================

Description

    Rename the file fetched from the BC Trans scheduled flow to a CSV format, date included in filename.


How to set up in your config:
--------------------------------
 
    Use ``callback accept.bc_trans``, and read about the config options above.
    
    For an example, see https://github.com/MetPX/sarracenia/tree/development/sarracenia/examples/flow files named ``*bc_trans*.conf``. 

    Your ``subtopic`` should match the ``path`` from the scheduled flow plugin.

Change log:
-----------
    - 2024-08-06: Inception of plugin.
"""

from sarracenia.flowcb import FlowCB
import logging
import requests,os,datetime,sys,time

logger = logging.getLogger(__name__)

class Bc_trans(FlowCB):
    def __init__(self, options):
        super().__init__(options, logger)
        
        # Allow setting a logLevel *only* for this plugin in the config file:
        # set gather.BC_TRANS.logLevel debug
        if hasattr(self.o, 'logLevel'):
            logger.setLevel(self.o.logLevel.upper())

        # end __init__


    def after_accept(self, worklist):

        new_messages = []

        for msg in worklist.incoming:

            # Build the sarracenia message with the specified format
            try: 

                now = datetime.datetime.now()
                msg['new_file'] = f"OB.BC.MOT.BC_TRAN.{now.strftime('%Y%m%d%H%M%S')}.csv"

            except Exception as e:
                logger.debug("Exception details:", exc_info=True)

            new_messages.append(msg)

        return new_messages
