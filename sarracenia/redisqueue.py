# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# more info: https://github.com/MetPX/sarracenia
#
# Code originally contributed by:
#  Michel Grenier - Shared Services Canada
#  first shot     : Wed Jan 10 16:06:16 UTC 2018
#  re-factored beyond recognition by PSilva 2021. Don't blame Michel
#

from _codecs import decode, encode

import jsonpickle, sarracenia, sys, time
import redis, redis_lock
import re

import logging

# class sarra/retry

logger = logging.getLogger(__name__)


class RedisQueue():
    """
    Process Persistent Queue...

    Persist messages to a Redis List so that processing can be attempted again later.
    So continuous operation, with an occasional housekeeping cycle to resolve them

    retry_ttl how long 

    self.retry_cache 
    * a dictionary indexed by some sort of key to prevent duplicate
        messages being stored in it.

    If <queueName> isn't specified
    key_name = 'sr3.retry_queue.<name>.<self.o.component>.<self.o.config>
    Otherise it's
    key_name = 'sr3.retry_queue.<name>.<self.o.component>.<self.o.queueName>

    It also gets various suffixes:

    .new -- messages added to the retry are pushed to this list.
    .hk  -- temporary list used during on_housekeeping.

    whenever a message is added to the retry_cache, it is appended to a 
    cumulative list of entries to add to the retry list.  

    every housekeeping interval, the two lists are consolidated.

    note that the *ack_id* of messages retreived from the retry list, is 
    removed. Files must be acked around the time they are placed on the 
    retry_list, as reception from the source should have already been acknowledged.
    """

    # ----------- magic Methods ------------
    def __init__(self, options, name):

        logger.debug(" %s __init__" % (name))

        self.o = options

        self.name = name

        if not hasattr(self.o, 'retry_ttl'):
            self.o.retry_ttl = None

        #logging.basicConfig(format=self.o.logFormat,
        #                    level=getattr(logging, self.o.logLevel.upper()))
        logger.setLevel(getattr(logging, self.o.logLevel.upper()))

        logger.debug('name=%s logLevel=%s' % (self.name, self.o.logLevel))

        if self.o.queueName == None: 
            self.key_name = 'sr3.retry_queue.' + name + '.' + self.o.component + '.' + self.o.config
        else:
            # #"autogenerated" queueName format taken from config.py
            # test_queueName = 'q_' + self.o.broker.url.username + '_' + self.o.component + '\.' + self.o.config
            # if hasattr(self.o, 'queue_suffix') and self.o.queue_suffix != None:
            #     test_queueName += '\.' + self.o.queue_suffix
            # test_queueName += '\.[0-9]{8}\.[0-9]{8}'
            # match = re.search(test_queueName ,self.o.queueName)
            # if match:
            #     logger.warn("Detected possible autogenerated queueName %s; should set it in config to avoid issues" % (self.o.queueName))
            
            self.key_name = 'sr3.retry_queue.' + name + '.' + self.o.component + '.' + self.o.queueName

        self.now = sarracenia.nowflt()

        # newer retries
        self.key_name_new = self.key_name + '.new'

        # working file at housekeeping
        self.key_name_hk = self.key_name + '.hk'

        # track last housekeeping to ensure that multiple instances don't try to do it more often than the defined interval
        self.key_name_lasthk = 'sr3.retry_queue.' + name + '.' + self.o.component + '.' + self.o.config + ".last_hk"

        self.o.add_option( 'redisqueue_serverurl', 'str')

        self.redis = redis.from_url(self.o.redisqueue_serverurl)

        self.redis.set(self.key_name_lasthk, self.now)

        # The lock will be set with a TTL of 'expire', but will auto renew at expire*2/3
        #  This should allow a crashed/failed/terminated instances' locks to clear out so others can do it
        self.redis_lock = redis_lock.Lock(self.redis, self.key_name_hk, expire=30, auto_renewal=True)

        # initialize ages and message counts


    def __len__(self) -> int:
        """Returns the total number of messages in the RedisQueue.

        Number of messages in the RedisQueue does not necessarily equal the number of messages available to ``get``.
        Messages in the .new list are counted, but can't be retrieved until
        :func:`~sarracenia.redisqueue.RedisQueue.on_housekeeping` has been run.

        Returns:
            int: number of messages in the RedisQueue.
        """
        return self.redis.llen(self.key_name) + self.redis.llen(self.key_name_new) 


    # ----------- Private Methods -----------
    def _in_cache(self, message) -> bool:
        """
        return whether the entry is message is in the cache or not.
        side effect: adds it.

        """
        urlstr = message['baseUrl'] + '/' + message['relPath']

        if 'noDupe' in message:
            sumstr = jsonpickle.encode(message['noDupe']['key'])
        elif 'fileOp' in message:
            sumstr = jsonpickle.encode(message['fileOp'])
        elif 'identity' in message:
            sumstr = jsonpickle.encode(message['identity'])
        elif 'pubTime' in message:
            sumstr = jsonpickle.encode(message['pubTime'])
        else:
            logger.info('no key found for message, cannot add')
            return False

        cache_key = urlstr + ' ' + sumstr

        if 'parts' in message:
            cache_key += ' ' + message['parts']

        if cache_key in self.retry_cache: return True
        self.retry_cache[cache_key] = True
        return False

    def _is_expired(self, message) -> bool:
        """
        return is the given message expired ?
        """
        # no expiry
        if self.o.retry_ttl is None: return False
        if self.o.retry_ttl <= 0: return False

        # compute message age
        msg_time = sarracenia.timestr2flt(message['pubTime'])
        msg_age = self.now - msg_time

        # expired ?
        return msg_age > self.o.retry_ttl

    def _needs_requeuing(self, message) -> bool:
        """
        return 
            * True if message is not expired, and not already in queue. 
            * False otherwise.   
        """
        if self._in_cache(message):
            logger.info("discarding duplicate message (in %s cache) %s" % (self.name, message))
            return False

        # log is info... it is good to log a retry message that expires
        if self._is_expired(message):
            logger.info("discarding expired message in (%s): %s" % (self.name, message))
            return False

        return True


    def _msgFromJSON(self, message):
        try:
            msg = jsonpickle.decode(message)
        except ValueError:
            logger.error("corrupted item in list: %s " % (message))
            logger.debug("Error information: ", exc_info=True)
            return None
        except TypeError:
            logger.error("wrong type item in list: %s " % (message))
            logger.debug("Error information: ", exc_info=True)
            return None

        return msg

    def _msgToJSON(self, message):
        return jsonpickle.encode(message)

    def _lpop(self, queue):

        raw_msg = self.redis.lpop(queue)
          
        if raw_msg == None:
            return None

        msg = self._msgFromJSON(raw_msg)
        logger.debug("lpop from list %s %s" % (queue, msg))

        return msg


    # ----------- Public Methods -----------
    def put(self, message_list):
        """
        add messages to the end of the queue.
        """

        for message in message_list:
            logger.debug("rpush to list %s %s" % (self.key_name_new, message))
            self.redis.rpush(self.key_name_new, self._msgToJSON(message))

    def cleanup(self):
        """
        remove statefiles.
        """
        logger.debug("Starting redis cleanup")
        self.redis_lock.reset()
        self.redis.delete(self.key_name_lasthk)
        self.redis.delete(self.key_name_new)
        self.redis.delete(self.key_name_hk)
        self.redis.delete(self.key_name)
        logger.debug("done redis cleanup")

    def close(self):
        """
        clean shutdown.
        """
        #self.redis_lock.reset()

        self.redis = None

    def get(self, maximum_messages_to_get=1):
        """
        qty number of messages to retrieve from the queue.
        """

        ml = []

        if self.redis_lock.locked():
            logger.debug("Can't pop because housekeeping lock is active")
            return ml

        count = 0
        while count < maximum_messages_to_get:

            message = self._lpop(self.key_name)
            if not message: break
                
            if self._is_expired(message):
                logger.warn("message expired %s" % (message))
                continue

            if 'ack_id' in message:
                del message['ack_id']
                message['_deleteOnPost'].remove('ack_id')

            ml.append(message)
            count += 1

        return ml

    def on_housekeeping(self):
        """
        read rest of queue_file (from current point of unretried ones.)
            - check if message is duplicate or expired.
            - write to .hk

        read .new file, 
            - check if message is duplicate or expired.
            - writing to .hk (housekeeping)

        remove .new

        rename housekeeping to queue for next period.
        """
        logger.info("%s on_housekeeping" % (self.name))

        if float(self.redis.get(self.key_name_lasthk)) + self.o.housekeeping > sarracenia.nowflt():
            logger.info("Housekeeping ran less than %ds ago; not running " % (self.o.housekeeping))
            return

        # A shared/distributed locking system is required when using Redis
        #  because only a single instance of a config should ever run the Housekeeping tasks
        if self.redis_lock.locked():
            logger.info("Another instance has lock on %s" % (self.key_name_hk))
            while self.redis_lock.locked():
                time.sleep(1)
            return

        self.redis_lock.acquire()
        logger.info("got redis_lock %s" % (self.key_name_hk))

        # finish retry before reshuffling all retries entries
        if self.redis.llen(self.key_name) > 0:
            logger.info("have not finished retry list; resuming retries from %s" % (self.key_name))
            return

        self.now = sarracenia.nowflt()
        self.retry_cache = {}
        N = 0

        # put this in try/except in case ctrl-c breaks something
        try:
            try:
                logger.debug('delete list: %s' % (self.key_name_hk))
                self.redis.delete(self.key_name_hk)
            except:
                pass

            i = 0

            logger.debug("%s has queue %s" % (self.key_name, bool(self.redis.llen(self.key_name))))

            # remaining of retry to housekeeping
            while True:

                message = self._lpop(self.key_name)
                if not message: break

                i = i + 1
                if not self._needs_requeuing(message): continue

                logger.debug("remaining of retry - rpush to %s %s" % (self.key_name_hk, message))
                self.redis.rpush(self.key_name_hk, self._msgToJSON(message))
                N = N + 1

            i = 0
            j = N

            # append new to housekeeping.
            while True:

                message = self._lpop(self.key_name_new)
                if not message: break

                i = i + 1
                #logger.debug("DEBUG message %s" % message)
                if not self._needs_requeuing(message): continue

                logger.debug("new to hk - rpush to %s %s" % (self.key_name_hk, message))
                self.redis.rpush(self.key_name_hk, self._msgToJSON(message))
                N = N + 1

            logger.debug("FIXME DEBUG took %d out of the %d retry" % (N - j, i))

        except Exception as Err:
            logger.error("something went wrong")
            logger.debug('Exception details: ', exc_info=True)

        # no more retry
        if N == 0:
            logger.info("No retry in list")
            try:
                logger.debug('no more retry - delete list: %s' % (self.key_name_hk))
                self.redis.delete(self.key_name_hk)
            except:
                pass

        # housekeeping file becomes new retry
        else:
            logger.info("Number of messages in retry list %d" % (N))

            try:
                logger.debug('rename list %s to %s' % (self.key_name_hk, self.key_name))
                self.redis.rename(self.key_name_hk, self.key_name)

            except Exception as Err:
                logger.error("Something went wrong with rename")
                logger.debug('Exception details: ', exc_info=True)


        self.redis.set(self.key_name_lasthk, self.now)
        self.redis_lock.release()
        logger.debug("released redis_lock")

        elapse = sarracenia.nowflt() - self.now
        logger.info("on_housekeeping elapse %f" % (elapse))