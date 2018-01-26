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

"""

A single checksum class is chosen by the source of data being injected into the network.
The following checksum classes are alternatives that are built-in.  Sources may define 
new algorithms that need to be added to networks.

checksums are used by:
    sr_post to generate the initial post.
    sr_post to compare against cached values to see if a given block is the same as what was already posted.
    sr_sarra to ensure that the post received is accurate before echoing further.
    sr_subscribe to compare the post with the file which is already on disk.
    sr_winnow to determine if a given post has been seen before.


The API of a checksum class (in calling sequence order):
   __init__   -- initialize the value of a checksum for a part.
   set_path   -- identify the checksumming algorithm to be used by update.
   update     -- given this chunk of the file, update the checksum for the part
   get_value  -- return the current calculated checksum value.

The API allows for checksums to be calculated while transfer is in progress 
rather than after the fact as a second pass through the data.  

"""

# ===================================
# checksum_0 class
# ===================================

class checksum_0(object):
      """
      Trivial minimalist checksumming algorithm, returns 0 for any file.
      """
      def __init__(self):
          self.value = '0'

      def get_value(self):
          self.value = '%.4d' % random.randint(0,9999)
          return self.value

      def update(self,chunk):
          pass

      def set_path(self,path):
          pass

# ===================================
# checksum_d class
# ===================================

class checksum_d(object):
      """
      The default algorithm is to do a checksum of the entire contents of the file, which is called 'd'.
      """
      def __init__(self):
          self.value = '0'

      def get_value(self):
          self.value = self.filehash.hexdigest()
          return self.value

      def update(self,chunk):
          if type(chunk) == bytes : self.filehash.update(chunk)
          else                    : self.filehash.update(bytes(chunk,'utf-8'))

      def set_path(self,path):
          self.filehash = md5()

# ===================================
# checksum_s class
# ===================================

class checksum_s(object):
      """
      The SHA512 algorithm to checksum the entire file, which is called 's'.
      """
      def __init__(self):
          self.value = '0'

      def get_value(self):
          self.value = self.filehash.hexdigest()
          return self.value

      def update(self,chunk):
          if type(chunk) == bytes : self.filehash.update(chunk)
          else                    : self.filehash.update(bytes(chunk,'utf-8'))

      def set_path(self,path):
          self.filehash = sha512()

# ===================================
# checksum_n class
# ===================================

class checksum_n(object):
      """
      when there is more than one processing chain producing products, it can happen that files are equivalent
      without being identical, for example if each server tags a product with ''generated on server 16', then
      the generation tags will differ.   The simplest option for checksumming then is to use the name of the
      product, which is generally the same from all the processing chains.  
      """
      def __init__(self):
          self.value = '0'

      def get_value(self):
          return self.value

      def update(self,chunk):
          pass

      def set_path(self,path):
          filename   = os.path.basename(path)
          self.value = md5(bytes(filename,'utf-8')).hexdigest()


# ===================================
# checksum_N class
# ===================================

class checksum_N(object):
      """
      look at C code for more details
      Did this just as a quick shot... not convinced it is ok
      Still put a test below... Use with care
      """
      def __init__(self):
          self.value = '0'

      def get_value(self):
          return self.value

      def update(self,chunk):
          pass

      def set_path(self,filename,partstr):
          self.filehash = sha512()
          self.filehash.update(bytes(filename+partstr,'utf-8'))
          self.value = self.filehash.hexdigest()

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

# ===================================
# self_test
# ===================================

def self_test():

    import tempfile

    status = 0

    # ===================================
    # TESTING checksum
    # ===================================

    # creating a temporary directory with testfile test_chksum_file

    tmpdirname = tempfile.TemporaryDirectory().name
    try    : os.mkdir(tmpdirname)
    except : pass
    tmpfilname = 'test_chksum_file'
    tmppath    = tmpdirname + os.sep + 'test_chksum_file'

    f=open(tmppath,'wb')
    f.write(b"0123456789")
    f.write(b"abcdefghij")
    f.write(b"ABCDEFGHIJ")
    f.write(b"9876543210")
    f.close()

    # checksum_0

    chk0 = checksum_0()
    chk0.set_path(tmppath)
    f = open(tmppath,'rb')
    for i in 0,1,2,3 :
        chunk = f.read(10)
        chk0.update(chunk)
    f.close()

    v = int(chk0.get_value())
    if v < 0 or v > 9999 :
          print("test checksum_0 Failed")
          status = 1
      

    # checksum_d

    chkd = checksum_d()
    chkd.set_path(tmppath)
    f = open(tmppath,'rb')
    for i in 0,1,2,3 :
        chunk = f.read(10)
        chkd.update(chunk)
    f.close()

    if chkd.get_value() != '7efaff9e615737b379a45646c755c492' :
          print("test checksum_d Failed")
          status = 1
      

    # checksum_n

    chkn = checksum_n()
    chkn.set_path(tmpfilname)
    f = open(tmppath,'rb')
    for i in 0,1,2,3 :
        chunk = f.read(10)
        chkn.update(chunk)
    f.close()

    v=chkn.get_value()

    if chkn.get_value() != 'fd6b0296fe95e19fcef6f21f77efdfed' :
          print("test checksum_n Failed")
          status = 1

    # checksum_N

    chkN = checksum_N()
    chkN.set_path(tmpfilname,'i,1,256,1,0,0')
    v = chkN.get_value()
  
    # this should do nothing
    chunk = 'aaa'
    chkN.update(chunk)

    if chkN.get_value() != 'a0847ab809f83cb573b76671bb500a430372d2e3d5bce4c4cd663c4ea1b5c40f5eda439c09c7776ff19e3cc30459acc2a387cf10d056296b9dc03a6556da291f' :
          print("test checksum_N Failed")
          status = 1

    # checksum_s

    chks = checksum_s()
    chks.set_path(tmppath)
    f = open(tmppath,'rb')
    for i in 0,1,2,3 :
        chunk = f.read(10)
        chks.update(chunk)
    f.close()

    if chks.get_value() != 'e0103da78bbff9a741116e04f8bea2a5b291605c00731dcf7d26c0848bccf76dd2caa6771cb4b909d5213d876ab85094654f36d15e265d322b68fea4b78efb33':
          print("test checksum_s Failed")
          status = 1
      
    os.unlink(tmppath)
    os.rmdir(tmpdirname)

    if status < 1 : print("test checksum_[0,d,n,s] OK")

    # ===================================
    # TESTING startup_args
    # ===================================

    targs   = [ '-randomize', 'True' ]
    taction = 'cleanup'
    tconfig = 'toto'
    told    = False

    # Tests

    testing_args     = {}

    testing_args[ 1] = ['program']
    testing_args[ 2] = ['program', taction ]

    testing_args[ 3] = ['program',                       taction, tconfig ]
    testing_args[ 4] = ['program', '-randomize', 'True', taction, tconfig ]

    testing_args[ 5] = ['program', '-a', taction,      '-randomize', 'True', tconfig ]
    testing_args[ 6] = ['program', '-c', tconfig,      '-randomize', 'True', taction ]

    testing_args[ 7] = ['program', '-action', taction, '-randomize', 'True', tconfig ]
    testing_args[ 8] = ['program', '-config', tconfig, '-randomize', 'True', taction ]

    testing_args[ 9] = ['program', '-config', tconfig, '-a', taction, '-randomize', 'True' ]

    # old style
    testing_args[10] = ['program', '-randomize', 'True', tconfig, taction ]
    testing_args[11] = ['program',                       tconfig, taction ]


    # testing...

    args,action,config,old = startup_args(testing_args[1])
    if args or action or config or old :
       print("test01 startup_args with %s : Failed" % testing_args[1])
       status = 2

    args,action,config,old = startup_args(testing_args[2])
    if args or action != taction or config or old :
       print("test02 startup_args with %s : Failed" % testing_args[2])
       status = 2

    args,action,config,old = startup_args(testing_args[3])
    if args != [] or action != taction or config != tconfig or old :
       print("test03 startup_args with %s : Failed" % testing_args[2])
       status = 2

    i = 4
    while i<11 :
          args,action,config,old = startup_args(testing_args[i])
          if args != targs  or action != taction or config != tconfig or old != told :
             print("test%.2d startup_args %s : Failed" % (i,testing_args[i]))
             status = 2
          i = i + 1
          if i == 10 : told = True

    args,action,config,old = startup_args(testing_args[11])
    if args != [] or action != taction or config != tconfig or old != told :
       print("test11 startup_args with %s : Failed" % testing_args[11])
       print(args,action,config,old)
       status = 2

    if status < 2 : print("test startup_args OK")

    # ===================================
    # TESTING timeflt2str and timestr2flt
    # ===================================

    dflt = 1500897051.125
    dstr = '20170724115051.125'

    tstr = timeflt2str(dflt)
    tflt = timestr2flt(dstr)

    if dflt != tflt or dstr != tstr :
          print("test timeflt2str timestr2flt : Failed")
          print("expected: %g, got: %g" % ( tflt, dflt ) )
          print("expected: %s, got: %s" % ( tstr, dstr ) )
          status = 3

    if status < 3 : print("test timeflt2str timestr2flt : OK")

    # ===================================
    # TESTING alarm
    # ===================================

    try: 
            status = 4
            alarm_set(1)
            time.sleep(2)
    except: status = 0

    if status == 4 : print("test alarm_set 1 NOT OK")

    try: 
            status = 0
            alarm_set(2)
            time.sleep(1)
            alarm_cancel()
            time.sleep(1)
    except: status = 4

    if status == 4 : print("test alarm_cancel 2 NOT OK")

    if status < 4 : print("test alarm: OK")

    return status

# ===================================
# MAIN
# ===================================

def main():

    status = self_test()
    sys.exit(status)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()

