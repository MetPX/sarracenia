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
#============================================================
# usage example
#
# sr_poll [options] [config] [start|stop|restart|reload|status]
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
# broker                  = where the message is announced... one specific user per poll source
# exchange                = xs_source_user
# url                     = taken from the destination
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

try :    
         from sr_amqp           import *
         from sr_ftp            import *
         from sr_instances      import *
         from sr_message        import *
         from sr_poster         import *
except : 
         from sarra.sr_amqp      import *
         from sarra.sr_ftp       import *
         from sarra.sr_instances import *
         from sarra.sr_message   import *
         from sarra.sr_poster    import *

class sr_poll(sr_instances):

    def __init__(self,config=None,args=None):
        sr_instances.__init__(self,config,args)

    def cd(self, path):
        try   :
                  self.dest.cd(path)
                  return True
        except :
                  self.logger.warning("Could not cd to directory %s" % path )
                  (stype, svalue, tb) = sys.exc_info()
                  self.logger.warning(" Type: %s, Value: %s" % (stype ,svalue))
        return False

    def check(self):
        # force 1 instance
        self.nbr_instances = 1
        self.sleeping      = False
        self.connected     = False 

        # to clusters requiered

        if self.to_clusters == None :
           self.logger.error("-to option is mandatory\n")
           sys.exit(1)

        # check destination

        self.details = None
        if self.destination != None :
           ok, self.details = self.credentials.get(self.destination)

        if self.destination == None or self.details == None :
           self.logger.error("destination option incorrect or missing\n")
           sys.exit(1)

        # check destination

        if self.exchange  == None :
           self.exchange   = 'xs_%s' % self.broker.username
        self.post_exchange = self.exchange

        # check sumflg should start with z,

        if len(self.sumflg) < 2 or self.sumflg[:2] != 'z,' :
           self.logger.error("sum should start with z,  ex.: z,d\n")
           sys.exit(1)

        # rebuild mask as pulls instructions
        # pulls[directory] = [mask1,mask2...]

        self.pulls   = {}
        for mask in self.masks:
            pattern, maskDir, maskFileOption, mask_regexp, accepting = mask
            self.logger.debug(mask)
            if not maskDir in self.pulls :
               self.pulls[maskDir] = []
            self.pulls[maskDir].append(mask)

    def close(self):
        self.poster.close()
        self.connected = False 

    def connect(self):

        # =============
        # create message
        # =============

        self.msg = sr_message(self)

        # =============
        # poster
        # =============

        self.post_broker      = self.broker
        self.post_exchange    = self.exchange
        self.poster           = sr_poster(self)

        self.msg.publisher    = self.poster.publisher
        self.msg.pub_exchange = self.post_exchange
        self.msg.post_exchange_split = self.post_exchange_split

        self.connected        = True 
           

    # =============
    # default_poll
    # =============

    def default_poll(self):

        # instantiate according to the protocol

        url = self.details.url

        self.dest = None
        if url.scheme == 'ftp'  : self.dest = sr_ftp(self)
        if url.scheme == 'ftps' : self.dest = sr_ftp(self)
        if url.scheme == 'sftp' :
           try    : from sr_sftp       import sr_sftp
           except : from sarra.sr_sftp import sr_sftp
           self.dest = sr_sftp(self)

        # General Attributes

        self.ls          = {}
        self.lsold       = {}
        self.lspath      = ''
        self.pulllst     = []
        self.originalDir = ''
        self.destDir     = ''

        ok = self.post_new_urls()

        return ok

    # find differences between current ls and last ls
    # only the newer or modified files will be kept...

    def differ(self):

        # get new list and description
        new_lst  = []
        for k in self.ls.keys():
            new_lst.append(k)
        new_desc = self.ls
        new_lst.sort()

        # get old list and description
        self.load_ls_file(self.lspath)

        old_lst  = []
        for k in self.lsold.keys():
            old_lst.append(k)
        old_desc = self.lsold
        old_lst.sort()

        # compare

        filelst  = []
        desclst  = {}

        for f in new_lst :

            # keep a newer entry
            if not f in old_lst :
               filelst.append(f)
               desclst[f] = new_desc[f]
               continue

            # keep a modified entry
            if new_desc[f] != old_desc[f] :
               filelst.append(f)
               desclst[f] = new_desc[f]
               continue

        return filelst,desclst


    # check for pattern matching in directory name

    def dirPattern(self,path) :
        """
        Replace pattern in directory... 
        """

        ndestDir = ''

        DD = path.split("/")
        for  ddword in DD[1:] :
             ndestDir += '/'
             if ddword == "" : continue

             nddword = ""
             DW = ddword.split("$")
             for dwword in DW :
                 nddword += self.matchPattern(dwword,dwword)

             ndestDir += nddword

        return ndestDir

    # =============
    # __do_poll__
    # =============

    def __do_poll__(self):

        if self.do_poll :
           ok = self.do_poll(self)
           return ok

        ok = self.default_poll()
        return ok

    def help(self):
        print("Usage: %s [OPTIONS] configfile [start|stop|restart|reload|status]\n" % self.program_name )
        print("OPTIONS:")
        print("DEBUG:")
        print("-debug")

    def load_ls_file(self,path):
        self.lsold = {}

        if not os.path.isfile(path) : return True
        try : 
                file=open(path,'r')
                lines=file.readlines()
                file.close()

                for line in lines :
                    parts = line.split()
                    fil   = parts[-1]
                    self.lsold[fil] = line[:-1]

                return True

        except:
                self.logger.error("Unable to parse files from %s" % path )

        return False

    def lsdir(self):
        try :
                self.ls = self.dest.ls()
                new_ls  = {}

                # apply selection on the list

                for f in self.ls :
                    self.line = self.ls[f]
                    for mask in self.pulllst :
                        pattern, maskDir, maskFileOption, mask_regexp, accepting = mask
                        if mask_regexp.match(f) and accepting :
                           if self.on_line : 
                              ok = self.on_line(self)
                              if not ok : continue
                           new_ls[f] = self.line

                self.ls = new_ls
                return True
        except:
                (stype, svalue, tb) = sys.exc_info()
                self.logger.warning("Could not ls directory %s" % self.destDir)
                self.logger.warning(" Type: %s, Value: %s" % (stype ,svalue))
        return False

    def matchPattern(self,keywd,defval) :
        """
        Matching keyword with different patterns
        """
        if keywd[:6] == "{YYYY}"         : 
                                           return   time.strftime("%Y", time.gmtime()) + keywd[6:]

        if keywd[:9] == "{YYYY-1D}"      : 
                                           epoch  = time.mktime(time.gmtime()) - 24*60*60
                                           return   time.strftime("%Y", time.localtime(epoch) ) + keywd[9:]

        if keywd[:4] == "{MM}"           : 
                                           return   time.strftime("%m", time.gmtime()) + keywd[4:]

        if keywd[:7] == "{MM-1D}"        : 
                                           epoch  = time.mktime(time.gmtime()) - 24*60*60
                                           return   time.strftime("%m", time.localtime(epoch) ) + keywd[7:]

        if keywd[:5] == "{JJJ}"          : 
                                           return   time.strftime("%j", time.gmtime()) + keywd[5:]

        if keywd[:8] == "{JJJ-1D}"       : 
                                           epoch  = time.mktime(time.gmtime()) - 24*60*60
                                           return   time.strftime("%j", time.localtime(epoch) ) + keywd[8:]

        if keywd[:10] == "{YYYYMMDD}"    : 
                                           return   time.strftime("%Y%m%d", time.gmtime()) + keywd[10:]

        if keywd[:13] == "{YYYYMMDD-1D}" :
                                           epoch  = time.mktime(time.gmtime()) - 24*60*60
                                           return   time.strftime("%Y%m%d", time.localtime(epoch) ) + keywd[13:]

        if keywd[:13] == "{YYYYMMDD-2D}" :
                                           epoch  = time.mktime(time.gmtime()) - 48*60*60
                                           return   time.strftime("%Y%m%d", time.localtime(epoch) ) + keywd[13:]

        if keywd[:13] == "{YYYYMMDD-3D}" :
                                           epoch  = time.mktime(time.gmtime()) - 72*60*60
                                           return   time.strftime("%Y%m%d", time.localtime(epoch) ) + keywd[13:]

        if keywd[:13] == "{YYYYMMDD-4D}" :
                                           epoch  = time.mktime(time.gmtime()) - 96*60*60
                                           return   time.strftime("%Y%m%d", time.localtime(epoch) ) + keywd[13:]

        if keywd[:13] == "{YYYYMMDD-5D}" : 
                                           epoch  = time.mktime(time.gmtime()) - 120*60*60
                                           return   time.strftime("%Y%m%d", time.localtime(epoch) ) + keywd[13:]

        return defval

    def overwrite_defaults(self):

        # overwrite defaults
        # default broker, exchange, destination None

        self.broker         = None
        self.exchange       = None
        self.destination    = None

        # Should there be accept/reject option used unmatch are accepted

        self.accept_unmatch = False

        # set parts to '1' so we always announce download the entire file

        self.parts          = '1'

        # need to compute checksum with d algo... in sarra

        self.sumflg         = 'z,d'

    # =============
    # for all directories, get urls to post
    # if True is returned it means : no sleep, retry on return
    # False means, go to sleep and retry after sleep seconds
    # =============

    def post_new_urls(self):

        # number of post files

        npost = 0

        # connection did not work

        try:
             self.dest.connect()
        except:
            (stype, svalue, tb) = sys.exc_info()
            self.logger.warning(" Type: %s, Value: %s" % (stype ,svalue))
            self.logger.error("Unable to connect to %s. Type: %s, Value: %s" % (self.destination, stype ,svalue))
            self.logger.error("Sleeping 30 secs and retry")
            time.sleep(30)
            return True

        # loop on all directories where there are pulls to do

        for destDir in self.pulls :

            self.destDir = destDir
            self.pulllst = self.pulls[destDir]

            pdir = self.dirPattern(self.destDir)
            if pdir != '' : self.destDir = pdir
            self.destDir = self.destDir[1:]

            # cd to that directory

            self.logger.debug(" cd %s" % self.destDir)
            ok = self.cd(self.destDir)
            if not ok : continue

            # create ls filename for that directory

            pdir = destDir
            pdir = pdir.replace('${','')
            pdir = pdir.replace('}','')
            pdir = pdir.replace('/','_')

            self.lspath = self.user_cache_dir + os.sep + 'ls' + pdir

            # ls that directory

            ok = self.lsdir()
            if not ok : continue

            # if we are sleeping and we are here it is because
            # this pull is retrieving difference between directory content
            # so write the directory content without retrieving files

            if self.sleeping :
               ok = self.write_ls_file(self.lspath)
               continue

            # get the file list from the ls
            
            filelst = []
            for k in self.ls.keys():
                filelst.append(k)
            desclst = self.ls

            # get file list from difference in ls

            filelst,desclst = self.differ()

            if len(filelst) == 0 :
               ok = self.write_ls_file(self.lspath)
               continue

            # for all files make a post
            for idx,remote_file in enumerate(filelst) :

                FileOption = None
                for mask in self.pulllst :
                    pattern, maskDir, maskFileOption, mask_regexp, accepting = mask
                    if mask_regexp.match(remote_file) and accepting :
                       FileOption = maskFileOption

                desc   = desclst[remote_file]
                fsiz   = desc.split()[4]

                self.urlstr  = self.destination + self.destDir + '/'+ remote_file
                self.url     = urllib.parse.urlparse(self.urlstr)
                self.partstr = '1,%s,1,0,0' % fsiz
                self.sumstr  = self.sumflg

                this_rename  = self.rename

                # FIX ME generalized fileOption
                if FileOption != None :
                   parts = FileOption.split('=')
                   option = parts[0].strip()
                   if option == 'rename' and len(parts) == 2 : 
                      this_rename = parts[1].strip()

                if this_rename != None and this_rename[-1] == '/' :
                   this_rename += remote_file
                
                ok = self.poster.post(self.exchange,self.url,self.to_clusters, \
                                      self.partstr,self.sumstr,this_rename,remote_file)

                if ok : npost += 1


            ok = self.write_ls_file(self.lspath)

        # close connection

        try   : self.dest.close()
        except: pass

        if self.sleeping:
           self.logger.info("oh! we are sleeping...")

        return npost > 0


    # write ls file

    def write_ls_file(self,path):

        filelst = []
        for k in self.ls.keys():
            filelst.append(k)
        desclst = self.ls
        filelst.sort()

        try : 
                fp=open(path,'w')
                for f in filelst :
                    fp.write(desclst[f]+'\n')
                fp.close()

                return True

        except:
                self.logger.error("Unable to write ls to file %s" % path )

        return False

    # =============
    # __on_post__ posting of message
    # =============

    def __on_post__(self):

        # invoke on_post when provided

        if self.on_post :
           ok = self.on_post(self)
           if not ok: return ok

        # should always be ok

        ok = self.msg.publish( )

        return ok

    def run(self):

        self.logger.info("sr_poll run")

        # connect to broker

        self.connect()

        # do pulls instructions

        while True :

              # log that we are waking up

              self.logger.info("poll %s is waking up" % self.config_name )

              self.sleeping = not self.has_vip()

              if self.sleeping :
                 self.logger.debug("poll is sleeping ")
              else :
                 self.logger.debug("poll is NOT sleeping ")

              # if pull is sleeping and we delete files... nothing to do
              # if we don't delete files, we will keep the directory state

              ok = False

              try  :
                      #  get a list of url to post
                      ok = self.__do_poll__()

              except:
                      (stype, svalue, tb) = sys.exc_info()
                      self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))

              if not ok :
                 self.logger.debug("poll is sleeping %d seconds " % self.sleep)
                 time.sleep(self.sleep)

    def reload(self):
        self.logger.info("%s reload" % self.program_name)
        self.close()
        self.configure()
        self.run()

    def start(self):
        self.logger.info("%s start" % self.program_name)
        self.run()

    def stop(self):
        self.logger.info("%s stop" % self.program_name)
        self.close()
        os._exit(0)

# ===================================
# MAIN
# ===================================

def main():

    action = None
    args   = None
    config = None

    if len(sys.argv) >= 2 : 
       action = sys.argv[-1]

    if len(sys.argv) >= 3 : 
       config = sys.argv[-2]
       args   = sys.argv[1:-2]

    poll = sr_poll(config,args)

    if   action == 'foreground' : poll.foreground_parent()
    elif action == 'reload'     : poll.reload_parent()
    elif action == 'restart'    : poll.restart_parent()
    elif action == 'start'      : poll.start_parent()
    elif action == 'stop'       : poll.stop_parent()
    elif action == 'status'     : poll.status_parent()
    else :
           poll.logger.error("action unknown %s" % action)
           sys.exit(1)

    sys.exit(0)


# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
