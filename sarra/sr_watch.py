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
# sr_watch [options] [config] [start|stop|restart|reload|status]
#
# sr_watch watch a file or a directory. When event occurs on file, sr_watch connects
# to a broker and an amqp message is sent...
#
# conditions:
#
# (messaging)
# broker                  = where the message is announced
# exchange                = xs_source_user
# subtopic                = default to the path of the URL with '/' replaced by '.'
# topic_prefix            = v02.post
# document_root           = the root directory from which the url path is exposed
# url                     = taken from the destination
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
except : 
         from sarra.sr_instances import *
         from sarra.sr_post      import *

inl = []



class sr_watch(sr_instances):

    def __init__(self,config=None,args=None):
        self.post = sr_post(config,args)
        sr_instances.__init__(self,config,args)

    def close(self):
        self.post.close()
        for ow in self.obs_watched:
            self.observer.unschedule(ow)
        self.observer.stop()

    def overwrite_defaults(self):

        if self.to_clusters == None:
            self.to_clusters = self.broker.hostname

        self.blocksize = 200 * 1024 * 1024
        self.caching   = True
        self.sleep     = 0.1
        
        
    def check(self):
        self.nbr_instances  = 1
        self.accept_unmatch = True
        self.post.configure()
        self.watch_path        = self.post.watchpath()
        self.post.logger       = self.logger
        self.post.program_name = 'sr_watch'
        self.post.blocksize    = self.blocksize
        self.post.partflg      = self.partflg
        self.post.sumflg       = self.sumflg
        self.post.caching      = self.caching
        self.post.watch_path   = self.watch_path
        self.post.realpath     = self.realpath
        self.post.follow_symlinks = self.follow_symlinks
        self.post.force_polling   = self.force_polling
        if self.reset :
           self.post.connect()
           self.post.poster.cache_reset()

    def validate_cache(self):
        self.cache_file  = self.user_cache_dir
        self.cache_file += '/' + self.watch_path.replace('/','_')
        self.cache_file += '_%d' % self.blocksize
        self.cache = shelve.open(self.cache_file)
        current_pid = os.getpid()
        k_pid = "pid"

        if "pid" in self.cache:
            if not self.cache[k_pid] == current_pid:
                if psutil.pid_exists(self.cache[k_pid]):
                    self.logger.error("Another sr_watch instance with same configuration is already running.")
                    os._exit(1)
                else:
                    self.logger.debug("Reusing cache with pid=%s" % str(current_pid))
                    self.cache["pid"] = current_pid
        else:
            self.logger.debug("Creating new cache with pid=%s" % str(current_pid))
            self.cache["pid"] = current_pid
        self.cache.close()


    def priming_walk(self,p):
        """
         Find all the subdirectories of the given path, start watches on them. 
         deal with symbolically linked directories correctly
        """
        global inl

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
               ow = self.observer.schedule(self.myeventhandler, d, recursive=False)
               self.obs_watched.append(ow)
               inl.append(dir_dev_id)
               self.logger.info("sr_watch priming watch (instance=%d) scheduled for: %s " % (len(self.obs_watched), d))
           except:
               self.logger.warning("sr_watch priming watch: %s failed, deferred." % d)
               self.myeventhandler.event_post(p,'create') # get it done later.
               return True

        else:
            self.logger.warning("sr_watch could not schedule priming watch of: %s (EPERM) deferred." % d)
            self.myeventhandler.event_post(p,'create') # get it done later.
            return True

        if not self.recursive:
           return True

        l=[]
        for i in os.listdir(d):

           if self.realpath:
               f = d + os.sep + i
           else:
               f = p + os.sep + i

           if os.path.isdir(f):
               self.priming_walk(f)

         
        return True
      
    def event_handler(self,meh):
        self.myeventhandler = meh

    def help(self):
        self.post.help()

    def run(self):
            self.post.logger = self.logger
            self.logger.info("sr_watch run partflg=%s, sum=%s, caching=%s recursive=%s " % \
                  ( self.partflg, self.sumflg, self.caching , self.recursive ))
            self.logger.info("sr_watch realpath=%s follow_links=%s force_polling=%s"  % \
                  ( self.post.realpath, self.follow_symlinks, self.force_polling ) )
            self.validate_cache()
            self.post.connect()

            if self.post.realpath: 
               sld = os.path.realpath( self.watch_path )
            else:
               sld = self.watch_path 

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
               self.myeventhandler.event_wakeup()
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


# ===================================
# GLOBAL
# ===================================


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
   

    # =========================================
    # instantiate sr_watch
    # =========================================

    watch = sr_watch(config,args)
   
    # =========================================
    # setup watchdog
    # =========================================
    
    class MyEventHandler(PatternMatchingEventHandler):
        ignore_patterns = ["*.tmp"]

        def __init__(self):
            super().__init__()
            self.new_events = {}
            self.events_outstanding = {}
            try: 
                watch.inflight = int(watch.inflight)
            except:
                pass

        def event_wakeup(self):

            # FIXME: Tiny potential for events to be dropped during copy.
            #     these lists might need to be replaced with watchdog event queues.
            #     left for later work. PS-20170105
            #     more details: https://github.com/gorakhargosh/watchdog/issues/392
            nu = self.new_events.copy()
            self.new_events={}

            self.events_outstanding.update(nu)
            if len(self.events_outstanding) > 0:
               watch.post.lock_set()
               done=[]
               for f in self.events_outstanding:
                   e=self.events_outstanding[f]

                   watch.logger.debug("event_wakeup looking at %s of %s " % (e, f) )
                   # waiting for file to be unmodified for 'inflight' seconds...
                   if e not in [ 'delete' ] and isinstance(watch.inflight,int):  
                      age = time.time() - os.stat(f)[stat.ST_MTIME] 
                      if age < watch.inflight :
                          watch.logger.debug("event_wakeup: %d vs. (inflight setting) %d seconds old. Too New!" % ( age, watch.inflight) )
                          continue

                   #directory creation. Make failures a soft error that is retried.
                   if os.path.isdir(f):
                        if watch.recursive: 
                            if os.path.islink(f): 
                                if watch.post.realpath: p=os.path.realpath(f)
                                else: p=f+os.sep+'.'
                            else: p=f
                       
                            watch.priming_walk(p)

                        continue

                   if (e not in [ 'create', 'modify'] ) or os.access(f, os.R_OK):
                       watch.logger.debug("event_wakeup calling do_post ! " )
                       self.do_post(f.replace( os.sep + '.' + os.sep, os.sep), e)
                       done += [ f ]
                   else:
                       watch.logger.debug("event_wakeup SKIPPING %s of %s " % (e, f) )

               watch.post.lock_unset()
               watch.logger.debug("event_wakeup done: %s " % done )
               for f in done:
                   del self.events_outstanding[f]

            watch.logger.debug("event_wakeup left over: %s " % self.events_outstanding )


        def event_post(self, path, tag):
            # FIXME: as per tiny potential, this routine should likely queue events.
            # that is why have not replaced this function by direct assignment in callers.
            self.new_events[path]=tag
        
        def do_post(self, path, tag):
            try:
                #if watch.isMatchingPattern(path, accept_unmatch=True) :
                watch.post.watching(path, tag)
            except PermissionError as err:
                self.outstanding_events[path] = tag
                watch.logger.error(str(err))

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
                watch.logger.error('Exiting!')
                os._exit(0)
            if (not event.is_directory):
                self.event_post(event.src_path, 'delete')
    
        def on_modified(self, event):
            if (not event.is_directory):
                self.event_post(event.src_path, 'modify')

        def on_moved(self, event):
            if (not event.is_directory):
               # not so sure about testing accept/reject on src and dst
               # but we dont care for now... it is not supported
               #if watch.isMatchingPattern(event.src_path, accept_unmatch=True) and \
               #   watch.isMatchingPattern(event.dest_path, accept_unmatch=True) :
               #Every file rename inside the watch path will trigger new copy
               #watch.post.move(event.src_path,event.dest_path)
               # FIXME: what if dest_path is outside of the tree being watched? what happens?
               self.event_post(event.dest_path, 'modify')

    watch.event_handler(MyEventHandler())

    if   action == 'foreground' : watch.foreground_parent()
    elif action == 'reload'     : watch.reload_parent()
    elif action == 'restart'    : watch.restart_parent()
    elif action == 'start'      : watch.start_parent()
    elif action == 'stop'       : watch.stop_parent()
    elif action == 'status'     : watch.status_parent()
    else :
        watch.logger.error("action unknown %s" % action)
        sys.exit(1)

    sys.exit(0)


# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
