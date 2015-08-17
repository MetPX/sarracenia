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

    LOG_FORMAT = ('%(asctime)s [%(levelname)s] %(message)s')
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    logger     = logging.getLogger(__name__)

    # =========================================
    # instanciate dd_post and determine watch_path
    # =========================================

    try    :
             post = dd_post(logger,config=None,args=sys.argv[1:])
             if post.ask4help : return

             watch_path = post.source.path

             if post.document_root != None :
                if not post.document_root in watch_path :
                   watch_path = post.document_root + os.sep + watch_path

             if not os.path.exists(watch_path):
                logger.error("Not found %s " % watch_path )
                sys.exit(1)

             if os.path.isfile(watch_path):
                logger.info("Watching file %s " % watch_path )

             if os.path.isdir(watch_path):
                logger.info("Watching directory %s " % watch_path )
    except :
             (stype, value, tb) = sys.exc_info()
             logger.error("Type: %s, Value:%s\n" % (stype, value))
             sys.exit(1)

    # =========================================
    # interrupt
    # =========================================

    def signal_handler(signal, frame):
        logger.info('Stop!')
        post.close()
        post.stop = True
        sys.exit(0)

    # =========================================
    # inotify callback
    # =========================================

    class EventHandler(pyinotify.ProcessEvent):
          def process_IN_CLOSE_WRITE(self,event):
              post.watching(event.pathname)


    # =========================================
    # inotify watch and loop start
    # =========================================

    try :
             post.connect()
             post.stop = False

             signal.signal(signal.SIGINT, signal_handler)

             wm       = pyinotify.WatchManager()
             notifier = pyinotify.AsyncNotifier(wm,EventHandler())
             wdd      = wm.add_watch(watch_path, pyinotify.IN_CLOSE_WRITE, rec=True)

             asyncore.loop()
             post.close()

    except :
             if not post.stop :
                (stype, value, tb) = sys.exc_info()
                logger.error("Type: %s, Value:%s\n" % (stype, value))
                post.help()

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
