#!/usr/bin/python3

import os, signal, sys, time

import asyncore 
import pyinotify 

try :    from dd_post      import *
except : from sara.dd_post import *

# ===================================
# MAIN
# ===================================

def help(logger):
    logger.info("Usage: dd_watch [-c configfile] [-r] [-bz blocksize] [-t tag] [-f flags] [-bd basedir] -s <source-url> -b <broker-url> -d destination")
    logger.info("default blocksize 0")
    logger.info("default tag ''")

def main():

    LOG_FORMAT = ('%(asctime)s [%(levelname)s] %(message)s')
    logger     = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    post = dd_post(logger,config=None,args=sys.argv)

# =========================================
# interrupt
# =========================================

    def signal_handler(signal, frame):
        print('Stop!')
        post.close()
        sys.exit()

    signal.signal(signal.SIGINT, signal_handler)

# =========================================
# setup the async inotifier
# =========================================

    class EventHandler(pyinotify.ProcessEvent):
      def process_IN_CLOSE_WRITE(self,event):
          post.watching(event.pathname)

    wm  = pyinotify.WatchManager()
    notifier = pyinotify.AsyncNotifier(wm,EventHandler())

    post.connect()

    wdd = wm.add_watch(post.watch_dir, pyinotify.IN_CLOSE_WRITE, rec=True)

#   watch loop

    asyncore.loop()

#   stop
    post.close()
    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
