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
# sr_post.py : python3 program allowing users to post an available product
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Nov  8 22:10:16 UTC 2017
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

#============================================================
# usage example
#
# sr_post [options] [config] [foreground|start|stop|restart|reload|status|cleanup|setup]
#
#============================================================


#============================================================
# DECLARE TRICK for false self.poster

from collections import *

#============================================================

import json,os,random,sys,time

from watchdog.observers         import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events            import PatternMatchingEventHandler

try :    
         from sr_amqp            import *
         from sr_cache           import *
         from sr_instances       import *
         from sr_message         import *
         from sr_util            import *
except : 
         from sarra.sr_amqp      import *
         from sarra.sr_cache     import *
         from sarra.sr_instances import *
         from sarra.sr_message   import *
         from sarra.sr_util      import *

#============================================================

class SimpleEventHandler(PatternMatchingEventHandler):

   def __init__(self,parent):
       self.on_created  = parent.on_created
       self.on_deleted  = parent.on_deleted
       self.on_modified = parent.on_modified
       self.on_moved    = parent.on_moved
       super().__init__()

#============================================================

class sr_post(sr_instances):

    def __init__(self,config=None,args=None,action=None):
        sr_instances.__init__(self,config,args,action)

    # =============
    # check 
    # =============

    def check(self):
        self.logger.debug("%s check" % self.program_name)

        if self.config_name == None : return

        # singleton

        self.nbr_instances = 1

        # ===============
        # FIXME remove 2018 :  temporary checks and fake subclass
        self.temporary_stuff()
        # ===============

        if self.post_broker   == None :
           self.logger.error("post_broker required")

        if self.post_exchange == None :
           self.post_exchange = 'xs_%s' % self.post_broker.username

        if self.post_base_url == None :
           self.logger.error("post_base_url required")

        # accept whatever not rejected

        self.accept_unmatch = True

        # sr_watch requieres a sleep > 0

        if self.program_name == 'watch' :
           if self.sleep <= 0  : self.sleep = 0.1
           if not self.caching : self.caching = 300

        # caching

        if self.caching :
           self.cache      = sr_cache(self)
           self.cache_stat = True
           self.cache.open()
           self.execfile("on_heartbeat",'heartbeat_cache')
           self.on_heartbeat_list.append(self.on_heartbeat)

        # permanent message headers fields

        if self.to_clusters == None:
           self.to_clusters = self.post_broker.hostname

        # inflight 

        try   : self.inflight = int(self.inflight)
        except: pass

    # =============
    # close 
    # =============

    def close(self):
        self.logger.debug("sr_post close")

        if self.post_hc :
           self.post_hc.close()
           self.post_hc = None

        if self.cache :
           self.cache.save()
           self.cache.close()

        if self.program_name == 'watch' :
           for ow in self.obs_watched:
               self.observer.unschedule(ow)
           self.observer.stop()

    # =============
    # connect 
    # =============

    def connect(self):
        self.logger.debug("sr_post connect")

        # =============
        # create message if needed
        # =============

        self.msg = sr_message(self)

        # =============
        # posting 
        # =============

        self.post_hc = HostConnect( logger = self.logger )
        self.post_hc.set_pika( self.use_pika )
        self.post_hc.set_url( self.post_broker )
        self.post_hc.connect()

        self.publisher = Publisher(self.post_hc)
        self.publisher.build()

        self.logger.info("Output AMQP broker(%s) user(%s) vhost(%s)" % \
                        (self.post_broker.hostname,self.post_broker.username,self.post_broker.path) )

        # =============
        # setup message publish
        # =============

        self.msg.user                 = self.post_broker.username
        self.msg.publisher            = self.publisher
        self.msg.pub_exchange         = self.post_exchange
        self.msg.post_exchange_split  = self.post_exchange_split

        self.logger.info("Output AMQP exchange(%s)" % self.msg.pub_exchange )

        # =============
        # amqp resources
        # =============

        self.declare_exchanges()

    # =============
    # help
    # =============

    def help(self):
        print("\nUsage: %s -u <url> -pb <post_broker> ... [OPTIONS]\n" % self.program_name )
        print("version: %s \n" % sarra.__version__ )
        print("OPTIONS:")
        print("-pb|post_broker   <broker>          default:amqp://guest:guest@localhost/")
        print("-c|config   <config_file>")
        print("-pbd <post_base_dir>   default:None")
        print("-e   <events>          default:create|delete|follow|link|modify\n")
        print("-pe  <post_exchange>        default:xs_\"broker.username\"")
        print("-h|--help\n")
        print("-parts [0|1|sz]        0-computed blocksize (default), 1-whole files (no partitioning), sz-fixed blocksize")
        print("-to  <name1,name2,...> defines target clusters, default: ALL")
        print("-tp  <topic_prefix>    default:v02.post")
        print("-sub <subtopic>        default:'path.of.file'")
        print("-rn  <rename>          default:None")
        print("-sum <sum>             default:d")
        print("-caching               default:enable caching")
        print("-reset                 default:enable reset")
        print("-path <path1... pathN> default:required")
        print("-on_post <script>      default:None")
        print("DEBUG:")
        print("-debug")
        print("-r  : randomize chunk posting")
        print("-rr : reconnect between chunks\n")

    # =============
    # on_created (for SimpleEventHandler)
    # =============

    def on_created(self, event):
        self.logger.debug("on_created %s" % event.src_path)
        self.new_events.append( ( 'create', event.src_path, None ) )

    # =============
    # on_deleted (for SimpleEventHandler)
    # =============

    def on_deleted(self, event):
        self.logger.debug("on_deleted %s" % event.src_path)
        self.new_events.append( ( 'delete', event.src_path, None ) )

    # =============
    # on_modified (for SimpleEventHandler)
    # =============

    def on_modified(self, event):
        self.logger.debug("on_modified %s" % event.src_path)
        self.new_events.append(  ( 'modify', event.src_path, None ))

    # =============
    # on_moved (for SimpleEventHandler)
    # =============

    def on_moved(self, event):
        self.logger.debug("on_moved %s %s" % ( event.src_path, event.dest_path ) )
        self.new_events.append( ( 'move',      event.src_path, event.dest_path ) )

    # =============
    # __on_post__ posting of message
    # =============

    def __on_post__(self):
        self.logger.debug("%s __on_post_" % self.program_name)

        # invoke on_post when provided

        for plugin in self.on_post_list:
           if not plugin(self): return False

        ok = self.msg.publish( )

        return ok

    # =============
    # __on_watch__
    # =============

    def __on_watch__(self):

        # invoke user defined on_message when provided

        for plugin in self.on_watch_list:
           if not plugin(self): return False

        return True

    # =============
    # overwride defaults
    # =============

    def overwrite_defaults(self):
        self.logger.debug("%s overwrite_defaults" % self.program_name)

        self.post_broker   = None
        self.post_exchange = None
        self.post_base_url = None

        self.post_hc       = None
        self.cache         = None

        self.obs_watched   = None
        self.watch_handler = None

        self.inl           = []
        self.new_events    = []
        self.left_events   = []
        self.moving_dir    = []

        self.blocksize     = 200 * 1024 * 1024

    # =============
    # path inflight
    # =============

    def path_inflight(self,path,lstat):
        self.logger.debug("path_inflight %s" % path )

        if not isinstance(self.inflight,int):
           self.logger.debug("ok inflight unused")
           return True

        if lstat == None :
           self.logger.debug("ok lstat None")
           return True

        age = time.time() - lstat[stat.ST_MTIME]
        if age < self.inflight :
           self.logger.debug("%d vs (inflight setting) %d seconds. Too New!" % (age,self.inflight) )
           return False

        return True

    # =============
    # path renamed
    # =============

    def path_renamed(self,path):

        newname = path

        # rename path given with no filename

        if self.rename :
           newname = self.rename
           if self.rename[-1] == os.sep :
              newname += os.path.basename(path)

        # strip 'N' heading directories

        if self.strip > 0:
           strip = self.strip
           if path[0] == '/' : strip = strip + 1
           # if we strip too much... keep the filename
           try :   token   = token[strip:]
           except: token   = [os.path.basename(path)]
           newname = os.sep+os.sep.join(token)

        if newname == path : return None

        return newname

    # =============
    # path rejected
    # =============

    def path_rejected(self,path):

        if self.masks == [] : return False

        self.logger.debug("path_accepted %s" % path )

        self.post_relpath = path
        if self.post_base_dir : self.post_relpath = path.replace(self.post_base_dir, '')

        urlstr = self.post_base_url + '/' + self.post_relpath
        
        if not self.isMatchingPattern(urlstr,self.accept_unmatch) :
           self.logger.debug("%s Rejected by accept/reject options" % urlstr )
           return True

        return False

    # =============
    # post_delete
    # =============

    def post_delete(self, path, key=None, value=None):
        self.logger.debug("post_delete %s (%s,%s)" % (path,key,value) )

        # sumstr
        hash   = sha512()
        hash.update(bytes(os.path.basename(path), encoding='utf-8'))
        sumstr = 'R,%s' % hash.hexdigest()

        # partstr
        partstr = None

        # caching
        if self.caching :
           new_post = self.cache.check(str(sumstr),path,partstr)
           self.cache.delete_path(path)  # dont keep delete in cache
           if not new_post :
              self.logger.debug("already posted as deleted %s %s"%(path,sumstr))
              return True

        # completing headers

        self.msg.headers['sum'] = sumstr

        # used when moving a file

        if key != None : self.msg.headers['key'] = value

        # post message

        ok = self.__on_post__()

        return ok

    # =============
    # post_file
    # =============

    def post_file(self, path, lstat, key=None, value=None):
        self.logger.debug("post_file %s" % path )

        # check if it is a part file

        if path.endswith('.'+self.msg.part_ext):
           return self.post_file_part(path,lstat)

        # check the value of blocksize

        fsiz  = lstat[stat.ST_SIZE]
        blksz = self.set_blocksize(self.blocksize,fsiz)

        # if we should send the file in parts

        if blksz > 0 and blksz < fsiz :
           return self.post_file_in_parts(path,lstat)

        # partstr

        partstr = '1,%d,1,0,0' % fsiz

        # sumstr

        if self.sumflg[:2] == 'z,' and len(self.sumflg) > 2 :
           sumstr = self.sumflg

        else:

           self.set_sumalgo(self.sumflg)
           sumalgo = self.sumalgo
           sumalgo.set_path(path)

           # compute checksum

           if self.sumflg in ['d','s'] :

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
           sumstr   = '%s,%s' % (self.sumflg,checksum)

        # caching

        if self.caching :
           new_post = self.cache.check(str(sumstr),self.post_relpath,partstr)
           if new_post : self.logger.info("caching %s"% path)
           else        : return False

        # complete  message

        self.msg.headers['parts'] = partstr
        self.msg.headers['sum']   = sumstr

        # used when moving a file

        if key != None : self.msg.headers['key'] = value

        # post message

        ok = self.__on_post__()

        return ok

    # =============
    # post_file_in_parts
    # =============

    def post_file_in_parts(self, path, lstat):
        self.logger.debug("post_file_in_parts %s" % path )

        # check the value of blocksize

        fsiz      = lstat[stat.ST_SIZE]
        chunksize = self.set_blocksize(self.blocksize,fsiz)

        # count blocks and remainder

        block_count = int(fsiz/chunksize)
        remainder   =     fsiz%chunksize
        if remainder > 0 : block_count = block_count + 1

        # info setup

        if self.sumflg[:2] == 'z,' :
           sumstr = self.sumflg

        else:
           self.set_sumalgo(self.sumflg)
           sumalgo = self.sumalgo
           sumalgo.set_path(path)

        # loop on chunks

        i = 0
        while i < block_count :
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
                 if new_post : self.logger.info("caching %s (%s)"% (path,partstr) )
                 else        : continue

              # complete  message

              self.msg.headers['parts'] = partstr
              self.msg.headers['sum']   = sumstr

              # post message

              ok = self.__on_post__()

        return True

    # =============
    # post_file_part
    # =============

    def post_file_part(self, path, lstat):
        self.logger.debug("post_file_part %s" % path )

        # verify suffix

        ok,log_msg,suffix,partstr,sumstr = self.msg.verify_part_suffix(path)

        # something went wrong

        if not ok:
           self.logger.error("file part extension but %s for file %s" % (log_msg,path))
           return False

        # check rename see if it has the right part suffix (if present)

        if 'rename' in self.msg.headers and not suffix in self.msg.headers['rename']:
           self.msg.headers['rename'] += suffix

        # caching

        if self.caching :
           new_post = self.cache.check(str(sumstr),path,partstr)
           if new_post : self.logger.info("caching %s"% path)
           else        : return False

        # complete  message

        self.msg.headers['parts'] = partstr
        self.msg.headers['sum']   = sumstr

        # post message

        ok = self.__on_post__()

        return ok

    # =============
    # post_init
    # =============

    def post_init(self, path, lstat=None, key=None, value=None):

        # relpath
        self.post_relpath = path
        if self.post_base_dir :
           self.post_relpath = path.replace(self.post_base_dir, '')

        # exchange
        self.msg.exchange = self.post_exchange

        # topic
        self.msg.set_topic(self.topic_prefix,self.post_relpath)
        if self.subtopic: self.msg.set_topic_usr(self.topic_prefix,self.subtopic)

        # notice
        self.msg.set_notice(self.post_base_url,self.post_relpath)

        # rename
        rename = self.path_renamed(self.post_relpath)

        # headers

        self.msg.headers = {}

        self.msg.trim_headers()

        if self.to_clusters != None : self.msg.headers['to_clusters']  = self.to_clusters
        if self.cluster     != None : self.msg.headers['from_cluster'] = self.cluster
        if self.source      != None : self.msg.headers['source']       = self.source
        if rename           != None : self.msg.headers['rename']       = rename
        if key              != None : self.msg.headers[key]            = value

        if lstat == None : return

        self.msg.headers['mtime'] = timeflt2str(lstat.st_mtime)
        self.msg.headers['atime'] = timeflt2str(lstat.st_atime)
        self.msg.headers['mode']  = "%o" % ( lstat[stat.ST_MODE] & 0o7777 )

    # =============
    # post_link
    # =============

    def post_link(self, path, key=None, value=None ):
        self.logger.debug("post_link %s" % path )

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
           new_post = self.cache.check(str(sumstr),path,partstr)
           self.cache.delete_path(path)  # dont keep link in cache
           if not new_post :
              self.logger.debug("already posted as a link %s %s"%(path,sumstr))
              return True

        # complete headers

        self.msg.headers['link'] = link
        self.msg.headers['sum']  = sumstr

        # used when moving a file

        if key != None : self.msg.headers['key'] = value

        # post message

        ok = self.__on_post__()

        return ok

    # =============
    # post_move
    # =============

    def post_move(self, src, dst ):
        self.logger.debug("post_move %s %s" % (src,dst) )

        if not os.path.isdir(dst) :
           ok = self.post_delete(src, 'newname', dst)
           if os.path.isfile(dst) : self.post_file  (dst, os.stat(dst), 'oldname', src)
           if os.path.islink(dst) : self.post_link  (dst, os.stat(dst), 'oldname', src)
           return True

        self.walk_move(src,dst)

        return True

    # =============
    # post1file
    # =============

    def post1file(self,path,lstat):

        done = True

        # watchdog funny ./ added at end of directory path ... removed

        path = path.replace(os.sep + '.' + os.sep, os.sep )

        # accept this file

        if self.path_rejected (path): return False

        # path deleted

        if lstat == None :
           self.post_init(path,lstat)
           ok = self.post_delete(path)
           return True

        # path is a link

        if os.path.islink(path):
           self.post_init(path,lstat)
           ok = self.post_link(path)

           if self.follow_symlinks :
              link  = os.readlink(path)
              try   : rpath = os.path.realpath(link)
              except: return done

              if os.path.exists(rpath):
                 ok = self.post1file(rpath,os.stat(rpath))

           return done

        # path is a file

        if os.path.isfile(path):
           self.post_init(path,lstat)
           ok = self.post_file(path,lstat)
           return done

        # at this point it is a directory

        self.walk(path)

        return done

    # =============
    # post1move
    # =============

    def post1move(self, src, dst ):
        self.logger.debug("post1move %s %s" % (src,dst) )

        self.move_dir_lst = []

        ok = self.post_move(src,dst)

        for tup in self.move_dir_lst :
            src, dst = tup
            ok = self.post_delete(src, 'newname', dst)

        return True

    # =============
    # process event
    # =============

    def process_event(self, event, src, dst ):

        self.logger.debug("process_event %s %s %s " % (event,src,dst) )

        done  = True
        later = False

        # lstat if src

        try   : lstat = os.stat(src)
        except: lstat = None

        # create or modify

        if event in [ 'create', 'modify'] :
           if not os.path.exists(src):       return done
           if self.path_inflight(src,lstat): return later
           ok = self.post1file(src,lstat)

        # delete

        if event == 'delete' :
           ok = self.post1file(src,lstat)

        # move

        if event == 'move' :
           ok = self.post1move(src,dst)

        return done

    # =============
    # set_blocksize ... directly from c code
    # =============

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


    # =============
    # wakeup
    # =============

    def wakeup(self):
        self.logger.debug("wakeup")

        # FIXME: Tiny potential for events to be dropped during copy.
        #     these lists might need to be replaced with watchdog event queues.
        #     left for later work. PS-20170105
        #     more details: https://github.com/gorakhargosh/watchdog/issues/392

        # heartbeat

        self.heartbeat_check()

        # on_watch 

        ok = self.__on_watch__()
        if not ok : return

        # pile up left events to process

        self.left_events.extend(self.new_events)
        self.new_events = []

        # work with a copy events and keep done events (to delete them)

        self.done_events = []
        self.cur_events  = []
        self.cur_events.extend(self.left_events)

        # nothing to do

        if len(self.cur_events) <= 0: return

        # loop on all events

        for idx,tup in enumerate(self.cur_events):

            event, src, dst = tup
            done = self.process_event( event, src, dst )
            if done : self.done_events += [idx] 

        # loop on reverse done events

        self.done_events.reverse()
        for idx in self.done_events:
            del self.left_events[idx]

    # =============
    # walk
    # =============

    def walk(self, src ):
        self.logger.debug("walk %s" % src )

        # how to proceed with symlink

        if os.path.islink(src) and self.realpath :
           src = os.path.realpath(src)

        # walk src directory

        for x in os.listdir(src):
            path = src + os.sep + x
            if os.path.isdir(path):
               self.walk(path)
               continue

            # add path created
            self.post1file(path,os.stat(path))

    # =============
    # walk_move
    # =============

    def walk_move(self, src, dst):
        self.logger.debug("walk_move %s %s" % (src,dst) )

        # how to proceed with symlink

        if os.path.islink(dst) and self.realpath :
           dst = os.path.realpath(dst)

        self.move_dir_lst.append( (src,dst) )

        # walk destination dir 

        for x in os.listdir(dst):

            dst_x = dst + os.sep + x
            src_x = src + os.sep + x

            if os.path.isdir(dst_x):
               self.walk_move(src_x,dst_x)
               continue

            ok = self.post_move(src_x,dst_x)

    # =============
    # original walk_priming
    # =============

    def walk_priming(self,p):
        """
         Find all the subdirectories of the given path, start watches on them. 
         deal with symbolically linked directories correctly
        """
        if os.path.islink(p):
            realp = os.path.realpath(p)
            self.logger.info("sr_watch %s is a link to directory %s" % ( p, realp) )
            if self.realpath:
                d=realp
            else:
                d=p + os.sep + '.'
        else:
            d=p

        fs = os.stat(d)
        dir_dev_id = '%s,%s' % ( fs.st_dev, fs.st_ino )
        if dir_dev_id in self.inl:
              return True

        if os.access( d , os.R_OK|os.X_OK ): 
           try:
               ow = self.observer.schedule(self.watch_handler, d, recursive=True )
               self.obs_watched.append(ow)
               self.inl[dir_dev_id] = (ow,d)
               self.logger.info("sr_watch priming watch (instance=%d) scheduled for: %s " % (len(self.obs_watched), d))
           except:
               self.logger.warning("sr_watch priming watch: %s failed, deferred." % d)

               # add path created
               tup  = ( p, 'create', None )
               self.new_events.append( tup )
               return True

        else:
            self.logger.warning("sr_watch could not schedule priming watch of: %s (EPERM) deferred." % d)

            # add path created
            tup  = ( p, 'create', None )
            self.new_events.append( tup )
            return True

        return True

    # =============
    # watch_dir
    # =============

    def watch_dir(self, sld ):
        self.logger.debug("watch_setup %s" % sld )

        if self.force_polling :
           self.logger.info("sr_watch polling observer overriding default (slower but more reliable.)")
           self.observer = PollingObserver()
        else:
           self.logger.info("sr_watch optimal observer for platform selected (best when it works).")
           self.observer = Observer()

        self.obs_watched = []

        self.watch_handler  = SimpleEventHandler(self)
        self.walk_priming(sld)

        self.logger.info("sr_watch priming walk done, but not yet active. Starting...")
        self.observer.start()
        self.logger.info("sr_watch now active on %s posting to exchange: %s"%(sld,self.post_exchange))


    # =============
    # watch_loop
    # =============

    def watch_loop(self ):
        self.logger.debug("watch_loop")

        last_time = time.time()
        while True:
             self.wakeup()
             now = time.time()
             elapse = now - last_time
             if elapse < self.sleep : time.sleep(self.sleep-elapse)
             last_time = now

        self.observer.join()


    # ==================================================
    # FIXME in 2018?  get rid of code from HERE TOP

    def temporary_stuff(self):

        # enforcing post_broker

        if self.post_broker == None :
           if self.broker   != None :
              self.post_broker = self.broker
              self.logger.warning("use post_broker to set broker")

        # enforcing post_exchange

        if self.post_exchange == None :
           if self.exchange   != None :
              self.post_exchange = self.exchange
              self.logger.warning("use post_exchange to set exchange")

        # verify post_base_dir

        if self.post_base_dir == None :
           if self.post_document_root != None :
              self.post_base_dir = self.post_document_root
              self.logger.warning("use post_base_dir instead of post_document_root")
           elif self.document_root != None :
              self.post_base_dir = self.document_root
              self.logger.warning("use post_base_dir instead of document_root")

        # faking having a subclass poster from which post is called

        addmodule = namedtuple('AddModule', ['post'])
        self.poster = addmodule(self.post_url)

        if self.poster.post == self.post_url :
           self.logger.debug("MY POSTER TRICK DID WORK !!!")

    def post_url(self,post_exchange,url,to_clusters,\
                      partstr=None,sumstr=None,rename=None,filename=None, \
                      mtime=None,atime=None,mode=None,link=None):

        self.logger.warning("instead of using self.poster.post(post_exchange,url... use self.post(post_exchange,post_base_url,post_relpath...")

        post_relpath  = url.path
        urlstr        = url.geturl()
        post_base_url = urlstr.replace(post_relpath,'')

        # apply accept/reject
        if not self.isMatchingPattern(urlstr,self.accept_unmatch) :
           self.logger.debug("post of %s Rejected by accept/reject options" % urlstr )
           return True  # need to return true because this isn´t a failure.

        # if caching is enabled make sure it was not already posted

        if self.caching :
           new_post = self.cache.check(str(sumstr),post_relpath,partstr)
           if new_post :

              # delete
              if sumstr.startswith('R,'):
                 self.cache.delete_path(post_relpath)

              # link - never store them, message contains whole payload.
              elif sumstr.startswith('L,'):
                 self.cache.delete_path(post_relpath)

              else:
                 self.logger.info("caching %s"% post_relpath )

           # modified, or repost
           else:
                self.logger.debug("skipped already posted %s %s %s" % (post_relpath,partstr,sumstr))
                return True
                 
        # set message exchange
        self.msg.exchange = post_exchange
        
        # set message topic
        self.msg.set_topic(self.topic_prefix,post_relpath)
        if self.subtopic != None :
           self.msg.set_topic_usr(self.topic_prefix,self.subtopic)

        # set message notice
        self.msg.set_notice(post_base_url,post_relpath)

        # set message headers
        self.msg.headers = {}

        self.msg.headers['to_clusters'] = to_clusters

        if partstr  != None : self.msg.headers['parts']        = partstr
        if sumstr   != None : self.msg.headers['sum']          = sumstr
        if rename   != None : self.msg.headers['rename']       = rename
        if mtime    != None : self.msg.headers['mtime']        = mtime
        if atime    != None : self.msg.headers['atime']        = atime
        if mode     != None : self.msg.headers['mode']         = "%o" % ( mode & 0o7777 )
        if link     != None : self.msg.headers['link']         = link

        if self.cluster != None : self.msg.headers['from_cluster']    = self.cluster
        if self.source  != None : self.msg.headers['source']          = self.source

        self.msg.trim_headers()

        ok = self.__on_post__()

        return ok

    # FIXME in 2018?  get rid of code to HERE BOTTOM
    # ==================================================


    # =============
    # run
    # =============
      
    def run(self):
            self.logger.info("%s run partflg=%s, sum=%s, caching=%s " % \
                  ( self.program_name, self.partflg, self.sumflg, self.caching ))
            self.logger.info("%s realpath=%s follow_links=%s force_polling=%s"  % \
                  ( self.program_name, self.realpath, self.follow_symlinks, self.force_polling ) )

            self.connect()

            if self.sleep > 0 : 
                   for d in self.postpath :
                       self.watch_dir(d)
                   self.watch_loop()
            else:
                   for d in self.postpath :
                       self.post1file(d)

    def reload(self):
        self.logger.info("%s reload" % self.program_name )
        self.close()
        self.configure()
        self.run()

    def start(self):
        self.logger.info("%s %s start" % (self.program_name, sarra.__version__) )
        self.run()

    def stop(self):
        self.logger.info("%s stop" % self.program_name)
        self.close()
        os._exit(0)

    def cleanup(self):
        self.logger.info("%s %s cleanup" % (self.program_name,self.config_name))

        if self.post_broker :
           self.post_hc = HostConnect( logger = self.logger )
           self.post_hc.set_pika( self.use_pika )
           self.post_hc.set_url( self.post_broker )
           self.post_hc.connect()
           self.declare_exchanges(cleanup=True)

        # caching

        if self.caching :
           self.cache.close(unlink=True)
           self.cache = None

        self.close()

    def declare(self):
        self.logger.info("%s %s declare" % (self.program_name,self.config_name))

        # on posting host
        if self.post_broker :
           self.post_hc = HostConnect( logger = self.logger )
           self.post_hc.set_pika( self.use_pika )
           self.post_hc.set_url( self.post_broker )
           self.post_hc.connect()
           self.declare_exchanges()

        self.close()

    def declare_exchanges(self, cleanup=False):

        # restore_queue mode has no post_exchange 

        if not self.post_exchange : return

        # define post exchange (splitted ?)

        exchanges = []

        if self.post_exchange_split != 0 :
           for n in list(range(self.post_exchange_split)) :
               exchanges.append(self.post_exchange + "%02d" % n )
        else :
               exchanges.append(self.post_exchange)

        # do exchanges
              
        for x in exchanges :
            if cleanup: self.post_hc.exchange_delete(x)
            else      : self.post_hc.exchange_declare(x)


    def setup(self):
        self.logger.info("%s %s setup" % (self.program_name,self.config_name))

        # on posting host
        if self.post_broker :
           self.post_hc = HostConnect( logger = self.logger )
           self.post_hc.set_pika( self.use_pika )
           self.post_hc.set_url( self.post_broker )
           self.post_hc.connect()
           self.declare_exchanges()

        if self.caching :
           self.cache = sr_cache(self)
           self.cache.open()

        self.close()
                 
# ===================================
# MAIN
# ===================================

def main():

    args,action,config,old = startup_args(sys.argv)

    post = sr_post(config,args,action)
    post.exec_action(action,old)

    os._exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
