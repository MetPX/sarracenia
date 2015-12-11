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
#  Daluma Sen     - Shared Services Canada
#  Last Changed   : Dec 11 16:07:32 EDT 2015
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
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

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

    # =========================================
    # setup watchdog
    # =========================================
    class MyEventHandler(PatternMatchingEventHandler):
        ignore_patterns = ["*.tmp"]
        def event_post(self, event, tag):
            if not event.is_directory:
                try:
                    post.watching(event.src_path, tag)
                except PermissionError as err:
                    post.logger.error(str(err))

        def on_created(self, event):
            self.event_post(event, 'IN_CLOSE_WRITE')
                    
        def on_deleted(self, event):
            if event.src_path == watch_path:
                post.logger.error('Exiting!')
                os._exit(0)
            self.event_post(event, 'IN_DELETE')

        def on_modified(self, event):
            self.event_post(event, 'IN_CLOSE_WRITE')

    try:
        observer = Observer()
        obs_watched = observer.schedule(MyEventHandler(), watch_path, recursive=post.recursive)
        observer.start()
    except OSError as err:
        post.logger.error("Can't watch directory: %s" % str(err))
        os._exit(0)

    # =========================================
    # signal reload
    # =========================================
    def signal_reload(signal, frame):
        post.logger.info('Reloading!')
        post.close()
        observer.unschedule(obs_watched)
        main()

    signal.signal(signal.SIGHUP, signal_reload)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        post.logger.info('Stop!')
        post.close()
        post.stop = True
        observer.stop()

    observer.join()
    sys.exit(0)

# =========================================
# direct invocation
# =========================================
if __name__=="__main__":
   main()
