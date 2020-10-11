#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#

import logging

import sarra.moth
from sarra.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Message(FlowCB):
    """
       gather messages from a message protocol source.
    """
    def __init__(self, options):

        self.o = options

        if hasattr(self.o, 'broker'):
            od = sarra.moth.default_options
            od.update(self.o.dictify())
            self.consumer = sarra.moth.Moth.subFactory(self.o.broker, od)

    def gather(self):
        """
           return a current list of messages.
        """
        return self.consumer.newMessages()

    def ack(self, mlist):
        for m in mlist:
            # see plugin/retry.py
            if not (('isRetry' in m) and m['isRetry']):
                self.consumer.ack(m)

    def on_stop(self):
        self.consumer.close()
        logger.info('closing')
