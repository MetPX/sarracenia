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
# sr_watch.py : python3 program allowing users to watch a directory or a file and
#               emit a sarracenia amqp message when the file is created,modified or deleted
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Daluma Sen     - Shared Services Canada
#  Last Changed   : Feb 29 11:25:05 EST 2016
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

from watchdog.observers.polling import PollingObserverVFS
from watchdog.events import PatternMatchingEventHandler

try :    
         from sr_instances       import *
         from sr_post            import *
except : 
         from sarra.sr_instances import *
         from sarra.sr_post      import *

class sr_watch(sr_instances):

    def __init__(self,config=None,args=None):
        self.post = sr_post(config,args)
        sr_instances.__init__(self,config,args)

    def close(self):
        self.post.close()
        self.observer.unschedule(self.obs_watched)
        self.observer.stop()

    def overwrite_defaults(self):
        self.blocksize = 200 * 1024 * 1024
        self.caching   = True
        self.sleep     = 5
        
    def check(self):
        self.nbr_instances  = 1
        self.accept_unmatch = True
        self.post.configure()
        self.watch_path        = self.post.watchpath()
        self.post.logger       = self.logger
        self.post.program_name = 'sr_watch'
        self.post.blocksize    = self.blocksize
        self.post.caching      = self.caching
        self.post.watch_path   = self.watch_path
        self.time_interval     = self.sleep

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

    def event_handler(self,meh):
        self.myeventhandler = meh

    def help(self):
        self.post.help()

    def run(self):
        self.logger.info("sr_watch run")
        self.validate_cache()
        self.post.connect()

        try:
            self.observer = PollingObserverVFS(os.stat, os.listdir, self.time_interval)
            self.obs_watched = self.observer.schedule(self.myeventhandler, self.watch_path, recursive=self.post.recursive)
            self.observer.start()
        except OSError as err:
            self.logger.error("Unable to start Observer: %s" % str(err))
            os._exit(0)

        self.observer.join()

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

    # =========================================
    # instantiate sr_watch
    # =========================================

    watch = sr_watch(config,args)
   
    # =========================================
    # setup watchdog
    # =========================================
    
    class MyEventHandler(PatternMatchingEventHandler):
        ignore_patterns = ["*.tmp"]

        def event_post(self, path, tag):
            try:
                if watch.isMatchingPattern(path, accept_unmatch=True) :
                    watch.post.lock_set()
                    watch.post.watching(path, tag)
                    watch.post.lock_unset()
            except PermissionError as err:
                watch.logger.error(str(err))

        def on_created(self, event):
            if (not event.is_directory):
                self.event_post(event.src_path, 'created')
 
        def on_deleted(self, event):
            if event.src_path == watch.watch_path:
                watch.stop_touch()
                watch.logger.error('Exiting!')
                os._exit(0)
            if (not event.is_directory):
                self.event_post(event.src_path, 'deleted')
    
        def on_modified(self, event):
            if (not event.is_directory):
                self.event_post(event.src_path, 'modified')

        def on_moved(self, event):
            if (not event.is_directory):
               # not so sure about testing accept/reject on src and dst
               # but we dont care for now... it is not supported
               if watch.isMatchingPattern(event.src_path, accept_unmatch=True) and \
                  watch.isMatchingPattern(event.dest_path, accept_unmatch=True) :
                  watch.post.lock_set()
                  watch.post.move(event.src_path,event.dest_path)
                  watch.post.lock_unset()

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
