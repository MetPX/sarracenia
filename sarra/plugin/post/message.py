#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#

import logging

import sarra.moth
from sarra.plugin import Plugin

logger = logging.getLogger(__name__)


class Message(Plugin):
    """
       gather messages from a message protocol source.
    """
    def __init__(self, options):

        self.o = options

        if hasattr(self.o, 'post_broker'):
            props = sarra.moth.default_options
            props.update({
                'broker': self.o.post_broker,
                'exchange': self.o.post_exchange,
            })
            self.poster = sarra.moth.Moth(self.o.post_broker,
                                          props,
                                          is_subscriber=False)

    def post(self, worklist):

        logger.debug('on_post starting for %d messages' % len(worklist.ok))

        for m in worklist.ok:
            # FIXME: outlet = url, outlet=json.
            logger.info('message: %s' % m)
            #if self.o.topic_prefix != self.o.post_topic_prefix:
            #    m['topic'] = m['topic'].replace( self.o.topic_prefix, self.o.post_topic_prefix )
            self.poster.putNewMessage(m)

        worklist.ok = []

    def on_stop(self):
        self.poster.close()
        logger.info('closing')
