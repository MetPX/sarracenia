# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# more info: https://github.com/MetPX/sarracenia
#

import os, json, sys, time
from _codecs import decode, encode

from sarracenia import nowflt, timestr2flt

import logging

from sarracenia.flowcb import FlowCB
from sarracenia.featuredetection import features


# class sarra/retry

logger = logging.getLogger(__name__)


class Retry(FlowCB):
    """
    overall goal:  

    * When file transfers fail, write the messages to a queue to be retried later. 
      There is also a second retry queue for failed posts.

    how it works:

    * the after_accept checks how many incoming messages we received.
      If there is a full batch to process, don't try to retry any.

    * if there is room, then fill in the batch with some retry requests.

    * when after_work is called, the worklist.failed list of messages
      is the files where the transfer failed. write those messages to
      a retry queue.

    * the DiskQueue or RedisQueue classes are used to store the retries, and it handles
      expiry on each housekeeping event.

    """
    def __init__(self, options) -> None:

        logger.debug("sr_retry __init__")

        super().__init__(options,logger)

        if not features['retry']['present'] :
            logger.critical( f"missing retry pre-requsites, module disabled")
            return

        self.o.add_option( 'retry_driver', 'str', 'disk')

        # retry_refilter False -- rety to send with existing processing.
        # retry_refilter True -- re-ingest and re-apply processing (if it has changed.)
        self.o.add_option( 'retry_refilter', 'flag', False)

        #queuedriver = os.getenv('SR3_QUEUEDRIVER', 'disk')

        if self.o.retry_driver == 'redis':
            from sarracenia.redisqueue import RedisQueue
            self.download_retry = RedisQueue(options, 'work_retry')
            self.post_retry = RedisQueue(options, 'post_retry')
        else:
            from sarracenia.diskqueue import DiskQueue
            self.download_retry_name = 'work_retry_%02d' % options.no
            self.download_retry = DiskQueue(options, self.download_retry_name)
            self.post_retry_name = 'post_retry_%03d' % options.no
            self.post_retry = DiskQueue(options, self.post_retry_name)

        logger.debug('logLevel=%s' % self.o.logLevel)


    def gather(self, qty) -> None:
        """
        If there are only a few new messages, get some from the download retry queue and put them into
        `worklist.incoming`.

        Do this in the gather() entry point if retry_refilter is True.

        """
        if not features['retry']['present'] or not self.o.retry_refilter:
            return []

        if qty <= 0: return []

        message_list = self.download_retry.get(qty)

        # eliminate calculated values so it is refiltered from scratch.
        for m in message_list:
             for k in m:
                 if k in m['_deleteOnPost'] or k.startswith('new_'):
                     del m[k]
             m['_isRetry'] = True
             m['_deleteOnPost'] = set( [ '_isRetry' ] )


        return message_list


    def after_accept(self, worklist) -> None:
        """
        If there are only a few new messages, get some from the download retry queue and put them into
        `worklist.incoming`.

        Do this in the after_accept() entry point if retry_refilter is False.

        """
        if not features['retry']['present'] or self.o.retry_refilter:
            return

        qty = (self.o.batch / 2) - len(worklist.incoming)
        #logger.info('qty: %d len(worklist.incoming) %d' % ( qty, len(worklist.incoming) ) )

        if qty <= 0: return

        mlist = self.download_retry.get(qty)

        #logger.debug("loading from %s: qty=%d ... got: %d " % (self.download_retry_name, qty, len(mlist)))
        if len(mlist) > 0:
            worklist.incoming.extend(mlist)

    def after_work(self, worklist) -> None:
        """
        Messages in `worklist.failed` should be put in the download retry queue. If there are only a few new
        messages, get some from the post retry queue and put them into `worklist.ok`.
        """
        if not features['retry']['present'] :
            return

        if len(worklist.failed) != 0:
            #logger.debug("putting %d messages into %s" % (len(worklist.failed),self.download_retry_name) )
            self.download_retry.put(worklist.failed)
            worklist.failed = []

        # retry posting...
        qty = (self.o.batch / 2) - len(worklist.ok)
        if qty <= 0: return

        mlist = self.post_retry.get(qty)

        #logger.debug("loading from %s: qty=%d ... got: %d " % (self.post_retry_name, qty, len(mlist)))
        if len(mlist) > 0:
            worklist.ok.extend(mlist)

    def after_post(self, worklist) -> None:
        """
        Messages in `worklist.failed` should be put in the post retry queue.
        """
        if not features['retry']['present'] :
            return

        self.post_retry.put(worklist.failed)
        worklist.failed=[]

    def metricsReport(self) -> dict:
        """Returns the number of messages in the download_retry and post_retry queues.

        Returns:
            dict: containing metrics: ``{'msgs_in_download_retry': (int), 'msgs_in_post_retry': (int)}``
        """
        return {'msgs_in_download_retry': len(self.download_retry), 'msgs_in_post_retry': len(self.post_retry)}

    def on_cleanup(self) -> None:
        logger.debug('starting retry cleanup')
        self.download_retry.cleanup()
        self.post_retry.cleanup()

    def on_housekeeping(self) -> None:
        logger.info("on_housekeeping")

        self.download_retry.on_housekeeping()
        self.post_retry.on_housekeeping()

    def on_stop(self) -> None:
        self.download_retry.close()
        self.post_retry.close()
