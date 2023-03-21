# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#

import logging

from sarracenia import naturalSize
import sarracenia.moth
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Message(FlowCB):
    """
       gather messages from a sarracenia.moth message queuing protocol source.
    """
    def __init__(self, options) -> None:

        super().__init__(options,logger)

        if hasattr(self.o, 'broker'):
            od = sarracenia.moth.default_options
            od.update(self.o.dictify())
            self.consumer = sarracenia.moth.Moth.subFactory(self.o.broker, od)

    def gather(self) -> list:
        """
           return a current list of messages.
        """
        return self.consumer.newMessages()

    def ack(self, mlist) -> None:
        for m in mlist:
            # messages being re-downloaded should not be re-acked, but they won't have an ack_id (see issue #466)
            self.consumer.ack(m)

    def metricsReport(self) -> dict:
        if hasattr(self,'consumer') and self.consumer:
           return self.consumer.metricsReport()
        else:
           return {}

    def on_housekeeping(self) -> None:
        m = self.consumer.metricsReport()
        average = (m['rxByteCount'] /
                   m['rxGoodCount'] if m['rxGoodCount'] != 0 else 0)
        logger.info( f"messages: good: {m['rxGoodCount']} bad: {m['rxBadCount']} " +\
           f"bytes: {naturalSize(m['rxByteCount'])} " +\
           f"average: {naturalSize(average)}" )
        self.consumer.metricsReset()

    def on_stop(self) -> None:
        self.consumer.close()
        logger.info('closing')
