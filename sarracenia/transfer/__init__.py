# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
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
import humanize
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
from sarracenia.featuredetection import features

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
     This is a sort of abstract base class for implementing transfer protocols.
     Implemented subclasses include support for: local files, https, sftp, and ftp. 

     This class has routines that do i/o given descriptors opened by the sub-classes,
     so that each one does not need to re-implement copying, for example.

     Each subclass needs to implement the following routines:

     if downloading:: 

         get    ( msg, remote_file, local_file, remote_offset=0, local_offset=0, length=0 )
         getAccellerated( msg, remote_file, local_file, length ) 
         ls     ()
         cd     (dir)
         delete (path)
    

     if sending:: 

         put    ( msg, remote_file, local_file, remote_offset=0, local_offset=0, length=0 )
         putAccelerated ( msg, remote_file, local_file, length=0 )
         cd     (dir)
         mkdir  (dir)
         umask  ()
         chmod  (perm)
         rename (old,new)

     Note that the ls() call returns are polymorphic. One of:

     * a dictionary where the key is the name of the file in the directory,
       and the value is an SFTPAttributes structure for if (from paramiko.)
       (sftp.py as an example)
     * a dictionary where the key is the name of the file, and the value is a string
       that looks like the output of a linux ls command.
       (ftp.py as an example.)
     * a sequence of bytes... will be parsed as an html page.
       (https.py as an example)

     The first format is the vastly preferred one. The others are fallbacks when the first
     is not available.
     The flowcb/poll/__init__.py lsdir() routing will turn ls tries to transform any of 
     these return values into the first form (a dictionary of SFTPAttributes)
     Each SFTPAttributes structure needs st_mode set, and folders need stat.S_IFDIR set.

     if the lsdir() routine gets a sequence of bytes, the on_html_page() and on_html_parser_init(,
     or perhaps handle_starttag(..) and handle_data() routines) will be used to turn them into
     the first form.

     web services with different such formats can be accommodated by subclassing and overriding
     the handle_* entry points.

     uses options (on Sarracenia.config data structure passed to constructor/factory.)
     * credentials - used to authentication information.
     * sendTo  - server to connect to.
     * batch   - how many files to transfer before a connection is torn down and re-established.
     * permDefault - what permissions to set on files transferred.
     * permDirDefault - what permission to set on directories created.
     * timeout  - how long to wait for operations to complete.
     * byteRateMax - maximum transfer rate (throttle to avoid exceeding)
     * bufSize - size of buffers for file transfers.

    """
    @staticmethod
    def factory(proto, options) -> 'Transfer':

        for sc in Transfer.__subclasses__():
            if (hasattr(sc, 'registered_as')
                    and (proto in sc.registered_as())):
                return sc(proto, options)
        return None

    def __init__(self, proto, options):

        self.o = options
        if 'sarracenia.transfer.Transfer' in self.o.settings and 'logLevel' in self.o.settings:
            ll = self.o.settings['sarracenia.transfer.Transfer']['logLevel']
        else:
            ll = self.o.logLevel

        logger.setLevel(getattr(logging, ll.upper()))

        logger.debug("class=%s , subclasses=%s" %
                     (type(self).__name__, Transfer.__subclasses__()))
        self.init()

    def init(self):
        self.sumalgo = None
        self.checksum = None
        self.data_sumalgo = None
        self.data_checksum = None
        self.fpos = 0
        self.tbytes = 0
        self.tbegin = nowflt()
        self.lastLog = self.tbegin
        self.byteRate = 0
        self.logMinimumInterval = 60
        #if hasattr(self.o,'sanity_log_dead'):
        #    self.logMinimumInterval = self.o.runStateThreshold_hung/4
        #else:
        #    self.logMinimumInterval = 30

    def logProgress(self,sz):
        """

           if there hasn't been a log message in at least logMinumumInterval, 
           then put out a message, so sanity does not think it is dead.
           
           this should print out a message once in a while for long file transfers.
        """
        now=nowflt()
        if now-self.lastLog > self.logMinimumInterval:
            logger.info( f"{humanize.naturalsize(sz,binary=True)} written so far.")
            self.lastLog=now

    def local_read_close(self, src):
        #logger.debug("sr_proto local_read_close")

        src.close()

        # finalize checksum

        if self.sumalgo: self.checksum = self.sumalgo.value
        if self.data_sumalgo:
            self.data_checksum = self.data_sumalgo.value

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

    def local_write_close(self, dst):

        # flush sync (make sure all io done)

        dst.flush()
        os.fsync(dst)

        # flush,sync, remember current position, truncate = no sparce, close

        self.fpos = dst.tell()
        dst.truncate()
        dst.close()

        # finalize checksum

        if self.sumalgo: self.checksum = self.sumalgo.value
        if self.data_sumalgo:
            self.data_checksum = self.data_sumalgo.value

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

    def on_data(self, chunk) -> bytes:
        """
            transform data as it is being read. 
            Given a buffer, return the transformed buffer. 
            Checksum calculation is based on pre transformation... likely need
            a post transformation value as well.
        """
        return chunk

        #FIXME ... need to re-enable on_data plugins... not sure how they should work.
        # sub-classing of transfer class?

    def read_write(self, src, dst, length=0):
        logger.debug("sr_proto read_write")

        # reset speed

        rw_length = 0
        self.tbytes = 0.0
        self.tbegin = nowflt()
        self.lastLog = self.tbegin

        # length = 0, transfer entire remote file to local file

        if length == 0:
            while True:
                if self.o.timeout: alarm_set(self.o.timeout)
                chunk = src.read(self.o.bufSize)
                if chunk:
                    new_chunk = self.on_data(chunk)
                    rw_length += len(new_chunk)
                    dst.write(new_chunk)
                    self.logProgress(rw_length)
                alarm_cancel()
                if not chunk: break
                if self.sumalgo: self.sumalgo.update(chunk)
                self.throttle(chunk)
            return rw_length

        # exact length to be transfered

        nc = int(length / self.o.bufSize)
        r = length % self.o.bufSize

        # read/write bufSize "nc" times

        i = 0
        while i < nc:
            if self.o.timeout: alarm_set(self.o.timeout)
            chunk = src.read(self.o.bufSize)
            if chunk:
                new_chunk = self.on_data(chunk)
                rw_length += len(new_chunk)
                dst.write(new_chunk)
                self.logProgress(rw_length)
            alarm_cancel()
            if not chunk: break
            if self.sumalgo: self.sumalgo.update(chunk)
            self.throttle(chunk)
            i = i + 1

        # remaining

        if r > 0:
            if self.o.timeout: alarm_set(self.o.timeout)
            chunk = src.read(r)
            if chunk:
                new_chunk = self.on_data(chunk)
                rw_length += len(new_chunk)
                dst.write(new_chunk)
                self.logProgress(rw_length)
            alarm_cancel()
            if self.sumalgo: self.sumalgo.update(chunk)
            self.throttle(chunk)

        return rw_length

    def read_writelocal(self,
                        src_path,
                        src,
                        local_file,
                        local_offset=0,
                        length=0, exactLength=False):
        #logger.debug("sr_proto read_writelocal")

        # open
        dst = self.local_write_open(local_file, local_offset)

        # initialize sumalgo

        if self.sumalgo: self.sumalgo.set_path(src_path)
        if self.data_sumalgo: self.data_sumalgo.set_path(src_path)

        # copy source to sendTo

        # 2022/12/02 - pas - need copies to always work...
        # in HPC mirroring case, a lot of short files, likely length is wrong in announcements.
        # grab the whole file unconditionally for now, detect error using mismatch.
        rw_length = self.read_write(src, dst, length if exactLength else 0)

        # close
        self.local_write_close(dst)

        # warn if length mismatch without transformation.
        # 2022/12/02 - pas should see a lot of these messages in HPC case from now on...
        
        if not self.o.acceptSizeWrong and length != 0 and rw_length != length:
            logger.debug(
                "util/writelocal mismatched file length writing %s. Message said to expect %d bytes.  Got %d bytes."
                % (local_file, length, rw_length))

        return rw_length

    def readlocal_write(self, local_file, local_offset=0, length=0, dst=None):
        logger.debug("sr_proto readlocal_write")

        # open
        src = self.local_read_open(local_file, local_offset)

        # copy source to sendTo

        rw_length = self.read_write(src, dst, length)

        # close

        self.local_read_close(src)

        # warn if length mismatch without transformation.

        # FIXME: 2020/09 - commented out for now... unsure about this.
        #if (not self.o.on_data_list) and length != 0 and rw_length != length :
        #   logger.error("util/readlocal mismatched file length reading %s. Message announced it as %d bytes, but read %d bytes " % (local_file,length,rw_length))

        # 2022/12/02 - pas attempting to get files that get shorter addressed.
        if ((length==0) or (rw_length < length)) and hasattr(dst,'truncate'):
             dst.truncate(rw_length)

        return rw_length

    def set_sumalgo(self, sumalgo):
        logger.debug("sr_proto set_sumalgo %s" % sumalgo)
        self.sumalgo = sarracenia.identity.Identity.factory(sumalgo)
        self.data_sumalgo = sarracenia.identity.Identity.factory(sumalgo)

    def set_sumArbitrary(self, value):
        self.sumalgo.value = value
        self.data_sumalgo.value = value

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

    def get_sumstr(self) -> dict:
        if self.sumalgo:
            #return { 'method':type(self.sumalgo).__name__, 'value':self.sumalgo.value }
            return {
                'method': self.sumalgo.get_method(),
                'value': self.sumalgo.value
            }
        else:
            return None

    def metricsReport(self):
        return { 'byteRateInstant': self.byteRate }

    # throttle
    def throttle(self, buf):
        self.tbytes = self.tbytes + len(buf)
        rspan = nowflt() - self.tbegin
        if rspan > 0:
            self.byteRate = self.tbytes/rspan

        if hasattr(self.o,'byteRateMax') and self.o.byteRateMax and self.o.byteRateMax > 0:
            span = self.tbytes / self.o.byteRateMax
            if span > rspan:
                stime = span - rspan
                if stime > 10:
                    logger.info( f"exceeded byteRateMax: {self.o.byteRateMax} sleeping for {stime:.2f}")
                time.sleep(stime)

    # write_chunk
    def write_chunk(self, chunk):
        if self.chunk_iow: self.chunk_iow.write(chunk)
        self.rw_length += len(chunk)
        alarm_cancel()
        self.logProgress(self.rw_length)
        if self.sumalgo: self.sumalgo.update(chunk)
        self.throttle(chunk)
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
        self.lastLog = self.tbegin
        self.rw_length = 0
        if self.o.timeout: alarm_set(self.o.timeout)

    def gethttpsUrl(self, path):
        return None

# batteries included.
import sarracenia.transfer.file
import sarracenia.transfer.ftp
import sarracenia.transfer.https

if features['sftp']['present']:
    import sarracenia.transfer.sftp

if features['s3']['present']:
    import sarracenia.transfer.s3

