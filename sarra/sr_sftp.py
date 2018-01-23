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

import paramiko, os,sys,time
from   paramiko import *

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
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Unable to load ssh config %s" % ssh_config)
                self.logger.error("sr_sftp/__init__ (Type: %s, Value: %s)" % (stype ,svalue))

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

        alarm_set(3*self.iotime)
        try:

                logger = logging.getLogger('paramiko')
                logger.setLevel(logging.CRITICAL)
                self.ssh = paramiko.SSHClient()
                # FIXME this should be an option... for security reasons... not forced
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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

                alarm_cancel()
                return True

        except:
            (stype, svalue, tb) = sys.exc_info()
            self.logger.error("Unable to connect to %s (user:%s). Type: %s, Value: %s" % (self.host,self.user, stype,svalue))

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
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Unable to get credentials for %s" % self.destination)
                self.logger.error("sr_sftp/credentials (Type: %s, Value: %s)" % (stype ,svalue))

        return False

    # delete
    def delete(self, path):
        self.logger.debug("sr_sftp rm %s" % path)
        alarm_set(self.iotime)
        # check if the file is there... if not we are done,no error
        try   :
                s = self.sftp.stat(path)
        except: 
                alarm_cancel()
                return
        # proceed with file removal
        self.sftp.remove(path)
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

        fil  = opart2[-1]
        line = ' '.join(opart2)

        self.entries[fil] = line

    # mkdir
    def mkdir(self, remote_dir):
        self.logger.debug("sr_sftp mkdir %s" % remote_dir)
        alarm_set(self.iotime)
        self.sftp.mkdir(remote_dir,self.parent.chmod_dir)
        alarm_cancel()

    # put
    def put(self, local_file, remote_file, local_offset=0, remote_offset=0, length=0 ):
        self.logger.debug("sr_sftp put %s %s %d %d %d" % (local_file,remote_file,local_offset,remote_offset,length))

        # this cannot be used : no throttling, no timeout on buffer ... etc
        #if length == 0 :
        #   self.sftp.put(local_file,remote_file)
        #   return

        # write : remote file open, seek if needed

        alarm_set(self.iotime)
        try   : self.sftp.stat(remote_file)
        except: 
                rfp = self.sftp.file(remote_file,'wb',self.bufsize)
                rfp.settimeout(1.0*self.iotime)
                rfp.close()
        alarm_cancel()

        alarm_set(2*self.iotime)
        rfp = self.sftp.file(remote_file,'r+b',self.bufsize)
        rfp.settimeout(1.0*self.iotime)
        if remote_offset != 0 : rfp.seek(remote_offset,0)
        alarm_cancel()

        # read from local_file and write to rfp

        rw_length = self.readlocal_write( local_file, local_offset, length, rfp )

        # no sparse file... truncate where we are at

        alarm_set(self.iotime)
        self.fpos = remote_offset + rw_length
        rfp.truncate(self.fpos)

        # close

        rfp.close()
        alarm_cancel()

    # rename
    def rename(self,remote_old,remote_new) :
        self.logger.debug("sr_sftp rename %s %s" % (remote_old,remote_new))
        alarm_set(self.iotime)
        try    : self.sftp.remove(remote_new)
        except : pass
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

#============================================================
#
# wrapping of downloads/sends using sr_sftp in sftp_transport
#
#============================================================

class sftp_transport(sr_transport):
    def __init__(self) :
        self.sftp     = None
        self.cdir     = None

    def close(self) :
        self.logger.debug("sftp_transport close")

        try    : self.sftp.close()
        except : pass

        self.cdir = None
        self.sftp = None

    def download( self, parent ):
        self.logger = parent.logger
        self.parent = parent
        self.logger.debug("sftp_transport download")

        msg         = parent.msg
        token       = msg.relpath.split('/')
        cdir        = '/'.join(token[:-1])
        remote_file = token[-1]
        urlstr      = msg.baseurl + '/' + msg.relpath
        new_lock    = ''

        try:    curdir = os.getcwd()
        except: curdir = None

        if curdir != parent.new_dir:
            os.chdir(parent.new_dir)

        try :
                parent.destination = msg.baseurl

                sftp = self.sftp
                if sftp == None or not sftp.check_is_connected() :
                   self.logger.debug("sftp_transport download connects")
                   sftp = sr_sftp(parent)
                   ok = sftp.connect()
                   if not ok : return False
                   self.sftp = sftp
                   self.cdir = None

                # for generalization purpose
                if not hasattr(sftp,'seek') and msg.partflg == 'i':
                   self.logger.error("sftp, inplace part file not supported")
                   msg.report_publish(499,'sftp does not support partitioned file transfers')
                   return False
                
                if self.cdir != cdir :
                   self.logger.debug("sftp_transport download cd to %s" %cdir)
                   sftp.cd(cdir)
                   self.cdir  = cdir
    
                remote_offset = 0
                if  msg.partflg == 'i': remote_offset = msg.offset
    
                str_range = ''
                if msg.partflg == 'i' :
                   str_range = 'bytes=%d-%d'%(remote_offset,remote_offset+msg.length-1)
    
                #download file
    
                msg.logger.debug('Beginning fetch of %s %s into %s %d-%d' % 
                    (urlstr,str_range,parent.new_file,msg.local_offset,msg.local_offset+msg.length-1))
    
                # FIXME  locking for i parts in temporary file ... should stay lock
                # and file_reassemble... take into account the locking

                sftp.set_sumalgo(msg.sumalgo)

                if parent.inflight == None or msg.partflg == 'i' :
                   sftp.get(remote_file,parent.new_file,remote_offset,msg.local_offset,msg.length)

                elif parent.inflight == '.' :
                   new_lock = '.' + parent.new_file
                   sftp.get(remote_file,new_lock,remote_offset,msg.local_offset,msg.length)
                   if os.path.isfile(parent.new_file) : os.remove(parent.new_file)
                   os.rename(new_lock, parent.new_file)
                      
                elif parent.inflight[0] == '.' :
                   new_lock  = parent.new_file + parent.inflight
                   sftp.get(remote_file,new_lock,remote_offset,msg.local_offset,msg.length)
                   if os.path.isfile(parent.new_file) : os.remove(parent.new_file)
                   os.rename(new_lock, parent.new_file)

                # fix permission 

                self.set_local_file_attributes(parent.new_file,msg)

                # fix message if no partflg (means file size unknown until now)

                if msg.partflg == None:
                   msg.set_parts(partflg='1',chunksize=sftp.fpos)
    
                msg.report_publish(201,'Downloaded')

                msg.onfly_checksum = sftp.checksum
    
                if parent.delete and hasattr(sftp,'delete') :
                   try   :
                           sftp.delete(remote_file)
                           msg.logger.debug ('file  deleted on remote site %s' % remote_file)
                   except: msg.logger.error('unable to delete remote file %s' % remote_file)
    
                return True
                
        except:
                #closing on problem
                try    : self.close()
                except : pass
    
                (stype, svalue, tb) = sys.exc_info()
                msg.logger.error("Download failed %s. Type: %s, Value: %s" % (urlstr, stype ,svalue))
                msg.report_publish(499,'sftp download failed')
                if os.path.isfile(new_lock) : os.remove(new_lock)
 
                return False

        #closing on problem
        try    : self.close()
        except : pass
    
        msg.report_publish(498,'sftp download failed')
    
        return False

    def send( self, parent ):
        self.logger = parent.logger
        self.parent = parent
        self.logger.debug("sftp_transport send")

        msg    = parent.msg
    
        local_file = parent.local_path
        new_dir = parent.new_dir
    
        try :

                sftp = self.sftp
                if sftp == None or not sftp.check_is_connected() :
                   self.logger.debug("sftp_transport send connects")
                   sftp = sr_sftp(parent)
                   ok   = sftp.connect()
                   if not ok : return False
                   self.sftp = sftp
                   self.cdir = None
                
                if self.cdir != new_dir :
                   self.logger.debug("sftp_transport send cd to %s" % new_dir)
                   sftp.cd_forced(775,new_dir)
                   self.cdir  = new_dir

                #=================================
                # delete event
                #=================================

                if msg.sumflg == 'R' :
                   msg.logger.debug("message is to remove %s" % parent.new_file)
                   sftp.delete(parent.new_file)
                   msg.report_publish(205,'Reset Content : deleted')
                   return True

                #=================================
                # link event
                #=================================

                if msg.sumflg == 'L' :
                   msg.logger.debug("message is to link %s to: %s" % ( parent.new_file, msg.headers['link'] ))
                   sftp.symlink(msg.headers['link'],parent.new_file)
                   msg.report_publish(205,'Reset Content : linked')
                   return True

                #=================================
                # send event
                #=================================

                offset = 0
                if  msg.partflg == 'i': offset = msg.offset
    
                str_range = ''
                if msg.partflg == 'i' :
                   str_range = 'bytes=%d-%d'%(offset,offset+msg.length-1)
    
                #upload file
    
                if parent.inflight == None or msg.partflg == 'i' :
                   sftp.put(local_file, parent.new_file, offset, offset, msg.length)
                elif parent.inflight == '.' :
                   new_lock = '.'  + parent.new_file
                   sftp.put(local_file, new_lock )
                   sftp.rename(new_lock, parent.new_file)
                elif parent.inflight[0] == '.' :
                   new_lock = parent.new_file + parent.inflight
                   sftp.put(local_file, new_lock )
                   sftp.rename(new_lock, parent.new_file)

                # fix permission 

                self.set_remote_file_attributes(sftp,parent.new_file,msg)
    
                msg.logger.info('Sent: %s %s into %s/%s %d-%d' % 
                    (parent.local_file,str_range,parent.new_dir,parent.new_file,offset,offset+msg.length-1))

                if parent.reportback :
                   msg.report_publish(201,'Delivered')
    
                #closing after batch or when destination is changing
                #sftp.close()
    
                return True
                
        except:
                #closing on problem
                try    : self.close()
                except : pass
    
                (stype, svalue, tb) = sys.exc_info()
                msg.logger.error("Delivery failed %s. Type: %s, Value: %s" % (parent.new_baseurl+'/'+parent.new_relpath, stype ,svalue))
                msg.report_publish(497,'sftp delivery failed')
    
                return False
    
        #closing on problem
        try    : self.close()
        except : pass

        msg.report_publish(496,'sftp delivery failed')
    
        return False

# ===================================
# self_test
# ===================================

try    :
         from sr_config         import *
         from sr_message        import *
         from sr_util           import *
except :
         from sarra.sr_config   import *
         from sarra.sr_message  import *
         from sarra.sr_util     import *

class test_logger:
      def silence(self,str):
          pass
      def __init__(self):
          self.debug   = print
          self.error   = print
          self.info    = print
          self.warning = print
          self.debug   = self.silence
          self.info    = self.silence

def self_test():

    logger = test_logger()


    # config setup
    cfg = sr_config()

    cfg.defaults()
    cfg.general()
    cfg.set_sumalgo('d')
    msg = sr_message(cfg)
    msg.filesize = None
    msg.onfly_checksum = False
    cfg.msg = msg
    #cfg.debug  = True
    if not cfg.debug : paramiko.util.logging.getLogger().setLevel(logging.WARN)
    opt1 = "destination sftp://localhost"
    cfg.option( opt1.split()  )
    cfg.logger = logger
    cfg.timeout = 5.0
    # 1 bytes par 5 secs
    #cfg.kbytes_ps = 0.0001
    cfg.kbytes_ps = 0.01
    cfg.chmod_dir = 0o775

    try:
           sftp = sr_sftp(cfg)
           sftp.connect()
           sftp.mkdir("tztz")
           sftp.chmod(0o775,"tztz")
           sftp.cd("tztz")
       
           f = open("aaa","wb")
           f.write(b"1\n")
           f.write(b"2\n")
           f.write(b"3\n")
           f.close()
       
           if hasattr(sftp,'put') :
              sftp.put("aaa", "bbb")
              ls = sftp.ls()
              logger.info("ls = %s" % ls )
       
              sftp.chmod(0o775,"bbb")
              ls = sftp.ls()
              logger.info("ls = %s" % ls )
       
              sftp.rename("bbb", "ccc")
              ls = sftp.ls()
              logger.info("ls = %s" % ls )
       
           if hasattr(sftp,'seek') :
              sftp.get("ccc", "bbb",0,0,6)
              f = open("bbb","rb")
              data = f.read()
              f.close()
       
              if data != b"1\n2\n3\n" :
                 logger.error("sr_sftp1 TEST FAILED")
                 sys.exit(1)

              os.unlink("bbb")

           msg.start_timer()
           msg.topic   = "v02.post.test"
           msg.notice  = "notice"
           msg.baseurl = "sftp://localhost"
           msg.relpath = "tztz/ccc"
           msg.partflg = '1'
           msg.offset  = 0
           msg.length  = 0

           msg.local_file   = "bbb"
           msg.local_offset = 0
           msg.sumalgo      = None

           cfg.new_file     = "bbb"
           cfg.new_dir      = "."

           cfg.msg     = msg
           cfg.batch   = 5
           cfg.inflight    = None
       
           if hasattr(sftp,'get') :
              dldr = sftp_transport()
              dldr.download(cfg)
              logger.debug("checksum = %s" % msg.onfly_checksum)
              dldr.download(cfg)
              dldr.download(cfg)
              cfg.logger.info("lock .")
              cfg.inflight    = '.'
              dldr.download(cfg)
              dldr.download(cfg)
              msg.sumalgo = cfg.sumalgo
              dldr.download(cfg)
              logger.debug("checksum = %s" % msg.onfly_checksum)
              cfg.logger.info("lock .tmp")
              cfg.inflight    = '.tmp'
              dldr.download(cfg)
              dldr.download(cfg)
              dldr.close()
              dldr.close()
              dldr.close()
    
           if hasattr(sftp,'put') :
              dldr = sftp_transport()
              cfg.local_file    = "bbb"
              cfg.local_path    = "./bbb"
              cfg.new_dir       = "tztz"
              cfg.new_file      = "ddd"
              cfg.remote_file   = "ddd"
              cfg.remote_path   = "tztz/ddd"
              cfg.remote_urlstr = "sftp://localhost/tztz/ddd"
              cfg.remote_dir    = "tztz"
              cfg.chmod         = 0o775
              cfg.inflight      = None
              dldr.send(cfg)
              if hasattr(sftp,'delete') : dldr.sftp.delete("ddd")
              if hasattr(sftp,'delete') : dldr.sftp.delete("zzz_unexistant")
              cfg.inflight        = '.'
              dldr.send(cfg)
              if hasattr(sftp,'delete') : dldr.sftp.delete("ddd")
              cfg.inflight        = '.tmp'
              dldr.send(cfg)
              dldr.send(cfg)
              dldr.send(cfg)
              dldr.send(cfg)
              dldr.send(cfg)
              dldr.send(cfg)
              dldr.close()
              dldr.close()
              dldr.close()

              sftp = sr_sftp(cfg)
              sftp.connect()
              sftp.cd("tztz")
              sftp.ls()
              sftp.delete("ccc")
              sftp.delete("ddd")
              logger.info("%s" % sftp.originalDir)
              sftp.cd("")
              logger.info("%s" % sftp.getcwd())
              sftp.rmdir("tztz")
              sftp.close()

           if hasattr(sftp,'seek') :
              
              pwd = os.getcwd()

              sftp = sr_sftp(cfg)
              sftp.connect()
              sftp.cd(pwd)

              sftp.set_sumalgo(cfg.sumalgo)
              sftp.put("aaa","bbb",0,0,2)
              sftp.get("aaa","bbb",2,2,2)
              sftp.put("aaa","bbb",4,4,2)

              f = open("bbb","rb")
              data = f.read()
              f.close()

              if data != b"1\n2\n3\n" :
                 logger.error("ICI")
                 logger.error("sr_file TEST FAILED ")
                 sys.exit(1)

              sftp.delete("bbb")
              sftp.delete("aaa")

              sftp.close()


    except:
           (stype, svalue, tb) = sys.exc_info()
           logger.error("(sr_sftp/self_test Type: %s, Value: %s)" % (stype ,svalue))
           logger.error("sr_sftp TEST FAILED")
           sys.exit(2)

    print("sr_sftp TEST PASSED")
    sys.exit(0)

# ===================================
# MAIN
# ===================================

def main():

    self_test()
    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()
