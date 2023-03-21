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

logger = logging.getLogger(__name__)


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
        logger.debug("sr_http check_is_connected")

        if not self.connected : return False

        if self.sendTo != self.o.sendTo:
            self.close()
            return False

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

        if not self.credentials(): return False

        return True

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

            return True

        except:
            logger.error(
                "sr_http/credentials: unable to get credentials for %s" %
                self.sendTo)
            logger.debug('Exception details: ', exc_info=True)

        return False

    # get
    def get(self,
            msg,
            remote_file,
            local_file,
            remote_offset=0,
            local_offset=0,
            length=0):
        logger.debug("get %s %s %d" % (remote_file, local_file, local_offset))
        logger.debug("sr_http self.path %s" % self.path)

        # open self.http

        if 'retrievePath' in msg:
            url = self.sendTo + '/' + msg['retrievePath']
        else:
            u = urllib.parse.urlparse( self.sendTo )
            url = u.scheme + '://' + u.netloc + '/' + urllib.parse.quote(self.path + '/' +
                                                              remote_file)

        ok = self.__open__(url, remote_offset, length)

        if not ok: return False

        # read from self.http write to local_file

        rw_length = self.read_writelocal(remote_file, self.http, local_file,
                                         local_offset, length)

        return rw_length

    def getAccelerated(self, msg, remote_file, local_file, length):

        arg1 = msg['baseUrl'] + '/' + msg['relPath']
        arg1 = arg1.replace(' ', '\ ')
        arg2 = local_file

        cmd = self.o.accelWgetCommand.replace('%s', arg1)
        cmd = cmd.replace('%d', arg2).split()
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

        url = self.sendTo + '/' + urllib.parse.quote(self.path)

        ok = self.__open__(url)

        if not ok: return self.entries

        # get html page for directory

        try:
            dbuf = None
            while True:
                alarm_set(self.o.timeout)
                chunk = self.http.read(self.o.bufsize)
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

    # open
    def __open__(self, path, remote_offset=0, length=0):
        logger.debug( f"{path}")

        self.http = None
        self.connected = False
        self.req = None
        self.urlstr = path

        # have noticed that some site does not allow // in path
        if path.startswith('http://') and '//' in path[7:]:
            self.urlstr = 'http://' + path[7:].replace('//', '/')

        if path.startswith('https://') and '//' in path[8:]:
            self.urlstr = 'https://' + path[8:].replace('//', '/')

        alarm_set(self.o.timeout)

        try:
            # when credentials are needed.
            headers = {'user-agent': 'Sarracenia ' + sarracenia.__version__}
            if self.bearer_token:
                logger.debug('bearer_token: %s' % self.bearer_token)
                headers['Authorization'] = 'Bearer ' + self.bearer_token

            if self.user != None:
                password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                # takeaway credentials info from urlstr
                cred = self.user + '@'
                self.urlstr = self.urlstr.replace(cred, '')
                if self.password != None:
                    cred = self.user + ':' + self.password + '@'
                    self.urlstr = self.urlstr.replace(cred, '')

                # continue with authentication
                password_mgr.add_password(None, self.urlstr, self.user,
                                          unquote(self.password))
                auth_handler = urllib.request.HTTPBasicAuthHandler(
                    password_mgr)

                #hctx = ssl.create_default_context()
                #hctx.check_hostname = False
                #hctx.verify_mode = ssl.CERT_NONE
                ssl_handler = urllib.request.HTTPSHandler(0, self.tlsctx)

                # create "opener" (OpenerDirector instance)
                opener = urllib.request.build_opener(auth_handler, ssl_handler)

                # use the opener to fetch a URL
                opener.open(self.urlstr)

                # Install the opener.
                urllib.request.install_opener(opener)

            # Now all calls to get the request use our opener.
            self.req = urllib.request.Request(self.urlstr, headers=headers)

            # set range in byte if needed
            if remote_offset != 0:
                str_range = 'bytes=%d-%d' % (remote_offset,
                                             remote_offset + length - 1)
                self.req.headers['Range'] = str_range

            # https without user : create/use an ssl context
            ctx = None
            if self.user == None and self.urlstr.startswith('https'):
                ctx = self.tlsctx
                #ctx.check_hostname = False
                #ctx.verify_mode = ssl.CERT_NONE

            # open... we are connected
            if self.timeout == None:
                self.http = urllib.request.urlopen(self.req, context=ctx)
            else:
                self.http = urllib.request.urlopen(self.req,
                                                   timeout=self.timeout,
                                                   context=ctx)

            self.connected = True

            alarm_cancel()

            return True

        except urllib.error.HTTPError as e:
            logger.error('Download failed 4 %s ' % self.urlstr)
            logger.error(
                'Server couldn\'t fulfill the request. Error code: %s, %s' %
                (e.code, e.reason))
            alarm_cancel()
            self.connected = False
            raise
        except urllib.error.URLError as e:
            logger.error('Download failed 5 %s ' % self.urlstr)
            logger.error('Failed to reach server. Reason: %s' % e.reason)
            alarm_cancel()
            self.connected = False
            raise
        except:
            logger.warning("unable to open %s" % self.urlstr)
            logger.debug('Exception details: ', exc_info=True)
            self.connected = False
            alarm_cancel()
            raise

        alarm_cancel()
        return False
