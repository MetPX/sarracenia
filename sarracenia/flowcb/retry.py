#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# more info: https://github.com/MetPX/sarracenia
#
# sr_retry.py : python3 standalone retry logic/testing
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  first shot     : Wed Jan 10 16:06:16 UTC 2018
#

import os, json, sys, time
from _codecs import decode, encode

from sarracenia import nowflt, timestr2flt

import logging

from sarracenia.flowcb import FlowCB

from sarracenia.diskqueue import DiskQueue

# class sarra/retry

logger = logging.getLogger(__name__)


class Retry(FlowCB):
    """
      store a message received for a later repeated attempt.
    """
    def __init__(self, options):

        logger.debug("sr_retry __init__")

        self.o = options

        self.download_retry_name =  'work_retry_%02d' % options.no
        self.download_retry = DiskQueue( options, self.download_retry_name )
        self.post_retry_name =  'post_retry_%03d' % options.no
        self.post_retry = DiskQueue( options, self.post_retry_name )

        logger.setLevel(getattr( logging, self.o.logLevel.upper()))
        logger.debug('logLevel=%s' % self.o.logLevel)

   
    def cleanup(self):
        self.download_retry.cleanup()
        self.post_retry.cleanup()

    def after_accept(self, worklist):
        """
          if there are only a few new messages, then get some from the retry list.
        """
  
        qty = (self.o.batch / 2) - len(worklist.incoming)
        logger.info('qty: %d len(worklist.incoming) %d' % ( qty, len(worklist.incoming) ) )

        if qty <= 0: return

        mlist = self.download_retry.get(qty)

        logger.debug("loading from %s: qty=%d ... got: %d " % (self.download_retry_name, qty, len(mlist)))
        if len(mlist) > 0:
            worklist.incoming.extend(mlist)


    def after_work(self, worklist):
        """
         worklist.failed should be put on the retry list.
        """
        if len(worklist.failed) == 0:
            return

        logger.debug("putting %d messages into %s" % (len(worklist.failed),self.download_retry_name) )

        self.download_retry.put(worklist.failed)
        worklist.failed = []

        # retry posting...
        qty = (self.o.batch / 2) - len(worklist.ok)
        if qty <= 0: return

        mlist = self.post_retry.get(qty)

        logger.debug("loading from %s: qty=%d ... got: %d " % (self.post_retry_name, qty, len(mlist)))
        if len(mlist) > 0:
            worklist.ok.extend(mlist)


    def after_post(self, worklist):
        self.post_retry.put(worklist.failed)
        worklist.failed=[]
        pass

    def on_housekeeping(self):
        logger.info("on_housekeeping")

        self.download_retry.on_housekeeping()
        self.post_retry.on_housekeeping()

    def on_stop(self):
        self.download_retry.close()
        self.post_retry.close()
