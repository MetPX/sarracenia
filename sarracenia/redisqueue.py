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
import redis, os

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
    key_name = 'sr3queue.<name>.<self.o.component>.<self.o.config>
    Otherise it's
    key_name = 'sr3queue.<name>.<self.o.component>.<self.o.queueName>

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
            self.key_name = 'sr3queue.' + name + '.' + self.o.component + '.' + self.o.config
        else:
            self.key_name = 'sr3queue.' + name + '.' + self.o.component + '.' + self.o.queueName

        self.now = sarracenia.nowflt()

        # newer retries
        self.key_name_new = self.key_name + '.new'

        # working file at housekeeping
        self.key_name_hk = self.key_name + '.hk'

        self.o.add_option( 'redisqueue_serverurl', 'str')
        self.o.add_option( 'redisqueue_stacktype', 'str', 'FIFO')
        
        #self.redisurl = os.getenv('SR3_REDISURL', 'redis://localhost:6379/0')
        #self.queue_stack_type = os.getenv('SR3_QUEUE_STACK_TYPE', 'FIFO').upper()

        self.redis = redis.from_url(self.o.redisqueue_serverurl)

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
        elif 'integrity' in message:
            sumstr = jsonpickle.encode(message['integrity'])
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

    # def msg_get_from_file(self, fp, path):
    #     """
    #         read a message from the state file.
    #     """
    #     if fp is None:
    #         if not os.path.isfile(path): return None, None
    #         logger.debug("DEBUG %s open read" % path)
    #         fp = open(path, 'r')
    #
    #     line = fp.readline()
    #     if not line:
    #         try:
    #             fp.close()
    #         except:
    #             pass
    #         return None, None
    #
    #     msg = self._msgFromJSON(line)
    #     # a corrupted line : go to the next
    #     if msg is None: return self.msg_get_from_file(fp, path)
    #
    #    return fp, msg


    # def _count_msgs(self, file_path) -> int:
    #     """Count the number of messages (lines) in the queue file. This should be used only when opening an existing
    #     file, because :func:`~sarracenia.diskqueue.DiskQueue.get` does not remove messages from the file.

    #     Args:
    #         file_path (str): path to the file to be counted.

    #     Returns:
    #         int: count of messages in file, -1 if the file could not be read.
    #     """
    #     count = -1

    #     if os.path.isfile(file_path):
    #         count = 0
    #         with open(file_path, mode='r') as f:
    #             for line in f:
    #                 if "{" in line:
    #                     count +=1
    #
    #    return count

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

    def _pop(self, queue):
        # Default behaviour is same as DiskQueue (pop off the head, push to the tail)
        #  Specifying a stacktype of LIFO makes it pop the newest items first
        if self.o.redisqueue_stacktype == "LIFO":
            json_msg = self.redis.rpop(queue)
            logger.debug("rpop from list %s %s" % (queue, json_msg))
        else:
            json_msg = self.redis.lpop(queue)
            logger.debug("lpop from list %s %s" % (queue, json_msg))

        if json_msg == None:
            return None

        return self._msgFromJSON(json_msg)


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
        #self.redis.delete(self.key_name)
        self.redis.delete(self.key_name)

    def close(self):
        """
        clean shutdown.
        """

        self.redis = None

    def get(self, maximum_messages_to_get=1):
        """
        qty number of messages to retrieve from the queue.
        """

        ml = []
        count = 0
        while count < maximum_messages_to_get:

            message = self._pop(self.key_name)

            if not message:
                break

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

                message = self._pop(self.key_name)

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

                message = self._pop(self.key_name_new)
                
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


        # cleanup
        try:
            logger.debug('cleanup - delete list: %s' % (self.key_name_new))
            self.redis.delete(self.key_name_new)
        except:
            pass

        elapse = sarracenia.nowflt() - self.now
        logger.info("on_housekeeping elapse %f" % (elapse))
