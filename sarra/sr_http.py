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
#  Last Revision  : Sep 22 10:41:32 EDT 2015
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

def http_download( parent ) :

    msg          = parent.msg
    url          = msg.url
    urlstr       = msg.urlstr

    ok, details  = parent.credentials.get(msg.urlcred)
    if details   : url = details.url 

    user         = url.username
    passwd       = url.password

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

            msg.logger.info('Downloads: %s %s into %s %d-%d' % (urlstr,str_range,msg.local_file,msg.local_offset,msg.length))  

            response = urllib.request.urlopen(req)
            #msg.logger.debug('response header = %s' % response.headers)

            # FIXME  locking for i parts in temporary file ... should stay lock
            # and file_reassemble... take into account the locking

            if   parent.lock == None or msg.partflg == 'i' :
                 ok = http_write(response,msg.local_file,msg,parent.bufsize)

            elif parent.lock == '.' :
                 local_lock = ''
                 local_dir  = os.path.dirname (msg.local_file)
                 if local_dir != '' : local_lock = local_dir + os.sep
                 local_lock += '.' + os.path.basename(msg.local_file)
                 ok = http_write(response,local_lock,msg,parent.bufsize)
                 if os.path.isfile(msg.local_file) : os.remove(msg.local_file)
                 os.rename(local_lock, msg.local_file)
            
            elif parent.lock[0] == '.' :
                 local_lock  = msg.local_file + parent.lock
                 ok = http_write(response,local_lock,msg,parent.bufsize)
                 if os.path.isfile(msg.local_file) : os.remove(msg.local_file)
                 os.rename(local_lock, msg.local_file)

            msg.log_publish(201,'Downloaded')

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

    msg.log_publish(499,'http download problem')
    msg.logger.error("Could not download")

    return False

def http_write(req,local_file,msg,bufsize) :
    if not os.path.isfile(local_file) :
       fp = open(local_file,'w')
       fp.close

    fp = open(local_file,'r+b')
    if msg.local_offset != 0 : fp.seek(msg.local_offset,0)

    # should not worry about length...
    # http provides exact data

    while True:
          chunk = req.read(bufsize)
          if not chunk : break
          fp.write(chunk)

    fp.close()

    msg.log_publish(201,'Downloaded')

    return True

# ===================================
# self_test
# ===================================

try    :
         from sr_config         import *
         from sr_message        import *
except : 
         from sarra.sr_config   import *
         from sarra.sr_message  import *

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

    # config setup
    cfg = sr_config()
    cfg.defaults()
    cfg.general()
    cfg.debug  = True
    cfg.logger = logger

    try:
           cfg.msg         = sr_message(cfg.logger)
           cfg.msg.start_timer()
           cfg.msg.topic   = 'v02.post.test'
           cfg.msg.host    = 'localhost'
           cfg.msg.user    = 'localuser'
           cfg.msg.notice  = 'noticest.test'

           cfg.msg.urlcred = "http://dd1.wxod-stage.cmc.ec.gc.ca"
           cfg.msg.urlstr  = "http://dd1.wxod-stage.cmc.ec.gc.ca/citypage_weather/xml/ON/s0000623_e.xml"
           cfg.msg.url     = urllib.parse.urlparse(cfg.msg.urlstr)
           cfg.msg.partflg = '1'
           cfg.msg.local_file   = './toto'
           cfg.msg.local_offset = 0
           cfg.msg.length       = 100000
                   
           cfg.lock = None
           http_download(cfg)
           cfg.lock = '.'
           http_download(cfg)
           cfg.lock = '.tmp'
           http_download(cfg)

    except:
           logger.error("sr_http TEST FAILED")
           (stype, svalue, tb) = sys.exc_info()
           logger.error('Unexpected error Type: %s, Value: %s' % (stype, svalue))
           sys.exit(2)

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

