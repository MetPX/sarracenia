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

import logging

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)

import os
import re
import urllib, urllib.parse
import sys


class Credential:
    r"""

    An object that holds information about a credential, read from a 
    credential file, which has one credential per line, format::

      url option1=value1, option2=value2
       
    Examples::
        sftp://alice@herhost/ ssh_keyfile=/home/myself/mykeys/.ssh.id_dsa
        ftp://georges:Gpass@hishost/  passive = True, binary = True
       
    `Format Documentation. <https://metpx.github.io/sarracenia/Reference/sr3_credentials.7.html>`_

    Attributes:
        url (urllib.parse.ParseResult): object with URL, password, etc.
        ssh_keyfile (str): path to SSH key file for SFTP
        passive (bool): use passive FTP mode, defaults to ``True``
        binary (bool): use binary FTP mode, defaults to ``True``
        tls (bool): use FTPS with TLS, defaults to ``False``
        prot_p (bool): use a secure data connection for TLS
        bearer_token (str): bearer token for HTTP authentication
        login_method (str): force a specific login method for AMQP (PLAIN,
            AMQPLAIN, EXTERNAL or GSSAPI)
        implicit_ftps (bool): use implicit FTPS, defaults to ``False`` (i.e. explicit FTPS)

    Usage:

       # build a credential from a url string:

       from sarracenia.credentials import Credential

       broker = Credential('amqps://anonymous:anonymous@hpfx.collab.science.gc.ca')



    """

    def __init__(self, urlstr=None):
        """Create a Credential object.

            Args:
                urlstr (str): a URL in string form to be parsed.
        """

        if urlstr is not None:
            self.url = urllib.parse.urlparse(urlstr)
        else:
            self.url = None

        self.ssh_keyfile = None
        self.passive = True
        self.binary = True
        self.tls = False
        self.prot_p = False
        self.bearer_token = None
        self.login_method = None
        self.s3_endpoint = None
        self.s3_session_token = None
        self.azure_credentials = None
        self.implicit_ftps = False

    def __str__(self):
        """Returns attributes of the Credential object as a readable string.
        """

        s = ''
        if False:
            s += self.url.geturl()
        else:
            s += self.url.scheme + '://'
            if self.url.username:
                s += self.url.username
            #if self.url.password:
            #   s += ':' + self.url.password
            if self.url.hostname:
                s += '@' + self.url.hostname
            if self.url.port:
                s += ':' + str(self.url.port)
            if self.url.path:
                s += self.url.path

        s += " %s" % self.ssh_keyfile
        s += " %s" % self.passive
        s += " %s" % self.binary
        s += " %s" % self.tls
        s += " %s" % self.prot_p
        s += " %s" % self.bearer_token
        s += " %s" % self.login_method
        s += " %s" % self.s3_endpoint
        #want to show they provided a session token, but not leak it (like passwords above)
        s += " %s" % 'Yes' if self.s3_session_token != None else 'No'
        s += " %s" % 'Yes' if self.azure_credentials != None else 'No'
        s += " %s" % self.implicit_ftps

        return s


class CredentialDB:
    """Parses, stores and manages Credential objects.

    Attributes:
        credentials (dict): contains all sarracenia.credentials.Credential objects managed by the CredentialDB.

    Usage:
       # build a credential via lookup in the normal files: 
       import CredentialDB from sarracenia.credentials

       credentials = CredentialDB.read( "/the/path/to/the/credentials.conf" )

       # if there are corresponding passwords or modulation of login information look it up.
       
       broker = credentials.get( "amqps://hpfx.collab.science.gc.ca" )
       remote = credentials.get( "sftp://hoho@theserver" )
    """

    def __init__(self, Unused_logger=None):
        """Create a CredentialDB.

        Args:
            Unused_logger: logger argument no longer used... left there for API compat with old calls.
        """
        self.credentials = {}
        self.pwre = re.compile(':[^/:]*@')

        logger.debug("__init__")

    def add(self, urlstr, details=None):
        """Add a new credential to the DB.

        Args:
            urlstr (str): string-formatted URL to be parsed and added to DB.
            details (sarracenia.credentials.Credential): a Credential object can be passed in, otherwise one is
                created by parsing urlstr.
        """

        # need to create url object
        key=urlstr
        if details == None:
            details = Credential()
            details.url = urllib.parse.urlparse(urlstr)
            if hasattr(details.url,'password'):
                key = key.replace( f":{details.url.password}", "" )

        self.credentials[key] = details

    def get(self, urlstr):
        """Retrieve a Credential from the DB by urlstr. If the Credential is valid, but not already cached, it will be
        added to the CredentialDB.

        Args:
            urlstr (str): credentials as URL string to be parsed.
        
        Returns:
            tuple: containing
                cache_result (bool): ``True`` if the credential was retrieved from the CredentialDB cache, ``False``
                    if it was not in the cache. Note that ``False`` does not imply the Credential or urlstr is
                    invalid.
                credential (sarracenia.credentials.Credential): the Credential
                    object matching the urlstr, ``None`` if urlstr is invalid.
        """
        #logger.debug("CredentialDB get %s" % urlstr)

        # already cached

        if self.has(urlstr):
            #logger.debug("CredentialDB get in cache %s %s" % (urlstr,self.credentials[urlstr]))
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
                return False, self.credentials[urlstr.replace(':anonymous@','@')]

        # resolved from defined credentials
        ok, details = self._resolve(urlstr, url)
        if ok: return True, details

        # not found... is it valid ?
        if not self.isValid(url):
            return False, None

        # cache it as is... we dont want to validate every time

        self.add(urlstr)
        if url and url.password:
            k=urlstr.replace( f':{url.password}@', '@' )
        else:
            k=urlstr
        return False, self.credentials[k]

    def has(self, urlstr):
        """Return ``True`` if the Credential matching the urlstr is already in the CredentialDB.
        
        Args:
            urlstr(str): credentials in a URL string.
        """
        logger.debug("has %s" % urlstr)
        return urlstr in self.credentials

    def isTrue(self, S):
        """Returns ``True`` if s is ``true``, ``yes``, ``on`` or ``1``.

        Args:
            S (str): string to check if true.
        """
        s = S.lower()
        if s == 'true' or s == 'yes' or s == 'on' or s == '1': return True
        return False

    def isValid(self, url, details=None):
        """Validates a URL and Credential object. Checks for empty passwords, schemes, etc.
            
        Args:
            url (urllib.parse.ParseResult): ParseResult object for a URL.
            details (sarracenia.credentials.Credential): sarra Credential object containing additional details about
                the URL.

        Returns:
            bool: ``True`` if a URL is valid, ``False`` if not.
        """

        # network location
        if url.netloc == '':
            # file (why here? anyway)
            if url.scheme == 'file': return True
            logger.error( f'no network location, and not a file url' )
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
            if url.scheme in ['http', 'https', 'sftp', 's3', 'azure', 'azblob']: return True
            logger.error( f'unknown scheme: {url.scheme}')
            return False

        #  we have a pasw no user
        if pasw:
            # not sure... sftp hope to get user from .ssh/config
            if url.scheme == 'sftp': return True
            logger.error( f'password with no username specified')
            return False

        #  we only have a user ... permitted only for sftp

        if url.scheme != 'sftp': 
            logger.error( f'credential not found'  )
            return False

        #  sftp and an ssh_keyfile was provided... check that it exists

        if details and details.ssh_keyfile:
            if not os.path.exists(details.ssh_keyfile): 
                logger.error( f'ssh_keyfile not found: {details.ssh_keyfile}')
                return False

        #  sftp with a user (and perhaps a valid ssh_keyfile)

        return True

    def _parse(self, line):
        """Parse a line of a credentials file, add it to the CredentialDB.

        Args:
            line (str): line to be parsed.
        """
        #logger.debug("parse %s" % self.pwre.sub(':<secret!>@', line, count=1) )

        try:
            sline = line.strip()
            if len(sline) == 0 or sline[0] == '#': return

            # first field url string = protocol://user:password@host:port[/vost]
            parts = sline.split()
            urlstr = parts[0]
            url = urllib.parse.urlparse(urlstr)

            # credential details
            details = Credential()
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
                    details.ssh_keyfile = os.path.expandvars(os.path.expanduser(parts[1].strip()))
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
                elif keyword == 'login_method':
                    details.login_method = parts[1].strip()
                elif keyword == 's3_session_token':
                    details.s3_session_token = urllib.parse.unquote(parts[1].strip())
                elif keyword == 's3_endpoint':
                    details.s3_endpoint = parts[1].strip()
                elif keyword == 'azure_storage_credentials':
                    details.azure_credentials = urllib.parse.unquote(parts[1].strip())
                elif keyword == 'implicit_ftps':
                    details.implicit_ftps = True
                    details.tls = True
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
        """Read in a file containing credentials (e.g. credentials.conf). All credentials are parsed and added to the
        CredentialDB.

        Args:
            path (str): path of file to be read.
        """
        logger.debug("read")

        # read in provided credentials (not mandatory)
        try:
            if os.path.exists(path):
                with open(path) as f:
                    lines = f.readlines()

                for line in lines:
                    self._parse(line)
        except:
            logger.error("credentials/read path = %s" % path)
            logger.debug('Exception details: ', exc_info=True)
        #logger.debug("Credentials = %s\n" % self.credentials)

    def _resolve(self, urlstr, url=None):
        """Resolve credentials for AMQP vhost from ones passed as a string, and optionally a urllib.parse.ParseResult
        object, into a sarracenia.credentials.Credential object.

        Args:
            urlstr (str): credentials in a URL string.
            url (urllib.parse.ParseResult): ParseResult object with creds.

        Returns:
            tuple: containing
                result (bool): ``False`` if the creds were not in the CredentialDB. ``True`` if they were.
                details (sarracenia.credentials.Credential): the updated Credential object, or ``None``.
                

        """

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
