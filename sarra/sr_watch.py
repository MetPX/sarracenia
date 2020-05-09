#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#
# sr_watch.py : python3 program allowing users to post an available product
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Nov  8 22:10:16 UTC 2017
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 2 of the License.
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
# sr_watch [options] [config] [foreground|start|stop|restart|reload|status|cleanup|setup]
#
#============================================================

try :    
         from sr_post            import *
except : 
         from sarra.sr_post      import *

class sr_watch(sr_post):

    def check(self):
        self.logger.debug("%s check" % self.program_name)

        if self.sleep <= 0  : self.sleep = 0.1
        # This gets executed after the config file parameters are read so you can't turn off caching with the line
        #if not self.caching : self.caching = 300 

        sr_post.check(self)

# ===================================
# MAIN
# ===================================

def main():

    args,action,config,old = startup_args(sys.argv)

    watch = sr_watch(config,args,action)
    watch.exec_action(action,old)

    os._exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
