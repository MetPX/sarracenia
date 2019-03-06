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
# sr_ftp.py : python3 utility tools for ftp usage in sarracenia
#             Since python3.2 supports ftps (RFC 4217)
#             I tested it and works for all our ftps pull/sender as of today
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Nov 23 21:12:24 UTC 2017
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

import ftplib,os,sys,time

try :
         from sr_util            import *
except :
         from sarra.sr_util      import *

#============================================================
# ftp protocol in sarracenia supports/uses :
#
# connect
# close
#
# if a source    : get    (remote,local)
#                  ls     ()
#                  cd     (dir)
#                  delete (path)
#
# if a sender    : put    (local,remote)
#                  cd     (dir)
#                  mkdir  (dir)
#                  umask  ()
#                  chmod  (perm)
#                  rename (old,new)
#
# FTP : no remote file seek... so 'I' part impossible
#

class sr_ftp(sr_proto):
    def __init__(self, parent) :
        parent.logger.debug("sr_ftp __init__")
        sr_proto.__init__(self,parent)
        self.user_cache_dir = parent.user_cache_dir
        # ftp command times out after 20 secs
        # this setting is different from the computed iotime (sr_proto)
        self.init()
 
    # cd
    def cd(self, path):
        self.logger.debug("sr_ftp cd %s" % path)

        alarm_set(self.iotime)
        self.ftp.cwd(self.originalDir)
        self.ftp.cwd(path)
        self.pwd = path
        alarm_cancel()

    def cd_forced(self,perm,path) :
        self.logger.debug("sr_ftp cd_forced %d %s" % (perm,path))

        # try to go directly to path

        alarm_set(self.iotime)
        self.ftp.cwd(self.originalDir)
        try   :
                self.ftp.cwd(path)
                alarm_cancel()
                return
        except: pass
        alarm_cancel()

        # need to create subdir

        subdirs = path.split("/")
        if path[0:1] == "/" : subdirs[0] = "/" + subdirs[0]

        for d in subdirs :
            if d == ''   : continue
            # try to go directly to subdir
            try   :
                    alarm_set(self.iotime)
                    self.ftp.cwd(d)
                    alarm_cancel()
                    continue
            except: pass

            # create
            alarm_set(self.iotime)
            self.ftp.mkd(d)
            alarm_cancel()

            # chmod
            alarm_set(self.iotime)
            self.ftp.voidcmd('SITE CHMOD ' + "{0:o}".format(perm) + ' ' + d)
            alarm_cancel()

            # cd
            alarm_set(self.iotime)
            self.ftp.cwd(d)
            alarm_cancel()

    # check_is_connected

    def check_is_connected(self):
        self.logger.debug("sr_ftp check_is_connected")

        if self.ftp == None  : return False
        if not self.connected : return False

        if self.destination != self.parent.destination :
           self.close()
           return False

        self.batch = self.batch + 1
        if self.batch > self.parent.batch :
           self.close()
           return False

        # really connected
        try    : cwd = self.getcwd()
        except :
                 self.close()
                 return False

        return True

    # chmod
    def chmod(self,perm,path):
        self.logger.debug("sr_ftp chmod %s %s" % (str(perm),path))
        alarm_set(self.iotime)
        self.ftp.voidcmd('SITE CHMOD ' + "{0:o}".format(perm) + ' ' + path)
        alarm_cancel()

    # close
    def close(self):
        self.logger.debug("sr_ftp close")

        old_ftp = self.ftp

        self.init()

        try:
                alarm_set(self.iotime)
                old_ftp.quit()
        except: pass
        alarm_cancel()

    # connect...
    def connect(self):
        self.logger.debug("sr_ftp connect %s" % self.parent.destination)

        self.connected   = False
        self.destination = self.parent.destination

        if not self.credentials() : return False


        # timeout alarm 100 secs to connect
        alarm_set(self.iotime)
        try:
                expire  = -999
                if self.parent.timeout : expire = self.parent.timeout
                if self.port == '' or self.port == None : self.port = 21

                if not self.tls :
                   ftp = ftplib.FTP()
                   ftp.connect(self.host,self.port,timeout=expire)
                   ftp.login(self.user, self.password)
                else :
                   # ftplib supports FTPS with TLS 
                   ftp = ftplib.FTP_TLS(self.host,self.user,self.password,timeout=expire)
                   if self.prot_p : ftp.prot_p()
                   # needed only if prot_p then set back to prot_c
                   #else          : ftp.prot_c()

                ftp.set_pasv(self.passive)

                self.originalDir = '.'

                try:
                    self.originalDir = ftp.pwd()
                except:
                    self.logger.warning("Unable to ftp.pwd")
                    self.logger.debug('Exception details: ', exc_info=True)

                self.pwd = self.originalDir

                self.connected = True

                self.ftp = ftp

                self.file_index_cache = self.user_cache_dir + os.sep + '.dest_file_index'
                if os.path.isfile(self.file_index_cache): self.load_file_index()
                else: self.init_file_index()

                #alarm_cancel()
                return True

        except:
            self.logger.error("Unable to connect to %s (user:%s)" % self.host, self.user)
            self.logger.debug('Exception details: ', exc_info=True)

        alarm_cancel()
        return False

    # credentials...
    def credentials(self):
        self.logger.debug("sr_ftp credentials %s" % self.destination)

        try:
                ok, details = self.parent.credentials.get(self.destination)
                if details  : url = details.url

                self.host     = url.hostname
                self.port     = url.port
                self.user     = url.username
                self.password = url.password

                self.passive  = details.passive
                self.binary   = details.binary
                self.tls      = details.tls
                self.prot_p   = details.prot_p

                return True

        except:
                self.logger.error("sr_ftp/credentials: unable to get credentials for %s" % self.destination)
                self.logger.debug('Exception details: ', exc_info=True)

        return False

    # delete
    def delete(self, path):
        self.logger.debug( "sr_ftp rm %s" % path)
        alarm_set(self.iotime)
        # if delete does not work (file not found) run pwd to see if connection is ok
        try   : self.ftp.delete(path)
        except: d = self.ftp.pwd()
        alarm_cancel()

    # get
    def get(self, remote_file, local_file, remote_offset=0, local_offset=0, length=0 ):
        self.logger.debug( "sr_ftp get %s %s %d" % (remote_file,local_file,local_offset))

        # open local file
        dst = self.local_write_open(local_file, local_offset)

        # initialize sumalgo
        if self.sumalgo : self.sumalgo.set_path(remote_file)

        # download
        self.write_chunk_init(dst)
        if self.binary : self.ftp.retrbinary('RETR ' + remote_file, self.write_chunk, self.bufsize )
        else           : self.ftp.retrlines ('RETR ' + remote_file, self.write_chunk )
        rw_length = self.write_chunk_end()

        # close
        self.local_write_close(dst)


    # getcwd
    def getcwd(self):
        alarm_set(self.iotime)
        pwd = self.ftp.pwd()
        alarm_cancel()
        return pwd

    # init
    def init(self):
        self.logger.debug("sr_ftp init")
        sr_proto.init(self)

        self.connected   = False 
        self.ftp         = None
        self.details     = None

        self.batch       = 0

    # init_file_index
    def init_file_index(self):
        self.logger.debug("sr_ftp init_file_index")
        self.init_nlst = sorted(self.ftp.nlst())
        self.logger.debug("sr_ftp nlst: %s" % self.init_nlst)
        self.init_nlst_index = 0
        if self.init_nlst:
            self.ftp.retrlines('LIST', self.ls_file_index )
        else:
            alarm_cancel()
        if hasattr(self,'file_index'): self.write_file_index()

    # load_file_index
    def load_file_index(self):
        self.logger.debug("sr_ftp load_file_index")
        alarm_cancel()
        try:
            with open(self.file_index_cache,'r') as fp:
                index = int(fp.read())
                self.file_index = index
        except:
            self.logger.error("load_file_index: Unable to determine file index from %s" % self.file_index_cache)

    # ls
    def ls(self):
        self.logger.debug("sr_ftp ls")
        self.entries = {}
        alarm_set(self.iotime)
        self.ftp.retrlines('LIST',self.line_callback )
        alarm_cancel()
        self.logger.debug("sr_ftp ls = %s" % self.entries )
        return self.entries

    # line_callback: entries[filename] = 'stripped_file_description'
    def line_callback(self,iline):
        self.logger.debug("sr_ftp line_callback %s" % iline)

        alarm_cancel()

        oline  = iline
        oline  = oline.strip('\n')
        oline  = oline.strip()
        oline  = oline.replace('\t',' ')
        opart1 = oline.split(' ')
        opart2 = []

        for p in opart1 :
            if p == ''  : continue
            opart2.append(p)
        # else case is in the event of unlikely race condition
        if hasattr(self, 'file_index'): fil = ' '.join(opart2[self.file_index:])
        else: fil = ' '.join(opart2[8:])
        # next line is for backwards compatibility only
        if not self.parent.ls_file_index in [-1,len(opart2)-1] : fil =  ' '.join(opart2[self.parent.ls_file_index:])
        line = ' '.join(opart2)

        self.entries[fil] = line

        alarm_set(self.iotime)

    # ls_file_index
    def ls_file_index(self,iline):
        self.logger.debug("sr_ftp ls_file_index")

        alarm_cancel()

        oline = iline
        oline = oline.strip('\n')
        oline = oline.strip()
        oline = oline.replace('\t',' ')
        opart1 = oline.split(' ')
        opart2 = []

        for p in opart1 :
            if p == ''  : continue
            opart2.append(p)

        try:
            file_index = opart2.index(self.init_nlst[self.init_nlst_index])
            self.file_index = file_index
        except:
            pass
        finally:
            self.init_nlst_index += 1

    # mkdir
    def mkdir(self, remote_dir):
        self.logger.debug("sr_ftp mkdir %s" % remote_dir)
        alarm_set(self.iotime)
        self.ftp.mkd(remote_dir)
        alarm_cancel()
        alarm_set(self.iotime)
        self.ftp.voidcmd('SITE CHMOD ' + "{0:o}".format(self.parent.chmod_dir) + ' ' + remote_dir)
        alarm_cancel()

    # put
    def put(self, local_file, remote_file, local_offset=0, remote_offset=0, length=0 ):
        self.logger.debug("sr_ftp put %s %s" % (local_file,remote_file))

        # open 
        src = self.local_read_open(local_file, local_offset)

        # upload
        self.write_chunk_init(None)
        if self.binary : self.ftp.storbinary("STOR " + remote_file, src, self.bufsize, self.write_chunk)
        else           : self.ftp.storlines ("STOR " + remote_file, src, self.write_chunk)
        rw_length = self.write_chunk_end()

        # close 
        self.local_read_close(src)

    # rename
    def rename(self,remote_old,remote_new) :
        self.logger.debug("sr_ftp rename %s %s" % (remote_old,remote_new))
        alarm_set(self.iotime)
        self.ftp.rename(remote_old,remote_new)
        alarm_cancel()

    # rmdir
    def rmdir(self, path):
        self.logger.debug("sr_ftp rmdir %s" % path)
        alarm_set(self.iotime)
        self.ftp.rmd(path)
        alarm_cancel()

    # umask
    def umask(self) :
        self.logger.debug("sr_ftp umask")
        alarm_set(self.iotime)
        self.ftp.voidcmd('SITE UMASK 777')
        alarm_cancel()

    # write_file_index
    def write_file_index(self):
        self.logger.debug("sr_ftp write_file_index")
        try:
            with open(self.file_index_cache,'w') as fp:
                fp.write(str(self.file_index))
        except:
            self.logger.warning("Unable to write file_index to cache file %s" % self.file_index_cache)

#============================================================
#
# ftp_transport inherited from sr_transport
#
#============================================================

class ftp_transport(sr_transport):
    def __init__(self) :
        sr_transport.__init__(self)
        self.pclass = sr_ftp
        self.scheme = 'ftp'
