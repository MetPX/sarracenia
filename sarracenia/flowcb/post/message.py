#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#

import logging

import sarracenia.moth
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Message(FlowCB):
    """
       gather messages from a message protocol source.
    """
    def __init__(self, options):

        self.o = options

        if hasattr(self.o, 'post_broker'):
            props = sarracenia.moth.default_options
            props.update(self.o.dictify())
            props.update({
                'broker': self.o.post_broker,
                'exchange': self.o.post_exchange,
                'topicPrefix': self.o.post_topicPrefix,
            })
            if hasattr( self.o, 'post_exchange_split' ):
                props.update({
                    'exchange_split': self.o.post_exchange_split,
                })
            self.poster = sarracenia.moth.Moth.pubFactory(self.o.post_broker, props)

    def post(self, worklist):

        for m in worklist.ok:
            if not self.poster.putNewMessage(m):
                worklist.failed.append(m)
        worklist.ok = []

    def on_stop(self):
        self.poster.close()
        logger.info('closing')
