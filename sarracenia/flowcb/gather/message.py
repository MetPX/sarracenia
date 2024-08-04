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

        self.od = sarracenia.moth.default_options
        self.od.update(self.o.dictify())

        if not hasattr(self.o, 'broker') or not self.o.broker:
            logger.critical('missing required broker specification')
            return

        if not hasattr(self.o, 'bindings') or not self.o.bindings:
            logger.critical('missing required bindings (exchange,subtopic) for broker')
            return

        self.brokers=[]
        for binding in self.o.bindings:
            if binding[0] not in self.brokers:
               self.brokers.append(binding[0])

        self.consumers={}
        for broker in self.brokers:
            self.od['broker']=broker
            self.consumers[broker] = sarracenia.moth.Moth.subFactory(self.od)

    def gather(self, messageCountMax) -> list:
        """
           return:
              True ... you can gather from other sources. and:
              a list of messages obtained from this source.
        """
        new_messages=[]
        if not hasattr(self,'consumers'):
            return (True, [])

        for broker in self.brokers:
            if broker in self.consumers and hasattr(self.consumers[broker],'newMessages'):
                new_messages.extend(self.consumers[broker].newMessages())
            else:
                logger.warning( f'not connected. Trying to connect to {broker}')
                self.od['broker']=broker
                self.consumers[broker] = sarracenia.moth.Moth.subFactory(self.od)

        return (True, new_messages)

    def ack(self, mlist) -> None:

        if not hasattr(self,'consumers'):
            return

        for m in mlist:
            # messages being re-downloaded should not be re-acked, but they won't have an ack_id (see issue #466)
            if 'broker' in m:
                 self.consumers[m['broker']].ack(m)
            else:
                logger.error( f"cannot ack, missing broker in {m}" )

    def metricsReport(self) -> dict:

        if not hasattr(self,'consumers'):
           return {}

        metrics={}
        for broker in self.brokers:
           if hasattr(self.consumers[broker],'metricsReport'):
               metrics[broker.geturl()] = self.consumers[broker].metricsReport()
        return metrics 

    def on_housekeeping(self) -> None:

        if not hasattr(self,'consumers'):
            return

        m = self.metricsReport()
        for broker in self.brokers:
            burl=broker.geturl()
            average = (m[burl]['rxByteCount'] /
                   m[burl]['rxGoodCount'] if m[burl]['rxGoodCount'] != 0 else 0)
            logger.info( f"{burl} messages: good: {m[burl]['rxGoodCount']} bad: {m[burl]['rxBadCount']} " +\
               f"bytes: {naturalSize(m[burl]['rxByteCount'])} " +\
               f"average: {naturalSize(average)}" )
            self.consumers[broker].metricsReset()

    def on_stop(self) -> None:
        if hasattr(self,'consumers'): 
            for broker in self.brokers:
                 if hasattr(self.consumers[broker], 'close'):
                     self.consumers[broker].close()
        logger.info('closing')
