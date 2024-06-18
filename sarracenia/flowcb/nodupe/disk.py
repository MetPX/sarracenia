# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#

import os

import urllib.parse

import logging

from sarracenia import nowflt, timestr2flt, timeflt2str

from sarracenia.flowcb.nodupe import NoDupe

logger = logging.getLogger(__name__)


class Disk(NoDupe):
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

       NoDupe supports/uses::
       
           cache_file : default ~/.cache/sarra/'pgm'/'cfg'/recent_files_0001.cache
                        each line in file is
                        sum time path part
       
           cache_dict : {}
                        cache_dict[key] = {path1: time1, path2: time2, ...}
       
    """
    def __init__(self, options):

        super().__init__(options,logger)
        logger.debug("NoDupe init")
        logging.basicConfig(format=self.o.logFormat, level=getattr(logging, self.o.logLevel.upper()))

        self.o.add_option( 'nodupe_ttl', 'duration', 0 ) 

        self.cache_dict = {}
        self.cache_file = None
        self.cache_hit = None
        self.fp = None

        self.last_expire = nowflt()
        self.count = 0

        self.last_time = nowflt()
        self.last_count = 0

    def on_housekeeping(self):

        logger.debug("start with %d entries)" % len(self.cache_dict))

        count = self.count
        self.save()

        self.now = nowflt()
        new_count = self.count

        if new_count > 0:
            logger.info( "was %d, but since %5.2f sec, increased up to %d, now saved %d entries"
                 % (self.last_count, self.now - self.last_time, count, new_count))

        self.last_time = self.now
        self.last_count = new_count

    def _not_in_cache(self, key, relpath) -> bool:
        """  return False if the given key=relpath value is already in the cache,
                    True otherwise
             side effect: add it to the cache if it isn't there.
        """
        # not found
        self.cache_hit = None
        qpath = urllib.parse.quote(relpath)

        if key not in self.cache_dict:
            logger.debug("adding entry to NoDupe cache")
            kdict = {}
            kdict[relpath] = self.now
            self.cache_dict[key] = kdict
            self.fp.write("%s %f %s\n" % (key, self.now, qpath))
            self.count += 1
            return True

        logger.debug( f"entry already in NoDupe cache: key={key}" )
        kdict = self.cache_dict[key]
        present = relpath in kdict
        kdict[relpath] = self.now

        # differ or newer, write to file
        self.fp.write("%s %f %s\n" % (key, self.now, qpath))
        self.count += 1

        if present:
            logger.debug( f"updated time of old NoDupe entry: relpath={relpath}" )
            self.cache_hit = relpath
            return False
        else:
            logger.debug( f"added relpath={relpath}")

        return True

    def check_message(self, msg) -> bool :
        """
           derive keys to be looked up in cache of messages already seen.
           then look them up in the cache, 

           return False if message is a dupe.
                  True if it is new.
        """

        key = self.deriveKey(msg)

        if ('nodupe_override' in msg) and ('path' in msg['nodupe_override']):
            path = msg['nodupe_override']['path']
        else:
            path = msg['relPath'].lstrip('/')

        msg['noDupe'] = { 'key': key, 'path': path }
        msg['_deleteOnPost'] |= set(['noDupe'])

        logger.debug("NoDupe calling check( %s, %s )" % (key, path))
        return self._not_in_cache(key, path)

    def after_accept(self, worklist):
        new_incoming = []
        self.now = nowflt()
        if self.o.fileAgeMax > 0:
            min_mtime = self.now - self.o.fileAgeMax
        else:
            min_mtime = 0

        if self.o.fileAgeMin > 0:
            max_mtime = self.now - self.o.fileAgeMin
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

            if '_isRetry' in m or self.check_message(m):
                new_incoming.append(m)
            else:
                m['_deleteOnPost'] |= set(['reject'])
                m['reject'] = "not modifified 1 (nodupe check)"
                m.setReport(304, 'Not modified 1 (cache check)')
                worklist.rejected.append(m)

        if self.fp:
            self.fp.flush()
        logger.debug( f"items registered in duplicate suppression cache: {len(self.cache_dict.keys())}" )
        worklist.incoming = new_incoming

    def on_start(self):
        self.open()

    def on_stop(self):
        self.save()
        self.close()

    def clean(self, persist=False, delpath=None):
        logger.debug("start")

        # create refreshed dict

        now = nowflt()
        new_dict = {}
        self.count = 0

        if delpath is not None:
            qdelpath = urllib.parse.quote(delpath)
        else:
            qdelpath = None

        # from  cache[sum] = [(time,[path,part]), ... ]
        for key in self.cache_dict.keys():
            ndict = {}
            kdict = self.cache_dict[key]

            for value in kdict:
                # expired or keep
                t = kdict[value]
                ttl = now - t
                if ttl > self.o.nodupe_ttl: continue

                parts = value.split('*')
                path = parts[0]
                qpath = urllib.parse.quote(path)

                if qpath == qdelpath: continue

                ndict[value] = t
                self.count += 1

                if persist:
                    self.fp.write("%s %f %s\n" % (key, t, qpath))

            if len(ndict) > 0: new_dict[key] = ndict

        # set cleaned cache_dict
        self.cache_dict = new_dict

    def close(self, unlink=False):
        logger.debug("start")
        try:
            self.fp.flush()
            self.fp.close()
        except Exception as err:
            logger.warning('did not close: cache_file={}, err={}'.format(
                self.cache_file, err))
            logger.debug('Exception details:', exc_info=True)
        self.fp = None

        if unlink:
            try:
                os.unlink(self.cache_file)
            except Exception as err:
                logger.warning("did not unlink: cache_file={}: err={}".format(
                    self.cache_file, err))
                logger.debug('Exception details:', exc_info=True)
        self.cache_dict = {}
        self.count = 0

    def delete_path(self, delpath):
        logger.debug("start")

        # close,remove file, open new empty file
        self.fp.close()
        if os.path.exists(self.cache_file):
            os.unlink(self.cache_file)
        self.fp = open(self.cache_file, 'w')

        # clean cache removing delpath
        self.clean(persist=True, delpath=delpath)

    def free(self):
        logger.debug("start")
        self.cache_dict = {}
        self.count = 0
        try:
            os.unlink(self.cache_file)
        except Exception as err:
            logger.warning("did not unlink: cache_file={}, err={}".format(
                self.cache_file, err))
            logger.debug('Exception details:', exc_info=True)
        self.fp = open(self.cache_file, 'w')

    def load(self):
        logger.debug("start")
        self.cache_dict = {}
        self.count = 0

        # create file if not existing
        if not os.path.isfile(self.cache_file):
            self.fp = open(self.cache_file, 'w')
            self.fp.close()

        # set time
        now = nowflt()

        # open file (read/append)...
        # read through
        # keep open to append entries

        self.fp = open(self.cache_file, 'r+')
        lineno = 0
        while True:
            # read line, parse words
            line = self.fp.readline()
            if not line: break
            lineno += 1

            # words  = [ sum, time, path ]
            try:
                words = line.split()
                key = words[0]
                ctime = float(words[1])
                qpath = words[2]
                path = urllib.parse.unquote(qpath)

                # skip expired entry

                ttl = now - ctime
                if ttl > self.o.nodupe_ttl: continue

            except Exception as err:
                err_msg_fmt = "load corrupted: lineno={}, cache_file={}, err={}"
                logger.error(err_msg_fmt.format(lineno, self.cache_file, err))
                logger.debug('Exception details:', exc_info=True)
                continue

            #  add info in cache

            if key in self.cache_dict: kdict = self.cache_dict[key]
            else: kdict = {}

            if not path in kdict: self.count += 1

            kdict[path] = ctime
            self.cache_dict[key] = kdict

    def open(self, cache_file=None):

        self.cache_file = cache_file

        if cache_file is None:
            self.cache_file = self.o.cfg_run_dir + os.sep
            self.cache_file += 'recent_files_%.3d.cache' % self.o.no

        self.load()

    def save(self):
        logger.debug("NoDupe save")

        # close,remove file
        if self.fp: self.fp.close()
        try:
            os.unlink(self.cache_file)
        except Exception as err:
            logger.warning("did not unlink: cache_file={}, err={}".format(
                self.cache_file, err))
            logger.debug('Exception details:', exc_info=True)
        # new empty file, write unexpired entries
        try:
            self.fp = open(self.cache_file, 'w')
            self.clean(persist=True)
        except Exception as err:
            logger.warning("did not clean: cache_file={}, err={}".format(
                self.cache_file, err))
            logger.debug('Exception details:', exc_info=True)
