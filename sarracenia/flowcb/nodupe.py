#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#
# duplicate_suppression.py : python3 program that generalise suppress_duplicates for sr
#            programs, it is used as a time based buffer that prevents, when activated,
#            identical files (of some kinds) from being processed more than once.
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Wed Jul 26 18:57:19 UTC 2017
#  copied and re-arranged after his retirement... don't blame him any more...
#  He wrote it as sr_cache.py Peter Silva turned it into a v3 plugin.
#

import os

import urllib.parse

import logging

from sarracenia import msg_set_report

#============================================================
# NoDupe supports/uses :
#
# cache_file : default ~/.cache/sarra/'pgm'/'cfg'/recent_files_0001.cache
#              each line in file is
#              sum time path part
#
# cache_dict : {}
#              cache_dict[sum] = {path1*part1: time1, path2*part2: time2, ...}
#

from sarracenia import nowflt

from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class NoDupe(FlowCB):
    """

       options:

       suppress_duplicates - duration in seconds (floating point.)
       basis - 'data', 'path', 'name'

    """
    def __init__(self, options):
        logger.debug("NoDupe init")

        self.o = options

        logging.basicConfig(format=self.o.logFormat,
                            level=getattr(logging, self.o.logLevel.upper()))

        if hasattr(options, 'suppress_duplicates'):
            self.o.time_to_live = options.suppress_duplicates

        if hasattr(options, 'suppress_duplicates_basis'):
            self.o.basis = options.suppress_duplicates_basis

        logger.info( 'time_to_live=%d, basis=%s, log_reject=%s' % \
           ( self.o.time_to_live, self.o.basis, self.o.log_reject ) )

        self.cache_dict = {}
        self.cache_file = None
        self.cache_hit = None
        self.fp = None

        self.last_expire = nowflt()
        self.count = 0

        self.last_time = nowflt()
        self.last_count = 0

    def on_housekeeping(self):

        logger.info("start (%d)" % len(self.cache_dict))

        count = self.count
        self.save()

        self.now = nowflt()
        new_count = self.count

        logger.info(
            "was %d, but since %5.2f sec, increased up to %d, now saved %d entries"
            % (self.last_count, self.now - self.last_time, count, new_count))

        self.last_time = self.now
        self.last_count = new_count

    def check(self, key, path, part):
        # not found
        self.cache_hit = None

        # set time and value
        relpath = self.__get_relpath(path)
        qpath = urllib.parse.quote(relpath)
        value = '%s*%s' % (relpath, part)

        if key not in self.cache_dict:
            #logger.debug("adding a new entry in NoDupe cache")
            kdict = {}
            kdict[value] = self.now
            self.cache_dict[key] = kdict
            self.fp.write("%s %f %s %s\n" % (key, self.now, qpath, part))
            self.count += 1
            return True

        #logger.debug("sum already in NoDupe cache: key={}".format(key))
        kdict = self.cache_dict[key]
        present = value in kdict
        kdict[value] = self.now

        # differ or newer, write to file
        self.fp.write("%s %f %s %s\n" % (key, self.now, qpath, part))
        self.count += 1

        if present:
            #logger.debug("updated time of old NoDupe entry: value={}".format(value))
            self.cache_hit = value
            return False
        else:
            logger.debug("added value={}".format(value))

        if part is None or part[0] not in "pi":
            logger.debug("new entry, not a part: part={}".format(part))
            return True

        ptoken = part.split(',')
        if len(ptoken) < 4:
            logger.debug("new entry, weird part: ptoken={}".format(ptoken))
            return True

        # build a wiser dict value without
        # block_count and remainder (ptoken 2 and 3)
        # FIXME the remainder of this method is wrong. It will trivially have a match because we just
        #  added the entry in kdict, then we will always find the value and return false. It will not change
        #  anything at all though. Worst, the cache hit will falsely indicate that we hit an old entry. Then,
        #  partitioned files would be lost. And why are we removing blktot and brem to do such a check.
        pvalue = value
        pvalue = pvalue.replace(',' + ptoken[2], '', 10)
        pvalue = pvalue.replace(',' + ptoken[3], '', 10)

        # check every key in kdict
        # build a similar value to compare with pvalue

        for value in kdict:
            kvalue = value
            kvalue = kvalue.replace(',' + ptoken[2], '', 10)
            kvalue = kvalue.replace(',' + ptoken[3], '', 10)

            # if we find the value... its in cache... its old

            if pvalue == kvalue:
                self.cache_hit = value
                return False

        # FIXME variable value was overwritten by loop variable value. Using pvalue is safer here
        #  for when the loop bug will be fixed.
        logger.debug("did not find it... its new: pvalue={}".format(pvalue))

        return True

    def check_message(self, msg):

        relpath = self.__get_relpath(msg['relPath'])
        sumstr = msg['integrity']['method'] + ',' + msg['integrity'][
            'value'].replace('\n', '')
        partstr = relpath

        if msg['integrity']['method'] not in ['remove', 'link']:
            if 'size' in msg:
                partstr = '1,' + str(msg['size'])
            else:
                partstr = msg['blocks']

        logger.debug("NoDupe calling check( %s, %s, %s )" % ( sumstr, relpath, partstr ) )
        return self.check(sumstr, relpath, partstr)

    def after_accept(self, worklist):

        new_incoming = []
        self.now = nowflt()
        for m in worklist.incoming:
            if self.check_message(m):
                new_incoming.append(m)
            else:
                if self.o.log_reject:
                    logger.info("rejected %s" % m['relPath'])
                msg_set_report(m, 304, 'Not modified 1 (cache check)')
                worklist.rejected.append(m)

        worklist.incoming = new_incoming

    def on_start(self):
        self.open()

    def on_stop(self):
        self.save()
        self.close()

    def __get_relpath(self, path):
        if self.o.basis == 'name':
            result = path.split('/')[-1]
        elif self.o.basis == 'path':
            result = path
        elif self.o.basis == 'data':
            result = "data"
        else:
            raise ValueError(
                "invalid choice for NoDupe basis valid ones:{}".format(
                    self.o.basis))
        return result

    def clean(self, persist=False, delpath=None):
        logger.debug("NoDupe clean")

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
                if ttl > self.o.time_to_live: continue

                parts = value.split('*')
                path = parts[0]
                qpath = urllib.parse.quote(path)
                part = parts[1]

                if qpath == qdelpath: continue

                ndict[value] = t
                self.count += 1

                if persist:
                    self.fp.write("%s %f %s %s\n" % (key, t, qpath, part))

            if len(ndict) > 0: new_dict[key] = ndict

        # set cleaned cache_dict
        self.cache_dict = new_dict

    def close(self, unlink=False):
        logger.debug("NoDupe close")
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
        logger.debug("NoDupe delete_path")

        # close,remove file, open new empty file
        self.fp.close()
        if os.path.exists(self.cache_file):
            os.unlink(self.cache_file)
        self.fp = open(self.cache_file, 'w')

        # clean cache removing delpath
        self.clean(persist=True, delpath=delpath)

    def free(self):
        logger.debug("NoDupe free")
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
        logger.debug("NoDupe load")
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

            # words  = [ sum, time, path, part ]
            try:
                words = line.split()
                key = words[0]
                ctime = float(words[1])
                qpath = words[2]
                path = urllib.parse.unquote(qpath)
                part = words[3]
                value = '%s*%s' % (path, part)

                # skip expired entry

                ttl = now - ctime
                if ttl > self.o.time_to_live: continue

            except Exception as err:
                err_msg_fmt = "load corrupted: lineno={}, cache_file={}, err={}"
                logger.error(err_msg_fmt.format(lineno, self.cache_file, err))
                logger.debug('Exception details:', exc_info=True)
                continue

            #  add info in cache

            if key in self.cache_dict: kdict = self.cache_dict[key]
            else: kdict = {}

            if not value in kdict: self.count += 1

            kdict[value] = ctime
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
