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
       post messages to sarracenia.moth message queuing protocol destination.
    """
    def __init__(self, options):

        super().__init__(options,logger)

        if hasattr(self.o, 'post_broker'):
            props = sarracenia.moth.default_options
            props.update(self.o.dictify())
            props.update({
                'broker': self.o.post_broker,
                'exchange': self.o.post_exchange,
                'topicPrefix': self.o.post_topicPrefix,
            })
            if hasattr(self.o, 'post_exchangeSplit'):
                props.update({
                    'exchangeSplit': self.o.post_exchangeSplit,
                })
            self.poster = sarracenia.moth.Moth.pubFactory(
                self.o.post_broker, props)

    def post(self, worklist):

        still_ok = []
        all_good=True
        for m in worklist.ok:
            if all_good and hasattr(self.poster,'putNewMessage') and self.poster.putNewMessage(m):
                still_ok.append(m)
            else:
                all_good=False
                worklist.failed.append(m)
        worklist.ok = still_ok

    def metricsReport(self) -> dict:
        if hasattr(self,'poster') and self.poster:
            return self.poster.metricsReport()
        else:
            return {}

    def on_housekeeping(self):
        if hasattr(self,'poster') and self.poster:
            m = self.poster.metricsReport()
            logger.info(
                f"messages: good: {m['txGoodCount']} bad: {m['txBadCount']} bytes: {m['txByteCount']}"
            )
            self.poster.metricsReset()
        else:
            logger.info( "no metrics available" )

    def on_stop(self):
        if hasattr(self,'poster') and self.poster:
            self.poster.close()
        logger.info('closing')
