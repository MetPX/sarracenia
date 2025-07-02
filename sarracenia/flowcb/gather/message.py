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

        self.consumers = []

        if hasattr(self.o, 'subscriptions') and len(self.o.subscriptions) > 0:
            i=0
            for s in self.o.subscriptions:
                od = sarracenia.moth.default_options()
                od.update(self.o.dictify())
                od['subscription_index']=i
                consumer = sarracenia.moth.Moth.subFactory(od)
                self.consumers.append(consumer)
                i+=1
        else:
            logger.critical('missing required subscription specification')

    def gather(self, messageCountMax) -> list:
        """
           return:
              True ... you can gather from other sources. and:
              a list of messages obtained from this source.
        """
        if not hasattr(self,'consumers'):
            return (True, [])

        messages=[]
        found_consumer=False
        i=0
        for c in self.consumers:
            if hasattr(c,'newMessages'):
                found_consumer=True
                messages.extend(c.newMessages())
            else:
                logger.warning( f'not connected. Trying to connect to {self.o.broker}')
                od = sarracenia.moth.default_options()
                od.update(self.o.dictify())
                od['subscription_index']=i
                c = sarracenia.moth.Moth.subFactory(od)
            i+=1
        return (True, messages)

    def ack(self, mlist) -> None:

        if not hasattr(self,'consumers'):
            return

        for c in self.consumers:
            for m in mlist:
                if 'ack_id' in m and m['ack_id']['broker'] == c.broker:
                    c.ack(m)

    def metricsReport(self) -> dict:

        reports={}
        if hasattr(self,'consumers'):
            i=0
            for c in self.consumers:
                if hasattr(self.o,'subscriptions'):
                    b=str(self.o.subscriptions[i]['broker'])
                    if hasattr(c,'metricsReport'):
                        reports[b]=c.metricsReport()
                i+=1
        return reports

    def on_housekeeping(self) -> None:

        if not hasattr(self,'metricsReport'):
            return

        mm = self.metricsReport()
        for b in mm:
            m = mm[b]
            average = (m['rxByteCount'] /
                   m['rxGoodCount'] if m['rxGoodCount'] != 0 else 0)
            logger.info( f"from {b} messages: good: {m['rxGoodCount']} bad: {m['rxBadCount']} " +\
               f"bytes: {naturalSize(m['rxByteCount'])} " +\
               f"average: {naturalSize(average)}" )

        if hasattr(self,'consumers'):
            for c in self.consumers:
                if hasattr(c,'metricsReset'):
                    c.metricsReset()

    def on_stop(self) -> None:

        if hasattr(self,'consumers'):
            for c in self.consumers:
                if hasattr(c,'close'):
                    c.close()

    def please_stop(self) -> None:
        """ pass stop request along to consumer Moth instance(s)
        """
        super().please_stop()
        if hasattr(self,'consumers'):
            for c in self.consumers:
                if hasattr(c,'please_stop'):
                    c.please_stop()
