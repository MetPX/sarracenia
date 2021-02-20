#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# more info: https://github.com/MetPX/sarracenia
#
# sr_retry.py : python3 standalone retry logic/testing
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  first shot     : Wed Jan 10 16:06:16 UTC 2018
#

import os, json, sys, time
from _codecs import decode, encode

from sarracenia import nowflt, timestr2flt

import logging

from sarracenia.flowcb import FlowCB

# class sarra/retry

logger = logging.getLogger(__name__)


class Retry(FlowCB):
    """
    Persist messages to a file so that processing can be attempted again later.
    For safety reasons, want to be writing to a file ASAP.
    For performance reasons, all those writes need to be Appends.

    so continuous, but append-only io... with an occasional housekeeping cycle.
    to resolve them
   
    retry_ttl how long 
    self.retry_cache 
          - a dictionary indexed by some sort of key to prevent duplicate messages
            being stored in it.

    retry_path = ~/.cache/sarra/<component>/<config>/instance_name.retry
    with various suffixes:

    .new  -- messages added to the retry list are appended to this file.

    .state.work --

    .state
            
    whenever a message is added to the retry_cache, it is appended to a cumulative
    list of entries to add to the retry list.  
      

    One must remove the *delivery_tag* of messages placed on the retry list,
    as reception from the source has already been acknowledged.
    """
    def __init__(self, options):

        logger.debug("sr_retry __init__")

        self.o = options

        if not hasattr(self.o, 'retry_ttl'):
            self.o.retry_ttl = None

        #logging.basicConfig(format=self.o.logFormat,
        #                    level=getattr(logging, self.o.logLevel.upper()))
        logger.setLevel(getattr( logging, self.o.logLevel.upper()))

        logger.debug('logLevel=%s' % self.o.logLevel)

        # initialize all retry path if retry_path is provided
        if hasattr(self.o, 'retry_path'): self.init()

    def add_msg_to_state_file(self, message, done=False):

        logger.debug("DEBUG add to state file %s %s %s" %
                     (os.path.basename(self.state_path), message, done))
        self.state_fp = self.msg_append_to_file(self.state_fp, self.state_path,
                                                message, done)
        # performance issue... only do before close
        #os.fsync(self.state_fp)

    def add_msg_to_new_file(self, message):
        logger.debug("DEBUG add to new file %s %s" %
                     (os.path.basename(self.new_path), message))
        self.new_fp = self.msg_append_to_file(self.new_fp, self.new_path,
                                              message)
        # performance issue... only do before close
        #os.fsync(self.new_fp)

    def cleanup(self):

        if os.path.exists(self.o.retry_path):
            os.unlink(self.o.retry_path)

        if hasattr(self.o, 'retry_work'):
            if os.path.exists(self.o.retry_work):
                os.unlink(self.o.retry_work)

    def close(self):
        try:
            self.heart_fp.close()
        except:
            pass
        try:
            os.fsync(self.new_fp)
            self.new_fp.close()
        except:
            pass
        try:
            self.retry_fp.close()
        except:
            pass
        try:
            os.fsync(self.state_fp)
            self.state_fp.close()
        except:
            pass
        self.heart_fp = None
        self.new_fp = None
        self.retry_fp = None
        self.state_fp = None

    def msgFromJSON(self, line):
        try:
            msg = json.loads(line)
            if '_deleteOnPost' in msg:
                msg['_deleteOnPost'] = set( msg['_deleteOnPost'] )
        except ValueError:
            logger.error("corrupted line in retry file: %s " % line)
            logger.debug("Error information: ", exc_info=True)
            return None

        return msg

    def msgToJSON(self, message, done=False):
        #logger.debug('Encoding msg to json: message={}'.format(message))

        if done:
            message['_retry_tag_'] = 'done'
            message['_deleteOnPost'] |= set(['_retry_tag_'])

        if '_deleteOnPost' in message:
            message['_deleteOnPost'] = list( message['_deleteOnPost'] )
        s = json.dumps(message, sort_keys=True) + '\n'
        #logger.debug('json version={}'.format(s))

        return s

    def get(self):
        """
          can we delete this function?
        """
        ok = False

        while not ok:
            ok, message = self.get_retry()

        return message

    def get_retry(self):
        self.retry_fp, message = self.msg_get_from_file(
            self.retry_fp, self.retry_path)

        # FIXME MG as discussed with Peter
        # no housekeeping in get ...
        # if no message (and new or state file there)
        # we wait for housekeeping to present retry messages
        if not message:
            try:
                os.unlink(self.retry_path)
            except:
                pass
            self.retry_fp = None
            #logger.debug("MG DEBUG retry get return None")
            return True, None

        # validation

        if not self.is_valid(message):
            #logger.error("MG invalid %s" % message)
            return False, None

        message['isRetry'] = True
        message['_deleteOnPost'] |= set(['isRetry'])

        return True, message

    def on_filter(self, worklist):
        """
          if there are no new messages, then get one from the retry list,
          and try processing that again.
        """

        qty = (self.o.batch / 2) - len(worklist.incoming)

        while qty > 0:
            (ok, m) = self.get_retry()

            if m is None:
                break

            logger.debug("loading from retry: qty=%d ... %s " % (qty, m))
            worklist.incoming.append(m)
            qty -= 1

        return True

    def init(self):

        # retry messages

        self.retry_path = self.o.retry_path
        self.retry_work = self.retry_path + '.work'
        self.retry_fp = None

        # newer retries

        self.new_path = self.o.retry_path + '.new'
        self.new_work = self.new_path + '.work'
        self.new_fp = None

        # state retry messages

        self.state_path = self.o.retry_path + '.state'
        self.state_work = self.state_path + '.work'
        self.state_fp = None

        # working file at housekeeping

        self.heart_path = self.o.retry_path + '.heart'
        self.heart_fp = None

    def in_cache(self, message):
        """
          return whether the entry is message is in the cache or not.
          side effect: adds it.

        """
        urlstr = message['baseUrl'] + '/' + message['relPath']
        sumstr = json.dumps(message['integrity'])
        cache_key = urlstr + ' ' + sumstr

        if 'parts' in message:
            cache_key += ' ' + message['parts']

        if cache_key in self.retry_cache: return True
        self.retry_cache[cache_key] = True
        return False

    def is_done(self, message):
        return ('_retry_tag_' in message) and (
            message['_retry_tag_'] == 'done')

    def is_expired(self, message):
        # no expiry
        if self.o.retry_ttl is None: return False
        if self.o.retry_ttl <= 0: return False

        # compute message age
        msg_time = timestr2flt(message['pubTime'])
        msg_age = nowflt() - msg_time

        # expired ?

        expired = msg_age > (self.o.retry_ttl / 1000)

        #logger.debug("DEBUG message is %d seconds old, retry_ttl is %d" % (msg_age, self.o.retry_ttl ) )

        return expired

    def is_valid(self, message):
        # validation

        # log is info... it is good to log a retry message that expires
        if self.is_expired(message):
            logger.info("expired message skipped %s" % message)
            return False

        # log is debug... the retry message was processed
        if self.is_done(message):
            logger.debug("done message skipped %s" % message)
            return False

        return True

    def msg_append_to_file(self, fp, path, message, done=False):
        if fp is None:
            fp = open(path, 'a')

        try:
            fp.write(self.msgToJSON(message, done))
            fp.flush()
        except:
            logger.error("failed to serialize message to JSON: %s" % message)
            logger.debug('Exception details:', exc_info=True)
        return fp

    def msg_get_from_file(self, fp, path):
        if fp is None:
            if not os.path.isfile(path): return None, None
            logger.debug("DEBUG %s open read" % path)
            fp = open(path, 'r')

        line = fp.readline()
        if not line:
            try:
                fp.close()
            except:
                pass
            return None, None

        msg = self.msgFromJSON(line)
        # a corrupted line : go to the next
        if msg is None: return self.msg_get_from_file(fp, path)

        return fp, msg

    def on_housekeeping(self):
        logger.info("sr_retry on_housekeeping")

        # finish retry before reshuffling all retries entries

        if os.path.isfile(self.retry_path) and self.retry_fp != None:
            logger.info("sr_retry resuming with retry file")
            return

        now = nowflt()
        self.retry_cache = {}
        N = 0

        # put this in try/except in case ctrl-c breaks something

        try:
            self.close()
            try:
                os.unlink(self.heart_path)
            except:
                pass
            fp = open(self.heart_path, 'w')
            fp.close()

            # rename to working file to avoid corruption

            if not os.path.isfile(self.retry_work):
                if os.path.isfile(self.retry_path):
                    os.rename(self.retry_path, self.retry_work)
                else:
                    fp = open(self.retry_work, 'w')
                    fp.close()

            if not os.path.isfile(self.state_work):
                if os.path.isfile(self.state_path):
                    os.rename(self.state_path, self.state_work)
                else:
                    fp = open(self.state_work, 'w')
                    fp.close()

            if not os.path.isfile(self.new_work):
                if os.path.isfile(self.new_path):
                    os.rename(self.new_path, self.new_work)
                else:
                    fp = open(self.new_work, 'w')
                    fp.close()

            # state to heart

            #logger.debug("MG DEBUG has state %s" % os.path.isfile(self.state_path))

            i = 0
            last = None

            fp = None
            while True:
                fp, message = self.msg_get_from_file(fp, self.state_work)
                if not message: break
                i = i + 1
                #logger.debug("DEBUG message %s" % message)
                if self.in_cache(message): continue
                valid = self.is_valid(message)
                if not valid: continue

                #logger.debug("DEBUG flush retry to state %s" % message)
                self.heart_fp = self.msg_append_to_file(
                    self.heart_fp, self.heart_path, message)
                N = N + 1
            try:
                fp.close()
            except:
                pass

            #logger.debug("MG DEBUG took %d out of the %d state" % (N, i))

            # remaining of retry to heart

            #logger.debug("MG DEBUG has retry %s" % os.path.isfile(self.retry_path))

            i = 0
            j = N

            fp = None
            while True:
                fp, message = self.msg_get_from_file(fp, self.retry_work)
                if not message: break
                i = i + 1
                logger.debug("DEBUG message %s" % message)
                if self.in_cache(message): continue
                if not self.is_valid(message): continue

                #logger.debug("MG DEBUG flush retry to state %s" % message)
                self.heart_fp = self.msg_append_to_file(
                    self.heart_fp, self.heart_path, message)
                N = N + 1
            try:
                fp.close()
            except:
                pass

            #logger.debug("MG DEBUG took %d out of the %d retry" % (N - j, i))

            # new to heart

            #logger.debug("MG DEBUG has new %s" % os.path.isfile(self.new_path))

            i = 0
            j = N

            fp = None
            while True:
                fp, message = self.msg_get_from_file(fp, self.new_work)
                if not message: break
                i = i + 1

                if self.in_cache(message): continue
                if not self.is_valid(message): continue

                #logger.debug("MG DEBUG flush retry to state %s" % message)
                self.heart_fp = self.msg_append_to_file(
                    self.heart_fp, self.heart_path, message)
                N = N + 1
            try:
                fp.close()
            except:
                pass

            #logger.debug("MG DEBUG took %d out of the %d new" % (N - j, i))

            # close heart

            try:
                close(self.heart_fp)
            except:
                pass

        except:
            logger.error("sr_retry/on_housekeeping: something went wrong")
            logger.debug('Exception details: ', exc_info=True)

        # no more retry

        if N == 0:
            logger.info("No retry in list")
            try:
                os.unlink(self.heart_path)
            except:
                pass

        # housekeeping file becomes new retry

        else:
            logger.info("Number of messages in retry list %d" % N)
            try:
                os.rename(self.heart_path, self.retry_path)
            except:
                logger.error("Something went wrong with rename")

        # cleanup
        try:
            os.unlink(self.state_work)
        except:
            pass
        try:
            os.unlink(self.retry_work)
        except:
            pass
        try:
            os.unlink(self.new_work)
        except:
            pass

        self.last_body = None
        elapse = nowflt() - now
        logger.info("sr_retry on_housekeeping elapse %f" % elapse)

    def on_work(self, worklist):
        """
         worklist.failed should be put on the retry list.
        """
        if len(worklist.failed) == 0:
            return

        logger.debug("adding %d to retry _list" % len(worklist.failed))

        for m in worklist.failed:
            if ('isRetry' in m) and m['isRetry']:
                if 'delivery_tag' in m:
                    del m['delivery_tag']
                self.add_msg_to_new_file(m)
            else:
                self.add_msg_to_state_file(m)

        worklist.failed = []

    def on_start(self):
        logger.info("sr_retry on_start")

        if not os.path.isfile(self.retry_path): return

        retry_age = os.stat(self.retry_path).st_mtime

        if os.path.isfile(self.state_path):
            state_age = os.stat(self.state_path).st_mtime
            if retry_age > state_age: os.unlink(self.state_path)

        if os.path.isfile(self.new_path):
            new_age = os.stat(self.new_path).st_mtime
            if retry_age > new_age: os.unlink(self.new_path)
