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
#  Jun Hu         - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Sep 22 10:41:32 EDT 2015
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

import os, signal, sys, time

import asyncore 
import pyinotify 

try :    from sr_post      import *
except : from sarra.sr_post import *

# ===================================
# MAIN
# ===================================


def main():

    post = sr_post(config=None,args=sys.argv[1:])
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
       events = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_DELETE   | pyinotify.IN_DELETE_SELF \
              | pyinotify.IN_ATTRIB      | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVE_SELF  
    elif d :
       events = pyinotify.IN_DELETE      | pyinotify.IN_DELETE_SELF
    elif w :
       events = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_ATTRIB    \
              | pyinotify.IN_MOVED_TO    | pyinotify.IN_MOVE_SELF 

    # =========================================
    # setup pyinotify watching
    # =========================================

    wm         = pyinotify.WatchManager()

    class EventHandler(pyinotify.ProcessEvent):
          def process_IN_ATTRIB(self,event):
              # Files we don't want to touch
              basename = os.path.basename(event.pathname)
              if basename[0] == '.' or basename[-4:] == ".tmp" or not os.access(event.pathname, os.R_OK):
                 return
              post.watching(event.pathname,'IN_CLOSE_WRITE')
          def process_IN_CLOSE_WRITE(self,event):
              # Files we don't want to touch
              basename = os.path.basename(event.pathname)
              if basename[0] == '.' or basename[-4:] == ".tmp" or not os.access(event.pathname, os.R_OK):
                 return
              post.watching(event.pathname,'IN_CLOSE_WRITE')
          def process_IN_DELETE(self,event):
              post.watching(event.pathname,'IN_DELETE')
          def process_IN_DELETE_SELF(self,event):
              post.watching(event.pathname,'IN_DELETE')
              post.logger.info("exiting")
              os._exit(0)
          def process_IN_MOVED_TO(self,event):
              # Files we don't want to touch
              basename = os.path.basename(event.pathname)
              if basename[0] == '.' or basename[-4:] == ".tmp" or not os.access(event.pathname, os.R_OK):
                 return
              post.watching(event.pathname,'IN_CLOSE_WRITE')
          def process_IN_MOVE_SELF(self,event):
              # Files we don't want to touch
              basename = os.path.basename(event.pathname)
              if basename[0] == '.' or basename[-4:] == ".tmp" or not os.access(event.pathname, os.R_OK):
                 os._exit(0)
              post.watching(event.pathname,'IN_CLOSE_WRITE')

    notifier   = pyinotify.AsyncNotifier(wm,EventHandler())
    wdd = wm.add_watch(watch_path, events, rec=post.recursive, auto_add=post.recursive)
    #  more options/defaults : proc_fun=None, do_glob=False, quiet=True, exclude_filter=None):


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
