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

def http_download( msg, iuser, ipassword ) :

    url       = msg.url
    urlstr    = url.geturl()
    user      = url.username
    password  = url.password

    if iuser     != None : user     = iuser
    if ipassword != None : password = ipassword

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
            ok       =  http_write(response,msg)

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

    msg.code    = 499
    msg.message = 'http download problem'
    msg.log_error()

    return False

def http_write(req,msg) :
    if not os.path.isfile(msg.local_file) :
       fp = open(msg.local_file,'w')
       fp.close

    fp = open(msg.local_file,'r+b')
    if msg.local_offset != 0 : fp.seek(msg.local_offset,0)

    # should not worry about length...
    # http provides exact data

    while True:
          chunk = req.read(msg.bufsize)
          if not chunk : break
          fp.write(chunk)

    fp.close()

    msg.code    = 201
    msg.message = 'Downloaded'
    msg.log_info()

    return True
