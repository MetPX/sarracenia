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
# sr_report.py : python3 program allowing users to receive all report messages
#             generated from his products
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Tue Oct  3 18:25 UTC 2017
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


#============================================================
# usage example
#
# sr_report -b broker

#============================================================

try :    
         from sr_subscribe       import *
except : 
         from sarra.sr_subscribe import *

class sr_report(sr_subscribe):

    def __init__(self,config=None,args=None,action=None):
        #start debug before it is set by args or config option
        #self.debug = True
        #self.setlog()
        sr_subscribe.__init__(self,config,args,action)

    def check(self):
        self.logger.debug("%s check" % self.program_name)
        if self.config_name == None : return

        self.nbr_instances = 1
        self.reportback    = False
        self.notify_only   = True
        self.post_broker   = None

        if self.broker == None :
           self.logger.error("no broker given")
           sys.exit(1)

        username = self.broker.username

        if self.exchange == None:
           self.exchange = 'xs_' + username
           if username in self.users.keys():
              if self.users[username] in [ 'feeder', 'admin' ]:
                 self.exchange = 'xreport'

        if self.bindings == [] :
           key = self.topic_prefix + '.' + self.subtopic
           self.bindings     = [ (self.exchange,key) ]
        else :
           for i,tup in enumerate(self.bindings):
               e,k   = tup
               if e != self.exchange :
                  self.logger.info("exchange forced to %s" % self.exchange)
                  e = self.exchange
               self.bindings[i] = (e,k)

        # pattern must be used
        # if unset we will accept unmatched... so everything

        self.use_pattern          = self.masks != []
        self.accept_unmatch       = self.masks == []

    def overwrite_defaults(self):
        self.logger.debug("%s overwrite_defaults" % self.program_name)
        self.broker               = None
        self.topic_prefix         = 'v02.report'
        self.subtopic             = '#'

    def help(self):
        print("Usage: %s [OPTIONS] configfile [foreground|start|stop|restart|reload|status|cleanup|setup]\n" % self.program_name )
        print("version: %s \n" % sarra.__version__ )
        print("Or   : %s [OPTIONS] -b <broker> [foreground|start|stop|restart|reload|status|cleanup|setup]\n" % self.program_name )
        self.logger.info("OPTIONS:")
        self.logger.info("-b   <broker>   default:amqp://guest:guest@localhost/")

# ===================================
# MAIN
# ===================================

def main():

    args,action,config,old = startup_args(sys.argv)

    # config is optional so check the argument

    if config != None:
       cfg = sr_config()
       cfg.defaults()
       cfg.general()
       ok,config = cfg.config_path('report',config,mandatory=False)
       if not ok :
          config = None
          args   = []
          args.extend(sys.argv[1:])
          args.remove(action)

    srreport = sr_report(config,args,action)

    if old :
       srreport.logger.warning("Should invoke : %s [args] action config" % sys.argv[0])

    srreport.exec_action(action,old)

    os._exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
