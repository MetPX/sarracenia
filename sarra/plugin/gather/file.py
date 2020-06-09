#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#

import json,os,random,sys,time

from sys import platform as _platform

from base64 import b64decode, b64encode
from mimetypes import guess_type

from random import choice

from collections import *

from watchdog.observers         import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events            import PatternMatchingEventHandler

from sarra.sr_xattr import *
from sarra.sr_util      import *
from sarra.plugin import Plugin

import logging

logger = logging.getLogger( __name__ )


class SimpleEventHandler(PatternMatchingEventHandler):

   def __init__(self,parent):
       self.on_created  = parent.on_created
       self.on_deleted  = parent.on_deleted
       self.on_modified = parent.on_modified
       self.on_moved    = parent.on_moved
       super().__init__()


class File(Plugin):
    """
    read the file system, create messages for the files you find.

    this is taken from v2's sr_post.py
    """
    def on_add(self, event, src, dst):
        #logger.debug("%s %s %s" % ( event, src, dst ) )
        self.new_events['%s %s'%(src,dst)] = ( event, src, dst )

    def on_created(self, event):
        # on_created (for SimpleEventHandler)
        self.on_add( 'create', event.src_path, None )

    def on_deleted(self, event):
        # on_deleted (for SimpleEventHandler)
        self.on_add( 'delete', event.src_path, None )

    def on_modified(self, event):
        # on_modified (for SimpleEventHandler)
        self.on_add( 'modify', event.src_path, None )

    def on_moved(self, event):
        # on_moved (for SimpleEventHandler)
        self.on_add( 'move', event.src_path, event.dest_path )

    def __init__(self, options ):
        """ 
        """ 

        logger.debug("%s used to be overwrite_defaults" % self.program_name)
     
        self.o = options
        self.obs_watched   = []
        self.watch_handler = None
        self.post_topic_prefix = "v02.post"

        self.inl           = OrderedDict()
        self.new_events    = OrderedDict()
        self.left_events   = OrderedDict()

        self.o.blocksize     = 200 * 1024 * 1024


    def path_inflight(self,path,lstat):
        """
          check the self.o.inflight, compare fail age against it.
          return True if the file is old enough to be posted.
        """
        logger.debug("path_inflight %s" % path )

        if not isinstance(self.o.inflight,int):
           #logger.debug("ok inflight unused")
           return False

        if lstat == None :
           #logger.debug("ok lstat None")
           return False

        age = nowflt() - lstat.st_mtime
        if age < self.o.inflight :
           logger.debug("%d vs (inflight setting) %d seconds. Too New!" % \
               (age,self.o.inflight) )
           return True

        return False

    def path_renamed(self,path):

        newname = path

        # rename path given with no filename

        if self.o.rename :
           newname = self.o.rename
           if self.o.rename[-1] == '/' :
              newname += os.path.basename(path)

        # strip 'N' heading directories

        if self.o.strip > 0:
           strip = self.o.strip
           if path[0] == '/' : strip = strip + 1
           # if we strip too much... keep the filename
           token = path.split('/')
           try :   token   = token[strip:]
           except: token   = [os.path.basename(path)]
           newname = '/'+'/'.join(token)

        if newname == path : return None

        return newname

    def path_rejected(self,path):
        #logger.debug("path_rejected %s" % path )

        if not self.o.post_base_url:
            self.o.post_base_url = 'file:/'
        
        if self.o.masks == [] : return False

        self.o.post_relpath = path
        if self.o.post_base_dir : self.o.post_relpath = path.replace(self.o.post_base_dir, '')

        urlstr = self.o.post_base_url + '/' + self.o.post_relpath

        if self.o.realpath_filter and not self.o.realpath_post :
           if os.path.exists(path) :
              fltr_post_relpath = os.path.realpath(path)
              if sys.platform == 'win32':
                  fltr_post_relpath = fltr_post_relpath.replace('\\','/')

              if self.o.post_base_dir : fltr_post_relpath = fltr_post_relpath.replace(self.post_base_dir, '')
              urlstr = self.o.post_base_url + '/' + fltr_post_relpath
        
        if not self.isMatchingPattern(urlstr,self.o.accept_unmatch) :
           logger.debug("%s Rejected by accept/reject options" % urlstr )
           return True

        logger.debug( "%s not rejected" % urlstr )
        return False

    def post_delete(self, path, key=None, value=None):
        logger.debug("post_delete %s (%s,%s)" % (path,key,value) )

        # post_init (message)
        self.post_init(path,None)

        # sumstr
        hash   = sha512()
        hash.update(bytes(os.path.basename(path), encoding='utf-8'))
        sumstr = 'R,%s' % hash.hexdigest()

        # partstr
        partstr = None

        # completing headers
        self.msg.headers['sum'] = sumstr

        # used when moving a file
        if key != None :
           self.msg.headers[key] = value
           if key == 'newname' and self.post_base_dir :
              self.msg.new_dir  = os.path.dirname( value)
              self.msg.new_file = os.path.basename(value)
              self.msg.headers[key] = value.replace(self.post_base_dir, '')

        return ok

    def post_file(self, path, lstat, key=None, value=None):
        #logger.debug("post_file %s" % path )

        # check if it is a part file
        if path.endswith('.'+self.msg.part_ext):
           return self.post_file_part(path,lstat)
        
        # This variable means that part_file_assemble plugin is loaded and will handle posting the original file (being assembled)

        elif hasattr(self, 'suppress_posting_partial_assembled_file'):
            return False

        # check the value of blocksize

        fsiz  = lstat[stat.ST_SIZE]
        blksz = self.set_blocksize(self.blocksize,fsiz)

        # if we should send the file in parts

        if blksz > 0 and blksz < fsiz :
           return self.post_file_in_parts(path,lstat)

        # post_init (message)
        self.post_init(path,lstat)

        # partstr

        partstr = '1,%d,1,0,0' % fsiz

        sumstr = self.compute_sumstr(path, fsiz)
 
        # caching ... 

        if self.caching :
           new_post = self.cache.check(str(sumstr),self.post_relpath,partstr)
           if new_post : logger.info("caching %s"% path)
           else        : 
                         logger.debug("already posted %s"% path)
                         return False

        # complete message        
        if self.post_topic_prefix.startswith('v03') and self.inline and fsiz < self.inline_max :        
 
           if self.inline_encoding == 'guess':
              e = guess_type(path)[0]
              binary = not e or not ('text' in e )
           else:
              binary = (self.inline_encoding == 'text' )

           f = open(path,'rb')
           d = f.read()
           f.close()

           if binary:
               self.msg.headers[ "content" ] = { "encoding": "base64", "value": b64encode(d).decode('utf-8') }
           else:
               try:
                   self.msg.headers[ "content" ] = { "encoding": "utf-8", "value": d.decode('utf-8') }
               except:
                   self.msg.headers[ "content" ] = { "encoding": "base64", "value": b64encode(d).decode('utf-8') }

        self.msg.headers['parts'] = partstr
        self.msg.headers['sum']   = sumstr

        # used when moving a file

        if key != None : 
           self.msg.headers[key] = value
           if key == 'oldname' and self.post_base_dir :
              self.msg.headers[key] = value.replace(self.post_base_dir, '')

        return msg

    def compute_sumstr(self, path, fsiz):
        xattr = sr_xattr(path)
        
        if self.randomize:
            algos = ['0', 'd', 'n', 's', 'z,d', 'z,s']
            sumflg = choice(algos)
        elif 'sum' in xattr.x and 'mtime' in xattr.x:
            if xattr.get('mtime') >= self.msg.headers['mtime']:
                logger.debug("mtime remembered by xattr")
                return xattr.get('sum')
            else:
                logger.debug("xattr sum too old")
                sumflg = self.sumflg
        else:
            sumflg = self.sumflg

        xattr.set('mtime', self.msg.headers['mtime'])

        logger.debug("sum set by compute_sumstr")

        if sumflg[:2] == 'z,' and len(sumflg) > 2:
            sumstr = sumflg
        else:
            if not sumflg[0] in ['0', 'd', 'n', 's', 'z']: sumflg = 'd'

            self.set_sumalgo(sumflg)
            sumalgo = self.sumalgo
            sumalgo.set_path(path)

            # compute checksum

            if sumflg in ['d','s'] :

                fp = open(path,'rb')
                i  = 0
                while i<fsiz :
                    buf = fp.read(self.bufsize)
                    if not buf: break
                    sumalgo.update(buf)
                    i  += len(buf)
                fp.close()

            # setting sumstr
            checksum = sumalgo.get_value()
            sumstr = '%s,%s' % (sumflg, checksum)

        xattr.set('sum', sumstr)
        xattr.persist()
        return sumstr

    def post_file_in_parts(self, path, lstat):
        #logger.debug("post_file_in_parts %s" % path )

        # post_init (message)
        self.post_init(path,lstat)

        # check the value of blocksize

        fsiz      = lstat[stat.ST_SIZE]
        chunksize = self.set_blocksize(self.blocksize,fsiz)

        # count blocks and remainder

        block_count = int(fsiz/chunksize)
        remainder   =     fsiz%chunksize
        if remainder > 0 : block_count = block_count + 1

        # default sumstr

        sumstr = self.sumflg

        # loop on chunks

        blocks = list(range(0,block_count))
        if self.randomize:
            random.shuffle(blocks)
            #blocks = [8, 3, 1, 2, 9, 6, 0, 7, 4, 5] # Testing
            logger.info('Sending partitions in the following order: '+str(blocks))

        for i in blocks: 

              # setting sumalgo for that part

              sumflg = self.sumflg

              if sumflg[:2] == 'z,' and len(sumflg) > 2 :
                 sumstr = sumflg

              else:
                 sumflg = self.sumflg
                 if not self.sumflg[0] in ['0','d','n','s','z' ]: sumflg = 'd'
                 self.set_sumalgo(sumflg)
                 sumalgo = self.sumalgo
                 sumalgo.set_path(path)

              # compute block stuff

              current_block = i

              offset = current_block * chunksize
              length = chunksize

              last   = current_block == block_count-1
              if last and remainder > 0 :
                 length = remainder

              # set partstr

              partstr = 'i,%d,%d,%d,%d' %\
                        (chunksize,block_count,remainder,current_block)

              # compute checksum if needed

              if not self.sumflg in ['0','n','z'] :
                 bufsize = self.bufsize
                 if length < bufsize : bufsize = length

                 fp = open(path,'rb')
                 if offset != 0 : fp.seek(offset,0)
                 t  = 0
                 while t<length :
                       buf = fp.read(bufsize)
                       if not buf: break
                       sumalgo.update(buf)
                       t  += len(buf)
                 fp.close()

                 checksum = sumalgo.get_value()
                 sumstr   = '%s,%s' % (sumflg,checksum)

              # caching

              if self.caching :
                 new_post = self.cache.check(str(sumstr),self.post_relpath,partstr)
                 if new_post : logger.info("caching %s (%s)"% (path,partstr) )
                 else        :
                               logger.debug("already posted %s (%s)"%(path,partstr) )
                               continue

              # complete  message

              self.msg.headers['parts'] = partstr
              self.msg.headers['sum']   = sumstr

        return True

    def post_file_part(self, path, lstat):

        # post_init (message)
        self.post_init(path,lstat)

        # verify suffix

        ok,log_msg,suffix,partstr,sumstr = self.msg.verify_part_suffix(path)

        # something went wrong

        if not ok:
           logger.debug("file part extension but %s for file %s" % (log_msg,path))
           return False

        # check rename see if it has the right part suffix (if present)
        if 'rename' in self.msg.headers and not suffix in self.msg.headers['rename']:
           self.msg.headers['rename'] += suffix

        # caching

        if self.caching :
           new_post = self.cache.check(str(sumstr),path,partstr)
           if new_post : logger.info("caching %s"% path)
           else        : 
                         logger.debug("already posted %s"% path)
                         return False

        # complete  message

        self.msg.headers['parts'] = partstr
        self.msg.headers['sum']   = sumstr

        return True

    def post_init(self, path, lstat=None, key=None, value=None):

        msg = {}
        msg[ 'new_dir' ]  = os.path.dirname(path)
        msg[ 'new_file' ] = os.path.basename(path)

        # relpath

        if self.o.post_base_dir :
           post_relPath = path.replace(self.o.post_base_dir, '')
        else:
           post_relPath = path

        # exchange
        msg['exchange'] = self.post_exchange

        # topic
        words = post_relPath.strip('/').split('/')
        if len(words) > 1 :
            subtopic = '.'.join(words[:-1]).replace('..','.')
        else:
            subtopic=''           
        msg['topic'] = self.o.post_topic_prefix + '.' + subtopic

        if self.subtopic: self.msg.set_topic_usr(self.post_topic_prefix,self.subtopic)
        msg[ '_deleteOnPost' ] = [ 'post_relpath', 'new_dir', 'new_file', 'exchange' ]

        # notice
        msg[ 'relPath' ]  = post_relPath
        msg[ 'baseUrl' ]  = self.o.post_base_url

        # rename
        rename = self.path_renamed(post_relPath)
        if rename           != None : msg['rename']       = rename

        # headers

        if self.o.to_clusters != None : msg['to_clusters']  = self.o.to_clusters
        if self.o.cluster     != None : msg['from_cluster'] = self.o.cluster
        if self.o.source      != None : msg['source']       = self.o.source
        if key              != None : msg[key]            = value

        if lstat == None : return

        if self.o.preserve_time:
            msg['mtime'] = timeflt2str(lstat.st_mtime)
            msg['atime'] = timeflt2str(lstat.st_atime)

        if self.o.preserve_mode:
            msg['mode']  = "%o" % ( lstat[stat.ST_MODE] & 0o7777 )

        return msg

    def post_link(self, path, key=None, value=None ):
        #logger.debug("post_link %s" % path )

        # accept this file

        if self.path_rejected (path): return False

        # post_init (message)
        self.post_init(path,None)

        # resolve link

        link = os.readlink(path)

        # partstr

        partstr = None

        # sumstr

        hash = sha512()
        hash.update( bytes( link, encoding='utf-8' ) )
        sumstr = 'L,%s' % hash.hexdigest()

        # caching

        if self.caching :
           new_post = self.cache.check(str(sumstr),self.post_relpath,partstr)
           if new_post : logger.info("caching %s"% path)
           else        : 
                         logger.debug("already posted %s"% path)
                         return False

        # complete headers

        self.msg.headers['link'] = link
        self.msg.headers['sum']  = sumstr

        # used when moving a file

        if key != None : self.msg.headers[key] = value

        # post message

        ok = self.__on_post__()

        return ok

    def post_move(self, src, dst ):
        #logger.debug("post_move %s %s" % (src,dst) )

        # watchdog funny ./ added at end of directory path ... removed

        src = src.replace('/./', '/' )
        dst = dst.replace('/./', '/' )

        if os.path.islink(dst) and self.realpath_post:
           dst = os.path.realpath(dst)
           if sys.platform == 'win32':
                  dst = dst.replace('\\','/')

        # file

        if os.path.isfile(dst) :
           ok = self.post_delete(src,               'newname', dst)
           ok = self.post_file  (dst, os.stat(dst), 'oldname', src)
           return True

        # link

        if os.path.islink(dst) :
           ok = self.post_delete(src, 'newname', dst)
           ok = self.post_link  (dst, 'oldname', src)
           return True

        # directory
        if os.path.isdir(dst) :
            for x in os.listdir(dst):

                dst_x = dst + '/' + x
                src_x = src + '/' + x

                ok = self.post_move(src_x,dst_x)

            # directory list to delete at end
            self.move_dir_lst.append( (src,dst) )

        return True

    def post1file(self,path,lstat):

        done = True

        # watchdog funny ./ added at end of directory path ... removed

        path = path.replace( '/./', '/' )

        # always use / as separator for paths being posted.
        if os.sep != '/' :  # windows
            path = path.replace( os.sep, '/' )

        # path is a link

        if os.path.islink(path):
           ok = self.post_link(path)

           if self.follow_symlinks :
              link  = os.readlink(path)
              try   : 
                   rpath = os.path.realpath(link)
                   if sys.platform == 'win32':
                       rpath = rpath.replace('\\','/')

              except: return done

              lstat = None
              if os.path.exists(rpath) : lstat = os.stat(rpath)

              ok = self.post1file(rpath,lstat)

           return done

        # path deleted

        if lstat == None :
           ok = self.post_delete(path)
           return done

        # path is a file

        if os.path.isfile(path):
           ok = self.post_file(path,lstat)
           return done

        # at this point it is a create,modify directory

        return done

    def post1move(self, src, dst ):
        #logger.debug("post1move %s %s" % (src,dst) )

        self.move_dir_lst = []

        ok = self.post_move(src,dst)

        for tup in self.move_dir_lst :
            src, dst = tup
            #logger.debug("deleting moved directory %s" % src )
            ok = self.post_delete(src, 'newname', dst)

        return True

    def process_event(self, event, src, dst ):
        #logger.debug("process_event %s %s %s " % (event,src,dst) )

        done  = True
        later = False

        # delete

        if event == 'delete' :
           if event in self.events:
              ok = self.post1file(src,None)
           return done

        # move

        if event == 'move':
           if self.create_modify:
              ok = self.post1move(src,dst)
           return done

        # create or modify

        # directory : skipped, its content is watched

        if os.path.isdir(src): 
            dirs = list( map( lambda x: x[1][1], self.inl.items() ) )
            logger.debug("skipping directory %s list: %s" % (src,dirs) )
            return done

        # link ( os.path.exists = false, lstat = None )

        if os.path.islink(src) :
           if 'link' in self.events :
              ok = self.post1file(src,None)
           return done

        # file : must exists
        #       (may have been deleted since event caught)

        if not os.path.exists(src) : return done

        # file : must be old enough

        lstat = os.stat(src)
        if self.path_inflight(src,lstat): return later

        # post it

        if self.create_modify :
           ok = self.post1file(src,lstat)

        return done

    def set_blocksize(self,bssetting,fsiz):

      tfactor =  50 * 1024 * 1024
      
      if bssetting == 0 : ## autocompute
            if   fsiz > 100*tfactor: return 10 * tfactor
            elif fsiz > 10*tfactor : return int((fsiz+9)/10)
            elif fsiz > tfactor :    return int((fsiz+2)/ 3)
            else:                    return fsiz 
             
      elif  bssetting == 1 : ## send file as one piece.
            return fsiz
             
      else: ## partstr=i
            return bssetting


    def wakeup(self):
        #logger.debug("wakeup")

        # FIXME: Tiny potential for events to be dropped during copy.
        #     these lists might need to be replaced with watchdog event queues.
        #     left for later work. PS-20170105
        #     more details: https://github.com/gorakhargosh/watchdog/issues/392

        # on_watch 

        ok = self.__on_watch__()
        if not ok:
            return

        # pile up left events to process

        self.left_events.update(self.new_events)
        self.new_events = OrderedDict()

        # work with a copy events and keep done events (to delete them)

        self.cur_events  = OrderedDict()
        self.cur_events.update(self.left_events)

        # loop on all events

        for key in self.cur_events:
            event, src, dst = self.cur_events[key]
            done = False
            try:
                done = self.process_event(event, src, dst)
            except OSError as err:
                logger.error("could not process event({}): {}".format(event, err))
                logger.debug("Exception details:", exc_info=True)
                self.left_events.pop(key)
            if done:
                self.left_events.pop(key)

    def walk(self, src ):
        logger.debug("walk %s" % src )

        # how to proceed with symlink

        if os.path.islink(src) and self.realpath_post :
           src = os.path.realpath(src)
           if sys.platform == 'win32':
               src = src.replace('\\','/')

        # walk src directory, this walk is depth first... there could be a lot of time
        # between *listdir* run, and when a file is visited, if there are subdirectories before you get there.
        # hence the existence check after listdir (crashed in flow_tests of > 20,000)
        for x in os.listdir(src):
            path = src + '/' + x
            if os.path.isdir(path):
               self.walk(path)
               continue

            # add path created
            if os.path.exists(path):
                self.post1file(path,os.stat(path))

    def walk_priming(self,p):
        """
         Find all the subdirectories of the given path, start watches on them. 
         deal with symbolically linked directories correctly
        """
        if os.path.islink(p):
            realp = os.path.realpath(p)
            if sys.platform == 'win32':
               realp = realp.replace('\\','/')

            logger.info("sr_watch %s is a link to directory %s" % ( p, realp) )
            if self.realpath_post:
                d=realp
            else:
                d=p + '/' + '.'
        else:
            d=p

        try:
            fs = os.stat(d)
            dir_dev_id = '%s,%s' % (fs.st_dev, fs.st_ino)
            if dir_dev_id in self.inl:
                return True
        except OSError as err:
            logger.warning("could not stat file ({}): {}".format(d, err))
            logger.debug("Exception details:", exc_info=True)

        if os.access( d , os.R_OK|os.X_OK ):
           try:
               ow = self.observer.schedule(self.watch_handler, d, recursive=True )
               self.obs_watched.append(ow)
               self.inl[dir_dev_id] = (ow,d)
               logger.info("sr_watch priming watch (instance=%d) scheduled for: %s " % (len(self.obs_watched), d))
           except:
               logger.warning("sr_watch priming watch: %s failed, deferred." % d)
               logger.debug('Exception details:', exc_info=True)

               # add path created
               self.on_add( 'create', p, None )
               return True

        else:
            logger.warning("sr_watch could not schedule priming watch of: %s (EPERM) deferred." % d)
            logger.debug('Exception details:', exc_info=True)

            # add path created
            self.on_add( 'create', p, None )
            return True

        return True

    def watch_dir(self, sld ):
        logger.debug("watch_dir %s" % sld )

        if self.force_polling :
           logger.info("sr_watch polling observer overriding default (slower but more reliable.)")
           self.observer = PollingObserver()
        else:
           logger.info("sr_watch optimal observer for platform selected (best when it works).")
           self.observer = Observer()

        self.obs_watched = []

        self.watch_handler  = SimpleEventHandler(self)
        self.walk_priming(sld)

        logger.info("sr_watch priming walk done, but not yet active. Starting...")
        self.observer.start()
        logger.info("sr_watch now active on %s posting to exchange: %s"%(sld,self.post_exchange))

        if self.post_on_start:
            self.walk(sld)


    def on_start(self):
        if self.sleep > 0 : 
            self.watch_dir(d)

    def gather(self):
        logger.info("%s run partflg=%s, sum=%s, caching=%s basis=%s" % \
              ( self.program_name, self.partflg, self.sumflg, self.caching, self.cache_basis ))
        logger.info("%s realpath_post=%s follow_links=%s force_polling=%s"  % \
              ( self.program_name, self.realpath_post, self.follow_symlinks, self.force_polling ) )

        pbd = self.post_base_dir

        for d in self.postpath :
            logger.debug("postpath = %s" % d)
            if pbd and not d.startswith(pbd) : d = pbd + '/' + d

            if os.path.isdir(d) :
                self.walk(d)
            elif os.path.islink(d):
                self.post1file(d,None)
            elif os.path.isfile(d):
                self.post1file(d,os.stat(d))
            else: 
                logger.error("could not post %s (exists %s)" % (d,os.path.exists(d)) )

