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
# sr_ftp.py : python3 utility tools for ftp usage in sarracenia
#             Since python3.2 supports ftps (RFC 4217)
#             I tested it and works for all our ftps pull/sender as of today
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Dec 30 11:34:07 EST 2015
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

import ftplib,os,sys,time

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

class sr_ftp():
    def __init__(self, parent) :
        self.logger = parent.logger
        self.logger.debug("sr_ftp __init__")

        self.parent      = parent 
        self.connected   = False 
        self.ftp         = None
        self.details     = None

        self.sumalgo     = None
        self.checksum    = None
 
    # cd
    def cd(self, path):
        self.logger.debug("sr_ftp cd %s" % path)
        self.ftp.cwd(self.originalDir)
        self.ftp.cwd(path)
        self.pwd = path

    def cd_forced(self,perm,path) :
        self.logger.debug("sr_ftp cd_forced %d %s" % (perm,path))

        # try to go directly to path

        self.ftp.cwd(self.originalDir)
        try   :
                self.ftp.cwd(path)
                return
        except: pass

        # need to create subdir

        subdirs = path.split("/")
        if path[0:1] == "/" : subdirs[0] = "/" + subdirs[0]

        for d in subdirs :
            if d == ''   : continue
            # try to go directly to subdir
            try   :
                    self.ftp.cwd(d)
                    continue
            except: pass

            # create and go to subdir
            self.ftp.mkd(d)
            self.ftp.voidcmd('SITE CHMOD ' + "{0:o}".format(perm) + ' ' + d)
            self.ftp.cwd(d)

    # chmod
    def chmod(self,perm,path):
        self.logger.debug("sr_ftp chmod %s %s" % (str(perm),path))
        self.ftp.voidcmd('SITE CHMOD ' + "{0:o}".format(perm) + ' ' + path)

    # close
    def close(self):
        self.logger.debug("sr_ftp close")
        self.connected = False
        if self.ftp == None : return
        self.ftp.quit()

    # connect...
    def connect(self):
        self.logger.debug("sr_ftp connect %s" % self.parent.destination)

        self.connected   = False
        self.destination = self.parent.destination

        try:
                ok, details = self.parent.credentials.get(self.destination)
                if details  : url = details.url

                host        = url.hostname
                port        = url.port
                user        = url.username
                password    = url.password

                self.passive = details.passive
                self.binary  = details.binary
                self.tls     = details.tls
                self.prot_p  = details.prot_p

                self.bufsize   = 8192
                self.kbytes_ps = 0

                if hasattr(self.parent,'kbytes_ps') : self.kbytes_ps = self.parent.kbytes_ps
                if hasattr(self.parent,'bufsize')   : self.bufsize   = self.parent.bufsize

        except:
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Unable to get credentials for %s" % self.destination)
                self.logger.error("(Type: %s, Value: %s)" % (stype ,svalue))
                return False

        try:
                expire  = -999
                if self.parent.timeout : expire = self.parent.timeout
                if port == '' or port == None : port = 21

                if not self.tls :
                   ftp = ftplib.FTP()
                   ftp.connect(host,port,timeout=expire)
                   ftp.login(user, password)
                else :
                   # ftplib supports FTPS with TLS 
                   ftp = ftplib.FTP_TLS(host,user,password,timeout=expire)
                   if self.prot_p : ftp.prot_p()
                   # needed only if prot_p then set back to prot_c
                   #else          : ftp.prot_c()

                ftp.set_pasv(self.passive)

                self.originalDir = '.'

                try   : self.originalDir = ftp.pwd()
                except:
                        (stype, svalue, tb) = sys.exc_info()
                        self.logger.warning("Unable to ftp.pwd (Type: %s, Value: %s)" % (stype ,svalue))

                self.pwd = self.originalDir

                self.connected = True

                self.ftp = ftp

                return True

        except:
            (stype, svalue, tb) = sys.exc_info()
            self.logger.error("Unable to connect to %s (user:%s). Type: %s, Value: %s" % (host,user, stype,svalue))
        return False

    # delete
    def delete(self, path):
        self.logger.debug( "sr_ftp rm %s" % path)
        self.ftp.delete(path)

    # fwrite
    def fpwrite(self, chunk):
        self.fp.write(chunk)
        if self.chk : self.chk.update(chunk)
        if self.cb  : self.cb(chunk)

    # fwritel
    def fpwritel(self, chunk):
        self.fp.write(chunk)
        if self.chk : self.chk.update( bytes(chunk,'utf-8') )
        if self.cb  : self.cb(chunk)
 
    # get
    def get(self, remote_file, local_file, remote_offset=0, local_offset=0, length=0):
        self.logger.debug( "sr_ftp get %s %s %d" % (remote_file,local_file,local_offset))

        # on fly checksum 

        self.checksum = None
        self.chk      = self.sumalgo
        if self.chk   : self.chk.set_path(remote_file)

        # throttling 

        self.cb = None

        if self.kbytes_ps > 0.0 :
           self.cb = self.throttle
           d1,d2,d3,d4,now = os.times()
           self.tbytes     = 0.0
           self.tbegin     = now + 0.0
           self.bytes_ps   = self.kbytes_ps * 1024.0

        if not os.path.isfile(local_file) :
           fp = open(local_file,'w')
           fp.close()

        # fixme : get throttled.... instead of fp.write... call get_throttle(buf) which calls fp.write
        if self.binary :
           self.fp = open(local_file,'r+b')
           if local_offset != 0 : self.fp.seek(local_offset,0)
           self.ftp.retrbinary('RETR ' + remote_file, self.fpwrite, self.bufsize )
           self.fp.close()
        else :
           self.fp = open(local_file,'r+')
           if local_offset != 0 : self.fp.seek(local_offset,0)
           self.ftp.retrlines ('RETR ' + remote_file, self.fpwritel )
           self.fp.close()

        if self.chk : self.checksum = self.chk.get_value()

    # ls
    def ls(self):
        self.logger.debug("sr_ftp ls")
        self.entries = {}
        self.ftp.retrlines('LIST',self.line_callback )
        self.logger.debug("sr_ftp ls = %s" % self.entries )
        return self.entries

    # line_callback: entries[filename] = 'stripped_file_description'
    def line_callback(self,iline):
        self.logger.debug("sr_ftp line_callback %s" % iline)

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
        self.logger.debug("sr_ftp mkdir %s" % remote_dir)
        self.ftp.mkd(remote_dir)
        self.ftp.voidcmd('SITE CHMOD ' + "{0:o}".format(self.parent.chmod_dir) + ' ' + remote_dir)
#        self.ftp.chmod(self.parent.chmod_dir,remote_dir)

    # put
    def put(self, local_file, remote_file, local_offset = 0, remote_offset = 0, length = 0):
        self.logger.debug("sr_ftp put %s %s" % (local_file,remote_file))
        cb        = None

        if self.kbytes_ps > 0.0 :
           cb = self.throttle
           d1,d2,d3,d4,now = os.times()
           self.tbytes     = 0.0
           self.tbegin     = now + 0.0
           self.bytes_ps   = self.kbytes_ps * 1024.0

        if self.binary :
           fp = open(local_file, 'rb')
           if local_offset != 0 : fp.seek(local_offset,0)
           self.ftp.storbinary("STOR " + remote_file, fp, self.bufsize, cb)
           fp.close()
        else :
           fp=open(local_file,'rb')
           if local_offset != 0 : fp.seek(local_offset,0)
           self.ftp.storlines ("STOR " + remote_file, fp, cb)
           fp.close()

    # rename
    def rename(self,remote_old,remote_new) :
        self.logger.debug("sr_ftp rename %s %s" % (remote_old,remote_new))
        self.ftp.rename(remote_old,remote_new)

    # rmdir
    def rmdir(self, path):
        self.logger.debug("sr_ftp rmdir %s" % path)
        self.ftp.rmd(path)

    # set_sumalgo checksum algorithm
    def set_sumalgo(self,sumalgo) :
        self.logger.debug("sr_ftp set_sumalgo %s" % sumalgo)
        self.sumalgo = sumalgo

    # throttle
    def throttle(self,buf) :
        self.logger.debug("sr_ftp throttle")
        self.tbytes = self.tbytes + len(buf)
        span = self.tbytes / self.bytes_ps
        d1,d2,d3,d4,now = os.times()
        rspan = now - self.tbegin
        if span > rspan :
           time.sleep(span-rspan)

    # umask
    def umask(self) :
        self.logger.debug("sr_ftp umask")
        self.ftp.voidcmd('SITE UMASK 777')


#============================================================
#
# wrapping of downloads/sends using sr_ftp in ftp_transport
#
#============================================================

class ftp_transport():
    def __init__(self) :
        self.batch = 0
        self.ftp   = None
        self.cdir  = None

    def check_is_connected(self):
        self.logger.debug("ftp_transport check_connection")

        if self.ftp == None       : return False
        if not self.ftp.connected : return False

        if self.ftp.destination != self.parent.destination :
           self.close()
           return False

        self.batch = self.batch + 1
        if self.batch > self.parent.batch :
           self.close()
           return False

        ok, details = self.parent.credentials.get(self.parent.destination)

        if self.ftp.passive != details.passive or \
           self.ftp.binary  != details.binary  or \
           self.ftp.tls     != details.tls     or \
           self.ftp.prot_p  != details.prot_p :
           self.close()
           return False

        return True

    def close(self) :
        self.logger.debug("ftp_transport close")

        self.batch = 0
        self.cdir  = None

        if self.ftp == None : return
        try    : self.ftp.close()
        except : pass
        self.ftp = None

    def download( self, parent ):
        self.logger = parent.logger
        self.logger.debug("ftp_transport download")
    
        self.parent = parent
        msg         = parent.msg
    
        # seek not supported
        if msg.partflg == 'i' :
           self.logger.error("ftp, inplace part file not supported")
           msg.report_publish(499,'ftp does not support partitioned file transfers')
           return False
    
        url         = msg.url
        urlstr      = msg.urlstr
        token       = msg.url.path[1:].split('/')
        cdir        = '/'.join(token[:-1])
        remote_file = token[-1]
        new_lock = ''
    
        try :
                parent.destination = msg.urlcred

                ftp = self.ftp
                if not self.check_is_connected() :
                   self.logger.debug("ftp_transport download connects")
                   ftp = sr_ftp(parent)
                   ftp.connect()
                   self.ftp = ftp
                
                if self.cdir != cdir :
                   self.logger.debug("ftp_transport download cd to %s" %cdir)
                   ftp.cd(cdir)
                   self.cdir  = cdir
    
                #download file
                self.logger.debug('Download: %s into %s %d-%d' % 
                           (urlstr,msg.local_file,msg.local_offset,msg.local_offset+msg.length-1))
    
    
                # FIXME  locking for i parts in temporary file ... should stay lock
                # and file_reassemble... take into account the locking

                ftp.set_sumalgo(msg.sumalgo)

                if parent.inflight == None :
                   ftp.get(remote_file,msg.local_file,msg.local_offset)

                elif parent.inflight == '.' :
                   local_dir  = os.path.dirname (msg.local_file)
                   if local_dir != '' : local_lock = local_dir + os.sep
                   local_lock += '.' + os.path.basename(msg.local_file)
                   ftp.get(remote_file,local_lock,msg.local_offset)
                   if os.path.isfile(msg.local_file) : os.remove(msg.local_file)
                   os.rename(local_lock, msg.local_file)
            
                elif parent.inflight[0] == '.' :
                   local_lock  = msg.local_file + parent.inflight
                   ftp.get(remote_file,local_lock,msg.local_offset)
                   if os.path.isfile(msg.local_file) : os.remove(msg.local_file)
                   os.rename(local_lock, msg.local_file)
    
                msg.report_publish(201,'Downloaded')

                msg.onfly_checksum = ftp.checksum
    
                if parent.delete :
                   try   :
                           ftp.delete(remote_file)
                           msg.logger.debug('file deleted on remote site %s' % remote_file)
                   except: msg.logger.error('unable to delete remote file %s' % remote_file)
    
                #closing after batch or when destination is changing
                #ftp.close()
    
                return True
                
        except:
                #closing after batch or when destination is changing
                #try    : ftp.close()
                #except : pass
    
                (stype, svalue, tb) = sys.exc_info()
                msg.logger.error("Download failed %s. Type: %s, Value: %s" % (urlstr, stype ,svalue))
                msg.report_publish(499,'ftp download failed')
                if os.path.isfile(local_lock) : os.remove(local_lock)
    
                return False
    
        msg.report_publish(499,'ftp download failed')
    
        return False

    def send( self, parent ):
        self.logger = parent.logger
        self.parent = parent
        self.logger.debug("ftp_transport send")

        msg    = parent.msg

        # 'i' cannot be supported by ftp/ftps
        # we cannot offset in the remote file to inject data
        #
        # FIXME instead of dropping the message
        # the inplace part could be delivered as 
        # a separate partfile and message set to 'p'
        if  msg.partflg == 'i':
            self.logger.error("ftp cannot send partitioned files")
            msg.report_publish(499,'ftp delivery failed')
            return False
    
        local_file = parent.local_path
        new_dir = parent.new_dir
    
        try :
                ftp = self.ftp
                if not self.check_is_connected() :
                   self.logger.debug("ftp_transport send connects")
                   ftp = sr_ftp(parent)
                   ftp.connect()
                   self.ftp = ftp
                
                if self.cdir != new_dir :
                   self.logger.debug("ftp_transport send cd to %s" % new_dir)
                   ftp.cd_forced(775,new_dir)
                   self.cdir  = new_dir

                #=================================
                # delete event
                #=================================

                if msg.sumflg == 'R' :
                   msg.logger.debug("message is to remove %s" % parent.new_file)
                   ftp.delete(parent.new_file)
                   msg.report_publish(205,'Reset Content : deleted')
                   return True

                #=================================
                # send event
                #=================================

                offset    = 0
                str_range = ''
    
                # deliver file
    
                msg.logger.debug('Beginning put of %s %s into %s/%s %d-%d' % 
                    (parent.local_file,str_range,parent.new_dir,parent.new_file,offset,offset+msg.length-1))
    
                if parent.inflight == None :
                   ftp.put(local_file, parent.new_file)
                elif parent.inflight == '.' :
                   new_lock = '.'  + parent.new_file
                   ftp.put(local_file, new_lock)
                   ftp.rename(new_lock, parent.new_file)
                elif parent.inflight[0] == '.' :
                   new_lock = parent.new_file + parent.inflight
                   ftp.put(local_file, new_lock)
                   ftp.rename(new_lock, parent.new_file)
                elif parent.inflight == 'umask' :
                   ftp.umask()
                   ftp.put(local_file, parent.new_file)
    
                try   : ftp.chmod(parent.chmod,parent.new_file)
                except: pass
    
                msg.report_publish(201,'Delivered')
    
                #closing after batch or when destination is changing
                #ftp.close()
    
                return True
                
        except:
                #closing after batch or when destination is changing
                #try    : ftp.close()
                #except : pass
    
                (stype, svalue, tb) = sys.exc_info()
                msg.logger.error("Delivery failed %s. Type: %s, Value: %s" % (parent.remote_urlstr, stype ,svalue))
                msg.report_publish(499,'ftp delivery failed')
    
                return False
    
        msg.report_publish(499,'ftp delivery failed')
    
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
    opt1 = "destination ftp://localhost"
    cfg.option( opt1.split()  )
    cfg.logger  = logger
    cfg.timeout = 5
    try:
           ftp = sr_ftp(cfg)
           ftp.connect()
           ftp.mkdir("tztz")
           ftp.chmod(775,"tztz")
           ftp.cd("tztz")
       
           ftp.umask()
           f = open("aaa","wb")
           f.write(b"1\n")
           f.write(b"2\n")
           f.write(b"3\n")
           f.close()
       
           ftp.put("aaa", "bbb")
           ls = ftp.ls()
           logger.info("ls = %s" % ls )
       
           ftp.chmod(775,"bbb")
           ls = ftp.ls()
           logger.info("ls = %s" % ls )
       
           ftp.rename("bbb", "ccc")
           ls = ftp.ls()
           logger.info("ls = %s" % ls )
       
           ftp.get("ccc", "bbb")
           f = open("bbb","rb")
           data = f.read()
           f.close()
           ftp.close()
       
           if data != b"1\n2\n3\n" :
              logger.error("sr_ftp TEST FAILED")
              sys.exit(1)

           os.unlink("bbb")

           msg         = sr_message(cfg)
           msg.start_timer()
           msg.topic   = "v02.post.test"
           msg.notice  = "notice"
           msg.urlcred = "ftp://localhost/"
           msg.urlstr  = "ftp://localhost/tztz/ccc"
           msg.url     = urllib.parse.urlparse(msg.urlcred+"tztz/ccc")
           msg.partflg = '1'
           msg.offset  = 0
           msg.length  = 0
           msg.sumalgo = None

           msg.local_file   = "bbb"
           msg.local_offset = 0

           cfg.msg     = msg
           cfg.batch   = 5
           cfg.kbytes_ps= 0.05
       
           dldr = ftp_transport()
           cfg.inflight        = None
           dldr.download(cfg)
           dldr.download(cfg)
           cfg.inflight        = '.'
           dldr.download(cfg)
           dldr.download(cfg)
           logger.debug("checksum = %s" % msg.onfly_checksum)
           dldr.download(cfg)
           cfg.inflight        = '.tmp'
           dldr.download(cfg)
           dldr.download(cfg)
           msg.sumalgo = cfg.sumalgo
           dldr.download(cfg)
           logger.debug("checksum = %s" % msg.onfly_checksum)
           
           logger.debug("change context")
           ok, details = cfg.credentials.get(cfg.destination)
           details.binary = False
           cfg.credentials.credentials[cfg.destination] = details
           dldr.download(cfg)
           logger.debug("checksum = %s" % msg.onfly_checksum)
           dldr.close()
           dldr.close()
           dldr.close()

           dldr = ftp_transport()
           cfg.local_file    = "bbb"
           cfg.local_path    = "./bbb"
           cfg.remote_file   = "ddd"
           cfg.remote_path   = "tztz/ddd"
           cfg.remote_urlstr = "ftp://localhost/tztz/ddd"
           cfg.remote_dir    = "tztz"
           cfg.chmod       = 775
           cfg.inflight      = None
           dldr.send(cfg)
           dldr.ftp.delete("ddd")
           cfg.inflight      = '.'
           dldr.send(cfg)
           dldr.ftp.delete("ddd")
           cfg.inflight      = '.tmp'
           dldr.send(cfg)
           dldr.send(cfg)
           dldr.send(cfg)

           logger.debug("change context back")
           ok, details = cfg.credentials.get(cfg.destination)
           details.binary = True
           cfg.credentials.credentials[cfg.destination] = details

           dldr.send(cfg)
           dldr.send(cfg)
           dldr.send(cfg)
           dldr.close()
           dldr.close()
           dldr.close()

           ftp = sr_ftp(cfg)
           ftp.connect()
           ftp.cd("tztz")
           ftp.delete("ccc")
           ftp.delete("ddd")
           logger.info("%s" % ftp.originalDir)
           ftp.cd("")
           logger.info("%s" % ftp.ftp.pwd())
           ftp.rmdir("tztz")
       
           ftp.close()
    except:
           logger.error("sr_ftp TEST FAILED")
           sys.exit(2)

    os.unlink('aaa')
    os.unlink('bbb')

    print("sr_ftp TEST PASSED")
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
