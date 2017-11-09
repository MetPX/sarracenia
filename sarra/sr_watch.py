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
# sr_watch.py : python3 program allowing users to watch a directory or a file and
#               emit a sarracenia amqp message when the file is created,modified or deleted
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Daluma Sen     - Shared Services Canada
#  Peter  Silva   - Shared Services Canada
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
# sr_watch [options] [config] [foreground|start|stop|restart|reload|status|cleanup|setup]
#
# sr_watch watch a file or a directory. When event occurs on file, sr_watch connects
# to a broker and an amqp message is sent...
#
# conditions:
#
# (messaging)
# post_broker             = where the message is announced
# post_exchange           = xs_source_user
# subtopic                = default to the path of the URL with '/' replaced by '.'
# topic_prefix            = v02.post
# post_base_dir           = the root directory from which the url path is exposed
# post_base_url           = taken from the destination
# sum                     = 0   no sum computed... if we dont download the product
#                           x   if we download the product
# rename                  = which path under root, the file should appear
# to                      = message.headers['to_clusters'] MANDATORY
#
#============================================================

import os, sys, time, shelve, psutil

from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import PatternMatchingEventHandler

try :    
         from sr_instances       import *
         from sr_post            import *
         from sr_util            import *
except : 
         from sarra.sr_instances import *
         from sarra.sr_post      import *
         from sarra.sr_util      import *

inl = {}
pol = {}

class sr_watch(sr_instances):

    def __init__(self,config=None,args=None,action=None):
        sr_instances.__init__(self,config,args,action)
        self.recursive      = True
        self.last_heartbeat = time.time()

    def close(self):
        self.post.close()
        for ow in self.obs_watched:
            self.observer.unschedule(ow)
        self.observer.stop()

    def overwrite_defaults(self):

        self.blocksize = 200 * 1024 * 1024
        self.caching   = True
        self.sleep     = 0.1
        #self.inflight  = 1.0
        
        
    def check(self):

        if self.config_name == None : return

        self.nbr_instances  = 1
        self.accept_unmatch = True

        self.post = sr_post(self.user_config,self.user_args)
        self.post.program_name = 'sr_watch'
        self.post.logger       = self.logger
        self.watch_path        = self.post.watchpath()
        self.post.blocksize    = self.blocksize
        self.post.partflg      = self.partflg
        self.post.sumflg       = self.sumflg
        self.post.caching      = self.caching
        self.post.watch_path   = self.watch_path
        self.post.realpath     = self.realpath
        self.post.follow_symlinks = self.follow_symlinks
        self.post.force_polling   = self.force_polling
        self.post.check()

        if self.reset :
           self.post.cache.close(unlink=True)
           self.post.setup()
           os._exit(0)

    def check_heartbeat(self):
        now    = time.time()
        elapse = now - self.last_heartbeat
        if elapse > self.heartbeat :
           self.__on_heartbeat__()
           self.last_heartbeat = now

    def __on_heartbeat__(self):
        self.logger.debug("__on_heartbeat__")

        # invoke on_hearbeat when provided
        for plugin in self.on_heartbeat_list:
           if not plugin(self): return False

        return True

    # =============
    # __on_watch__
    # =============

    def __on_watch__(self):
 
        # invoke user defined on_message when provided

        for plugin in self.on_watch_list:
           if not plugin(self): return False

        return True

    def priming_walk(self,p):
        """
         Find all the subdirectories of the given path, start watches on them. 
         deal with symbolically linked directories correctly
        """
        global inl,pol

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
        if dir_dev_id in inl:
              return True

        if os.access( d , os.R_OK|os.X_OK ): 
           try:
               ow = self.observer.schedule(self.myeventhandler, d, recursive=self.recursive )
               self.obs_watched.append(ow)
               inl[dir_dev_id] = (ow,d)
               pol[d] = ow
               self.logger.info("sr_watch priming watch (instance=%d) scheduled for: %s " % (len(self.obs_watched), d))
           except:
               self.logger.warning("sr_watch priming watch: %s failed, deferred." % d)
               self.myeventhandler.event_post(p,'create') # get it done later.
               return True

        else:
            self.logger.warning("sr_watch could not schedule priming watch of: %s (EPERM) deferred." % d)
            self.myeventhandler.event_post(p,'create') # get it done later.
            return True

        #if not self.recursive:
        #   return True

        #l=[]
        #for i in os.listdir(d):

        #   if self.realpath:
        #       f = d + os.sep + i
        #   else:
        #       f = p + os.sep + i

        #   if os.path.isdir(f):
        #       self.priming_walk(f)

         
        return True
      
    def event_handler(self,meh):
        self.myeventhandler = meh

    def help(self):
        self.post.help()

    def run(self):
            self.post.logger = self.logger
            self.logger.info("sr_watch run partflg=%s, sum=%s, caching=%s " % \
                  ( self.partflg, self.sumflg, self.caching ))
            self.logger.info("sr_watch realpath=%s follow_links=%s force_polling=%s"  % \
                  ( self.post.realpath, self.follow_symlinks, self.force_polling ) )
            self.post.connect()

            # amqp resources
            self.post.declare_exchanges()

            if self.post.realpath: 
               sld = os.path.realpath( self.watch_path )
            else:
               sld = self.watch_path 

            self.myeventhandler.set_logger(self.logger)

            if self.post.force_polling :
                self.logger.info("sr_watch polling observer overriding default (slower but more reliable.)")
                self.observer = PollingObserver()
            else:
                self.logger.info("sr_watch optimal observer for platform selected (best when it works).")
                self.observer = Observer()

            self.obs_watched = []

            self.priming_walk(sld)

            self.logger.info("sr_watch priming walk done, but not yet active. Starting...")
            self.observer.start()
            self.logger.info("sr_watch now active on %s posting to exchange: %s " % (self.watch_path, self.post.exchange))

            # do periodic events (at most, once every 'sleep' seconds)
            while True:
               start_sleep_event = time.time()
               self.check_heartbeat()
               ok = self.__on_watch__()
               if ok : self.myeventhandler.event_wakeup()
               end_sleep_event = time.time()
               how_long = self.sleep - ( end_sleep_event - start_sleep_event )
               if how_long > 0:
                  time.sleep(how_long)

        #except OSError as err:
        #    self.logger.error("Unable to start Observer: %s" % str(err))
        #    os._exit(0)


            self.observer.join()

    def reload(self):
        self.logger.info("%s reload" % self.program_name)
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
        self.post.cleanup()

    def declare(self):
        self.post.declare()

    def setup(self):
        self.post.setup()

# ===================================
# GLOBAL
# ===================================


# ===================================
# MAIN
# ===================================

def main():

    args,action,config,old = startup_args(sys.argv)

    watch = sr_watch(config,args,action)

    if old :
       watch.logger.warning("Should invoke : %s [args] action config" % sys.argv[0])

    if action in ['add','disable', 'edit', 'enable', 'list',    'log',    'remove' ] :
       watch.exec_action(action,old)
       os._exit(0)


    # =========================================
    # setup watchdog
    # =========================================
    
    class MyEventHandler(PatternMatchingEventHandler):
        ignore_patterns = ["*.tmp"]

        def __init__(self):
            super().__init__()
            self.new_events = []
            self.events_outstanding = []
            try: 
                watch.inflight = int(watch.inflight)
            except:
                pass

        def set_logger(self,logger):
            self.logger = logger

        def dont_watch(self,path):
            global inl,pol

            self.logger.info("turning watch down for path %s" % path)
            if not path in pol : self.logger.info("could not")
            if not path in pol : return

            self.logger.info("doing it")
            ow = pol[path]
            self.observer.remove_handler_for_watch(self.myeventhandler, ow)
            self.observer.unschedule(ow)
            del pol[path]

        def post_recursive_move(self,f,e,k,v):
            self.logger.debug("post_recursive_move %s of %s (%s,%s) " % (e, f, k,v) )

            for x in os.listdir(v):
                dst = v+os.sep+x
                src = f+os.sep+x
                sok = src.replace( os.sep + '.' + os.sep, os.sep)
                if os.path.isdir(dst):
                   self.moving_dir.append((sok,e,k,dst))
                   self.post_recursive_move(sok,e,k,dst)
                   continue

                #self.dont_watch(sok)

                self.do_post(sok, e, k, dst)

        def event_wakeup(self):

            # FIXME: Tiny potential for events to be dropped during copy.
            #     these lists might need to be replaced with watchdog event queues.
            #     left for later work. PS-20170105
            #     more details: https://github.com/gorakhargosh/watchdog/issues/392
            watch.check_heartbeat()

            self.events_outstanding.extend(self.new_events)
            self.new_events=[]

            cur_events=[]
            cur_events.extend(self.events_outstanding)

            if len(cur_events) > 0:
               done=[]
               for idx,t in enumerate(cur_events):

                   f, e, k, v = t

                   self.logger.debug("event_wakeup looking at %s of %s (%s,%s) " % (e, f, k,v) )
                   # waiting for file to be unmodified for 'inflight' seconds...
                   if e not in [ 'delete', '*move*' ] and isinstance(watch.inflight,int):  
                      # sometime the file vanished at this point... if so skip it
                      try   : age = time.time() - os.stat(f)[stat.ST_MTIME] 
                      except: 
                              done += [ idx ]
                              continue
                      if age < watch.inflight :
                          self.logger.debug("event_wakeup: %d vs. (inflight setting) %d seconds old. Too New!" % ( age, watch.inflight) )
                          continue

                   #directory creation. Make failures a soft error that is retried.

                   check_dir = f
                   if e == '*move*' : check_dir = v
                   
                   if os.path.isdir(check_dir):
                        self.logger.debug("dir event_wakeup %s of %s (%s,%s)" % (e, f, k, v) )
                        if e == '*move*' :
                           fok = f.replace( os.sep + '.' + os.sep, os.sep)
                           # specify v... to turn off f
                           #self.dont_watch(fok)
                           self.do_post(fok, e, k, v)
                           done += [ idx ]
                           self.moving_dir = []
                           self.post_recursive_move(f,e,k,v)
                           # at the end of posting all moved files,
                           # old directories should announced their removal
                           # reverse list to have lower subdirs first
                           self.moving_dir.reverse()
                           for mt in self.moving_dir :
                               mf, me, mk, mv = mt
                               #self.dont_watch(mf)
                               self.do_post(mf, me, mk, mv)

                        if watch.recursive: 
                            p = check_dir
                            if os.path.islink(check_dir): 
                                if watch.post.realpath: p=os.path.realpath(check_dir)
                                else: p=check_dir+os.sep+'.'
                       
                            self.logger.info("set priming_walk on %s" % p )
                            watch.priming_walk(p)

                        continue

                   # MG link would not work without this line
                   if e in ['create', 'modify'] and os.path.islink(f) : e = 'link'

                   if (e not in [ 'create', 'modify'] ) or os.access(f, os.R_OK):
                       self.logger.debug("event_wakeup calling do_post ! " )
                       self.do_post(f.replace( os.sep + '.' + os.sep, os.sep), e, k, v)
                       done += [ idx ]

                   # MG skipped events will never get processed... get rid of them
                   else:
                       self.logger.debug("event_wakeup SKIPPING %s of %s (%s,%s)" % (e, f, k, v) )
                       done += [ idx ]

               self.logger.debug("event_wakeup done: %s " % done )
               done.reverse()
               for idx in done:
                   del self.events_outstanding[idx]

            #self.logger.debug("event_wakeup left over: %s " % self.events_outstanding )


        def event_post(self, path, tag, key=None, value=None):
            # FIXME: as per tiny potential, this routine should likely queue events.
            # that is why have not replaced this function by direct assignment in callers.
            self.new_events.append((path,tag,key,value))
        
        def do_post(self, path, tag, key, value):
            try:
                # tag *move* triggers 2 events that represent a move in 2 different ways
                # the hope is that one of the two at least will go through and get done if necessary
                if tag == '*move*' :
                   watch.post.watching(path,  'delete', 'newname', value)
                   if os.path.isdir(value) : return
                   watch.post.watching(value, 'modify', 'oldname', path)
                # other regular event tags
                else :
                   watch.post.watching(path, tag, key, value)
            except PermissionError as err:
                self.outstanding_events[path] = (tag,key,value)
                self.logger.error(str(err))

        def on_created(self, event):
            # need to us test, rather than event to so symlinked directories get added.
            if not os.path.isdir(event.src_path):
                self.event_post(event.src_path, 'create')
            elif watch.recursive:
                if os.path.islink(event.src_path): 
                    if watch.post.realpath: p=os.path.realpath(event.src_path)
                    else: p=event.src_path+os.sep+'.'
                else: p=event.src_path
                watch.priming_walk(p)

 
        def on_deleted(self, event):
            if event.src_path == watch.watch_path:
                watch.stop_touch()
                self.logger.error('Exiting!')
                os._exit(0)
            self.event_post(event.src_path, 'delete')
    
        def on_modified(self, event):
            if (not event.is_directory):
                self.event_post(event.src_path, 'modify')

        # special move event_post tag *move*
        def on_moved(self, event):
            #if (not event.is_directory):
            #   self.event_post(event.src_path, '*move*', 'newname', event.dest_path)
            #self.logger.debug("MOVE dir event %s %s %s %s" % (event.src_path, '*move*', 'newname', event.dest_path))
            self.event_post(event.src_path, '*move*', 'newname', event.dest_path)

    watch.event_handler(MyEventHandler())

    watch.exec_action(action,old)

    os._exit(0)


# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
