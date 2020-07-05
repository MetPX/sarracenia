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

import calendar,datetime
import logging
import os
import random
import signal
import stat
import sys
import time
import urllib
import urllib.parse

logger = logging.getLogger( __name__ )

from sarra.sr_xattr import *

from sarra import nowflt


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
# sr_proto : one place for throttle, onfly checksum, buffer io timeout
# =========================================

class Protocol():
    """
    v2: sarra.sr_proto -> v3: sarra.transfer.Protocol
    ============================================================
     protocol in sarracenia supports/uses :
    
     connect
     close
    
     if a source    : get    (remote,local)
                      ls     ()
                      cd     (dir)
                      delete (path)
    
     if a sender    : put    (local,remote)
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

    def __init__(self, proto, options) :
        #options.logger.debug("sr_proto __init__")

        self.o = options 
  
        for sc in Protocol.__subclasses__():
            if proto[0:4] == sc.__name__.lower():
               break

        if sc is None: return None

        self.init()
        sc.__init__(self) 

    # init
    def init(self):
        #logger.debug("sr_proto init")

        self.sumalgo   = None
        self.checksum  = None
        self.data_sumalgo   = None
        self.data_checksum = None
        self.fpos      = 0

        self.tbytes    = 0
        self.tbegin    = nowflt()

        logger.debug("timeout %d" % self.o.timeout)

    # local_read_close
    def local_read_close(self, src ):
        #logger.debug("sr_proto local_read_close")

        src.close()

        # finalize checksum

        if self.sumalgo : self.checksum = self.sumalgo.get_value()
        if self.data_sumalgo : self.data_checksum = self.data_sumalgo.get_value()

    # local_read_open
    def local_read_open(self, local_file, local_offset=0 ):
        #logger.debug("sr_proto local_read_open")

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
        #logger.debug("sr_proto local_write_open")

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

        if not self.o.on_data_list:
           return chunk

        new_chunk = chunk
        for plugin in self.o.on_data_list :
           new_chunk = plugin(self,new_chunk)

        if self.data_sumalgo  : self.data_sumalgo.update(new_chunk)
        return new_chunk
        

    # read_write
    def read_write(self, src, dst, length=0):
        #logger.debug("sr_proto read_write")

        # reset speed

        rw_length     = 0
        self.tbytes   = 0.0
        self.tbegin   = nowflt()


        # length = 0, transfer entire remote file to local file

        if length == 0 :
           while True :
                 if self.o.timeout: alarm_set(self.o.timeout)
                 chunk = src.read(self.o.bufsize)
                 if chunk :
                    new_chunk = self.__on_data__(chunk)
                    dst.write(new_chunk)
                    rw_length += len(chunk)
                 alarm_cancel()
                 if not chunk : break
                 if self.sumalgo  : self.sumalgo.update(chunk)
                 if self.o.bytes_per_second: self.throttle(chunk)
           return rw_length

        # exact length to be transfered

        nc = int(length/self.o.bufsize)
        r  = length%self.o.bufsize

        # read/write bufsize "nc" times

        i  = 0
        while i < nc :
              if self.o.timeout : alarm_set(self.o.timeout)
              chunk = src.read(self.o.bufsize)
              if chunk :
                 new_chunk = self.__on_data__(chunk)
                 rw_length += len(new_chunk)
                 dst.write(new_chunk)
              alarm_cancel()
              if not chunk : break
              if self.sumalgo  : self.sumalgo.update(chunk)
              if self.o.bytes_per_second: self.throttle(chunk)
              i = i + 1

        # remaining

        if r > 0 :
           if self.o.timeout : alarm_set(self.o.timeout)
           chunk = src.read(r)
           if chunk :
              new_chunk = self.__on_data__(chunk)
              rw_length += len(new_chunk)
              dst.write(new_chunk)
           alarm_cancel()
           if self.sumalgo  : self.sumalgo.update(chunk)
           if self.o.bytes_per_second: self.throttle(chunk)

        return rw_length

    # read_writelocal
    def read_writelocal(self, src_path, src, local_file, local_offset=0, length=0):
        #logger.debug("sr_proto read_writelocal")

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

        if (not self.o.on_data_list) and length != 0 and rw_length != length :
           logger.error("util/writelocal mismatched file length writing %s. Message said to expect %d bytes.  Got %d bytes." % (local_file,length,rw_length))

        return rw_length

    # readlocal_write
    def readlocal_write(self, local_file, local_offset=0, length=0, dst=None ):
        #logger.debug("sr_proto readlocal_write")

        # open
        src = self.local_read_open(local_file, local_offset)

        # copy source to destination

        rw_length = self.read_write( src, dst, length )

        # close

        self.local_read_close(src)

        # warn if length mismatch without transformation.

        if (not self.o.on_data_list) and length != 0 and rw_length != length :
           logger.error("util/readlocal mismatched file length reading %s. Message announced it as %d bytes, but read %d bytes " % (local_file,length,rw_length))

        return rw_length

    # set_iotime : bypass automated computation of iotime
    #def set_iotime(self.o.timeout) :
    #    logger.debug("sr_proto set_iotime %s" % iotime)
    #    if iotime < 1 : iotime = 1
    #    self.o.timeout = iotime

    # set_sumalgo
    def set_sumalgo(self, sumalgo):
        logger.debug("sr_proto set_sumalgo %s" % sumalgo)
        self.sumalgo = sumalgo
        self.data_sumalgo = sumalgo

    def get_sumstr(self):
        if self.sumalgo:
            return "{},{}".format(self.sumalgo.registered_as(), self.sumalgo.get_value())
        else:
            return None

    # throttle
    def throttle(self,buf) :
        logger.debug("sr_proto throttle")
        self.tbytes = self.tbytes + len(buf)
        span  = self.tbytes / self.o.bytes_per_second
        rspan = nowflt() - self.tbegin
        if span > rspan :
           stime = span-rspan
           if stime > 10 :
               logger.debug("sr_proto throttle sleeping for %g" % stime )
           time.sleep(stime)

    # write_chunk
    def write_chunk(self,chunk):
        if self.chunk_iow : self.chunk_iow.write(chunk)
        self.rw_length += len(chunk)
        alarm_cancel()
        if self.sumalgo  : self.sumalgo.update(chunk)
        if self.o.bytes_per_second: self.throttle(chunk)
        if self.o.timeout   : alarm_set(self.o.timeout)

    # write_chunk_end
    def write_chunk_end(self):
        alarm_cancel()
        self.chunk_iow = None
        return self.rw_length

    # write_chunk_init
    def write_chunk_init(self,proto):
        self.chunk_iow = proto
        self.tbytes    = 0.0
        self.tbegin    = nowflt()
        self.rw_length = 0
        if self.o.timeout : alarm_set(self.o.timeout)

# =========================================
# sr_transport : one place for upload/download common stuff
# =========================================

class Transport():

    def __init__(self) :
        self.cdir   = None
        self.pclass = None
        self.proto  = None
        self.scheme = None

    def close(self) :
        logger.debug("%s_transport close" % self.scheme)

        try    : self.proto.close()
        except : pass

        self.cdir  = None
        self.proto = None

    # generalized download...
    def download( self, msg, options ):

        self.o = options

        logger.debug("%s_transport download" % self.scheme)

        token       = msg['relpath'].split('/')
        cdir        = '/'.join(token[:-1])
        remote_file = token[-1]
        urlstr      = msg['baseUrl'] + '/' + msg['relPath']
        new_lock    = ''

        new_dir     = msg['new_dir']
        new_file    = msg['new_file']

        try:    curdir = os.getcwd()
        except: curdir = None

        if curdir != new_dir:
           os.chdir(new_dir)

        try :
                options.destination = msg['baseUrl']

                proto = self.proto
                if not proto or not proto.check_is_connected() :
                   logger.debug("%s_transport download connects" % self.scheme)
                   proto = self.pclass(self.o)
                   ok = proto.connect()
                   if not ok : return False
                   self.proto = proto

                #=================================
                # if parts, check that the protol supports it
                #=================================

                #if not hasattr(proto,'seek') and msg.partflg == 'i':
                #   logger.error("%s, inplace part file not supported" % self.scheme)
                #   return False
                
                cwd = None
                if hasattr(proto,'getcwd') : cwd = proto.getcwd()
                if cwd != cdir :
                   logger.debug("%s_transport download cd to %s" % (self.scheme,cdir))
                   proto.cd(cdir)
    
                remote_offset = 0
                if  msg.partflg == 'i': remote_offset = msg['offset']
    
                block_length = msg['size']
                str_range = ''
                if msg.partflg == 'i' :
                   block_length=msg['blocks']['size']
                   str_range = 'bytes=%d-%d'%(remote_offset,remote_offset+block_length-1)
    
                #download file
    
                logger.debug('Beginning fetch of %s %s into %s %d-%d' % 
                    (urlstr,str_range,new_file,msg['local_offset'],msg['local_offset']+block_length-1))
    
                # FIXME  locking for i parts in temporary file ... should stay lock
                # and file_reassemble... take into account the locking

                proto.set_sumalgo(msg['integrity']['method'])

                if options.inflight == None or msg['partflg'] == 'i' :
                   self.get(remote_file,new_file,remote_offset,msg['local_offset'],block_length)

                elif type(options.inflight) == str :
                   if options.inflight == '.' :
                       new_lock = '.' + new_file
                       self.get(remote_file,new_lock,remote_offset,msg['local_offset'],block_length)
                       if os.path.isfile(new_file) : os.remove(new_file)
                       os.rename(new_lock, new_file)
                    
                   elif options.inflight[0] == '.' :
                       new_lock  = new_file + options.inflight
                       self.get(remote_file,new_lock,remote_offset,msg['local_offset'],block_length)
                       if os.path.isfile(new_file) : os.remove(new_file)
                       os.rename(new_lock, new_file)

                   elif options.inflight[-1] == '/' :
                       try :  
                              os.mkdir(options.inflight)
                              os.chmod(options.inflight,options.chmod_dir)
                       except:pass
                       new_lock  = options.inflight + new_file
                       self.get(remote_file,new_lock,remote_offset,msg['local_offset'],block_length)
                       if os.path.isfile(new_file) : os.remove(new_file)
                       os.rename(new_lock, new_file)
                else:
                    logger.error('inflight setting: %s, not for remote.' % options.inflight )

                logger.debug('proto.checksum={}, msg.sumstr={}'.format(proto.checksum, msg['sumstr']))
                msg['onfly_checksum'] = proto.get_sumstr()
                msg['data_checksum'] = proto.data_checksum
                msg['_DeleteOnPost'].extend( [ 'onfly_checksum', 'data_checksum' ] )

                # fix message if no partflg (means file size unknown until now)
                if msg['partflg'] == None:
                   msg.set_parts(partflg='1',chunksize=proto.fpos)
    
                # fix permission 
                self.set_local_file_attributes(new_file,msg)

                if options.delete and hasattr(proto,'delete') :
                   try   :
                           proto.delete(remote_file)
                           logger.debug ('file deleted on remote site %s' % remote_file)
                   except:
                           logger.error('unable to delete remote file %s' % remote_file)
                           logger.debug('Exception details: ', exc_info=True)

        except:
                #closing on problem
                try    : self.close()
                except : pass
    
                logger.error("Download failed 3 %s" % urlstr)
                logger.debug('Exception details: ', exc_info=True)
                if os.path.isfile(new_lock) :
                    os.remove(new_lock)
                return False
        return True

    # generalized get...
    def get( self, remote_file, local_file, remote_offset, local_offset, length ):
        msg = self.o.msg

        ok = None
        if self.scheme in self.o.do_gets :
           logger.debug("using registered do_get for %s" % self.scheme)
           do_get = self.o.do_gets[self.scheme]
           new_file     = msg.new_file
           msg.new_file = local_file
           ok = do_get(self.o)
           msg.new_file = new_file
           if ok:
              return
           elif ok is False:
              raise Exception('do_get returned')
           else:
              logger.debug("sr_util/get ok is None executing this do_get %s" % do_get)
        self.proto.get(remote_file, local_file, remote_offset, local_offset, length)

    # generalized put...
    def put(self, local_file, remote_file, local_offset=0, remote_offset=0, length=0 ):
        msg = self.o.msg

        ok = None
        if self.scheme in self.o.do_puts :
           logger.debug("using registered do_put for %s" % self.scheme)
           new_file     = msg.new_file
           msg.new_file = remote_file
           do_put = self.o.do_puts[self.scheme]
           ok = do_put(self.o)
           msg.new_file = new_file
           if ok:
              return
           elif ok is False:
              raise Exception('do_put returned')
           else:
              logger.debug("sr_util/put ok is None executing this do_put %s" % do_put)
        self.proto.put(local_file, remote_file, local_offset, remote_offset, length)

    # generalized send...
    def send( self, options ):
        self.o = options
        msg         = options.msg
        logger.debug("%s_transport send %s %s" % (self.scheme,msg.new_dir, msg.new_file) )

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
                   logger.debug("%s_transport send connects" % self.scheme)
                   proto = self.pclass(options)
                   ok = proto.connect()
                   if not ok : return False
                   self.proto = proto
                   self.cdir = None

                #=================================
                # if parts, check that the protol supports it
                #=================================

                if not hasattr(proto,'seek') and msg.partflg == 'i':
                   logger.error("%s, inplace part file not supported" % self.scheme)
                   return False

                #=================================
                # if umask, check that the protocol supports it ... 
                #=================================

                inflight = options.inflight
                if not hasattr(proto,'umask') and options.inflight == 'umask' :
                   logger.warning("%s, umask not supported" % self.scheme)
                   inflight = None

                #=================================
                # if renaming used, check that the protocol supports it ... 
                #=================================

                if not hasattr(proto,'rename') and options.inflight.startswith('.') :
                   logger.warning("%s, rename not supported" % self.scheme)
                   inflight = None

                #=================================
                # remote set to new_dir
                #=================================
                
                cwd = None
                if hasattr(proto,'getcwd') : cwd = proto.getcwd()
                if cwd != new_dir :
                   logger.debug("%s_transport send cd to %s" % (self.scheme,new_dir))
                   proto.cd_forced(775,new_dir)

                #=================================
                # delete event
                #=================================

                if msg.sumflg == 'R' :
                   if hasattr(proto,'delete') :
                      logger.debug("message is to remove %s" % new_file)
                      proto.delete(new_file)
                      return True
                   logger.error("%s, delete not supported" % self.scheme)
                   return False

                #=================================
                # link event
                #=================================

                if msg.sumflg == 'L' :
                   if hasattr(proto,'symlink') :
                      logger.debug("message is to link %s to: %s" % ( new_file, msg.headers['link'] ))
                      proto.symlink(msg.headers['link'],new_file)
                      return True
                   logger.error("%s, symlink not supported" % self.scheme)
                   return False

                #=================================
                # send event
                #=================================

                # the file does not exist... warn, sleep and return false for the next attempt
                if not os.path.exists(local_file):
                   logger.warning("product collision or base_dir not set, file %s does not exist" % local_file)
                   time.sleep(0.01)
                   return False

                offset = 0
                if  msg.partflg == 'i': offset = msg.offset

                new_offset = msg.local_offset
    
                str_range = ''
                if msg.partflg == 'i' :
                   str_range = 'bytes=%d-%d'%(offset,offset+msg.length-1)
    
                #upload file
    
                if inflight == None or msg.partflg == 'i' :
                   self.put(local_file, new_file, offset, new_offset, msg.length)
                elif inflight == '.' :
                   new_lock = '.'  + new_file
                   self.put(local_file, new_lock )
                   proto.rename(new_lock, new_file)
                elif inflight[0] == '.' :
                   new_lock = new_file + inflight
                   self.put(local_file, new_lock )
                   proto.rename(new_lock, new_file)
                elif options.inflight[-1] == '/' :
                   try :
                          proto.cd_forced(775,new_dir+'/'+options.inflight)
                          proto.cd_forced(775,new_dir)
                   except:pass
                   new_lock  = options.inflight + new_file
                   self.put(local_file,new_lock)
                   proto.rename(new_lock, new_file)
                elif inflight == 'umask' :
                   proto.umask()
                   self.put(local_file, new_file)

                # fix permission 

                self.set_remote_file_attributes(proto,new_file,msg)
    
                logger.info('Sent: %s %s into %s/%s %d-%d' % 
                    (local_path,str_range,new_dir,new_file,offset,offset+msg.length-1))

        except Exception as err:

                #removing lock if left over
                if new_lock != None and hasattr(proto,'delete') :
                   try   : proto.delete(new_lock)
                   except: pass

                #closing on problem
                try    : self.close()
                except : pass

                logger.error("Delivery failed %s" % msg.new_dir+'/'+msg.new_file)
                logger.debug('Exception details: ', exc_info=True)

                return False
        return True

    # set_local_file_attributes
    def set_local_file_attributes(self,local_file, msg) :
        #logger.debug("sr_transport set_local_file_attributes %s" % local_file)

        # if the file is not partitioned, the the onfly_checksum is for the whole file.
        # cache it here, along with the mtime.
        if ( msg.partstr[0:2] == '1,' ) : 
           if 'onfly_checksum' in msg:
               sumstr = msg['onfly_checksum']
           else:
               sumstr = msg['sumstr']

           x = sr_xattr( local_file )
           x.set( 'sum' , sumstr )

           if self.o.preserve_time and 'mtime' in msg and msg['mtime'] :
               x.set( 'mtime' , msg['mtime'] )
           else:
               st = os.stat(local_file)
               mtime = timeflt2str( st.st_mtime )
               x.set( 'mtime' , mtime )
           x.persist()

        mode = 0
        if self.o.preserve_mode and 'mode' in msg :
           try: 
               mode = int( msg['mode'], base=8)
           except: 
               mode = 0
           if mode > 0 : 
               os.chmod( local_file, mode )

        if mode == 0 and  self.o.chmod !=0 : 
           os.chmod( local_file, self.o.chmod )

        if self.o.preserve_time and 'mtime' in msg and msg['mtime'] :
           mtime = timestr2flt( msg[ 'mtime' ] )
           atime = mtime
           if 'atime' in msg and msg['atime'] :
               atime  =  timestr2flt( msg[ 'atime' ] )
           os.utime( local_file, (atime, mtime))

    # set_remote_file_attributes
    def set_remote_file_attributes(self, proto, remote_file, msg) :
        #logger.debug("sr_transport set_remote_file_attributes %s" % remote_file)

        if hasattr(proto,'chmod') :
           mode = 0
           if self.o.preserve_mode and 'mode' in msg :
              try   : mode = int( msg['mode'], base=8)
              except: mode = 0
              if mode > 0 :
                 try   : proto.chmod( mode, remote_file )
                 except: pass

           if mode == 0 and  self.o.chmod !=0 : 
              try   : proto.chmod( self.o.chmod, remote_file )
              except: pass

        if hasattr(proto,'chmod') :
           if self.o.preserve_time and 'mtime' in msg and msg['mtime'] :
              mtime = timestr2flt( msg[ 'mtime' ] )
              atime = mtime
              if 'atime' in msg and msg['atime'] :
                  atime  =  timestr2flt( msg[ 'atime' ] )
              try   : proto.utime( remote_file, (atime, mtime))
              except: pass

import sarra.transfer.ftp
import sarra.transfer.sftp
import sarra.transfer.https
import sarra.transfer.file
