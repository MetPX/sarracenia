# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#

import copy
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

        if not hasattr(self.o, 'post_broker'):
            return

        self.posters=[]
        i=0

        for p in self.o.publishers:
            props = sarracenia.moth.default_options()
            props.update(self.o.dictify())
            props.update(p)
            props['publisher_index']=i
            # adjust settings post_xxx to be xxx, as Moth does not use post_ ones.
            self.posters.append(sarracenia.moth.Moth.pubFactory(props))
            i+=1
        #else:
        #    logger.error( f"no publishers for {self.o.component}/{self.o.config}")


    def post(self, worklist):
        old_ok = worklist.ok
        worklist.ok = []
        all_good=True
        for m in old_ok:
            i=0
            failures=[]
            if 'publisher_index' in m:
                i=m['publisher_index']
                p=self.posters[i]
                if hasattr(p,'putNewMessage'):
                    try:
                        if not p.putNewMessage(m):
                            failures.append(i)
                    except Exception as e:
                        failures.append(i)
            else:
                for p in self.posters:
                    if hasattr(p,'putNewMessage'):
                        try:
                            if 'post_failures' in m: 
                                if i in m['post_failures']:
                                    if not p.putNewMessage(m):
                                        failures.append(i)
                            else:
                                if not p.putNewMessage(m):
                                    failures.append(i)
     
                        except Exception as e:
                            if i not in failures:
                                failures.append(i)
                            logger.error(f"crashed: {e}")
                            logger.debug("Exception details:", exc_info=True)
     
                    else:
                        failures.append( i )
                    i+=1
                   
            if len(failures)<1:
                if 'post_failures' in m:
                   del m['post_failures']
                worklist.ok.append(m)
            else:
                m['post_failures'] = failures
                m['_deleteOnPost'] |= set(['post_failures'])
                worklist.failed.append(m)


    def metricsReport(self) -> dict:

        reports={}
        if hasattr(self,'posters'):
            i=0
            for p in self.posters:
                if hasattr(p,'metricsReport'): 
                    reports[str(self.o.publishers[i]['broker'])] = p.metricsReport()
                i+=1
        return reports 

    def on_housekeeping(self):

        if hasattr(self,'publishers') and len(self.publishers)>0:
            i=0
            for p in self.posters:
                m = p.metricsReport()
                logger.debug(
                        f"messages to {str(self.o.publishers[i]['broker'])} good: {m['txGoodCount']} bad: {m['txBadCount']} bytes: {m['txByteCount']}"
                )
                p.metricsReset()
                i+=1
        else:
            logger.debug( "no metrics available" )

    def on_start(self):
        for p in self.posters:
            if hasattr(p,'putSetup'):
                p.putSetup()

        logger.debug('starting')

    def on_stop(self):
        for p in self.posters:
            if hasattr(p,'close'):
                p.close()
        logger.debug('closing')
    
    def please_stop(self) -> None:
        """ pass stop request along to publisher Moth instance(s)
        """
        super().please_stop()
        if hasattr(self, 'poster') and self.poster:
            logger.debug("asking Moth publisher to please_stop")
            for p in self.posters:
                if hasattr(p,'please_stop'):
                    p.please_stop()
