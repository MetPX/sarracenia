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
# sr_http.py : python3 utility tools for http usage in sarracenia
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Jun Hu         - Shared Services Canada
#  Last Changed   : Nov 23 15:30:22 UTC 2017
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

import os, urllib.request, urllib.error, ssl, sys

try :
         from sr_util            import *
except :
         from sarra.sr_util      import *

#============================================================
# http protocol in sarracenia supports/uses :
#
# connect
# close
#
# get    (remote,local)
# ls     ()
# cd     (dir)
#
# check_is_connected()
# getcwd()
#
# credentials()

class sr_http(sr_proto):

    def __init__(self, parent) :
        parent.logger.debug("sr_http __init__")
        sr_proto.__init__(self,parent)
        self.init()

    # cd
    def cd(self, path):
        self.logger.debug("sr_http cd %s" % path)
        self.cwd  = os.path.dirname(path)
        self.path = path

    # for compatibility... always new connection with http
    def check_is_connected(self):
        self.logger.debug("sr_http check_is_connected")

        if self.destination != self.parent.destination :
           self.close()
           return False

        return True

    # close
    def close(self):
        self.logger.debug("sr_http close")
        self.init()

    # connect...
    def connect(self):
        self.logger.debug("sr_http connect %s" % self.parent.destination)

        if self.connected: self.close()

        self.connected   = False
        self.destination = self.parent.destination
        self.timeout     = self.parent.timeout

        if not self.credentials() : return False

        return True

    # credentials...
    def credentials(self):
        self.logger.debug("sr_http credentials %s" % self.destination)

        try:
                ok, details = self.parent.credentials.get(self.destination)
                if details  : url = details.url

                self.user        = url.username
                self.password    = url.password

                if url.username == '' : self.user     = None
                if url.password == '' : self.password = None

                return True

        except:
                self.logger.error("sr_http/credentials: unable to get credentials for %s" % self.destination)
                self.logger.debug('Exception details: ', exc_info=True)

        return False

    # get
    def get(self, remote_file, local_file, remote_offset=0, local_offset=0, length=0):
        self.logger.debug( "sr_http get %s %s %d" % (remote_file,local_file,local_offset))
        self.logger.debug( "sr_http self.path %s" % self.path)

        # open self.http

        url = self.destination + '/' + self.path + '/' + remote_file

        ok  = self.__open__(url, remote_offset, length )

        if not ok : return False

        # read from self.http write to local_file

        rw_length = self.read_writelocal(remote_file, self.http, local_file, local_offset, length)

        return True

    # init
    def init(self):
        sr_proto.init(self)
        self.logger.debug("sr_http init")
        self.connected   = False
        self.http        = None
        self.details     = None
        self.seek        = True

        self.urlstr      = ''
        self.path        = ''
        self.cwd         = ''

        self.data        = ''
        self.entries     = {}

   # ls
    def ls(self):
        self.logger.debug("sr_http ls")

        # open self.http

        self.entries = {}

        url = self.destination + '/' + self.path

        ok  = self.__open__( url )

        if not ok : return self.entries

        # get html page for directory

        try :
                 dbuf = None
                 while  True:
                        alarm_set(self.iotime)
                        chunk = self.http.read(self.bufsize)
                        alarm_cancel()
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
                self.logger.warning("sr_http/ls: unable to open %s" % self.urlstr)
                self.logger.debug('Exception details: ', exc_info=True)

        return self.entries

    # open
    def __open__(self, path, remote_offset=0, length=0):
        self.logger.debug( "sr_http open")

        self.http      = None
        self.connected = False
        self.req       = None
        self.urlstr    = path

        # have noticed that some site does not allow // in path
        if path.startswith('http://')  and '//' in path[7:] :
           self.urlstr = 'http://' + path[7:].replace('//','/')
           
        if path.startswith('https://') and '//' in path[8:] :
           self.urlstr = 'https://' + path[8:].replace('//','/')

        alarm_set(self.iotime)

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

                # https without user : create/use an ssl context
                ctx = None
                if self.user == None and self.urlstr.startswith('https'):
                   ctx = ssl.create_default_context()
                   ctx.check_hostname = False
                   ctx.verify_mode = ssl.CERT_NONE

                # open... we are connected
                if self.timeout == None :
                   self.http = urllib.request.urlopen(self.req, context=ctx)
                else :
                   self.http = urllib.request.urlopen(self.req, timeout=self.timeout, context=ctx)

                self.connected = True

                alarm_cancel()

                return True

        except urllib.error.HTTPError as e:
               self.logger.error('Download failed %s ' % self.urlstr)
               self.logger.error('Server couldn\'t fulfill the request. Error code: %s, %s' % (e.code, e.reason))
               alarm_cancel()
               raise
        except urllib.error.URLError as e:
               self.logger.error('Download failed %s ' % self.urlstr)
               self.logger.error('Failed to reach server. Reason: %s' % e.reason)
               alarm_cancel()
               raise
        except:
               self.logger.warning("sr_http/__open__: unable to open %s" % self.urlstr)
               self.logger.debug('Exception details: ', exc_info=True)
               alarm_cancel()
               raise

        alarm_cancel()
        return False

#============================================================
#
# http_transport inherited from sr_transport
#
#============================================================

class http_transport(sr_transport):
    def __init__(self) :
        sr_transport.__init__(self)
        self.pclass = sr_http
        self.scheme = 'http'
