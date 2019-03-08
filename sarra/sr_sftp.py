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
# sr_sftp.py : python3 utility tools for sftp usage in sarracenia
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Nov 23 21:08:09 UTC 2017
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

import logging, paramiko, os,sys,time
from   paramiko import *
from   stat     import *

try :
         from sr_util            import *
except :
         from sarra.sr_util      import *

#============================================================
# sftp protocol in sarracenia supports/uses :
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
# SFTP : supports remote file seek... so 'I' part possible
#
#
# require   parent.logger
#           parent.credentials
#           parent.destination 
#           parent.batch 
#           parent.chmod
#           parent.chmod_dir
#     opt   parent.kbytes_ps
#     opt   parent.bufsize

class sr_sftp(sr_proto):
    def __init__(self, parent) :
        parent.logger.debug("sr_sftp __init__")
        sr_proto.__init__(self,parent)
        self.user_cache_dir = parent.user_cache_dir

        # sftp command times out after 20 secs
        # this setting is different from the computed iotime (sr_proto)

        self.init()

        self.ssh_config  = None

        try :
                self.ssh_config = paramiko.SSHConfig()
                ssh_config      = os.path.expanduser('~/.ssh/config')
                if os.path.isfile(ssh_config) :
                   fp = open(ssh_config,'r')
                   self.ssh_config.parse(fp)
                   fp.close()
        except:
                self.logger.error("sr_sftp/__init__: unable to load ssh config %s" % ssh_config)
                self.logger.debug('Exception details: ', exc_info=True)

    # cd
    def cd(self, path):
        self.logger.debug("sr_sftp cd %s" % path)
        alarm_set(self.iotime)
        self.sftp.chdir(self.originalDir)
        self.sftp.chdir(path)
        self.pwd = path
        alarm_cancel()

    # cd forced
    def cd_forced(self,perm,path) :
        self.logger.debug("sr_sftp cd_forced %d %s" % (perm,path))

        # try to go directly to path

        alarm_set(self.iotime)
        self.sftp.chdir(self.originalDir)
        try   :
                self.sftp.chdir(path)
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
                    self.sftp.chdir(d)
                    alarm_cancel()
                    continue
            except: pass

            # create and go to subdir
            alarm_set(self.iotime)
            self.sftp.mkdir(d,self.parent.chmod_dir)
            self.sftp.chdir(d)
            alarm_cancel()

    def check_is_connected(self):
        self.logger.debug("sr_sftp check_is_connected")

        if self.sftp == None  : return False
        if not self.connected : return False

        if self.destination != self.parent.destination :
           self.close()
           return False

        self.batch = self.batch + 1
        if self.batch > self.parent.batch :
           self.close()
           return False

        # really connected, getcwd would not work, send_ignore would not work... so chdir used
        try    :
                 alarm_set(self.iotime)
                 self.sftp.chdir(self.originalDir)
                 alarm_cancel()
        except :
                 self.close()
                 return False

        return True

    # chmod
    def chmod(self,perm,path):
        self.logger.debug("sr_sftp chmod %s %s" % ( "{0:o}".format(perm),path))
        alarm_set(self.iotime)
        self.sftp.chmod(path,perm)
        alarm_cancel()

    # close
    def close(self):
        self.logger.debug("sr_sftp close")

        old_sftp = self.sftp
        old_ssh  = self.ssh

        self.init()

        alarm_set(self.iotime)
        try   : old_sftp.close()
        except: pass
        try   : old_ssh.close()
        except: pass
        alarm_cancel()

    # connect...
    def connect(self):
        self.logger.debug("sr_sftp connect %s" % self.parent.destination)

        if self.connected: self.close()

        self.connected   = False
        self.destination = self.parent.destination
        self.timeout     = self.parent.timeout

        if not self.credentials() : return False

        alarm_set(self.iotime)
        try:

                logger = logging.getLogger('paramiko')
                logger.setLevel(logging.CRITICAL)
                self.ssh = paramiko.SSHClient()
                # FIXME this should be an option... for security reasons... not forced
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                if self.password:
                   self.ssh.connect(self.host,self.port,self.user,self.password, \
                                    pkey=None,key_filename=self.ssh_keyfile,\
                                    timeout=self.timeout,allow_agent=False,look_for_keys=False)
                else:
                   self.ssh.connect(self.host,self.port,self.user,self.password, \
                                    pkey=None,key_filename=self.ssh_keyfile,\
                                    timeout=self.timeout)
                #if ssh_keyfile != None :
                #  key=DSSKey.from_private_key_file(ssh_keyfile,password=None)

                sftp = self.ssh.open_sftp()
                if self.timeout != None :
                   self.logger.debug("sr_sftp connect setting timeout %f" % self.timeout)
                   channel = sftp.get_channel()
                   channel.settimeout(self.timeout)

                sftp.chdir('.')
                self.originalDir = sftp.getcwd()
                self.pwd         = self.originalDir

                self.connected   = True
                self.sftp        = sftp

                self.file_index_cache = self.user_cache_dir + os.sep + '.dest_file_index'
                if os.path.isfile(self.file_index_cache): self.load_file_index()
                else: self.init_file_index()

                #alarm_cancel()
                return True

        except:
            self.logger.error("sr_sftp/connect: unable to connect to %s (user:%s)" % (self.host, self.user))
            self.logger.debug('Exception details: ', exc_info=True)

        alarm_cancel()
        return False

    # credentials...
    def credentials(self):
        self.logger.debug("sr_sftp credentials %s" % self.destination)

        try:
                ok, details = self.parent.credentials.get(self.destination)
                if details  : url = details.url

                self.host        = url.hostname
                self.port        = url.port
                self.user        = url.username
                self.password    = url.password
                self.ssh_keyfile = details.ssh_keyfile

                if url.username == '' : self.user     = None
                if url.password == '' : self.password = None
                if url.port     == '' : self.port     = None
                if self.ssh_keyfile   : self.password = None

                if self.port == None  : self.port     = 22

                self.logger.debug("h u:p s = %s:%d %s:%s %s"%(self.host,self.port,self.user,self.password,self.ssh_keyfile))

                if self.ssh_config  == None : return True

                if self.user        == None or \
                 ( self.ssh_keyfile == None and self.password == None):
                   self.logger.debug("check in ssh_config")
                   for key,value in self.ssh_config.lookup(self.host).items() :
                       if   key == "hostname":
                            self.host = value
                       elif key == "user":
                            self.user = value
                       elif key == "port":
                            self.port = int(value)
                       elif key == "identityfile":
                            self.ssh_keyfile = os.path.expanduser(value[0])

                self.logger.debug("h u:p s = %s:%d %s:%s %s"%(self.host,self.port,self.user,self.password,self.ssh_keyfile))
                return True

        except:
                self.logger.error("sr_sftp/credentials: unable to get credentials for %s" % self.destination)
                self.logger.debug('Exception details: ', exc_info=True)

        return False

    # delete
    # MG sneak rmdir here in case 'R' message implies a directory (remote mirroring)
    def delete(self, path):
        self.logger.debug("sr_sftp rm %s" % path)

        alarm_set(self.iotime)
        # check if the file is there... if not we are done,no error
        try   :
                s = self.sftp.lstat(path)
        except: 
                alarm_cancel()
                return

        # proceed with file/link removal
        if not S_ISDIR(s.st_mode) :
           self.logger.debug("sr_sftp remove %s" % path)
           self.sftp.remove(path)

        # proceed with directory removal
        else:
           self.logger.debug("sr_sftp rmdir %s" % path)
           self.sftp.rmdir(path)

        alarm_cancel()

    # symlink
    def symlink(self, link, path):
        self.logger.debug("sr_sftp symlink %s %s" % (link, path) )
        alarm_set(self.iotime)
        self.sftp.symlink(link, path)
        alarm_cancel()

    # get 
    def get(self, remote_file, local_file, remote_offset=0, local_offset=0, length=0 ) :
        self.logger.debug("sr_sftp get %s %s %d %d %d" % (remote_file,local_file,remote_offset,local_offset,length))

        # read : remote file open, seek if needed

        alarm_set(2*self.iotime)
        rfp = self.sftp.file(remote_file,'rb',self.bufsize)
        if remote_offset != 0 : rfp.seek(remote_offset,0)
        rfp.settimeout(1.0*self.iotime)
        alarm_cancel()

        # read from rfp and write to local_file

        rw_length = self.read_writelocal(remote_file, rfp, local_file, local_offset, length)

        # close

        alarm_set(self.iotime)
        rfp.close()
        alarm_cancel()

    # getcwd
    def getcwd(self):
        alarm_set(self.iotime)
        cwd =  self.sftp.getcwd()
        alarm_cancel()
        return cwd

    # init
    def init(self):
        self.logger.debug("sr_sftp init")
        sr_proto.init(self)
        self.connected   = False 
        self.sftp        = None
        self.ssh         = None
        self.seek        = True

        self.batch       = 0

    # init_file_index
    def init_file_index(self):
        self.logger.debug("sr_sftp init_file_index")
        dir_fils = self.sftp.listdir()
        self.logger.debug("sr_sftp listdir(): %s" % dir_fils)
        if dir_fils:
            dir_attr = self.sftp.listdir_attr()
            alarm_cancel()
            for index in range(len(dir_fils)):
                attr = dir_attr[index]
                line = attr.__str__()
                fil = dir_fils[index]
                self.ls_file_index(fil,line)
        else:
            alarm_cancel()
        if hasattr(self,'file_index'): self.write_file_index()

    # load_file_index
    def load_file_index(self):
        self.logger.debug("sr_sftp load_file_index")
        alarm_cancel()
        try:
            with open(self.file_index_cache,'r') as fp:
                index = int(fp.read())
                self.file_index = index
        except:
            self.logger.error("load_file_index: Unable to determine file index from %s" % self.file_index_cache)

    # ls
    def ls(self):
        self.logger.debug("sr_sftp ls")
        self.entries  = {}
        # iotime is at least 30 secs, say we wait for max 5 mins
        alarm_set( 10 * self.iotime )
        dir_attr = self.sftp.listdir_attr()
        alarm_cancel()
        for index in range(len(dir_attr)):
            attr = dir_attr[index]
            line = attr.__str__()
            self.line_callback(line)
        #self.logger.debug("sr_sftp ls = %s" % self.entries )
        return self.entries

    # line_callback: ls[filename] = 'stripped_file_description'
    def line_callback(self,iline):
        #self.logger.debug("sr_sftp line_callback %s" % iline)

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

    # ls_file_index
    def ls_file_index(self,ifil,iline):
        oline = iline
        oline = oline.strip('\n')
        oline  = oline.strip()
        oline  = oline.replace('\t',' ')
        opart1 = oline.split(' ')
        opart2 = []

        for p in opart1 :
            if p == ''  : continue
            opart2.append(p)

        try:
            file_index = opart2.index(ifil)
            self.file_index = file_index
        except:
            pass

    # mkdir
    def mkdir(self, remote_dir):
        self.logger.debug("sr_sftp mkdir %s" % remote_dir)
        alarm_set(self.iotime)
        self.sftp.mkdir(remote_dir,self.parent.chmod_dir)
        alarm_cancel()

    # put
    def put(self, local_file, remote_file, local_offset=0, remote_offset=0, length=0 ):
        self.logger.debug("sr_sftp put %s %s %d %d %d" % (local_file,remote_file,local_offset,remote_offset,length))

        # simple file

        alarm_set(2*self.iotime)

        if length == 0 :
           rfp = self.sftp.file(remote_file,'wb',self.bufsize)
           rfp.settimeout(1.0*self.iotime)

        # parts
        else:
           try   : self.sftp.stat(remote_file)
           except: 
                   rfp = self.sftp.file(remote_file,'wb',self.bufsize)
                   rfp.close()

           rfp = self.sftp.file(remote_file,'r+b',self.bufsize)
           rfp.settimeout(1.0*self.iotime)
           if remote_offset != 0 : rfp.seek(remote_offset,0)

        alarm_cancel()

        # read from local_file and write to rfp

        rw_length = self.readlocal_write( local_file, local_offset, length, rfp )

        # no sparse file... truncate where we are at

        alarm_set(self.iotime)
        self.fpos = remote_offset + rw_length
        if length != 0 : rfp.truncate(self.fpos)

        # close

        rfp.close()
        alarm_cancel()

    # rename
    def rename(self,remote_old,remote_new) :
        self.logger.debug("sr_sftp rename %s %s" % (remote_old,remote_new))
        try    : self.delete(remote_new)
        except : pass
        alarm_set(self.iotime)
        self.sftp.rename(remote_old,remote_new)
        alarm_cancel()

    # rmdir
    def rmdir(self,path) :
        self.logger.debug("sr_sftp rmdir %s " % path)
        alarm_set(self.iotime)
        self.sftp.rmdir(path)
        alarm_cancel()

    # utime
    def utime(self,path,tup) :
        self.logger.debug("sr_sftp utime %s %s " % (path,tup))
        alarm_set(self.iotime)
        self.sftp.utime(path,tup)
        alarm_cancel()

    # write_file_index
    def write_file_index(self):
        self.logger.debug("sr_sftp write_file_index")
        try:
            with open(self.file_index_cache,'w') as fp:
                fp.write(str(self.file_index))
        except:
            self.logger.warning("Unable to write file_index to cache file %s" % self.file_index_cache)

#============================================================
#
# wrapping of downloads/sends using sr_sftp in sftp_transport
#
#============================================================

class sftp_transport(sr_transport):
    def __init__(self) :
        sr_transport.__init__(self)
        self.pclass = sr_sftp
        self.scheme = 'sftp'
