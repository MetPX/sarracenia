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
# sr_poll.py : python3 program allowing users to poll a remote server (destination)
#              browse directories and get a list of products of interest. Each product
#              is announced (AMQP) as ready to be downloaded.
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Dec 29 13:12:43 EST 2015
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
#============================================================
# usage example
#
# sr_poll [options] [config] [foreground|start|stop|restart|reload|status|cleanup|setup]
#
# sr_poll connects to a destination. For each directory given, it lists its content
# and match the accept/reject products in that directory. Each file is announced and
# the list of announced product is kept.
#
# conditions:
#
# (polling)
# do_poll                 = a script supporting the protocol defined in the destination
# destination             = an url of the credentials of the remote server and its options (see credentials)
# directory               = one or more directories to browse
# accept/reject           = pattern matching what we want to poll in that directory
# do_line                 = a script reformatting the content of the list directory...
#                           (it is needed sometimes to takeaway useless or unstable fields)
# (messaging)
# post_broker             = where the message is announced... one specific user per poll source
# post_exchange           = xs_source_user
# post_base_url           = taken from the destination
# sum                     = 0   no sum computed... if we dont download the product
#                           x   if we download the product
# part                    = 1   file entirely downloaded (for now) ... find filesize from ls ?
# rename                  = which path under root, the file should appear
# source                  = None (fixed by sr_sarra)
# cluster                 = None (fixed by sr_sarra)
# to                      = message.headers['to_clusters'] MANDATORY
#
# option to only post... no download ... or only post
#============================================================

#

import os,sys,time

#============================================================
# DECLARE TRICK for false self.poster

from collections import *

#============================================================

try :    
         from sr_cache          import *
         from sr_file           import *
         from sr_ftp            import *
         from sr_http           import *
         from sr_message        import *
         from sr_post           import *
         from sr_util           import *
except : 
         from sarra.sr_cache     import *
         from sarra.sr_file      import *
         from sarra.sr_ftp       import *
         from sarra.sr_http      import *
         from sarra.sr_message   import *
         from sarra.sr_post      import *
         from sarra.sr_util      import *



class sr_poll(sr_post):

    def cd(self, path):
        try   :
                  self.dest.cd(path)
                  return True
        except :
                  self.logger.warning("sr_poll/cd: could not cd to directory %s" % path )
                  self.logger.debug('Exception details: ', exc_info=True)
        return False

    def check(self):

        if self.config_name == None : return

        # check destination

        self.details = None
        if self.destination != None :
           ok, self.details = self.credentials.get(self.destination)

        if self.destination == None or self.details == None :
           self.logger.error("destination option incorrect or missing\n")
           self.help()
           sys.exit(1)

        if self.post_base_url == None :
           self.post_base_url = self.details.url.geturl()
           if self.post_base_url[-1] != '/' : self.post_base_url += '/'
           if self.post_base_url.startswith('file:'): self.post_base_url = 'file:'
           if self.details.url.password :
              self.post_base_url = self.post_base_url.replace(':'+self.details.url.password,'')

        sr_post.check(self)

        self.sleeping      = False
        self.connected     = False 

        # rebuild mask as pulls instructions
        # pulls[directory] = [mask1,mask2...]

        self.pulls   = {}
        for mask in self.masks:
            pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask
            self.logger.debug(mask)
            if not maskDir in self.pulls :
               self.pulls[maskDir] = []
            self.pulls[maskDir].append(mask)

    # find differences between current ls and last ls
    # only the newer or modified files will be kept...

    def differ_ls_file(self,ls,lspath):

        # get new list and description

        new_lst = sorted(ls.keys())

        # get old list and description

        old_ls  = self.load_ls_file(lspath)

        # compare

        filelst  = []
        desclst  = {}

        for f in new_lst :
            #self.logger.debug("checking %s (%s)" % (f,ls[f]))

            # keep a newer entry
            if not f in old_ls:
               #self.logger.debug("IS NEW %s" % f)
               filelst.append(f)
               desclst[f] = ls[f]
               continue

            # keep a modified entry
            if ls[f] != old_ls[f] :
               #self.logger.debug("IS DIFFERENT %s from (%s,%s)" % (f,old_ls[f],ls[f]))
               filelst.append(f)
               desclst[f] = ls[f]
               continue

            #self.logger.debug("IS IDENTICAL %s" % f)

        return filelst,desclst


    # =============
    # __do_poll__
    # =============

    def __do_poll__(self):

        scheme    = self.details.url.scheme

        # try registered do_poll first... might overload defaults

        try:
                if   scheme in self.do_polls :
                     self.logger.debug("using registered do_poll for %s" % scheme)
                     do_poll = self.do_polls[scheme]
                     ok = do_poll(self)
                     return ok
        except: pass

        # try supported hardcoded download

        self.dest = None

        if   scheme == 'file'          : self.dest = sr_file(self)
        elif scheme in ['ftp','ftps']  : self.dest = sr_ftp(self)
        elif scheme in ['http','https']: self.dest = sr_http(self)
        elif scheme == 'sftp' :
             try    : from sr_sftp       import sr_sftp
             except : from sarra.sr_sftp import sr_sftp
             self.dest = sr_sftp(self)

        # user defined poll scripts
        # if many are configured, this one is the last one in config
        if self.do_poll :
           ok = self.do_poll(self)
           return ok

        # standard poll to post new urls

        if self.dest != None :
           ok = self.post_new_urls()
           return ok

        # user defined poll scripts
        # if many are configured, this one is the last one in config

        #if self.do_poll :
        #   ok = self.do_poll(self)
        #   return ok

        # something went wrong

        self.logger.error("Service unavailable %s" % scheme)

        return False

    def help(self):
        print("Usage: %s [OPTIONS] configfile [add|cleanup|declare|disable|edit|enable|foreground|remove|start|stop|restart|reload|setup|status]\n" % self.program_name )
        print("version: %s \n" % sarra.__version__ )
        print("\n\tPoll a remote server to produce announcements of new files appearing there\n" +
          "\npoll.conf file settings, MANDATORY ones must be set for a valid configuration:\n" +
          "\nAMQP broker settings:\n" +
          "\tpost_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>\n" +
          "\t\t(default: amqp://anonymous:anonymous@dd.weather.gc.ca/ ) \n" +
          "\nAMQP Queue bindings:\n" +
          "\tpost_exchange      <name>         (default: xreport for feeders, xs_<user>)\n" +
          "\ttopic_prefix  <amqp pattern> (invariant prefix, currently v02.report)\n" +
          "\tsubtopic      <amqp pattern> (MANDATORY)\n" +
          "\t\t  <amqp pattern> = <directory>.<directory>.<directory>...\n" +
          "\t\t\t* single directory wildcard (matches one directory)\n" +
          "\t\t\t# wildcard (matches rest)\n" +
          "\nAMQP Queue settings:\n" +
          "\tdurable       <boolean>      (default: False)\n" +
          "\texpire        <minutes>      (default: None)\n" +
          "\tmessage-ttl   <minutes>      (default: None)\n" +
          "\tqueue_name    <name>         (default: program set it for you)\n" +
          "\nProcessing:\n" +
          "\tdo_line           <script>        (default None)\n" +
          "\tdo_poll           <script>        (default None)\n" +
          "\ton_post           <script>        (default None)\n" +
          "" )

        print("OPTIONS:")
        print("DEBUG:")
        print("-debug")

    def load_ls_file(self,path):
        lsold = {}

        if not os.path.isfile(path) : return lsold
        try : 
                file=open(path,'r')
                lines=file.readlines()
                file.close()

                for line in lines :
                    line  = line.strip('\n')
                    parts = line.split()
                    if hasattr(self,'dest_file_index'):
                        fil = ' '.join(parts[self.dest_file_index:])
                    else:
                        fil   = parts[-1]
                        if not self.ls_file_index in [-1,len(parts)-1] : fil = ' '.join(parts[self.ls_file_index:])
                    lsold[fil] = line

                return lsold

        except:
                self.logger.error("load_ls_file: Unable to parse files from %s" % path )

        return lsold

    def lsdir(self):
        try :
            ls      = self.dest.ls()
            new_ls  = {}
            new_dir = {}

            # apply selection on the list

            for f in ls :
                matched = False
                self.line = ls[f]

                if self.on_line_list : 
                    for plugin in self.on_line_list :
                        ok = plugin(self)
                        if not ok: break
                    if not ok: continue
      
                if self.line[0] == 'd' :
                   d = f.strip(os.sep)
                   new_dir[d] = self.line
                   continue

                for mask in self.pulllst :
                   pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask
                   if mask_regexp.match(f):
                       if accepting:
                           matched=True
                           new_ls[f] = self.line.strip('\n')
                       break


            return True, new_ls, new_dir
        except:
            self.logger.warning("dest.lsdir: Could not ls directory")
            self.logger.debug("Exception details:", exc_info=True)

        return False, {}, {}

    def overwrite_defaults(self):

        sr_post.overwrite_defaults(self)

        # Set minimum permissions to something that might work most of the time.
        self.chmod = 0o400

        # cache initialisation

        self.caching     = 1200

        # set parts to '1' so we always announce download the entire file

        self.parts       = '1'

        # need to compute checksum with d algo... in sarra

        self.sumflg      = 'z,d'

        self.accept_unmatch = False


    def poll_directory(self,pdir,lspath):
        self.logger.debug("poll_directory %s %s" % (pdir,lspath))
        npost = 0

        # cd to that directory

        self.logger.debug(" cd %s" % pdir)
        ok = self.cd( pdir )
        if not ok : return npost

        # ls that directory

        ok, file_dict, dir_dict = self.lsdir()
        if not ok : return npost

        # when not sleeping

        if not self.sleeping :

           # get file list from difference in ls

           filelst,desclst = self.differ_ls_file(file_dict,lspath)
           self.logger.debug("poll_directory: after differ, len=%d" % len(filelst) )

           # post poll list

           n = self.poll_list_post( pdir, desclst, filelst ) 
           npost += n

        # sleeping or not, write the directory file content 

        ok = self.write_ls_file(file_dict,lspath)

        # poll in children directory

        sdir = sorted(dir_dict.keys())
        for d in sdir :
            if d == '.' or d == '..' : continue

            d_lspath = lspath + '_'    + d
            d_pdir   = pdir   + os.sep + d
                        
            n = self.poll_directory(d_pdir, d_lspath)
            npost += n

        return npost

    def post(self,post_exchange,post_base_url,post_relpath,to_clusters, \
                  partstr=None,sumstr=None,rename=None,mtime=None,atime=None,mode=None,link=None):

        self.msg.exchange = post_exchange
        
        self.msg.set_topic(self.post_topic_prefix,post_relpath)
        if self.subtopic != None : self.msg.set_topic_usr(self.post_topic_prefix,self.subtopic)

        self.msg.set_notice(post_base_url,post_relpath)

        # set message headers
        self.msg.headers = {}

        self.msg.headers['to_clusters'] = to_clusters

        if partstr  != None : self.msg.headers['parts']        = partstr
        if sumstr   != None : self.msg.headers['sum']          = sumstr
        if rename   != None : self.msg.headers['rename']       = rename

        if self.preserve_time:
            if mtime    != None : self.msg.headers['mtime']        = mtime
            if atime    != None : self.msg.headers['atime']        = atime

        if self.preserve_mode:
            if mode     != None : self.msg.headers['mode']         = "%o" % ( mode & 0o7777 )

        if link     != None : self.msg.headers['link']         = link

        if self.cluster != None : self.msg.headers['from_cluster'] = self.cluster
        if self.source  != None : self.msg.headers['source']       = self.source

        # ========================================
        # cache testing
        # ========================================

        if self.caching :
           if not self.cache.check(sumstr,post_relpath,partstr):
              self.logger.debug("Ignored %s" % (self.msg.notice))
              return False

        self.logger.debug("Added %s" % (self.msg.notice))

        self.msg.trim_headers()

        ok = self.__on_post__()

        return ok


    def poll_file_post(self,ssiz,destDir,remote_file):

        FileOption = None
        for mask in self.pulllst :
            pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask
            if mask_regexp.match(remote_file) and accepting :
               FileOption = maskFileOption

        path = destDir + '/'+ remote_file

        # posting a localfile
        if self.post_base_url.startswith('file:') :
           if os.path.isfile(path)   :
              try   : lstat = os.stat(path)
              except: lstat = None
              ok    = self.post1file(path,lstat)
              return ok

        self.post_relpath = destDir + '/'+ remote_file

        self.sumstr  = self.sumflg
        self.partstr = None

        try :
                isiz = int(ssiz)
                self.partstr = '1,%d,1,0,0' % isiz
        except: pass

        this_rename  = self.rename

        # FIX ME generalized fileOption
        if FileOption != None :
           parts = FileOption.split('=')
           option = parts[0].strip()
           if option == 'rename' and len(parts) == 2 : 
              this_rename = parts[1].strip()

        if this_rename != None and this_rename[-1] == '/' :
           this_rename += remote_file
                
        ok = self.post(self.post_exchange,self.post_base_url,self.post_relpath,self.to_clusters, \
                       self.partstr,self.sumstr,this_rename)

        return ok


    def poll_list_post(self, destDir, desclst, filelst ):
 
        n = 0

        for idx,remote_file in enumerate(filelst) :
            desc = desclst[remote_file]
            ssiz = desc.split()[4]

            ok = self.poll_file_post(ssiz,destDir,remote_file)
            if ok : n += 1

        return n


    # =============
    # for all directories, get urls to post
    # if True is returned it means : no sleep, retry on return
    # False means, go to sleep and retry after sleep seconds
    # =============

    def post_new_urls(self):

        # General Attributes

        self.pulllst     = []

        # number of post files

        npost = 0

        # connection did not work

        try:
             self.dest.connect()
        except:
            self.logger.error("sr_poll/post_new_url: unable to connect to %s" % self.destination)
            self.logger.debug('Exception details: ', exc_info=True)
            self.logger.error("Sleeping 30 secs and retry")
            time.sleep(30)
            return True

        if hasattr(self.dest,'file_index'): self.dest_file_index = self.dest.file_index
        # loop on all directories where there are pulls to do

        for destDir in self.pulls :

            # setup of poll directory info

            self.pulllst = self.pulls[destDir]

            path         = destDir
            path         = path.replace('${','')
            path         = path.replace('}','')
            path         = path.replace('/','_')
            lsPath       = self.user_cache_dir + os.sep + 'ls' + path

            currentDir   = self.set_dir_pattern(destDir)

            if currentDir == '' : currentDir = destDir

            npost += self.poll_directory( currentDir, lsPath )

        # close connection

        try   : self.dest.close()
        except: pass


        return npost > 0


    # write ls file

    def write_ls_file(self,ls,lspath):

        if len(ls) == 0 : 
           try   : os.unlink(lspath)
           except: pass
           return True

        filelst = sorted(ls.keys())

        try : 
                fp=open(lspath,'w')
                for f in filelst :
                    fp.write(ls[f]+'\n')
                fp.close()

                return True

        except:
                self.logger.error("Unable to write ls to file %s" % lspath )

        return False

    def run(self):
        self.logger.debug("sr_poll run")

        # connect to broker

        self.connect()

        # caching
        if self.caching :
           self.cache      = sr_cache(self)
           self.cache_stat = True
           if self.reset:
              self.cache.close(unlink=True)
           self.cache.open()
           if not hasattr(self,'heartbeat_cache_installed') or not self.heartbeat_cache_installed :
              self.execfile("on_heartbeat",'hb_cache')
              self.on_heartbeat_list.append(self.on_heartbeat)
              self.heartbeat_cache_installed = True

        # do pulls instructions

        if self.vip : last = self.has_vip()

        for plugin in self.on_start_list:
           if not plugin(self): break

        while True :

              try  :
                      #  heartbeat (may be used to check if program is alive if not "has_vip")
                      ok = self.heartbeat_check()

                      # if vip provided, check if has vip
                      if self.vip :
                         self.sleeping = not self.has_vip()

                         #  sleeping
                         if self.sleeping:
                            if not last: self.logger.info("%s is sleeping without vip=%s"% (self.program_name,self.vip))
                         #  active
                         else:
                            if last:     self.logger.info("%s is active on vip=%s"%        (self.program_name,self.vip))

                         last  = self.sleeping

                      if not self.sleeping: self.logger.debug("poll %s is waking up" % self.config_name )

                      # if pull is sleeping and we delete files... nothing to do
                      # if we don't delete files, we will keep the directory state

                      ok  = False
                      now = time.time()

                      #  do poll stuff
                      ok = self.__do_poll__()

                      #  check if sleep is to short
                      poll_time = time.time() - now
                      ratio     = self.sleep/poll_time
                      if ratio < 0.1 :
                         self.logger.warning("sr_poll sleep too low (%d) secs is less than 10%% of poll time (%f)" % (self.sleep, poll_time))

              except:
                      self.logger.error("sr_poll/run failed")
                      self.logger.debug('Exception details: ', exc_info=True)

              self.logger.debug("poll is sleeping %d seconds " % self.sleep)
              time.sleep(self.sleep)

# ===================================
# MAIN
# ===================================

def main():

    args,action,config,old = startup_args(sys.argv)

    poll = sr_poll(config,args,action)
    poll.exec_action(action,old)

    os._exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
