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
# sr_sftp.py : python3 utility tools for sftp usage in sarracenia
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

import paramiko, os,sys
from   paramiko import *

import logging


def sftp_download( msg, iuser, ipassword, ssh_keyfile ):
    url       = msg.url
    host      = url.hostname
    port      = url.port
    user      = url.username
    password  = url.password
    urlstr    = url.geturl()

    if iuser     != None : user = iuser
    if ipassword != None : password = ipassword

    token    = url.path[1:].split('/')
    
    cdir     = '/'.join(token[:-1])
    cfile    = token[-1]

    try :

            paramiko.util.logging.getLogger().setLevel(logging.WARN)

            t = None
            if port == None : 
               t = paramiko.Transport(host)
            else:
               t_args = (host,port)
               t = paramiko.Transport(t_args)

            if ssh_keyfile != None :
               key=DSSKey.from_private_key_file(ssh_keyfile,password=None)
               t.connect(username=user,pkey=key)
            else:
               t.connect(username=user,password=password)

            sftp = paramiko.SFTP.from_transport(t)
            sftp.chdir(cdir)

            str_range = ''
            if msg.partflg == 'i' :
               str_range = 'bytes=%d-%d'%(msg.offset,msg.offset+msg.length-1)

            #download file

            msg.logger.info('Downloads: %s %s into %s %d-%d' % 
                (urlstr,str_range,msg.local_file,msg.local_offset,msg.local_offset+msg.length-1))


            response  = sftp.file(cfile,'rb',msg.bufsize)
            if msg.partflg == 'i' :
               response.seek(msg.offset,0)
               ok = sftp_write_length(response,msg)
            else :
               ok = sftp_write(response,msg)

            try    : sftp.close()
            except : pass
            try    : t.close()
            except : pass

            return ok
            
    except:
            try    : sftp.close()
            except : pass
            try    : t.close()
            except : pass

            (stype, svalue, tb) = sys.exc_info()
            msg.logger.error("Download failed %s. Type: %s, Value: %s" % (urlstr, stype ,svalue))
            msg.code    = 499
            msg.message = 'sftp download problem'
            msg.log_error()

            return False

    msg.code    = 499
    msg.message = 'sftp download problem'
    msg.log_error()

    return False

# read all file no worry

def sftp_write(req,msg):
    if not os.path.isfile(msg.local_file) :
       fp = open(msg.local_file,'w')
       fp.close

    fp = open(msg.local_file,'r+b')
    if msg.local_offset != 0 : fp.seek(msg.local_offset,0)

    while True:
          chunk = req.read(msg.bufsize)
          if not chunk : break
          fp.write(chunk)

    fp.close()

    msg.code    = 201
    msg.message = 'Downloaded'
    msg.log_info()

    return True


# read exact length

def sftp_write_length(req,msg):
    # file should exists
    if not os.path.isfile(msg.local_file) :
       fp = open(msg.local_file,'w')
       fp.close()

    # file open read/modify binary
    fp = open(msg.local_file,'r+b')
    if msg.local_offset != 0 : fp.seek(msg.local_offset,0)

    nc = int(msg.length/msg.bufsize)
    r  =     msg.length%msg.bufsize

    # read/write bufsize "nc" times
    i  = 0
    while i < nc :
          chunk = req.read(msg.bufsize)
          fp.write(chunk)
          i = i + 1

    # remaining
    if r > 0 :
       chunk = req.read(r)
       fp.write(chunk)

    fp.close()

    msg.code    = 201
    msg.message = 'Downloaded'
    msg.log_info()

    return True

