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
# sr_ftp.py : python3 utility tools for ftp usage in sarracenia
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

import ftplib,os,sys

class ftp_chunk():
      def __init__(self, fp, msg):
          self.fp    = fp
          self.msg   = msg
          self.begin = msg.offset
          self.end   = msg.offset + msg.length - 1

          # bufr pos
          self.bpos  = 0
          self.blast = 0

      def write(self,buf):
          # too far
          if self.bpos > self.end : return

          size = len(buf)

          # too soon
          self.blast = self.bpos + size - 1
          if self.blast < self.begin : 
             self.bpos = self.blast + 1
             return

          # ok inside

          start = 0
          if self.bpos < self.begin : start = self.begin - self.bpos

          end   = 0
          if self.blast > self.end  : end   = self.end   - self.blast

          if end == 0 :
             self.fp.write(buf[start:])
          else :
             self.fp.write(buf[start:end])



def ftp_download( msg, iuser, ipassword, iftp_mode, ibinary ):

    url       = msg.url
    host      = url.hostname
    port      = url.port
    user      = url.username
    password  = url.password
    urlstr    = url.geturl()

    if iuser     != None : user = iuser
    if ipassword != None : password = ipassword

    token       = url.path[1:].split('/')
    cdir        = '/'.join(token[:-1])
    remote_file = token[-1]

    try :
            if port == None or port == 21:
               ftp = ftplib.FTP(host, user, password)
            else :
               ftp = ftplib.FTP()
               ftp.connect(host,port)
               ftp.login(user, password)

            if iftp_mode == 'active':
                ftp.set_pasv(False)
            else:
                ftp.set_pasv(True)

            ftp.cwd(cdir)

            str_range = ''
            if msg.partflg == 'i' :
               str_range = 'bytes=%d-%d'%(msg.offset,msg.offset+msg.length-1)

            #download file

            msg.logger.info('Downloads: %s %s into %s %d-%d' % 
                (urlstr,str_range,msg.local_file,msg.local_offset,msg.local_offset+msg.length-1))

            # downloading entire file... no sweat

            if msg.partflg != 'i' :
               ok = ftp_write(ftp,remote_file,msg,ibinary)

            # no seek in ftplib.py
            # to get a fraction of a file, read the entire file and
            # keep the part needed... should never be used... but supported

            else:
               ok = ftp_write_from_chunk(ftp,remote_file,msg,ibinary)

            try    : ftp.close()
            except : pass

            return ok
            
    except:
            try    : ftp.close()
            except : pass

            (stype, svalue, tb) = sys.exc_info()
            msg.logger.error("Download failed %s. Type: %s, Value: %s" % (urlstr, stype ,svalue))
            msg.code    = 499
            msg.message = 'ftp download problem'
            msg.log_error()

            return False

    msg.code    = 499
    msg.message = 'ftp download problem'
    msg.log_error()

    return False

# read all file no worry

def ftp_write(ftp,remote_file,msg,binary):
    if not os.path.isfile(msg.local_file) :
       fp = open(msg.local_file,'w')
       fp.close

    fp = open(msg.local_file,'r+b')
    if msg.local_offset != 0 : fp.seek(msg.local_offset,0)

    if binary :
       ftp.retrbinary('RETR ' + remote_file, fp.write )
    else :
       ftp.retrlines('RETR '  + remote_file, fp.write )

    fp.close()

    msg.code    = 201
    msg.message = 'Downloaded'
    msg.log_info()

    return True

# read all file no worry

def ftp_write_chunk(buf):
    size = len(buf)

def ftp_write_from_chunk(ftp,remote_file,msg,binary):
  
    if not os.path.isfile(msg.local_file) :
       fp = open(msg.local_file,'w')
       fp.close

    fp = open(msg.local_file,'r+b')
    if msg.local_offset != 0 : fp.seek(msg.local_offset,0)


    chunk = ftp_chunk(fp,msg)

    if binary :
       ftp.retrbinary('RETR ' + remote_file, chunk.write )
    else :
       ftp.retrlines('RETR '  + remote_file, chunk.write )

    fp.close()

    msg.code    = 201
    msg.message = 'Downloaded'
    msg.log_info()

    return True
