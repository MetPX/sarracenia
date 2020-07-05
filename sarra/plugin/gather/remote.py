#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#


from sarra.plugin import Plugin

import logging

logger = logging.getLogger( __name__ )


import sarra.config 

import os,sys,time

import sarra.transfer

class Remote(Plugin):

    def cd(self, path):
        try   :
                  self.dest.cd(path)
                  return True
        except :
                  logger.warning("sr_poll/cd: could not cd to directory %s" % path )
        return False

    
    def __init__(self,options):

        self.o = options
        # check destination

        self.details = None
        if self.o.destination is not None :
            ok, self.details = sarra.config.Config.credentials.get(self.o.destination)

        if self.o.destination is None or self.details == None :
            logger.error("destination option incorrect or missing\n")
            sys.exit(1)

        if self.o.post_baseUrl is None :
            self.o.post_baseUrl = self.details.url.geturl()
            if self.o.post_baseUrl[-1] != '/' : self.o.post_baseUrl += '/'
            if self.o.post_baseUrl.startswith('file:'): self.o.post_baseUrl = 'file:'
            if self.details.url.password :
                self.o.post_baseUrl = self.o.post_baseUrl.replace(':'+self.details.url.password,'')

        self.dest = sarra.transfer.Protocol( self.details.url.scheme, options )

        if self.dest is None: 
            logger.critical("unsupported polling protocol")

        # rebuild mask as pulls instructions
        # pulls[directory] = [mask1,mask2...]

        self.pulls   = {}
        for mask in self.o.masks:
            pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask
            logger.debug(mask)
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
            #logger.debug("checking %s (%s)" % (f,ls[f]))

            # keep a newer entry
            if not f in old_ls:
                #logger.debug("IS NEW %s" % f)
                filelst.append(f)
                desclst[f] = ls[f]
                continue

            # keep a modified entry
            if ls[f] != old_ls[f] :
                #logger.debug("IS DIFFERENT %s from (%s,%s)" % (f,old_ls[f],ls[f]))
                filelst.append(f)
                desclst[f] = ls[f]
                continue

            #logger.debug("IS IDENTICAL %s" % f)

        return filelst,desclst


    def gather(self):

        if self.dest != None :
           ok = self.post_new_urls()
           return ok

        logger.error("Service unavailable %s" % scheme)

        return False

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
                logger.error("load_ls_file: Unable to parse files from %s" % path )

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

            return True, new_ls, new_dir
        except:
            logger.warning("dest.lsdir: Could not ls directory")
            logger.debug("Exception details:", exc_info=True)

        return False, {}, {}


    def poll_directory(self,pdir,lspath):
        logger.debug("poll_directory %s %s" % (pdir,lspath))
        npost = 0

        # cd to that directory

        logger.debug(" cd %s" % pdir)
        ok = self.cd( pdir )
        if not ok : return npost

        # ls that directory

        ok, file_dict, dir_dict = self.lsdir()
        if not ok : return npost

        # when not sleeping

        if not self.sleeping :

           # get file list from difference in ls

           filelst,desclst = self.differ_ls_file(file_dict,lspath)
           logger.debug("poll_directory: after differ, len=%d" % len(filelst) )

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

    def post(self,post_exchange,post_baseUrl,post_relpath,to_clusters, \
                  partstr=None,sumstr=None,rename=None,mtime=None,atime=None,mode=None,link=None):

        self.msg.exchange = post_exchange
        
        self.msg.set_topic(self.post_topic_prefix,post_relpath)
        if self.subtopic != None : self.msg.set_topic_usr(self.post_topic_prefix,self.subtopic)

        self.msg.set_notice(post_baseUrl,post_relpath)

        # set message headers
        msg = {}

        msg['to_clusters'] = to_clusters

        if partstr  != None : msg['parts']        = partstr
        if sumstr   != None : msg['sum']          = sumstr
        if rename   != None : msg['rename']       = rename

        if self.preserve_time:
            if mtime    != None : msg['mtime']        = mtime
            if atime    != None : msg['atime']        = atime

        if self.preserve_mode:
            if mode     != None : msg['mode']         = "%o" % ( mode & 0o7777 )

        if link     != None : msg['link']         = link

        if self.cluster != None : msg['from_cluster'] = self.cluster
        if self.source  != None : msg['source']       = self.source

        logger.debug("Added %s" % (self.msg.notice))

        return ok


    def poll_file_post(self,ssiz,destDir,remote_file):

        path = destDir + '/'+ remote_file

        # posting a localfile
        if self.o.post_baseUrl.startswith('file:') :
           if os.path.isfile(path)   :
              try   : lstat = os.stat(path)
              except: lstat = None
              ok    = self.post1file(path,lstat)
              return ok

        self.o.post_relPath = destDir + '/'+ remote_file

        self.sumstr  = self.o.sumflg
        self.partstr = None

        try :
                isiz = int(ssiz)
                msg['size'] = isiz
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
                
        ok = self.post(self, self.o.post_exchange,self.o.post_baseUrl,self.o.post_relPath,self.o.to_clusters, \
                       self.partstr, self.sumstr,this_rename)

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
            logger.error("sr_poll/post_new_url: unable to connect to %s" % self.o.destination)
            logger.debug('Exception details: ', exc_info=True)
            logger.error("Sleeping 30 secs and retry")
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

        try: 
                fp=open(lspath,'w')
                for f in filelst :
                    fp.write(ls[f]+'\n')
                fp.close()

                return True

        except:
                logger.error("Unable to write ls to file %s" % lspath )

        return False
