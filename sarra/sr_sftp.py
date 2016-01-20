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
#  Last Changed   : Dec 29 07:52:45 EST 2015
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

class sr_sftp():
    def __init__(self, parent) :
        self.logger = parent.logger
        self.logger.debug("sr_sftp __init__")

        self.parent      = parent 
        self.connected   = False 
        self.sftp        = None

    # cd
    def cd(self, path):
        self.logger.debug("sr_sftp cd %s" % path)
        self.sftp.chdir(self.originalDir)
        self.sftp.chdir(path)
        self.pwd = path

    # cd forced
    def cd_forced(self,perm,path) :
        self.logger.debug("sr_sftp cd_forced %d %s" % (perm,path))

        # try to go directly to path

        self.sftp.chdir(self.originalDir)
        try   :
                self.sftp.chdir(path)
                return
        except: pass

        # need to create subdir

        subdirs = path.split("/")
        if path[0:1] == "/" : subdirs[0] = "/" + subdirs[0]

        for d in subdirs :
            if d == ''   : continue
            # try to go directly to subdir
            try   :
                    self.sftp.chdir(d)
                    continue
            except: pass

            # create and go to subdir
            self.sftp.mkdir(d,eval('0o'+ str(perm)))
            self.sftp.chdir(d)

    # chmod
    def chmod(self,perm,path):
        self.logger.debug("sr_sftp chmod %s %s" % (str(perm),path))
        self.sftp.chmod(path,eval('0o'+str(perm)))

    # close
    def close(self):
        self.logger.debug("sr_sftp close")
        self.connected = False
        try   : self.sftp.close()
        except: pass
        self.sftp = None
        try   : self.ssh.close()
        except: pass
        self.ssh  = None

    # connect...
    def connect(self):
        self.logger.debug("sr_sftp connect %s" % self.parent.destination)

        self.connected   = False
        self.destination = self.parent.destination

        try:
                ok, details = self.parent.credentials.get(self.destination)
                if details  : url = details.url

                host        = url.hostname
                port        = url.port
                user        = url.username
                password    = url.password

                self.ssh_keyfile = details.ssh_keyfile
                if self.ssh_keyfile : password = None

                self.kbytes_ps = 0
                self.bufsize   = 8192

                if hasattr(self.parent,'kbytes_ps') : self.kbytes_ps = self.parent.kbytes_ps
                if hasattr(self.parent,'bufsize')   : self.bufsize   = self.parent.bufsize

        except:
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Unable to get credentials for %s" % self.destination)
                self.logger.error("(Type: %s, Value: %s)" % (stype ,svalue))

        try:
                if port == '' or port == None : port = 22

                paramiko.util.logging.getLogger().setLevel(logging.WARN)

                self.ssh = paramiko.SSHClient()
                # FIXME this should be an option... for security reasons... not forced
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh.connect(host,port,user,password,pkey=None,key_filename=self.ssh_keyfile,timeout=None)

                #if ssh_keyfile != None :
                #  key=DSSKey.from_private_key_file(ssh_keyfile,password=None)

                sftp = self.ssh.open_sftp()

                sftp.chdir('.')
                self.originalDir = sftp.getcwd()
                self.pwd         = self.originalDir

                self.connected = True

                self.sftp = sftp

                return True

        except:
            (stype, svalue, tb) = sys.exc_info()
            self.logger.error("Unable to connect to %s (user:%s). Type: %s, Value: %s" % (host,user, stype,svalue))
        return False

    # delete
    def delete(self, path):
        self.logger.debug("sr_sftp rm %s" % path)
        self.sftp.remove(path)

    # get  fixme : implement trottle...
    def get(self, remote_file, local_file, remote_offset=0, local_offset=0, length=0):
        self.logger.debug("sr_sftp get %s %s %d %d %d" % (remote_file,local_file,remote_offset,local_offset,length))

        if length == 0 :
           self.sftp.get(remote_file,local_file)
           return

        if not os.path.isfile(local_file) :
           fp = open(local_file,'w')
           fp.close()

        fp = open(local_file,'r+b')
        if local_offset != 0 : fp.seek(local_offset,0)

        rfp = self.sftp.file(remote_file,'rb',self.bufsize)
        if remote_offset != 0 : rfp.seek(remote_offset,0)

        nc = int(length/self.bufsize)
        r  = length%self.bufsize

        # read/write bufsize "nc" times
        i  = 0
        while i < nc :
              chunk = rfp.read(self.bufsize)
              fp.write(chunk)
              i = i + 1

        # remaining
        if r > 0 :
           chunk = rfp.read(r)
           fp.write(chunk)

        rfp.close()
        fp.close()

    # ls
    def ls(self):
        self.logger.debug("sr_sftp ls")
        self.entries  = {}
        dir_attr = self.sftp.listdir_attr()
        for index in range(len(dir_attr)):
            attr = dir_attr[index]
            line = attr.__str__()
            self.line_callback(line)
        self.logger.debug("sr_sftp ls = %s" % self.entries )
        return self.entries

    # line_callback: ls[filename] = 'stripped_file_description'
    def line_callback(self,iline):
        self.logger.debug("sr_sftp line_callback %s" % iline)

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
        self.sftp.mkdir(remote_dir,0o775)

    # put
    def put(self, local_file, remote_file, local_offset=0, remote_offset=0, length=0):
        self.logger.debug("sr_sftp put %s %s %d %d %d" % (local_file,remote_file,local_offset,remote_offset,length))

        if length == 0 :
           self.sftp.put(local_file,remote_file)
           return

        cb        = None

        if self.kbytes_ps > 0.0 :
           cb = self.trottle
           d1,d2,d3,d4,now = os.times()
           self.tbytes     = 0.0
           self.tbegin     = now + 0.0
           self.bytes_ps   = self.kbytes_ps * 1024.0

        if not os.path.isfile(local_file) :
           fp = open(local_file,'w')
           fp.close()

        fp = open(local_file,'r+b')
        if local_offset != 0 : fp.seek(local_offset,0)

        rfp = self.sftp.file(remote_file,'wb',self.bufsize)
        if remote_offset != 0 : rfp.seek(remote_offset,0)

        nc = int(length/self.bufsize)
        r  = length%self.bufsize

        # read/write bufsize "nc" times
        i  = 0
        while i < nc :
              chunk = fp.read(self.bufsize)
              rfp.write(chunk)
              if cb : cb(chunk)
              i = i + 1

        # remaining
        if r > 0 :
           chunk = fp.read(r)
           rfp.write(chunk)
           if cb : cb(chunk)

        fp.close()
        rfp.close()

    # rename
    def rename(self,remote_old,remote_new) :
        self.logger.debug("sr_sftp rename %s %s" % (remote_old,remote_new))
        self.sftp.rename(remote_old,remote_new)

    # rmdir
    def rmdir(self,path) :
        self.logger.debug("sr_sftp rmdir %s " % path)
        self.sftp.rmdir(path)

    # trottle
    def trottle(self,buf) :
        self.logger.debug("sr_sftp trottle")
        self.tbytes = self.tbytes + len(buf)
        span = self.tbytes / self.bytes_ps
        d1,d2,d3,d4,now = os.times()
        rspan = now - self.tbegin
        if span > rspan :
           time.sleep(span-rspan)


#============================================================
#
# wrapping of sr_sftp in sftp_download
#
#============================================================

def sftp_download( parent ):
    logger = parent.logger
    msg    = parent.msg

    url         = msg.url
    urlstr      = msg.urlstr
    token       = msg.url.path[1:].split('/')
    cdir        = '/'.join(token[:-1])
    remote_file = token[-1]

    try :
            parent.destination = msg.urlcred
            sftp = sr_sftp(parent)
            sftp.connect()

            sftp.cd_forced(775,cdir)

            remote_offset = 0
            if  msg.partflg == 'i': remote_offset = msg.offset

            str_range = ''
            if msg.partflg == 'i' :
               str_range = 'bytes=%d-%d'%(remote_offset,remote_offset+msg.length-1)

            #download file

            msg.logger.info('Downloads: %s %s into %s %d-%d' % 
                (urlstr,str_range,msg.local_file,msg.local_offset,msg.local_offset+msg.length-1))

            sftp.get(remote_file,msg.local_file,remote_offset,msg.local_offset,msg.length)

            msg.log_publish(201,'Downloaded')

            sftp.close()

            return True
            
    except:
            try    : sftp.close()
            except : pass

            (stype, svalue, tb) = sys.exc_info()
            msg.logger.error("Download failed %s. Type: %s, Value: %s" % (urlstr, stype ,svalue))
            msg.log_publish(499,'sftp download problem')

            return False

    msg.log_publish(499,'sftp download problem')

    return False

#============================================================
#
# wrapping of sr_sftp in sftp_send
#
#============================================================

def sftp_send( parent ):
    logger = parent.logger
    msg    = parent.msg

    local_file = parent.local_path
    remote_dir = parent.remote_dir

    try :
            sftp = sr_sftp(parent)
            sftp.connect()
            sftp.cd_forced(775,remote_dir)

            offset = 0

            if  msg.partflg == 'i': offset = msg.offset

            str_range = ''
            if msg.partflg == 'i' :
               str_range = 'bytes=%d-%d'%(offset,offset+msg.length-1)

            #download file

            msg.logger.info('Sends: %s %s into %s %d-%d' % 
                (parent.local_file,str_range,parent.remote_path,offset,offset+msg.length-1))

            if parent.lock == None or msg.partflg == 'i' :
               sftp.put(local_file, parent.remote_file, offset, offset, msg.length)
            elif parent.lock == '.' :
               remote_lock = '.'  + parent.remote_file
               sftp.put(local_file, remote_lock)
               sftp.rename(remote_lock, parent.remote_file)
            elif parent.lock[0] == '.' :
               remote_lock = parent.remote_file + parent.lock
               sftp.put(local_file, remote_lock)
               sftp.rename(remote_lock, parent.remote_file)

            try   : sftp.chmod(parent.chmod,parent.remote_file)
            except: pass

            msg.log_publish(201,'Delivered')

            sftp.close()

            return True
            
    except:
            try    : sftp.close()
            except : pass

            (stype, svalue, tb) = sys.exc_info()
            msg.logger.error("Delivery failed %s. Type: %s, Value: %s" % (parent.remote_urlstr, stype ,svalue))
            msg.log_publish(499,'sftp delivery problem')

            return False

    msg.log_publish(499,'sftp delivery problem')

    return False
                 
# ===================================
# self_test
# ===================================

try    : from sr_config         import *
except : from sarra.sr_config   import *

class test_logger:
      def silence(self,str):
          pass
      def __init__(self):
          self.debug   = self.silence
          self.error   = print
          self.info    = self.silence
          self.warning = print

def self_test():

    logger = test_logger()

    # config setup
    cfg = sr_config()
    cfg.defaults()
    cfg.general()
    cfg.debug  = True
    opt1 = "destination sftp://localhost"
    cfg.option( opt1.split()  )
    cfg.logger = logger

    try:
           sftp = sr_sftp(cfg)
           sftp.connect()
           sftp.mkdir("tztz")
           sftp.chmod(775,"tztz")
           sftp.cd("tztz")
       
           f = open("aaa","wb")
           f.write(b"1\n")
           f.write(b"2\n")
           f.write(b"3\n")
           f.close()
       
           sftp.put("aaa", "bbb")
           ls = sftp.ls()
           logger.info("ls = %s" % ls )
       
           sftp.chmod(775,"bbb")
           ls = sftp.ls()
           logger.info("ls = %s" % ls )
       
           sftp.rename("bbb", "ccc")
           ls = sftp.ls()
           logger.info("ls = %s" % ls )
       
           sftp.get("ccc", "bbb")
           f = open("bbb","rb")
           data = f.read()
           f.close()
       
           if data != b"1\n2\n3\n" :
              logger.error("sr_sftp1 TEST FAILED")
              sys.exit(1)
       
           sftp.delete("ccc")
           logger.info("%s" % sftp.originalDir)
           sftp.cd("")
           logger.info("%s" % sftp.sftp.getcwd())
           sftp.rmdir("tztz")

           sftp.put("aaa","bbb",0,0,2)
           sftp.put("aaa","bbb",2,4,2)
           sftp.put("aaa","bbb",4,2,2)
           sftp.get("bbb","bbb",2,2,2)
           sftp.delete("bbb")
           f = open("bbb","rb")
           data = f.read()
           f.close()
       
           if data != b"1\n3\n3\n" :
              logger.error("sr_sftp TEST FAILED ")
              sys.exit(1)
       
           sftp.close()
    except:
           (stype, svalue, tb) = sys.exc_info()
           logger.error("(Type: %s, Value: %s)" % (stype ,svalue))
           logger.error("sr_sftp TEST FAILED")
           sys.exit(2)

    os.unlink('aaa')
    os.unlink('bbb')

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
