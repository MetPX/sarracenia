#!/usr/bin/python3

import os, signal, sys, time

import asyncore 
import pyinotify 

try :    from dd_post      import *
except : from sara.dd_post import *

# ===================================
# MAIN
# ===================================


def main():

    post = dd_post(config=None,args=sys.argv[1:])
    post.configure()
    post.instantiate()
    post.connect()

    # =========================================
    # watch_path ready
    # =========================================

    watch_path = post.watchpath()
    events     = 0

    d = 'IN_DELETE'       in post.events 
    w = 'IN_CLOSE_WRITE'  in post.events 
    if d and w :
       events = pyinotify.IN_CLOSE_WRITE|pyinotify.IN_DELETE|pyinotify.IN_DELETE_SELF
    elif d :
       events = pyinotify.IN_DELETE|pyinotify.IN_DELETE_SELF
    elif w :
       events = pyinotify.IN_CLOSE_WRITE

    # =========================================
    # setup pyinotify watching
    # =========================================

    wm         = pyinotify.WatchManager()

    class EventHandler(pyinotify.ProcessEvent):
          def process_IN_CLOSE_WRITE(self,event):
              post.watching(event.pathname,'IN_CLOSE_WRITE')
          def process_IN_DELETE(self,event):
              post.watching(event.pathname,'IN_DELETE')
          def process_IN_DELETE_SELF(self,event):
              post.watching(event.pathname,'IN_DELETE')
              post.logger.info("exiting")
              os._exit(0)

    notifier   = pyinotify.AsyncNotifier(wm,EventHandler())
    wdd = wm.add_watch(watch_path, events, rec=True)

    # =========================================
    # signal reload
    # =========================================

    def signal_reload(signal, frame):
        post.logger.info('Reloading!')
        post.close()
        wm.rm_watch( wm.get_wd(watch_path))
        main()

    # =========================================
    # signal stop
    # =========================================

    def signal_stop(signal, frame):
        post.logger.info('Stop!')
        post.close()
        post.stop = True
        sys.exit(0)

    # =========================================
    # signal handling
    # =========================================

    signal.signal(signal.SIGINT, signal_stop)
    signal.signal(signal.SIGHUP, signal_reload)

    # =========================================
    # looping
    # =========================================

    asyncore.loop(100000000)
    post.close()

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
