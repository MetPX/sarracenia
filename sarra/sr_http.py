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
# sr_http.py : python3 utility tools for http usage in sarracenia
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Jun Hu         - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Feb  4 13:59:22 EST 2016
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

import os, urllib.request, urllib.error, sys

#============================================================
# http protocol in sarracenia supports/uses :
#
# connect
# close
#
# if a source    : get    (remote,local)
#                  ls     ()
#                  cd     (dir)
#
# *** will never support source part:
#                  delete (path)
#
# *** will never support sender part:
#                  put    (local,remote)
#                  cd     (dir)
#                  mkdir  (dir)
#                  umask  ()
#                  chmod  (perm)
#                  rename (old,new)
#                  symlink(link,path)

class sr_http():
    def __init__(self, parent) :
        self.logger = parent.logger
        self.logger.debug("sr_http __init__")

        self.parent      = parent
        self.connected   = False
        self.http        = None
        self.details     = None

        self.sumalgo     = None
        self.checksum    = None
        self.fpos        = 0

        self.urlstr      = ''
        self.path        = ''

        self.data        = ''
        self.entries     = {}


    # cd
    def cd(self, path):
        self.logger.debug("sr_http cd %s" % path)
        self.path = self.destination + path

    # close
    def close(self):
        self.logger.debug("sr_http close")
        self.connected = False
        self.http      = None

    # connect... 
    def connect(self):
        self.logger.debug("sr_http connect %s" % self.parent.destination)

        self.connected   = False
        self.destination = self.parent.destination
        self.timeout     = self.parent.timeout

        try:
                ok, self.details = self.parent.credentials.get(self.destination)
                if self.details  : url = self.details.url

                self.user        = url.username
                self.password    = url.password

                self.kbytes_ps = 0
                self.bufsize   = 8192

                if hasattr(self.parent,'kbytes_ps') : self.kbytes_ps = self.parent.kbytes_ps
                if hasattr(self.parent,'bufsize')   : self.bufsize   = self.parent.bufsize

        except:
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Unable to get credentials for %s" % self.destination)
                self.logger.error("(Type: %s, Value: %s)" % (stype ,svalue))

    # delete
    def delete(self, path):
        self.logger.debug( "sr_http delete %s not supported" % path)

    # get
    def get(self, remote_file, local_file, remote_offset=0, local_offset=0, length=0, filesize=None):
        self.logger.debug( "sr_http get %s %s %d" % (remote_file,local_file,local_offset))

        # open self.http

        self.__open__(self.path + '/' + remote_file, remote_offset, length )

        # on fly checksum 

        chk           = self.sumalgo
        self.checksum = None

        # throttle 

        cb = None

        if self.kbytes_ps > 0.0 :
           cb = self.throttle
           d1,d2,d3,d4,now = os.times()
           self.tbytes     = 0.0
           self.tbegin     = now + 0.0
           self.bytes_ps   = self.kbytes_ps * 1024.0

        if not os.path.isfile(local_file) :
           fp = open(local_file,'w')
           fp.close

        fp = open(local_file,'r+b')
        if local_offset != 0 : fp.seek(local_offset,0)


        if chk : chk.set_path(remote_file)

        # should not worry about length...
        # http provides exact data

        while True:
              chunk = self.http.read(self.bufsize)
              if not chunk: break
              fp.write(chunk)
              if chk : chk.update(chunk)
              if cb  : cb(chunk)

        self.fpos = fp.tell()
        # if new version of file replaces longer previous version.
        # FIXME  this truncate code makes no sense...  
        if self.fpos >= filesize:
           fp.truncate()

        fp.close()

        if chk : self.checksum = chk.get_value()

        return True

   # ls
    def ls(self):
        self.logger.debug("sr_http ls")

        # open self.http

        self.__open__(self.path)

        self.entries = {}

        # get html page for directory

        try :
                 dbuf = None
                 while  True:
                        chunk = self.http.read(self.bufsize)
                        if not chunk: break
                        if dbuf : dbuf += chunk
                        else    : dbuf  = chunk

                 self.data = dbuf.decode('utf-8')

                 # invoke parent defined on_html_page ... if any

                 for plugin in self.parent.on_html_page_list:
                     if not plugin(self):
                        self.logger.warning("something wrong")
                        return self.entries

        except:
                (stype, svalue, tb) = sys.exc_info()
                self.logger.warning("Unable to open %s" % self.urlstr)
                self.logger.warning("(Type: %s, Value: %s)" % (stype ,svalue))

        return self.entries

    # mkdir
    def mkdir(self, remote_dir):
        self.logger.debug( "sr_http mkdir %s not supported" % remote_dir)

    # open
    def __open__(self, path, remote_offset=0, length=0):
        self.logger.debug( "sr_http open")

        self.http      = None
        self.connected = False
        self.req       = None
        self.urlstr    = path

        try:
                # when credentials are needed.
                if self.user != None :                          
                   password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                   password_mgr.add_password(None, self.urlstr,self.user,self.password)
                   handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
            
                   # create "opener" (OpenerDirector instance)
                   opener = urllib.request.build_opener(handler)

                   # use the opener to fetch a URL
                   opener.open(self.urlstr)

                   # Install the opener.
                   urllib.request.install_opener(opener)

                # Now all calls to get the request use our opener.
                self.req = urllib.request.Request(self.urlstr)

                # set range in byte if needed
                if remote_offset != 0 :
                   str_range = 'bytes=%d-%d'%(remote_offset,remote_offset + length-1)
                   self.req.headers['Range'] = str_range

                # open... we are connected
                if self.timeout == None :
                   self.http = urllib.request.urlopen(self.req)
                else :
                   self.http = urllib.request.urlopen(self.req, timeout=self.timeout)

                self.connected = True

        except:
                (stype, svalue, tb) = sys.exc_info()
                self.logger.warning("Unable to open %s" % self.urlstr)
                self.logger.warning("(Type: %s, Value: %s)" % (stype ,svalue))

    # put
    def put(self, local_file, remote_file, local_offset = 0, remote_offset = 0, length = 0):
        self.logger.debug( "sr_http put %s %s not supported" % (local_file,remote_file))

    # rename
    def rename(self,remote_old,remote_new) :
        self.logger.debug( "sr_http rename %s %s not supported" % (remote_old,remote_new))

    # rmdir
    def rmdir(self, path):
        self.logger.debug( "sr_http rmdir %s not supported" % path)

    # set_sumalgo
    def set_sumalgo(self,sumalgo) :
        self.logger.debug("sr_http set_sumalgo %s" % sumalgo)
        self.sumalgo = sumalgo

    # throttle
    def throttle(self,buf) :
        self.logger.debug("sr_http throttle")
        self.tbytes = self.tbytes + len(buf)
        span = self.tbytes / self.bytes_ps
        d1,d2,d3,d4,now = os.times()
        rspan = now - self.tbegin
        if span > rspan :
           time.sleep(span-rspan)

    # umask
    def umask(self) :
        self.logger.debug("sr_http umask %s unsupported")

class http_transport():
    def __init__(self) :
        self.bufsize   = 8192
        self.sumalgo   = None
        self.kbytes_ps = 0
        self.fpos      = 0

    def close(self) :
        pass

    def download( self, parent ):
        self.logger  = parent.logger
        self.parent  = parent

        msg          = parent.msg
        url          = msg.url
        urlstr       = msg.urlstr
        token        = msg.url.path[1:].split('/')
        remote_file  = token[-1]

        ok, details  = parent.credentials.get(msg.urlcred)
        if details   : url = details.url 

        user         = url.username
        passwd       = url.password

        if hasattr(self.parent,'kbytes_ps') : self.kbytes_ps = self.parent.kbytes_ps
        if hasattr(self.parent,'bufsize')   : self.bufsize   = self.parent.bufsize

        self.sumalgo     = msg.sumalgo
        self.remote_file = remote_file
        local_lock = ''

        try :
                # create a password manager                
                if user != None :                          
                    # Add the username and password.
                    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                    password_mgr.add_password(None, urlstr,user,passwd)
                    handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
                            
                    # create "opener" (OpenerDirector instance)
                    opener = urllib.request.build_opener(handler)
        
                    # use the opener to fetch a URL
                    opener.open(urlstr)
        
                    # Install the opener.
                    # Now all calls to urllib2.urlopen use our opener.
                    urllib.request.install_opener(opener)

                # set a byte range to pull from remote file
                req   = urllib.request.Request(urlstr)
                str_range = ''
                if msg.partflg == 'i' :
                   str_range = 'bytes=%d-%d'%(msg.offset,msg.offset+msg.length-1)
                   req.headers['Range'] = str_range
                       
                #download file

                msg.logger.debug('Beginning fetch of %s %s into %s/%s %d-%d inflight=+%s+' % \
                      (urlstr, str_range, parent.new_dir,parent.new_file,msg.local_offset,msg.length, parent.inflight))

                response = urllib.request.urlopen(req)

                if os.getcwd() != parent.new_dir:
                    os.chdir(parent.new_dir)

                # FIXME  locking for i parts in temporary file ... should stay lock
                # and file_reassemble... take into account the locking

                if   parent.inflight == None or msg.partflg == 'i' :
                     ok = self.get(response,parent.new_file,msg)

                elif parent.inflight == '.' :
                     local_lock = ''
                     local_dir  = parent.new_dir
                     if local_dir != '' : local_lock = local_dir + os.sep
                     local_lock += '.' + os.path.basename(parent.new_file)
                     ok = self.get(response,local_lock,msg)
                     if os.path.isfile(parent.new_file) : os.remove(parent.new_file)
                     os.rename(local_lock, parent.new_file)
                
                elif parent.inflight[0] == '.' :
                     local_lock  = parent.new_file + parent.inflight
                     new= self.get(response,local_lock,msg)
                     if os.path.isfile(parent.new_file) : os.remove(parent.new_file)
                     os.rename(local_lock, parent.new_file)

                h = parent.msg.headers
                if parent.preserve_mode and 'mode' in h :
                    os.chmod(parent.new_file, int(h['mode'], base=8) )
                elif parent.chmod != 0:
                    os.chmod(parent.new_file, parent.chmod )
        
                if parent.preserve_time and 'mtime' in h :
                   os.utime(parent.new_file, times=( timestr2flt( h['atime']), timestr2flt( h[ 'mtime' ] )))
        
                # fix message if no partflg (means file size unknown until now)

                if msg.partflg == None:
                   msg.set_parts(partflg='1',chunksize=self.fpos)

                msg.onfly_checksum = self.checksum

                msg.report_publish(201,'Downloaded')

                return ok

        except urllib.error.HTTPError as e:
               msg.logger.error('Download failed %s ' % urlstr)
               msg.logger.error('Server couldn\'t fulfill the request. Error code: %s, %s', e.code, e.reason)
        except urllib.error.URLError as e:
               msg.logger.error('Download failed %s ' % urlstr)
               msg.logger.error('Failed to reach server. Reason: %s', e.reason)
        except:
               (stype, svalue, tb) = sys.exc_info()
               msg.logger.error('Download failed %s ' % urlstr)
               msg.logger.error('Unexpected error Type: %s, Value: %s' % (stype, svalue))
        
        msg.report_publish(499,'http download failed')
        msg.logger.error("sr_http could not download")
        if os.path.isfile(local_lock) : os.remove(local_lock)

        return False

    def get(self,req,local_file,msg) :

        # on fly checksum 

        chk           = self.sumalgo
        self.checksum = None

        # throttle 

        cb = None

        if self.kbytes_ps > 0.0 :
           cb = self.throttle
           d1,d2,d3,d4,now = os.times()
           self.tbytes     = 0.0
           self.tbegin     = now + 0.0
           self.bytes_ps   = self.kbytes_ps * 1024.0

        if not os.path.isfile(local_file) :
           fp = open(local_file,'w')
           fp.close

        fp = open(local_file,'r+b')
        if msg.local_offset != 0 : fp.seek(msg.local_offset,0)


        if chk : chk.set_path(self.remote_file)

        # should not worry about length...
        # http provides exact data

        while True:
              chunk = req.read(self.bufsize)
              if not chunk: break
              fp.write(chunk)
              if chk : chk.update(chunk)
              if cb  : cb(chunk)

        # if new version of file replaces longer previous version.
        self.fpos = fp.tell()
        if self.fpos >= msg.filesize:
           fp.truncate()

        fp.close()

        if chk : self.checksum = chk.get_value()


        return True

    # throttle
    def throttle(self,buf) :
        self.logger.debug("http_transport throttle")
        self.tbytes = self.tbytes + len(buf)
        span = self.tbytes / self.bytes_ps
        d1,d2,d3,d4,now = os.times()
        rspan = now - self.tbegin
        if span > rspan :
           time.sleep(span-rspan)

# ===================================
# self_test
# ===================================

try    :
         from sr_config         import *
         from sr_consumer       import *
         from sr_message        import *
         from sr_util           import *
except : 
         from sarra.sr_config   import *
         from sarra.sr_consumer import *
         from sarra.sr_message  import *
         from sarra.sr_util     import *

class test_logger:
      def silence(self,str):
          pass
      def __init__(self):
          self.debug   = self.silence
          self.error   = print
          self.info    = self.silence
          self.warning = print

def self_test():

    logger = test_logger()


    #setup consumer to catch first post
    cfg = sr_config()
    cfg.defaults()
    cfg.general()
    cfg.logger         = logger
    cfg.debug          = True
    cfg.broker         = urllib.parse.urlparse("amqp://anonymous:anonymous@dd.weather.gc.ca/")
    cfg.prefetch       = 10
    cfg.bindings       = [ ( 'xpublic', 'v02.post.#') ]
    cfg.durable        = False
    cfg.expire         = 30
    cfg.message_ttl    = 30
    cfg.user_cache_dir = os.getcwd()
    cfg.config_name    = "test"
    cfg.queue_name     = None
    cfg.kbytes_ps      = 100.0
    cfg.reset          = False
    cfg.timeout        = 10.0

    opt1 = 'accept .*'
    cfg.option( opt1.split()  )
    opt2 = "heartbeat 1"
    cfg.option( opt2.split()  )

    consumer = sr_consumer(cfg)

    i = 0
    while True :
          ok, msg = consumer.consume()
          if ok: break

    cfg.msg = msg
    cfg.set_sumalgo('d')
    cfg.new_dir  = "."
    cfg.new_file = "toto"

    cfg.msg.local_offset = 0

    try:
             
          tr = http_transport()

          cfg.inflight = None
          tr.download(cfg)
          logger.debug("checksum = %s" % cfg.msg.onfly_checksum)
          cfg.inflight = '.'
          tr.download(cfg)
          logger.debug("checksum = %s" % cfg.msg.onfly_checksum)
          cfg.inflight = '.tmp'
          tr.download(cfg)
          logger.debug("checksum = %s" % cfg.msg.onfly_checksum)
          cfg.msg.sumalgo = cfg.sumalgo
          tr.download(cfg)
          logger.debug("checksum = %s" % cfg.msg.onfly_checksum)
          logger.debug("checksum = %s" % cfg.msg.checksum)

          cfg.timeout = 12
          cfg.inflight = None
          tr.download(cfg)

    except:
          logger.error("sr_http TEST FAILED")
          (stype, svalue, tb) = sys.exc_info()
          logger.error('Unexpected error Type: %s, Value: %s' % (stype, svalue))
          sys.exit(2)

    os.unlink(consumer.queuepath)
    consumer.close()

    print("sr_http TEST PASSED")
    sys.exit(0)

# ===================================
# MAIN
# ===================================

def main():

    self_test()
    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()

