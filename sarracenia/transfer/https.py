# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, 2008-2021
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

import datetime
import logging
import os
import sarracenia
import ssl
import subprocess
import sys

from sarracenia.transfer import Transfer
from sarracenia.transfer import alarm_cancel, alarm_set, alarm_raise

import urllib.error, urllib.parse, urllib.request
from urllib.parse import unquote
from urllib.request import HTTPRedirectHandler 

logger = logging.getLogger(__name__)

class HTTPRedirectHandlerSameMethod(HTTPRedirectHandler):
    """ Instead of returning a new Request without a method (defaults to GET), use the 
        same method in the new Request.
        https://docs.python.org/3/library/urllib.request.html#urllib.request.HTTPRedirectHandler.redirect_request
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections note [2]
    """
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        orig_method = req.get_method()
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        new_req.method = orig_method
        logger.debug(f"redirect from {req.get_method()} {req.get_full_url()} "
                     + f"to {new_req.get_method()} {new_req.get_full_url()}")
        return new_req

class Https(Transfer):
    """
    HyperText Transfer Protocol (HTTP)  ( https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol ) 
    sarracenia transfer protocol subclass supports/uses additional custom options:

    * accelWgetCommand (default: '/usr/bin/wget %s -o - -O %d' )

    built with: 
         urllib.request ( https://docs.python.org/3/library/urllib.request.html )
    """
    def __init__(self, proto, options):

        super().__init__(proto, options)

        self.o.add_option('accelWgetCommand', 'str', '/usr/bin/wget %s -o - -O %d')

        logger.debug("sr_http __init__")

        self.tlsctx = ssl.create_default_context()
        if hasattr(self.o, 'tlsRigour'):
            self.o.tlsRigour = self.o.tlsRigour.lower()
            if self.o.tlsRigour == 'lax':
                self.tlsctx = ssl.create_default_context()
                self.tlsctx.check_hostname = False
                self.tlsctx.verify_mode = ssl.CERT_NONE

            elif self.o.tlsRigour == 'strict':
                self.tlsctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
                self.tlsctx.options |= ssl.OP_NO_TLSv1
                self.tlsctx.options |= ssl.OP_NO_TLSv1_1
                self.tlsctx.check_hostname = True
                self.tlsctx.verify_mode = ssl.CERT_REQUIRED
                self.tlsctx.load_default_certs()
                # TODO Find a way to reintroduce certificate revocation (CRL) in the future
                #  self.tlsctx.verify_flags = ssl.VERIFY_CRL_CHECK_CHAIN
                #  https://github.com/MetPX/sarracenia/issues/330
            elif self.o.tlsRigour == 'normal':
                pass
            else:
                logger.warning(
                    "option tlsRigour must be one of:  lax, normal, strict")

        self.init()

    def registered_as():
        return ['http', 'https']

    # cd
    def cd(self, path):
        logger.debug("sr_http cd %s" % path)
        self.cwd = os.path.dirname(path)
        self.path = path

    # for compatibility... always new connection with http
    def check_is_connected(self):        
        if (not self.connected 
            or not self.opener 
            or not self.head_opener 
            or self.sendTo != self.o.sendTo):
            logger.debug("sr_http check_is_connected -> no")
            self.close()
            return False
        
        logger.debug("sr_http check_is_connected -> yes")
        return True

    # close
    def close(self):
        logger.debug("sr_http close")
        self.init()

    # connect...
    def connect(self):
        logger.debug("sr_http connect %s" % self.o.sendTo)

        if self.connected: self.close()

        self.connected = False
        self.sendTo = self.o.sendTo
        self.timeout = self.o.timeout
        self.opener = None
        self.head_opener = None
        self.password_mgr = None
        
        # Set up an opener, this used to be done in every call to __open__ uses a lot of CPU (issue #1261)
        #   FIXME? When done in connect, we create a new opener every time the destination changes
        #   which might still be too frequently, depending on the config. I'm not convinced that we ever 
        #   need to create a new opener. Maybe just put it in __init__ ?
        try:
            self.password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            auth_handler = urllib.request.HTTPBasicAuthHandler(self.password_mgr)
        
            ssl_handler = urllib.request.HTTPSHandler(0, self.tlsctx)

            head_redirect_handler = HTTPRedirectHandlerSameMethod()

            # create "opener" (OpenerDirector instance)
            self.opener = urllib.request.build_opener(auth_handler, ssl_handler)
            self.head_opener = urllib.request.build_opener(auth_handler, ssl_handler, head_redirect_handler)

        except:
            logger.error(f'unable to connect {self.o.sendTo}')
            logger.debug('Exception details: ', exc_info=True)
            self.connected = False

        if not self.credentials(): 
            self.connected = False

        self.connected = True
        return self.connected

    # credentials...
    def credentials(self):
        logger.debug("sr_http credentials %s" % self.sendTo)

        try:
            ok, details = self.o.credentials.get(self.sendTo)
            if details: url = details.url

            self.user = url.username if url.username != '' else None
            self.password = url.password if url.password != '' else None
            self.bearer_token = details.bearer_token if hasattr(
                details, 'bearer_token') else None

             # username and password credentials
            if self.user != None:
                # continue with authentication
                self.password_mgr.add_password(None, self.sendTo, self.user, unquote(self.password))

            return True

        except:
            logger.error("sr_http/credentials: unable to get credentials for %s" % self.sendTo)
            logger.debug('Exception details: ', exc_info=True)

        return False

    # get
    def get(self,
            msg,
            remote_file,
            local_file,
            remote_offset=0,
            local_offset=0,
            length=0, exactLength=False):
        logger.debug("get %s %s %d" % (remote_file, local_file, local_offset))
        logger.debug("sr_http self.path %s" % self.path)

        # open self.http

        if 'retrievePath' in msg:
            url = self.sendTo + '/' + msg['retrievePath']
        else:
            u = urllib.parse.urlparse( self.sendTo )
            url = u.scheme + '://' + u.netloc + '/' + urllib.parse.quote(self.path + '/' +
                                                              remote_file, safe='/+')

        ok = self.__open__(url, remote_offset, length)

        if not ok: return False

        # read from self.http write to local_file

        rw_length = self.read_writelocal(remote_file, self.http, local_file,
                                         local_offset, length, exactLength)

        return rw_length

    def getAccelerated(self, msg, remote_file, local_file, length, remote_offset=0, exactLength=False ):

        arg1 = msg['baseUrl'] + '/' + msg['relPath']
        arg1 = arg1.replace(' ', '\\ ')
        arg2 = local_file

        cmd = self.o.accelWgetCommand.replace('%s', arg1)

        cmd = cmd.replace('%d', arg2).split()

        if exactLength:
            cmd = [cmd[0]] + [ f"--header=Range: bytes={remote_offset}-{length-1}" ] + cmd[1:]
        else:
            cmd = [cmd[0]] + cmd[1:]

        logger.info("accel_wget: %s" % ' '.join(cmd))
        p = subprocess.Popen(cmd)
        p.wait()
        if p.returncode != 0:
            logger.warning("binary accelerator %s returned: %d" % ( cmd, p.returncode ) )
            return -1
        # FIXME: length is not validated.
        return length

    # init
    def init(self):
        Transfer.init(self)

        logger.debug("sr_http init")
        self.connected = False
        self.http = None
        self.details = None
        self.seek = True

        self.opener = None
        self.head_opener = None
        self.password_mgr = None

        self.urlstr = ''
        self.path = ''
        self.cwd = ''

        self.data = ''
        self.entries = {}

    # ls
    def ls(self):
        logger.debug("sr_http ls")

        # open self.http

        self.entries = {}

        url = self.sendTo + '/' + urllib.parse.quote(self.path, safe='/+')

        ok = self.__open__(url)

        if not ok: return self.entries

        # get html page for directory

        try:
            dbuf = None
            while True:
                alarm_set(self.o.timeout)
                try:
                    chunk = self.http.read(self.o.bufSize)
                finally:
                    alarm_cancel()
                if not chunk: break
                if dbuf: dbuf += chunk
                else: dbuf = chunk

            #self.data = dbuf.decode('utf-8')

            # invoke option defined on_html_page ... if any

            #for plugin in self.o.on_html_page_list:
            #    if not plugin(self):
            #        logger.warning("something wrong")
            #        return self.entries

        except:
            logger.warning("sr_http/ls: unable to open %s" % self.urlstr)
            logger.debug('Exception details: ', exc_info=True)

        return dbuf

    def __url_redir_str(self):
        """ Returl self.urlstr, unless the request was redirected to a different URL.
            If so, it will return 'self.urlstr redirected to new_url'
        """
        redir_msg = self.urlstr
        try:
            actual_url = self.http.geturl()
            if actual_url != self.urlstr:
                redir_msg = redir_msg + f" redirected to {actual_url}"
        except:
            pass
        return redir_msg

    # open
    def __open__(self, path, remote_offset=0, length=0, method:str=None, add_headers:dict=None) -> bool:
        """ Open a URL. When the open is successful, self.http is set to a urllib.response instance that can be
            read from like a file.

            Returns True when successfully opened, False if there was a problem.
        """
        logger.debug( f"{path} " + (method if method else ''))

        self.http = None
        self.req = None
        self.urlstr = path

        if not self.check_is_connected():
            self.connect()

        # have noticed that some site does not allow // in path
        if path.startswith('http://') and '//' in path[7:]:
            self.urlstr = 'http://' + path[7:].replace('//', '/')

        if path.startswith('https://') and '//' in path[8:]:
            self.urlstr = 'https://' + path[8:].replace('//', '/')

        alarm_set(self.o.timeout)

        try:
            headers = {'user-agent': 'Sarracenia ' + sarracenia.__version__}
            
            # Bearer token credential is passed as a header
            if self.bearer_token:
                logger.debug('bearer_token: %s' % self.bearer_token)
                headers['Authorization'] = 'Bearer ' + self.bearer_token

            # set range in byte if needed
            if remote_offset != 0:
                str_range = 'bytes=%d-%d' % (remote_offset, remote_offset + length - 1)
                headers['Range'] = str_range
            
            # add everything from add_headers dict into headers dict. if anything in add_headers already
            # exists in headers, the values from add_headers will replace the values in headers.
            # This is done last to allow add_headers values to override Range/Authorization.
            if add_headers:
                headers.update(add_headers)

            # username and password credentials
            if self.user != None:
                # takeaway credentials info from urlstr
                cred = self.user + '@'
                self.urlstr = self.urlstr.replace(cred, '')
                if self.password != None:
                    cred = self.user + ':' + self.password + '@'
                    self.urlstr = self.urlstr.replace(cred, '')
 
            # Build the request that will get opened. If None is passed to method it defaults to GET.
            self.req = urllib.request.Request(self.urlstr, headers=headers, method=method)

            # open... we are connected
            opener = self.head_opener if method == 'HEAD' else self.opener
            if self.timeout == None:
                # when timeout is not passed, urllib defaults to socket._GLOBAL_DEFAULT_TIMEOUT
                self.http = opener.open(self.req)
            else:
                self.http = opener.open(self.req, timeout=self.timeout)

            # knowing if we got redirected is useful for debugging
            try:
                actual_url = self.http.geturl()
                if actual_url != self.urlstr:
                    logger.debug(f"{self.urlstr} redirected to {actual_url}")
            except:
                pass

            self.connected = True
            return self.connected

        except urllib.error.HTTPError as e:
            logger.error(f'failed 4 {self.__url_redir_str()}')
            logger.error(
                'Server couldn\'t fulfill the request. Error code: %s, %s' %
                (e.code, e.reason))
            self.connected = False
            raise
        except urllib.error.URLError as e:
            logger.error(f'failed 5 {self.__url_redir_str()}')
            logger.error('Failed to reach server. Reason: %s' % e.reason)
            self.connected = False
            raise
        except:
            logger.error(f'unable to open {self.__url_redir_str()}')
            logger.debug('Exception details: ', exc_info=True)
            self.connected = False
            raise
        finally:
            alarm_cancel()

        return False
    
    def stat(self,path,msg) -> sarracenia.filemetadata.FmdStat:
        st = sarracenia.filemetadata.FmdStat()
        # logger.debug( f" baseUrl:{msg['baseUrl']}, path:{self.path}, cwd:{self.cwd}, path:{path} " )

        url = msg['baseUrl']
        if msg['baseUrl'][-1] != '/' and self.path[0] != '/' :
            url += '/' 
        url += self.path
        if url[-1] != '/':
            url += '/' 
        url += path

        ok = self.__open__(url, method='HEAD', add_headers={'Accept-Encoding': 'identity'})
        if not ok:
            logger.debug(f"failed")
            return None
        status_code = self.http.getcode()
        if status_code != 200:
            logger.debug(f"status code {status_code}")
            return None
        
        have_metadata = False
        try:
            # Content-Length: 9659
            st.st_size = int(self.http.getheader('Content-Length'))
            have_metadata = True
        except:
            pass
        try: 
            # Last-Modified: Thu, 22 Aug 2024 20:37:53 GMT
            lm = self.http.getheader('Last-Modified')
            lm = datetime.datetime.strptime(lm, '%a, %d %b %Y %H:%M:%S GMT').timestamp()
            if lm:
                st.st_atime = lm
                st.st_mtime = lm
                have_metadata = True
        except:
            pass

        if have_metadata:
            return st
        else:
            logger.warning(f"failed, HEAD request returned {status_code} but metadata was not available for {url}")
            try:
                result = str(self.http.info()).replace('\n', ' , ').strip()
            except Exception as e:
                result = e
            logger.debug(f"HEAD request for {self.__url_redir_str()} result: {result}")

        return None
