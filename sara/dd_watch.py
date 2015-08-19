#!/usr/bin/python3

import os, signal, sys, time

import asyncore 
import pyinotify 

try :    from dd_post      import *
except : from sara.dd_post import *

# ===================================
# MAIN
# ===================================

post = dd_post(config=None,args=sys.argv[1:])

def main():

    # =========================================
    # posting and watch_path ready
    # =========================================

    post.configure()
    post.connect()

    watch_path = post.watchpath()

    # =========================================
    # setup pyinotify watching
    # =========================================

    class EventHandler(pyinotify.ProcessEvent):
          def process_IN_CLOSE_WRITE(self,event):
              post.watching(event.pathname)

    wm         = pyinotify.WatchManager()
    notifier   = pyinotify.AsyncNotifier(wm,EventHandler())
    wdd        = wm.add_watch(watch_path, pyinotify.IN_CLOSE_WRITE, rec=True)

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

    asyncore.loop()
    post.close()

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
