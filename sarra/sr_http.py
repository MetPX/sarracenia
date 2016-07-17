#!/usr/bin/python3
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

class http_transport():
    def __init__(self) :
        self.bufsize   = 8192
        self.sumalgo   = None
        self.kbytes_ps = 0

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

                msg.logger.debug('Beginning fetch of %s %s into %s %d-%d' % (urlstr,str_range,msg.local_file,msg.local_offset,msg.length))  

                response = urllib.request.urlopen(req)
                #msg.logger.debug('response header = %s' % response.headers)

                # FIXME  locking for i parts in temporary file ... should stay lock
                # and file_reassemble... take into account the locking

                if   parent.lock == None or msg.partflg == 'i' :
                     ok = self.http_write(response,msg.local_file,msg)

                elif parent.lock == '.' :
                     local_lock = ''
                     local_dir  = os.path.dirname (msg.local_file)
                     if local_dir != '' : local_lock = local_dir + os.sep
                     local_lock += '.' + os.path.basename(msg.local_file)
                     ok = self.http_write(response,local_lock,msg)
                     if os.path.isfile(msg.local_file) : os.remove(msg.local_file)
                     os.rename(local_lock, msg.local_file)
                
                elif parent.lock[0] == '.' :
                     local_lock  = msg.local_file + parent.lock
                     ok = self.http_write(response,local_lock,msg)
                     if os.path.isfile(msg.local_file) : os.remove(msg.local_file)
                     os.rename(local_lock, msg.local_file)

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

        return False

    def http_write(self,req,local_file,msg) :
        self.logger.debug("sr_http http_write")

        # on fly checksum 

        chk           = self.sumalgo
        self.checksum = None

        # trottle 

        cb = None

        if self.kbytes_ps > 0.0 :
           cb = self.trottle
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
              self.logger.debug("http_write read loop")
              chunk = req.read(self.bufsize)
              if not chunk: break
              fp.write(chunk)
              if chk : chk.update(chunk)
              if cb  : cb(chunk)

        fp.close()

        if chk : self.checksum = chk.get_value()

        return True

    # trottle
    def trottle(self,buf) :
        self.logger.debug("http_transport trottle")
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
          self.debug   = print
          self.error   = print
          self.info    = print
          self.warning = print

def self_test():

    logger = test_logger()

    # config setup
    cfg = sr_config()
    cfg.defaults()
    cfg.general()
    cfg.debug  = True
    cfg.logger = logger
    cfg.kbytes_ps = 10.0

    #setup consumer to catch first post
    #dd.weather has strange permissions, so queue declare fails. 'unknown method'
    #ok, cfg.broker     = cfg.validate_urlstr("amqp://anonymous@dd.weather.gc.ca/")

    ok, cfg.broker     = cfg.validate_urlstr("amqp://tsub@localhost/")
    cfg.bindings       = [ ( 'xpublic', 'v02.post.#') ]
    cfg.user_cache_dir = os.getcwd()
    cfg.config_name    = "test"
    cfg.queue_name     = None
    cfg.reset          = True

    consumer = sr_consumer(cfg)

    i = 0
    while True :
          ok, msg = consumer.consume()
          if ok: break

    cfg.msg = msg
    cfg.msg.sumalgo = None
    cfg.msg.local_file = "toto"
    cfg.msg.local_offset = 0

    try:
             
          tr = http_transport()

          cfg.lock = None
          tr.download(cfg)
          logger.debug("checksum = %s" % cfg.msg.onfly_checksum)
          cfg.lock = '.'
          tr.download(cfg)
          logger.debug("checksum = %s" % cfg.msg.onfly_checksum)
          cfg.lock = '.tmp'
          tr.download(cfg)
          logger.debug("checksum = %s" % cfg.msg.onfly_checksum)
          cfg.msg.sumalgo = cfg.sumalgo
          tr.download(cfg)
          logger.debug("checksum = %s" % cfg.msg.onfly_checksum)
          logger.debug("checksum = %s" % cfg.msg.checksum)

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

