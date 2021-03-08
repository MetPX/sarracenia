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
# sr_util.py : python3 utility mostly for checksum and file part
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Feb  4 09:09:03 EST 2016
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 2 of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#
#

import calendar, datetime
from hashlib import md5
from hashlib import sha512
import logging
import os
import random
import signal
import stat
import sys
import time
import urllib
import urllib.parse

#from sarracenia.sr_xattr import *
from sarracenia import nowflt, timestr2flt

logger = logging.getLogger(__name__)

#============================================================
# sigalarm
#============================================================


class TimeoutException(Exception):
    """timeout exception"""
    pass


# alarm_cancel
def alarm_cancel():
    if sys.platform != 'win32':
        signal.alarm(0)


# alarm_raise
def alarm_raise(n, f):
    raise TimeoutException("signal alarm timed out")


# alarm_set
def alarm_set(time):
    """
       FIXME: replace with set itimer for > 1 second resolution... currently rouding to nearest second. 
    """

    if sys.platform != 'win32':
        signal.signal(signal.SIGALRM, alarm_raise)
        signal.alarm(int(time + 0.5))


# =========================================
# sr_proto : one place for throttle, onfly checksum, buffer io timeout
# =========================================


class Transfer():
    """
    v2: sarracenia.sr_proto -> v3: sarracenia.transfer
    ============================================================
     protocol in sarracenia supports/uses :
    
     connect
     close
    
     if downloading : 
         get    ( msg, remote_file, local_file, remote_offset=0, local_offset=0, length=0 )
         getAccellerated( msg, remote_file, local_file, length ) 
         ls     ()
         cd     (dir)
         delete (path)
    
     if a sending    : 
         put    ( msg, remote_file, local_file, remote_offset=0, local_offset=0, length=0 )
         putAccelerated ( msg, remote_file, local_file, length=0 )
         cd     (dir)
         mkdir  (dir)
         umask  ()
         chmod  (perm)
         rename (old,new)
    
     SFTP : supports remote file seek... so 'I' part possible
    
    
     require   
               options.credentials
               options.destination 
               options.batch 
               options.chmod
               options.chmod_dir
               options.timeout
         opt   options.bytes_per_second
         opt   options.bufsize

    """
    @staticmethod
    def factory(proto, options):

        for sc in Transfer.__subclasses__():
            if (hasattr(sc, 'registered_as')
                    and (proto in sc.registered_as())):
                return sc(proto, options)
        return None

    def __init__(self, proto, options):

        self.o = options
        if 'sarracenia.transfer.Transfer.logLevel' in self.o.settings:
            ll = self.o.settings[sarracenia.transfer.Transfer.logLevel]
        else:
            ll = self.o.logLevel

        logger.setLevel( getattr( logging, ll.upper() ))

        logger.debug("class=%s , subclasses=%s" % ( type(self).__name__, Transfer.__subclasses__()))
        self.init()

    def init(self):
        self.sumalgo = None
        self.checksum = None
        self.data_sumalgo = None
        self.data_checksum = None
        self.fpos = 0
        self.tbytes = 0
        self.tbegin = nowflt()

    # local_read_close
    def local_read_close(self, src):
        #logger.debug("sr_proto local_read_close")

        src.close()

        # finalize checksum

        if self.sumalgo: self.checksum = self.sumalgo.get_value()
        if self.data_sumalgo:
            self.data_checksum = self.data_sumalgo.get_value()

    # local_read_open
    def local_read_open(self, local_file, local_offset=0):
        logger.debug("sr_proto local_read_open getcwd=%s self.cwd=%s" %
                     (os.getcwd(), self.getcwd()))

        self.checksum = None

        # local_file opening and seeking if needed

        src = open(local_file, 'rb')
        if local_offset != 0: src.seek(local_offset, 0)

        # initialize sumalgo

        if self.sumalgo: self.sumalgo.set_path(local_file)
        if self.data_sumalgo: self.data_sumalgo.set_path(local_file)

        return src

    # local_write_close
    def local_write_close(self, dst):

        # flush sync (make sure all io done)

        dst.flush()
        os.fsync(dst)

        # flush,sync, remember current position, truncate = no sparce, close

        self.fpos = dst.tell()
        dst.truncate()
        dst.close()

        # finalize checksum

        if self.sumalgo: self.checksum = self.sumalgo.get_value()
        if self.data_sumalgo:
            self.data_checksum = self.data_sumalgo.get_value()

    # local_write_open
    def local_write_open(self, local_file, local_offset=0):
        #logger.debug("sr_proto local_write_open")

        # reset ckecksum, fpos

        self.checksum = None
        self.fpos = 0

        # local_file has to exists

        if not os.path.isfile(local_file):
            dst = open(local_file, 'w')
            dst.close()

        # local_file opening and seeking if needed

        dst = open(local_file, 'r+b')
        if local_offset != 0: dst.seek(local_offset, 0)

        return dst

    def __on_data__(self, chunk):

        if 'on_data' not in self.o.plugins:
            return chunk

        new_chunk = chunk
        for plugin in self.o.plugins['on_data']:
            new_chunk = plugin(self, new_chunk)

        if self.data_sumalgo: self.data_sumalgo.update(new_chunk)
        return new_chunk

    # read_write
    def read_write(self, src, dst, length=0):
        logger.debug("sr_proto read_write")

        # reset speed

        rw_length = 0
        self.tbytes = 0.0
        self.tbegin = nowflt()

        # length = 0, transfer entire remote file to local file

        if length == 0:
            while True:
                logger.debug("FIXME: reading a chunk")
                if self.o.timeout: alarm_set(self.o.timeout)
                chunk = src.read(self.o.bufsize)
                if chunk:
                    new_chunk = self.__on_data__(chunk)
                    dst.write(new_chunk)
                    rw_length += len(chunk)
                alarm_cancel()
                if not chunk: break
                if self.sumalgo: self.sumalgo.update(chunk)
                if self.o.bytes_per_second: self.throttle(chunk)
            return rw_length

        # exact length to be transfered

        nc = int(length / self.o.bufsize)
        r = length % self.o.bufsize

        # read/write bufsize "nc" times

        i = 0
        while i < nc:
            if self.o.timeout: alarm_set(self.o.timeout)
            chunk = src.read(self.o.bufsize)
            if chunk:
                new_chunk = self.__on_data__(chunk)
                rw_length += len(new_chunk)
                dst.write(new_chunk)
            alarm_cancel()
            if not chunk: break
            if self.sumalgo: self.sumalgo.update(chunk)
            if self.o.bytes_per_second: self.throttle(chunk)
            i = i + 1

        # remaining

        if r > 0:
            if self.o.timeout: alarm_set(self.o.timeout)
            chunk = src.read(r)
            if chunk:
                new_chunk = self.__on_data__(chunk)
                rw_length += len(new_chunk)
                dst.write(new_chunk)
            alarm_cancel()
            if self.sumalgo: self.sumalgo.update(chunk)
            if self.o.bytes_per_second: self.throttle(chunk)

        return rw_length

    # read_writelocal
    def read_writelocal(self,
                        src_path,
                        src,
                        local_file,
                        local_offset=0,
                        length=0):
        #logger.debug("sr_proto read_writelocal")

        # open
        dst = self.local_write_open(local_file, local_offset)

        # initialize sumalgo

        if self.sumalgo: self.sumalgo.set_path(src_path)
        if self.data_sumalgo: self.data_sumalgo.set_path(src_path)

        # copy source to destination

        rw_length = self.read_write(src, dst, length)

        # close
        self.local_write_close(dst)

        # warn if length mismatch without transformation.

        if (not 'on_data' in self.o.plugins
            ) and length != 0 and rw_length != length:
            logger.error(
                "util/writelocal mismatched file length writing %s. Message said to expect %d bytes.  Got %d bytes."
                % (local_file, length, rw_length))

        return rw_length

    # readlocal_write
    def readlocal_write(self, local_file, local_offset=0, length=0, dst=None):
        logger.debug("sr_proto readlocal_write")

        # open
        src = self.local_read_open(local_file, local_offset)

        # copy source to destination

        rw_length = self.read_write(src, dst, length)

        # close

        self.local_read_close(src)

        # warn if length mismatch without transformation.

        # FIXME: 2020/09 - commented out for now... unsure about this.
        #if (not self.o.on_data_list) and length != 0 and rw_length != length :
        #   logger.error("util/readlocal mismatched file length reading %s. Message announced it as %d bytes, but read %d bytes " % (local_file,length,rw_length))

        return rw_length

    # set_iotime : bypass automated computation of iotime
    #def set_iotime(self.o.timeout) :
    #    logger.debug("sr_proto set_iotime %s" % iotime)
    #    if iotime < 1 : iotime = 1
    #    self.o.timeout = iotime

    # set_sumalgo
    def set_sumalgo(self, sumalgo):
        logger.debug("sr_proto set_sumalgo %s" % sumalgo)
        self.sumalgo = sarracenia.integrity.Integrity.factory(sumalgo)
        self.data_sumalgo = sarracenia.integrity.Integrity.factory(sumalgo)

    def update_file(self, path):
        if self.sumalgo:
            self.sumalgo.update_file(path)
        if self.data_sumalgo:
            self.data_sumalgo.update_file(path)

    def set_path(self, path):
        if self.sumalgo:
            self.sumalgo.set_path(path)
        if self.data_sumalgo:
            self.data_sumalgo.set_path(path)

    def get_sumstr(self):
        if self.sumalgo:
            #return { 'method':type(self.sumalgo).__name__, 'value':self.sumalgo.get_value() }
            return {
                'method': self.sumalgo.get_method(),
                'value': self.sumalgo.get_value()
            }
        else:
            return None

    # throttle
    def throttle(self, buf):
        logger.debug("sr_proto throttle")
        self.tbytes = self.tbytes + len(buf)
        span = self.tbytes / self.o.bytes_per_second
        rspan = nowflt() - self.tbegin
        if span > rspan:
            stime = span - rspan
            if stime > 10:
                logger.debug("sr_proto throttle sleeping for %g" % stime)
            time.sleep(stime)

    # write_chunk
    def write_chunk(self, chunk):
        if self.chunk_iow: self.chunk_iow.write(chunk)
        self.rw_length += len(chunk)
        alarm_cancel()
        if self.sumalgo: self.sumalgo.update(chunk)
        if self.o.bytes_per_second: self.throttle(chunk)
        if self.o.timeout: alarm_set(self.o.timeout)

    # write_chunk_end
    def write_chunk_end(self):
        alarm_cancel()
        self.chunk_iow = None
        return self.rw_length

    # write_chunk_init
    def write_chunk_init(self, proto):
        self.chunk_iow = proto
        self.tbytes = 0.0
        self.tbegin = nowflt()
        self.rw_length = 0
        if self.o.timeout: alarm_set(self.o.timeout)


import sarracenia.transfer.ftp
import sarracenia.transfer.sftp
import sarracenia.transfer.https
import sarracenia.transfer.file
