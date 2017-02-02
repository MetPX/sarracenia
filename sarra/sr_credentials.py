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
# sr_credentials.py : python3 utility tool to configure all protocol credentials
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Dec 29 11:42:11 EST 2015
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

import os,urllib,urllib.parse,sys,re

# a class for credential details/options
# add any other options here... and process in parse

class credential_details:
      def __init__(self):
          self.url         = None
          self.ssh_keyfile = None
          self.passive     = True
          self.binary      = True
          self.tls         = False
          self.prot_p      = False
      def __str__(self):
          s  = ''
          s += self.url.geturl()
          s += " %s" % self.ssh_keyfile
          s += " %s" % self.passive
          s += " %s" % self.binary
          s += " %s" % self.tls
          s += " %s" % self.prot_p
          return s

# class credentials

class sr_credentials:

    def __init__(self, logger):
        self.logger      = logger
        self.credentials = {}
        self.pwre=re.compile(':[^/:]*@')
        
        self.logger.debug("sr_credentials __init__")

    def add(self,urlstr,details=None):

        # need to create url object
        if details == None :
           details     = credential_details()
           details.url = urllib.parse.urlparse(urlstr)

        self.credentials[urlstr] = details

    def get(self, urlstr ):
        self.logger.debug("sr_credentials get %s" % urlstr)

        # already cached

        if self.has(urlstr) :
           #self.logger.debug("sr_credentials get in cache %s %s" % (urlstr,self.credentials[urlstr]))
           return True, self.credentials[urlstr]

        # create url object if needed

        url = urllib.parse.urlparse(urlstr)

        # resolved from defined credentials

        ok, details = self.resolve(urlstr, url)
        if ok : return True, details

        # not found... is it valid ?
        if not self.isValid(url) :
           return False,None

        # cache it as is... we dont want to validate every time

        self.add(urlstr)
        self.logger.debug("sr_credentials get add %s %s" % (urlstr,self.credentials[urlstr]))
        return False,self.credentials[urlstr]

    def has(self, urlstr ):
        self.logger.debug("sr_credentials has %s" % urlstr)
        return urlstr in self.credentials

    def isTrue(self,S):
        s = S.lower()
        if  s == 'true' or s == 'yes' or s == 'on' or s == '1': return True
        return False

    def isValid(self,url,details=None):

        # network location
        if url.netloc == '' :
           # file (why here? anyway)
           if url.scheme == 'file' : return True
           return False

        # amqp... vhost not check: default / (sr_amqp.py)

        # user and password provided we are ok 
        user  = url.username != None and url.username != '' 
        pasw  = url.password != None and url.password != ''
        both  = user and pasw

        # we have everything
        if both : return True

        # we have no user and no pasw
        if not user and not pasw :
           if url.scheme == 'http'  : return True
           return False

        #  we have a pasw no user ?
        if pasw : return False

        #  we have a user (no pasw)
        if url.scheme != 'sftp' : return False
        if details    == None   : return False

        ssh_keyfile = details.ssh_keyfile

        if ssh_keyfile == None        : return False
        if os.path.exists(ssh_keyfile): return True
        return False

    def parse(self,line):
        self.logger.debug("sr_credentials parse %s" % self.pwre.sub(':<secret!>@', line, count=1) )

        try:
                sline = line.strip()
                if len(sline) == 0 or sline[0] == '#' : return
        
                # first field url string = protocol://user:password@host:port[/vost]
                parts  = sline.split()
                urlstr = parts[0]
                url    = urllib.parse.urlparse(urlstr)

                # credential details
                details     = credential_details()
                details.url = url
        
                # no option
                if len(parts) == 1 :
                   if not self.isValid(url,details) :
                      self.logger.error("bad credential 1 (%s)" % line)
                      return
                   self.add(urlstr,details)
                   return
        
                # parsing options :  comma separated option names
                # some option has name = value : like ssh_keyfile
        
                optline = sline.replace(urlstr,'')
                optline = optline.strip()
                optlist = optline.split(',')
        
                for optval in optlist:
                    parts   = optval.split('=')
                    keyword = parts[0].strip()
        
                    if    keyword == 'ssh_keyfile' : details.ssh_keyfile = parts[1].strip()
                    elif  keyword == 'passive'     : details.passive     = True
                    elif  keyword == 'active'      : details.passive     = False
                    elif  keyword == 'binary'      : details.binary      = True
                    elif  keyword == 'ascii'       : details.binary      = False
                    elif  keyword == 'ssl'         : details.tls         = False
                    elif  keyword == 'tls'         : details.tls         = True
                    elif  keyword == 'prot_p'      : details.prot_p      = True
                    else: self.logger.warning("bad credential option (%s)" % keyword)
        
                # need to check validity
                if not self.isValid(url,details) :
                   self.logger.error("bad credential 2 (%s)" % line)
                   return

                # seting options to protocol
        
                self.add(urlstr,details)
        
        except: 
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Type: %s, Value: %s" % (stype, svalue))
                self.logger.error("sr_credentials parse %s" % line)


    def read(self,path):
        self.logger.debug("sr_credentials read")

        # read in provided credentials (not mandatory)
        try :
              if os.path.exists(path):

                 f = open(path,'r')
                 lines = f.readlines()
                 f.close

                 for line in lines :
                     self.parse(line)

        except : 
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s" % (stype, svalue))
                 self.logger.error("sr_credentials read path = %s" % path)

        #self.logger.debug("credentials = %s\n" % self.credentials)


    def resolve(self,urlstr, url = None):

        # create url object if needed

        if not url :
           url = urllib.parse.urlparse(urlstr)

        # resolving credentials

        for s in self.credentials :
            details = self.credentials[s]
            u       = details.url

            if url.scheme        != u.scheme   : continue
            if url.hostname      != u.hostname : continue
            if url.port          != u.port     : continue
            if url.username      != u.username : 
               if url.username   != None       : continue
            if url.password      != u.password : 
               if url.password   != None       : continue

            # for AMQP...  vhost checking
            # amqp users have same credentials for any vhost
            # default /  may not be set...
            if 'amqp' in url.scheme :
                url_vhost = url.path
                u_vhost   = u.path
                if url_vhost == '' : url_vhost = '/'
                if u_vhost   == '' : u_vhost   = '/'

                if url_vhost != u_vhost : continue

            # resolved : cache it and return

            self.credentials[urlstr] = details
            #self.logger.debug("sr_credentials get resolved %s %s" % (urlstr,details))
            return True, details

        return False, None


# ===================================
# self testing
# ===================================

class test_logger:
      def silence(self,str):
          pass
      def __init__(self):
          self.debug   = self.silence
          self.error   = print
          self.info    = self.silence
          self.warning = print

def test_sr_credentials():

    logger      = test_logger()
    credentials = sr_credentials(logger)

    # covers : parse, credential_details obj, isTrue, add
    line = "ftp://guest:toto@localhost active , binary"
    credentials.parse(line)

    # covers get with match
    urlstr = "ftp://guest:toto@localhost"
    ok, details = credentials.get(urlstr)
    if not ok :
       print("sr_credentials TEST 1a FAILED")
       sys.exit(1)

    # check details
    if not details.passive == False or \
       not details.binary  == True   :
       print("sr_credentials TEST 1b FAILED")
       sys.exit(1)


    # covers get with resolve 1
    urlstr = "ftp://localhost"
    ok, details = credentials.get(urlstr)
    if not ok :
       print("sr_credentials TEST 2 FAILED")
       print(urlstr,details)
       sys.exit(1)

    # covers get with resolve 2
    urlstr = "ftp://guest@localhost"
    ok, details = credentials.get(urlstr)
    if not ok :
       print("sr_credentials TEST 3 FAILED")
       print(urlstr,details)
       sys.exit(1)

    # covers unresolve get
    urlstr = "http://localhost"
    ok, details = credentials.get(urlstr)
    if ok :
       print("sr_credentials TEST 4 FAILED")
       print(urlstr,details)
       sys.exit(1)

    # covers read
    urlstr = "sftp://ruser@remote"
    f = open('/tmp/mytoto2','w')
    f.write(urlstr + " ssh_keyfile=/tmp/mytoto2\n")
    f.close()

    credentials.read('/tmp/mytoto2')
    ok, details = credentials.get(urlstr)
    if not ok or details.ssh_keyfile != '/tmp/mytoto2' :
       print("sr_credentials TEST 5 FAILED")
       print(urlstr,details)
       sys.exit(1)

    os.unlink('/tmp/mytoto2')

    # covers isValid
    if credentials.isValid(urllib.parse.urlparse("ftp://host"))       or \
       credentials.isValid(urllib.parse.urlparse("file://aaa/"))      or \
       credentials.isValid(urllib.parse.urlparse("ftp://user@host"))  or \
       credentials.isValid(urllib.parse.urlparse("ftp://user:@host")) or \
       credentials.isValid(urllib.parse.urlparse("ftp://:pass@host"))    :
       print("sr_credentials TEST 6 FAILED")
       sys.exit(1)

    print("sr_credentials TEST PASSED")


# ===================================
# MAIN
# ===================================

def main():

    test_sr_credentials()
    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()
