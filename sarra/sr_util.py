#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SarraDocumentation
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
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
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

from hashlib import md5
from hashlib import sha512

import calendar,datetime
import os,random,signal,stat,sys,time
import urllib
import urllib.parse

#============================================================
# sigalarm
#============================================================

class TimeoutException(Exception):
    """timeout exception"""
    pass

# alarm_cancel
def alarm_cancel():
    signal.alarm(0)

# alarm_raise
def alarm_raise(n, f):
    raise TimeoutException("signal alarm timed out")

# alarm_set
def alarm_set(time):
    signal.signal(signal.SIGALRM, alarm_raise)
    signal.alarm(time)

# =========================================
# raw_message to mimic raw amqplib
# use for retry and to convert from pika
# =========================================

class raw_message:

   def __init__(self,logger):
       self.logger        = logger
       self.delivery_info = {}
       self.properties    = {}

   def pika_to_amqplib(self, method_frame, properties, body ):
       try :
               self.body  = body

               self.delivery_info['exchange']         = method_frame.exchange
               self.delivery_info['routing_key']      = method_frame.routing_key
               self.delivery_tag                      = method_frame.delivery_tag

               self.properties['application_headers'] = properties.headers
       except:
               (stype, value, tb) = sys.exc_info()
               self.logger.error("sr_amqp/pika_to_amqplib Type: %s, Value: %s" % (stype, value))
               self.logger.error("in pika to amqplib %s %s" %(vars(method_frame),vars(properties)))

# =========================================
# sr_proto : one place for throttle, onfly checksum, buffer io timeout
# =========================================

class sr_proto():

    def __init__(self, parent) :
        #parent.logger.debug("sr_proto __init__")

        self.logger = parent.logger
        self.parent = parent 

        self.init()

    # init
    def init(self):
        #self.logger.debug("sr_proto init")

        self.sumalgo   = None
        self.checksum  = None
        self.fpos      = 0

        self.bufsize   = self.parent.bufsize
        self.kbytes_ps = self.parent.kbytes_ps
        self.bytes_ps  = self.kbytes_ps * 1024
        self.tbytes    = 0
        self.tbegin    = time.time()
        self.timeout   = self.parent.timeout

        self.iotime    = 30

        if self.timeout > self.iotime: self.iotime = int(self.timeout)

        self.logger.debug("iotime %d" % self.iotime)

    # local_read_close
    def local_read_close(self, src ):
        #self.logger.debug("sr_proto local_read_close")

        src.close()

        # finalize checksum

        if self.sumalgo : self.checksum = self.sumalgo.get_value()

    # local_read_open
    def local_read_open(self, local_file, local_offset=0 ):
        #self.logger.debug("sr_proto local_read_open")

        self.checksum = None

        # local_file opening and seeking if needed

        src = open(local_file,'r+b')
        if local_offset != 0 : src.seek(local_offset,0)

        # initialize sumalgo

        if self.sumalgo : self.sumalgo.set_path(local_file)

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

        if self.sumalgo : self.checksum = self.sumalgo.get_value()

    # local_write_open
    def local_write_open(self, local_file, local_offset=0):
        #self.logger.debug("sr_proto local_write_open")

        # reset ckecksum, fpos

        self.checksum = None
        self.fpos     = 0

        # local_file has to exists

        if not os.path.isfile(local_file) :
           dst = open(local_file,'w')
           dst.close()

        # local_file opening and seeking if needed

        dst = open(local_file,'r+b')
        if local_offset != 0 : dst.seek(local_offset,0)

        return dst

    # read_write
    def read_write(self, src, dst, length=0):
        #self.logger.debug("sr_proto read_write")

        # reset speed

        rw_length     = 0
        self.tbytes   = 0.0
        self.tbegin   = time.time()

        # length = 0, transfer entire remote file to local file

        if length == 0 :
           while True :
                 if self.iotime: alarm_set(self.iotime)
                 chunk = src.read(self.bufsize)
                 if chunk :
                    dst.write(chunk)
                    rw_length += len(chunk)
                 alarm_cancel()
                 if not chunk : break
                 if self.sumalgo  : self.sumalgo.update(chunk)
                 if self.kbytes_ps: self.throttle(chunk)
           return rw_length

        # exact length to be transfered

        nc = int(length/self.bufsize)
        r  = length%self.bufsize

        # read/write bufsize "nc" times

        i  = 0
        while i < nc :
              if self.iotime : alarm_set(self.iotime)
              chunk = src.read(self.bufsize)
              if chunk :
                 rw_length += len(chunk)
                 dst.write(chunk)
              alarm_cancel()
              if not chunk : break
              if self.sumalgo  : self.sumalgo.update(chunk)
              if self.kbytes_ps: self.throttle(chunk)
              i = i + 1

        # remaining

        if r > 0 :
           if self.iotime : alarm_set(self.iotime)
           chunk = src.read(r)
           if chunk :
              rw_length += len(chunk)
              dst.write(chunk)
           alarm_cancel()
           if self.sumalgo  : self.sumalgo.update(chunk)
           if self.kbytes_ps: self.throttle(chunk)

        return rw_length

    # read_writelocal
    def read_writelocal(self, src_path, src, local_file, local_offset=0, length=0):
        #self.logger.debug("sr_proto read_writelocal")

        # open
        dst = self.local_write_open(local_file, local_offset)

        # initialize sumalgo

        if self.sumalgo : self.sumalgo.set_path(src_path)

        # copy source to destination

        rw_length = self.read_write( src, dst, length)

        # close
        self.local_write_close( dst )

        # warn if length mismatch

        if length != 0 and rw_length != length :
           self.logger.error("util/writelocal mismatched file length writing %s. Message said to expect %d bytes.  Got %d bytes." % (local_file,length,rw_length))

        return rw_length

    # readlocal_write
    def readlocal_write(self, local_file, local_offset=0, length=0, dst=None ):
        #self.logger.debug("sr_proto readlocal_write")

        # open
        src = self.local_read_open(local_file, local_offset)

        # copy source to destination

        rw_length = self.read_write( src, dst, length )

        # close

        self.local_read_close(src)

        # warn if length mismatch

        if length != 0 and rw_length != length :
           self.logger.error("util/readlocal mismatched file length reading %s. Message announced it as %d bytes, but read %d bytes " % (local_file,length,rw_length))

        return rw_length

    # set_iotime : bypass automated computation of iotime
    def set_iotime(self,iotime) :
        self.logger.debug("sr_proto set_iotime %s" % iotime)
        if iotime < 1 : iotime = 1
        self.iotime = iotime

    # set_sumalgo
    def set_sumalgo(self,sumalgo) :
        #self.logger.debug("sr_proto set_sumalgo %s" % sumalgo)
        self.sumalgo = sumalgo

    # throttle
    def throttle(self,buf) :
        self.logger.debug("sr_proto throttle")
        self.tbytes = self.tbytes + len(buf)
        span  = self.tbytes / self.bytes_ps
        rspan = time.time() - self.tbegin
        if span > rspan :
           stime = span-rspan
           time.sleep(span-rspan)

    # write_chunk
    def write_chunk(self,chunk):
        if self.chunk_iow : self.chunk_iow.write(chunk)
        self.rw_length += len(chunk)
        alarm_cancel()
        if self.sumalgo  : self.sumalgo.update(chunk)
        if self.kbytes_ps: self.throttle(chunk)
        if self.iotime   : alarm_set(self.iotime)

    # write_chunk_end
    def write_chunk_end(self):
        alarm_cancel()
        self.chunk_iow = None
        return self.rw_length

    # write_chunk_init
    def write_chunk_init(self,proto):
        self.chunk_iow = proto
        self.tbytes    = 0.0
        self.tbegin    = time.time()
        self.rw_length = 0
        if self.iotime : alarm_set(self.iotime)

# =========================================
# sr_transport : one place for upload/download common stuff
# =========================================

class sr_transport():

    def __init__(self) :
        pass

    # set_local_file_attributes
    def set_local_file_attributes(self,local_file, msg) :
        #self.logger.debug("sr_transport set_local_file_attributes %s" % local_file)

        hdr  = msg.headers

        mode = 0
        if self.parent.preserve_mode and 'mode' in hdr :
           try   : mode = int( hdr['mode'], base=8)
           except: mode = 0
           if mode > 0 : os.chmod( local_file, mode )

        if mode == 0 and  self.parent.chmod !=0 : 
           os.chmod( local_file, self.parent.chmod )

        if self.parent.preserve_time and 'mtime' in hdr and hdr['mtime'] :
           mtime = timestr2flt( hdr[ 'mtime' ] )
           atime = mtime
           if 'atime' in hdr and hdr['atime'] :
               atime  =  timestr2flt( hdr[ 'atime' ] )
           os.utime( local_file, (atime, mtime))

    # set_remote_file_attributes
    def set_remote_file_attributes(self,proto, remote_file, msg) :
        #self.logger.debug("sr_transport set_remote_file_attributes %s" % remote_file)

        hdr  = msg.headers

        if hasattr(proto,'chmod') :
           mode = 0
           if self.parent.preserve_mode and 'mode' in hdr :
              try   : mode = int( hdr['mode'], base=8)
              except: mode = 0
              if mode > 0 :
                 try   : proto.chmod( mode, remote_file )
                 except: pass

           if mode == 0 and  self.parent.chmod !=0 : 
              try   : proto.chmod( self.parent.chmod, remote_file )
              except: pass

        if hasattr(proto,'chmod') :
           if self.parent.preserve_time and 'mtime' in hdr and hdr['mtime'] :
              mtime = timestr2flt( hdr[ 'mtime' ] )
              atime = mtime
              if 'atime' in hdr and hdr['atime'] :
                  atime  =  timestr2flt( hdr[ 'atime' ] )
              try   : proto.utime( remote_file, (atime, mtime))
              except: pass

# ===================================
# startup args parsing
# ===================================

def startup_args(sys_argv):

    actions = ['foreground', 'start', 'stop', 'status', 'restart', 'reload', 'cleanup', 'declare', 'setup' ]
    actions.extend( ['add','disable', 'edit', 'enable', 'list',    'log',    'remove' ] )

    args    = None
    action  = None
    config  = None
    old     = False

    # work with a copy

    argv = []
    argv.extend(sys_argv)
    largv = len(argv)

    # program

    if largv < 2 : return (args,action,config,old)

    # look for an action

    last = largv-1
    for idx,A in enumerate(argv):
        a = A.lower()
        if a in actions :
          action = a
          if idx == last  : old = True
          break

    # action preceeded by '-a' or '-action'

    if action != None :
       if argv[idx-1].lower() in [ '-a','-action' ] :
          old   = False
          argv.pop(idx-1)
       argv.remove(a)

    # program action?

    if largv < 3 :
       if a.strip('-') in ['h','help'] : args = [ argv[-1] ]
       return (args,action,config,False)

    # program [... -[c|config] config...]

    idx   = -1
    largv = len(argv)
    try    : idx = argv.index('-c')
    except :
             try    : idx = argv.index('-config')
             except : pass
    if idx > -1 and idx < largv-1 :
       config = argv[idx+1]
       argv.pop(idx+1)
       argv.pop(idx)
       largv = len(argv)
       old   = False

    # if we have a config we are done

    if config != None :
       args = argv[1:]
       return (args,action,config,old)

    # program [...] action config
    # program [...] config action
    # program [...] -a action [...] config
    # if action was present it was removed with its [-a|-action]
    # so the config must be last arg

    args   = argv[1:-1]
    config = argv[-1]
    return (args,action,config,old)

"""

  Time conversion routines.  
   - os.stat, and time.now() return floating point 
   - The floating point representation is a count of seconds since the beginning of the epoch.
   - beginning of epoch is platform dependent, and conversion to actual date is fraught (leap seconds, etc...)
   - Entire SR_* formats are text, no floats are sent over the protocol (avoids byte order issues, null byte / encoding issues, 
     and enhances readability.) 
   - str format: YYYYMMDDHHMMSS.msec goal of this representation is that a naive conversion to floats yields comparable numbers.
   - but the number that results is not useful for anything else, so need these special routines to get a proper epochal time.
   - also OK for year 2032 or whatever (rollover of time_t on 32 bits.)
   - string representation is forced to UTC timezone to avoid having to communicate timezone.

   timeflt2str - accepts a float and returns a string.
   timestr2flt - accepts a string and returns a float.


  caveat:
   - FIXME: this encoding will break in the year 10000 (assumes four digit year) and requires leading zeroes prior to 1000.
     one will have to add detection of the decimal point, and change the offsets at that point.
    
"""

def timeflt2str( f ):
    nsec = ('%.9g' % (f%1))[1:]
    s  = time.strftime("%Y%m%d%H%M%S",time.gmtime(f)) + nsec
    return(s) 
    

def timestr2flt( s ):
    t=datetime.datetime(  int(s[0:4]), int(s[4:6]), int(s[6:8]), int(s[8:10]), int(s[10:12]), int(s[12:14]), 0, datetime.timezone.utc )
    f=calendar.timegm(  t.timetuple())+float('0'+s[14:])
    return(f)

