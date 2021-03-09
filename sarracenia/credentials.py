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
# credentials.py : python3 utility tool to configure all protocol credentials
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Dec 29 11:42:11 EST 2015
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
# in the credential file, one description per line
# url option1=value1, option2=value2
#
# ex:
#
# sftp://alice@herhost/ ssh_keyfile=/home/myself/mykeys/.ssh.id_dsa
# ftp://georges:Gpass@hishost/  passive = True, binary = True
#
# (passive true and binary true are credentials default and may be omitted)
#

import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)

import os
import re
import urllib, urllib.parse
import sys

# a class for credential details/options
# add any other options here... and process in parse


class credential_details:
    def __init__(self):
        self.url = None
        self.ssh_keyfile = None
        self.passive = True
        self.binary = True
        self.tls = False
        self.prot_p = False
        self.bearer_token = None

    def __str__(self):
        s = ''
        s += self.url.geturl()
        s += " %s" % self.ssh_keyfile
        s += " %s" % self.passive
        s += " %s" % self.binary
        s += " %s" % self.tls
        s += " %s" % self.prot_p
        s += " %s" % self.bearer_token
        return s


# class credentials


class Credentials:
    def __init__(self, Unused_logger=None):
        """
           logger argument no longer used... left there for API compat with old calls.
        """
        self.credentials = {}
        self.pwre = re.compile(':[^/:]*@')

        logger.debug("__init__")

    def add(self, urlstr, details=None):

        # need to create url object
        if details == None:
            details = credential_details()
            details.url = urllib.parse.urlparse(urlstr)

        self.credentials[urlstr] = details

    def get(self, urlstr):
        #logger.debug("Credentials get %s" % urlstr)

        # already cached

        if self.has(urlstr):
            #logger.debug("Credentials get in cache %s %s" % (urlstr,self.credentials[urlstr]))
            return True, self.credentials[urlstr]

        # create url object if needed

        url = urllib.parse.urlparse(urlstr)

        # add anonymous default, if necessary.
        if ( 'amqp' in url.scheme ) and \
           ( (url.username == None) or (url.username == '') ):
            urlstr = urllib.parse.urlunparse( ( url.scheme, \
                'anonymous:anonymous@%s' % url.netloc, url.path, None, None, url.port ) )
            url = urllib.parse.urlparse(urlstr)
            if self.isValid(url):
                self.add(urlstr)
                return False, self.credentials[urlstr]

        # resolved from defined credentials

        ok, details = self.resolve(urlstr, url)
        if ok: return True, details

        # not found... is it valid ?
        if not self.isValid(url):
            return False, None

        # cache it as is... we dont want to validate every time

        self.add(urlstr)
        return False, self.credentials[urlstr]

    def has(self, urlstr):
        logger.debug("has %s" % urlstr)
        return urlstr in self.credentials

    def isTrue(self, S):
        s = S.lower()
        if s == 'true' or s == 'yes' or s == 'on' or s == '1': return True
        return False

    def isValid(self, url, details=None):

        # network location
        if url.netloc == '':
            # file (why here? anyway)
            if url.scheme == 'file': return True
            return False

        # amqp... vhost not check: default /

        # user and password provided we are ok
        user = url.username != None and url.username != ''
        pasw = url.password != None and url.password != ''
        both = user and pasw

        # we have everything
        if both: return True

        # we have no user and no pasw (http normal, https... no cert,  sftp hope for .ssh/config)
        if not user and not pasw:
            if url.scheme in ['http', 'https', 'sftp']: return True
            return False

        #  we have a pasw no user
        if pasw:
            # not sure... sftp hope to get user from .ssh/config
            if url.scheme == 'sftp': return True
            return False

        #  we only have a user ... permitted only for sftp

        if url.scheme != 'sftp': return False

        #  sftp and an ssh_keyfile was provided... check that it exists

        if details and details.ssh_keyfile:
            if not os.path.exists(details.ssh_keyfile): return False

        #  sftp with a user (and perhaps a valid ssh_keyfile)

        return True

    def parse(self, line):
        #logger.debug("parse %s" % self.pwre.sub(':<secret!>@', line, count=1) )

        try:
            sline = line.strip()
            if len(sline) == 0 or sline[0] == '#': return

            # first field url string = protocol://user:password@host:port[/vost]
            parts = sline.split()
            urlstr = parts[0]
            url = urllib.parse.urlparse(urlstr)

            # credential details
            details = credential_details()
            details.url = url

            # no option
            if len(parts) == 1:
                if not self.isValid(url, details):
                    logger.error("bad credential 1 (%s)" % line)
                    return
                self.add(urlstr, details)
                return

            # parsing options :  comma separated option names
            # some option has name = value : like ssh_keyfile

            optline = sline.replace(urlstr, '')
            optline = optline.strip()
            optlist = optline.split(',')

            for optval in optlist:
                parts = optval.split('=')
                keyword = parts[0].strip()

                if keyword == 'ssh_keyfile':
                    details.ssh_keyfile = parts[1].strip()
                elif keyword == 'passive':
                    details.passive = True
                elif keyword == 'active':
                    details.passive = False
                elif keyword == 'binary':
                    details.binary = True
                elif keyword == 'ascii':
                    details.binary = False
                elif keyword == 'ssl':
                    details.tls = False
                elif keyword == 'tls':
                    details.tls = True
                elif keyword == 'prot_p':
                    details.prot_p = True
                elif keyword in ['bearer_token', 'bt']:
                    details.bearer_token = parts[1].strip()
                else:
                    logger.warning("bad credential option (%s)" % keyword)

            # need to check validity
            if not self.isValid(url, details):
                logger.error("bad credential 2 (%s)" % line)
                return

            # seting options to protocol

            self.add(urlstr, details)

        except:
            logger.error("credentials/parse %s" % line)
            logger.debug('Exception details: ', exc_info=True)

    def read(self, path):
        logger.debug("read")

        # read in provided credentials (not mandatory)
        try:
            if os.path.exists(path):
                with open(path) as f:
                    lines = f.readlines()

                for line in lines:
                    self.parse(line)
        except:
            logger.error("credentials/read path = %s" % path)
            logger.debug('Exception details: ', exc_info=True)
        #logger.debug("Credentials = %s\n" % self.credentials)

    def resolve(self, urlstr, url=None):

        # create url object if needed

        if not url:
            url = urllib.parse.urlparse(urlstr)

        # resolving credentials

        for s in self.credentials:
            details = self.credentials[s]
            u = details.url

            if url.scheme != u.scheme: continue
            if url.hostname != u.hostname: continue
            if url.port != u.port: continue
            if url.username != u.username:
                if url.username != None: continue
            if url.password != u.password:
                if url.password != None: continue

            # for AMQP...  vhost checking
            # amqp users have same credentials for any vhost
            # default /  may not be set...
            if 'amqp' in url.scheme:
                url_vhost = url.path
                u_vhost = u.path
                if url_vhost == '': url_vhost = '/'
                if u_vhost == '': u_vhost = '/'

                if url_vhost != u_vhost: continue

            # resolved : cache it and return

            self.credentials[urlstr] = details
            #logger.debug("Credentials get resolved %s %s" % (urlstr,details))
            return True, details

        return False, None
