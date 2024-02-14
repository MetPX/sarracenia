# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#

import os

import urllib.parse

import logging

from sarracenia import nowflt, timestr2flt, timeflt2str

from sarracenia.flowcb.nodupe import NoDupe

import redis

logger = logging.getLogger(__name__)


class Redis(NoDupe):
    """
    generalised duplicate suppression for sr3 programs. It is used as a 
    time based buffer that prevents, when activated, identical files (of some kinds) 
    from being processed more than once, by rejecting files identified as duplicates.

    options:

    nodupe_ttl - duration in seconds (floating point.)
                The time horizon of the receiption cache.
                how long to remember files, so they are rejected as duplicates.

    The expiry based on nodupe_ttl is applied every housekeeping interval.

    fileAgeMax - the oldest file that will be considered for processing.
                        files older than this threshold will be rejected.

    fileAgeMin - the newest file that can be considered for processing.
                        files newer than this threshold will be rejected.
                        if not specified, the value of option *inflight*
                        may be referenced if it is an integer value.

    """

    # ----------- magic Methods ------------
    def __init__(self, options):

        super().__init__(options,logger)
        logger.debug("NoDupe_Redis init")
        logging.basicConfig(format=self.o.logFormat, level=getattr(logging, self.o.logLevel.upper()))

        self.o.add_option( 'nodupe_ttl', 'duration', 0 ) 

        logger.info('time_to_live=%d, ' % (self.o.nodupe_ttl))

        self.o.add_option( 'nodupe_redis_serverurl', 'str')
        self.o.add_option( 'nodupe_redis_keybase', 'str', 'sr3.nodupe.' + self.o.component + '.' + self.o.config.replace(".","_")) 

        self._rkey_base = self.o.nodupe_redis_keybase
        self._rkey_count = self._rkey_base + ".count"
        self._cache_hit = None

        self._redis = redis.from_url(self.o.nodupe_redis_serverurl)

        self._last_expire = nowflt()

        self._last_time = nowflt()

        self._redis.set(self._rkey_count, 0, nx=True)
        self._last_count = self._count()


    # ----------- Private Methods -----------
    def _hash(self, text) -> str:
        from hashlib import blake2b
        h = blake2b(key=bytes(self._rkey_base, 'utf-8'), digest_size=16)
        h.update(bytes(text, 'utf-8'))
        return h.hexdigest()
    
    def _is_new(self, message) -> bool :
        """
        Derive keys to be looked up in cache of messages already seen, then look them up in the cache, 

        return False if message is a dupe.
                True if it is new.
        """

        key = self.deriveKey(message)

        if ('nodupe_override' in message) and ('path' in message['nodupe_override']):
            path = message['nodupe_override']['path']
        else:
            path = message['relPath'].lstrip('/')

        message['noDupe'] = { 'key': key, 'path': path }
        message['_deleteOnPost'] |= set(['noDupe'])

        logger.debug("checking (%s, %s)" % (key, path))

        self.cache_hit = None
        key_hashed = self._hash(key)
        path_quoted = urllib.parse.quote(path)
        path_hashed = self._hash(path)

        redis_key = self._rkey_base + ":" + key_hashed + "." + path_hashed

        got = self._redis.get(redis_key)

        #logger.debug("ttl type =%s" % (type(self.o.nodupe_ttl)) )
        self._redis.set(redis_key, str(self.now) + "|" + path_quoted, ex=int(self.o.nodupe_ttl))
        
        if got != None:
            logger.debug("entry already in cache: key=%s" % (redis_key) )
            logger.debug("updated time entry: time=%s" % (str(self.now)) )
            self.cache_hit = path_quoted
            return False
        else:
            logger.debug("adding entry to cache; key=%s" % (redis_key) )
            #self._redis.incr(self._rkey_count)
            return True

    def _count(self):
        count = self._redis.get(self._rkey_count)
        if count == None:
            return 0
        else:
            return int(count)
        
    # ----------- Public Methods -----------
    def on_housekeeping(self):

        logger.info("start")

        new_count = len(self._redis.keys(self._rkey_base + ":*"))
        self.now = nowflt()
        
        logger.info("cache size was %d items %5.2f sec ago, now saved %d entries" % (self._last_count, self.now - self._last_time, new_count))

        self._last_time = self.now

        self._last_count = new_count

    def after_accept(self, worklist):
        new_incoming = []
        self.now = nowflt()
        if self.o.fileAgeMax > 0:
            min_mtime = self.now - self.o.fileAgeMax
        else:
            min_mtime = 0

        if self.o.fileAgeMin > 0:
            max_mtime = self.now - self.o.fileAgeMin
        elif type(self.o.inflight) in [ int, float ] and self.o.inflight > 0:
            max_mtime = self.now - self.o.inflight
        else:
            # FIXME: should we add some time here to allow for different clocks?
            #        100 seconds in the future? hmm...
            max_mtime = self.now + 100

        for m in worklist.incoming:
            if ('mtime' in m) :
                mtime=timestr2flt(m['mtime'])
                if mtime < min_mtime:
                    m['_deleteOnPost'] |= set(['reject'])
                    m['reject'] = f"{m['mtime']} too old (nodupe check), oldest allowed {timeflt2str(min_mtime)}"
                    m.setReport(304,  f"{m['mtime']} too old (nodupe check), oldest allowed {timeflt2str(min_mtime)}" )
                    worklist.rejected.append(m)
                    continue
                elif mtime > max_mtime:
                    m['_deleteOnPost'] |= set(['reject'])
                    m['reject'] = f"{m['mtime']} too new (nodupe check), newest allowed {timeflt2str(max_mtime)}"
                    m.setReport(304,  f"{m['mtime']} too new (nodupe check), newest allowed {timeflt2str(max_mtime)}" )
                    worklist.rejected.append(m)
                    continue

            if '_isRetry' in m or self._is_new(m):
                new_incoming.append(m)
            else:
                m['_deleteOnPost'] |= set(['reject'])
                m['reject'] = "not modifified 1 (nodupe check)"
                m.setReport(304, 'Not modified 1 (cache check)')
                worklist.rejected.append(m)

        logger.debug("items registered in duplicate suppression cache: %d" % (len(self._redis.keys(self._rkey_base + ":*"))) )
        worklist.incoming = new_incoming

    def on_start(self):
        self._last_count = len(self._redis.keys(self._rkey_base + ":*"))
        

    def on_stop(self):
        self._last_count = None

