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
# sr_log.py : python3 program allowing users to receive all log messages
#             generated from his products
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Apr 19 13:20:00 CDT 2016
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

import signal

#============================================================
# usage example
#
# sr_log -b broker

#============================================================

try :    
         from sr_consumer        import *
         from sr_instances       import *
except : 
         from sarra.sr_consumer  import *
         from sarra.sr_instances import *


class sr_log(sr_instances):

    def __init__(self,config=None,args=None):
        #start debug before it is set by args or config option
        #self.debug = True
        #self.setlog()
        sr_instances.__init__(self,config,args)

    def check(self):
        self.nbr_instances = 1

        if self.broker == None :
           self.logger.error("no broker given")
           sys.exit(1)

        if self.exchange == None:
           if self.users[self.broker.username] == 'feeder' or self.users[self.broker.username] == 'admin':
              self.exchange = 'xlog'
           else:
              self.exchange = 'xl_' + self.broker.username

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

    def close(self):
        self.consumer.close()

    def overwrite_defaults(self):
        self.broker               = None
        self.topic_prefix         = 'v02.log'
        self.subtopic             = '#'

    def help(self):
        print("Usage: %s [OPTIONS] configfile [foreground|start|stop|restart|reload|status]\n" % self.program_name )
        print("Or   : %s [OPTIONS] -b <broker> [foreground|start|stop|restart|reload|status]\n" % self.program_name )
        self.logger.info("OPTIONS:")
        self.logger.info("-b   <broker>   default:amqp://guest:guest@localhost/")

    # =============
    # __on_message__  internal message validation
    # =============

    def __on_message__(self):
        self.logger.debug("sr_log __on_message__")

        self.logger.debug("Received topic   %s" % self.msg.topic)
        self.logger.info("Received notice  %s" % self.msg.notice)
        self.logger.debug("Received headers %s\n" % self.msg.hdrstr)

        # user provided an on_message script

        ok = True

        if self.on_message : ok = self.on_message(self)

        return ok


    def run(self):

        self.logger.info("sr_log run")

        parent        = self
        self.consumer = sr_consumer(parent)

        #
        # loop on all message
        #

        while True :

          try  :
                 ok, self.msg = self.consumer.consume()
                 if not ok : continue

                 ok = self.__on_message__()

          except :
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
                 

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

    if len(sys.argv) > 1 :
       action = sys.argv[-1]
       args   = sys.argv[1:-1]

    if len(sys.argv) > 2 : 
       config    = sys.argv[-2]
       cfg       = sr_config()
       cfg.defaults()
       cfg.general()
       ok,config = cfg.config_path('log',config,mandatory=False)
       if ok     : args = sys.argv[1:-2]
       if not ok : config = None

    srlog = sr_log(config,args)

    if   action == 'foreground': srlog.foreground_parent()
    elif action == 'reload'    : srlog.reload_parent()
    elif action == 'restart'   : srlog.restart_parent()
    elif action == 'start'     : srlog.start_parent()
    elif action == 'stop'      : srlog.stop_parent()
    elif action == 'status'    : srlog.status_parent()
    else :
           srlog.logger.error("action unknown %s" % action)
           sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
