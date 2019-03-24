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

from hashlib import md5
from hashlib import sha512

import sys
import calendar,datetime
import os,random,signal,stat,sys,time
import urllib
import urllib.parse

try:
    import xattr

except:
    pass

#============================================================
# sigalarm
#============================================================

class TimeoutException(Exception):
    """timeout exception"""
    pass

# alarm_cancel
def alarm_cancel():
    if sys.platform != 'win32' :
        signal.alarm(0)

# alarm_raise
def alarm_raise(n, f):
    raise TimeoutException("signal alarm timed out")

# alarm_set
def alarm_set(time):
    if sys.platform != 'win32' :
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
               self.logger.error("sr_amqp/pika_to_amqplib: in pika to amqplib %s %s" %(vars(method_frame),
                                                                                       vars(properties)))
               self.logger.debug('Exception details: ', exc_info=True)


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
        self.data_sumalgo   = None
        self.data_checksum = None
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
        if self.data_sumalgo : self.data_checksum = self.data_sumalgo.get_value()

    # local_read_open
    def local_read_open(self, local_file, local_offset=0 ):
        #self.logger.debug("sr_proto local_read_open")

        self.checksum = None

        # local_file opening and seeking if needed

        src = open(local_file,'rb')
        if local_offset != 0 : src.seek(local_offset,0)

        # initialize sumalgo

        if self.sumalgo : self.sumalgo.set_path(local_file)
        if self.data_sumalgo : self.data_sumalgo.set_path(local_file)

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
        if self.data_sumalgo : self.data_checksum = self.data_sumalgo.get_value()

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

    def __on_data__(self, chunk):

        if not self.parent.on_data_list:
           return chunk

        new_chunk = chunk
        for plugin in self.parent.on_data_list :
           new_chunk = plugin(self,new_chunk)

        if self.data_sumalgo  : self.data_sumalgo.update(new_chunk)
        return new_chunk
        

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
                    new_chunk = self.__on_data__(chunk)
                    dst.write(new_chunk)
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
                 new_chunk = self.__on_data__(chunk)
                 rw_length += len(new_chunk)
                 dst.write(new_chunk)
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
              new_chunk = self.__on_data__(chunk)
              rw_length += len(new_chunk)
              dst.write(new_chunk)
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
        if self.data_sumalgo : self.data_sumalgo.set_path(src_path)

        # copy source to destination

        rw_length = self.read_write( src, dst, length)

        # close
        self.local_write_close( dst )

        # warn if length mismatch without transformation.

        if (not self.parent.on_data_list) and length != 0 and rw_length != length :
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

        # warn if length mismatch without transformation.

        if (not self.parent.on_data_list) and length != 0 and rw_length != length :
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
        self.data_sumalgo = sumalgo

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
        self.cdir   = None
        self.pclass = None
        self.proto  = None
        self.scheme = None

    def close(self) :
        self.logger.debug("%s_transport close" % self.scheme)

        try    : self.proto.close()
        except : pass

        self.cdir  = None
        self.proto = None

    # generalized download...
    def download( self, parent ):
        self.logger = parent.logger
        self.parent = parent
        msg         = parent.msg
        self.logger.debug("%s_transport download" % self.scheme)

        token       = msg.relpath.split('/')
        cdir        = '/'.join(token[:-1])
        remote_file = token[-1]
        urlstr      = msg.baseurl + '/' + msg.relpath
        new_lock    = ''

        new_dir     = msg.new_dir
        new_file    = msg.new_file

        try:    curdir = os.getcwd()
        except: curdir = None

        if curdir != new_dir:
           os.chdir(new_dir)

        try :
                parent.destination = msg.baseurl

                proto = self.proto
                if proto== None or not proto.check_is_connected() :
                   self.logger.debug("%s_transport download connects" % self.scheme)
                   proto = self.pclass(parent)
                   ok = proto.connect()
                   if not ok : return False
                   self.proto = proto

                #=================================
                # if parts, check that the protol supports it
                #=================================

                if not hasattr(proto,'seek') and msg.partflg == 'i':
                   self.logger.error("%s, inplace part file not supported" % self.scheme)
                   msg.report_publish(499,'%s does not support partitioned file transfers' % self.scheme)
                   return False
                
                cwd = None
                if hasattr(proto,'getcwd') : cwd = proto.getcwd()
                if cwd != cdir :
                   self.logger.debug("%s_transport download cd to %s" % (self.scheme,cdir))
                   proto.cd(cdir)
    
                remote_offset = 0
                if  msg.partflg == 'i': remote_offset = msg.offset
    
                str_range = ''
                if msg.partflg == 'i' :
                   str_range = 'bytes=%d-%d'%(remote_offset,remote_offset+msg.length-1)
    
                #download file
    
                self.logger.debug('Beginning fetch of %s %s into %s %d-%d' % 
                    (urlstr,str_range,new_file,msg.local_offset,msg.local_offset+msg.length-1))
    
                # FIXME  locking for i parts in temporary file ... should stay lock
                # and file_reassemble... take into account the locking

                proto.set_sumalgo(msg.sumalgo)

                if parent.inflight == None or msg.partflg == 'i' :
                   self.get(remote_file,new_file,remote_offset,msg.local_offset,msg.length)

                elif parent.inflight == '.' :
                   new_lock = '.' + new_file
                   self.get(remote_file,new_lock,remote_offset,msg.local_offset,msg.length)
                   if os.path.isfile(new_file) : os.remove(new_file)
                   os.rename(new_lock, new_file)
                      
                elif parent.inflight[0] == '.' :
                   new_lock  = new_file + parent.inflight
                   self.get(remote_file,new_lock,remote_offset,msg.local_offset,msg.length)
                   if os.path.isfile(new_file) : os.remove(new_file)
                   os.rename(new_lock, new_file)

                elif parent.inflight[-1] == '/' :
                   try :  
                          os.mkdir(parent.inflight)
                          os.chmod(parent.inflight,parent.chmod_dir)
                   except:pass
                   new_lock  = parent.inflight + new_file
                   self.get(remote_file,new_lock,remote_offset,msg.local_offset,msg.length)
                   if os.path.isfile(new_file) : os.remove(new_file)
                   os.rename(new_lock, new_file)

                msg.onfly_checksum = proto.checksum
                msg.data_checksum = proto.data_checksum

                # fix permission 

                self.set_local_file_attributes(new_file,msg)

                # fix message if no partflg (means file size unknown until now)

                if msg.partflg == None:
                   msg.set_parts(partflg='1',chunksize=proto.fpos)
    
                msg.report_publish(201,'Downloaded')
    
                if parent.delete and hasattr(proto,'delete') :
                   try   :
                           proto.delete(remote_file)
                           msg.logger.debug ('file deleted on remote site %s' % remote_file)
                   except:
                           msg.logger.error('unable to delete remote file %s' % remote_file)
                           msg.logger.debug('Exception details: ', exc_info=True)

        except:
                #closing on problem
                try    : self.close()
                except : pass
    
                msg.logger.error("Download failed %s" % urlstr)
                msg.logger.debug('Exception details: ', exc_info=True)
                msg.report_publish(499,'%s download failed' % self.scheme)
                if os.path.isfile(new_lock) :
                    os.remove(new_lock)
                return False
        return True

    # generalized get...
    def get( self, remote_file, local_file, remote_offset, local_offset, length ):
        msg = self.parent.msg

        ok = None
        if self.scheme in self.parent.do_gets :
           self.logger.debug("using registered do_get for %s" % self.scheme)
           do_get = self.parent.do_gets[self.scheme]
           new_file     = msg.new_file
           msg.new_file = local_file
           ok = do_get(self.parent)
           msg.new_file = new_file
           if ok:
              return
           elif ok is False:
              raise Exception('Not ok')
           else:
              self.logger.debug("sr_util/get ok is None executing this do_get %s" % do_get)
        self.proto.get(remote_file, local_file, remote_offset, local_offset, length)

    # generalized put...
    def put(self, local_file, remote_file, local_offset=0, remote_offset=0, length=0 ):
        msg = self.parent.msg

        ok = None
        if self.scheme in self.parent.do_puts :
           self.logger.debug("using registered do_put for %s" % self.scheme)
           new_file     = msg.new_file
           msg.new_file = remote_file
           do_put = self.parent.do_puts[self.scheme]
           ok = do_put(self.parent)
           msg.new_file = new_file
           if ok:
              return
           elif ok is False:
              raise Exception('Not ok')
           else:
              self.logger.debug("sr_util/put ok is None executing this do_put %s" % do_put)
        self.proto.put(local_file, remote_file, local_offset, remote_offset, length)

    # generalized send...
    def send( self, parent ):
        self.logger = parent.logger
        self.parent = parent
        msg         = parent.msg
        self.logger.debug("%s_transport send %s %s" % (self.scheme,msg.new_dir, msg.new_file) )

        local_path = msg.relpath
        local_dir  = os.path.dirname( local_path).replace('\\','/')
        local_file = os.path.basename(local_path).replace('\\','/')
        new_dir    = msg.new_dir.replace('\\','/')
        new_file   = msg.new_file.replace('\\','/')
        new_lock   = None

        try:    curdir = os.getcwd()
        except: curdir = None

        if curdir != local_dir:
           os.chdir(local_dir)

        try :

                proto = self.proto
                if proto == None or not proto.check_is_connected() :
                   self.logger.debug("%s_transport send connects" % self.scheme)
                   proto = self.pclass(parent)
                   ok = proto.connect()
                   if not ok : return False
                   self.proto = proto
                   self.cdir = None

                #=================================
                # if parts, check that the protol supports it
                #=================================

                if not hasattr(proto,'seek') and msg.partflg == 'i':
                   self.logger.error("%s, inplace part file not supported" % self.scheme)
                   msg.report_publish(499,'%s does not support partitioned file transfers' % self.scheme)
                   return False

                #=================================
                # if umask, check that the protocol supports it ... 
                #=================================

                inflight = parent.inflight
                if not hasattr(proto,'umask') and parent.inflight == 'umask' :
                   self.logger.warning("%s, umask not supported" % self.scheme)
                   inflight = None

                #=================================
                # if renaming used, check that the protocol supports it ... 
                #=================================

                if not hasattr(proto,'rename') and parent.inflight.startswith('.') :
                   self.logger.warning("%s, rename not supported" % self.scheme)
                   inflight = None

                #=================================
                # remote set to new_dir
                #=================================
                
                cwd = None
                if hasattr(proto,'getcwd') : cwd = proto.getcwd()
                if cwd != new_dir :
                   self.logger.debug("%s_transport send cd to %s" % (self.scheme,new_dir))
                   proto.cd_forced(775,new_dir)

                #=================================
                # delete event
                #=================================

                if msg.sumflg == 'R' :
                   if hasattr(proto,'delete') :
                      msg.logger.debug("message is to remove %s" % new_file)
                      proto.delete(new_file)
                      msg.report_publish(205,'Reset Content : deleted')
                      return True
                   self.logger.error("%s, delete not supported" % self.scheme)
                   msg.report_publish(499,'%s does not support delete' % self.scheme)
                   return False

                #=================================
                # link event
                #=================================

                if msg.sumflg == 'L' :
                   if hasattr(proto,'symlink') :
                      msg.logger.debug("message is to link %s to: %s" % ( new_file, msg.headers['link'] ))
                      proto.symlink(msg.headers['link'],new_file)
                      msg.report_publish(205,'Reset Content : linked')
                      return True
                   self.logger.error("%s, symlink not supported" % self.scheme)
                   msg.report_publish(499,'%s does not support symlink' % self.scheme)
                   return False

                #=================================
                # send event
                #=================================

                # the file does not exist... warn, sleep and return false for the next attempt
                if not os.path.exists(local_file):
                   self.logger.warning("file %s does not exist (product collision or base_dir not set)" % local_file)
                   time.sleep(0.01)
                   return False

                offset = 0
                if  msg.partflg == 'i': offset = msg.offset
    
                str_range = ''
                if msg.partflg == 'i' :
                   str_range = 'bytes=%d-%d'%(offset,offset+msg.length-1)
    
                #upload file
    
                if inflight == None or msg.partflg == 'i' :
                   #self.put(local_file, new_file, offset, offset, msg.length)
                   # If remote offset is not 0 then partitions are prepender with all 0s...
                   self.put(local_file, new_file, offset, 0, msg.length)
                elif inflight == '.' :
                   new_lock = '.'  + new_file
                   self.put(local_file, new_lock )
                   proto.rename(new_lock, new_file)
                elif inflight[0] == '.' :
                   new_lock = new_file + inflight
                   self.put(local_file, new_lock )
                   proto.rename(new_lock, new_file)
                elif parent.inflight[-1] == '/' :
                   try :
                          proto.cd_forced(775,new_dir+'/'+parent.inflight)
                          proto.cd_forced(775,new_dir)
                   except:pass
                   new_lock  = parent.inflight + new_file
                   self.put(local_file,new_lock)
                   proto.rename(new_lock, new_file)
                elif inflight == 'umask' :
                   proto.umask()
                   self.put(local_file, new_file)

                # fix permission 

                self.set_remote_file_attributes(proto,new_file,msg)
    
                msg.logger.info('Sent: %s %s into %s/%s %d-%d' % 
                    (local_path,str_range,new_dir,new_file,offset,offset+msg.length-1))

                if parent.reportback :
                   msg.report_publish(201,'Delivered')

        except:

                #removing lock if left over
                if new_lock != None and hasattr(proto,'delete') :
                   try   : proto.delete(new_lock)
                   except: pass

                #closing on problem
                try    : self.close()
                except : pass

                msg.logger.error("Delivery failed %s" % msg.new_dir+'/'+msg.new_file)
                msg.logger.debug('Exception details: ', exc_info=True)
                msg.report_publish(497,'%s delivery failed' % self.scheme)

                return False
        return True

    # set_local_file_attributes
    def set_local_file_attributes(self,local_file, msg) :
        #self.logger.debug("sr_transport set_local_file_attributes %s" % local_file)

        hdr  = msg.headers

        # if the file is not partitioned, the the onfly_checksum is for the whole file.
        # cache it here, along with the mtime.
        if ( msg.partstr[0:2] == '1,' ) and self.parent.supports_extended_attributes:
           if msg.onfly_checksum:
               sumstr = msg.sumstr[0:2] + msg.onfly_checksum
           else:
               sumstr = msg.sumstr

           xattr.setxattr(local_file, 'user.sr_sum', bytes(sumstr,"utf-8"))

           if self.parent.preserve_time and 'mtime' in hdr and hdr['mtime'] :
               xattr.setxattr(local_file, 'user.sr_mtime', bytes(hdr['mtime'],"utf-8"))
           else:
               st = os.stat(local_file)
               mtime = timeflt2str( st.st_mtime )
               xattr.setxattr(local_file, 'user.sr_mtime', bytes(mtime,"utf-8"))

        mode = 0
        if self.parent.preserve_mode and 'mode' in hdr :
           try: 
               mode = int( hdr['mode'], base=8)
           except: 
               mode = 0
           if mode > 0 : 
               os.chmod( local_file, mode )

        if mode == 0 and  self.parent.chmod !=0 : 
           os.chmod( local_file, self.parent.chmod )

        if self.parent.preserve_time and 'mtime' in hdr and hdr['mtime'] :
           mtime = timestr2flt( hdr[ 'mtime' ] )
           atime = mtime
           if 'atime' in hdr and hdr['atime'] :
               atime  =  timestr2flt( hdr[ 'atime' ] )
           os.utime( local_file, (atime, mtime))

    # set_remote_file_attributes
    def set_remote_file_attributes(self, proto, remote_file, msg) :
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

    actions = ['foreground', 'start', 'stop', 'status', 'sanity', 'restart', 'reload', 'cleanup', 'declare', 'setup' ]
    actions.extend( ['add','disable', 'edit', 'enable', 'help', 'list',    'log',    'remove', 'rename'] )

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

def v3timeflt2str( f ):

    nsec = ('%.9g' % (f%1))[1:]
    s  = time.strftime("%Y%m%dT%H%M%S",time.gmtime(f)) + nsec
    return(s) 
 

def timestr2flt( s ):

    if s[8] == "T":
        t=datetime.datetime(  int(s[0:4]), int(s[4:6]), int(s[6:8]), int(s[9:11]), int(s[11:13]), int(s[13:15]), 0, datetime.timezone.utc )
        f=calendar.timegm(  t.timetuple())+float('0'+s[15:])
    else:
        t=datetime.datetime(  int(s[0:4]), int(s[4:6]), int(s[6:8]), int(s[8:10]), int(s[10:12]), int(s[12:14]), 0, datetime.timezone.utc )
        f=calendar.timegm(  t.timetuple())+float('0'+s[14:])
    return(f)

def timev2tov3str( s ):

    if s[8] == 'T':
        return(s)
    else:
        return s[0:8] + 'T' + s[8:] 
