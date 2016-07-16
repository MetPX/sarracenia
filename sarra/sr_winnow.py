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
# sr_winnow.py : python3 program allowing to winnow duplicated messages
#                and post the unique and first message in.
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Murray Rennie  - Shared Services Canada
#  Last Changed   : Dec  8 15:22:58 GMT 2015
#  Last Revision  : Jan  8 15:03:11 EST 2016
#  Last Revision  : Apr  11 09:00:00 CDT 2016
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

import os,sys,time

try :    
         from sr_amqp           import *
         from sr_consumer       import *
         from sr_instances      import *
         from sr_message        import *
         from sr_poster         import *
except : 
         from sarra.sr_amqp      import *
         from sarra.sr_consumer  import *
         from sarra.sr_instances import *
         from sarra.sr_message   import *
         from sarra.sr_poster    import *

class sr_winnow(sr_instances):

    def __init__(self,config=None,args=None):
        sr_instances.__init__(self,config,args)

        self.cache          = {}
        self.maxEntries     = 12000

    def cache_add(self, key):
        if len(self.cache) >= self.maxEntries: 
            self.cache_clean()
        self.cache[key] = time.time()
        self.logger.debug("Size of cache: %d  new_key: %s" % (len(self.cache),key))
            

    def cache_clean(self):
        temp = [ (item[1],item[0]) for item in self.cache.items() ]
        temp.sort()
        half,md5 = temp[self.maxEntries//2]
        for item  in self.cache.items():
            if item[1] <= half: 
#               self.logger.info("In cache_clean: delete {0}" .format(item)) 
                r=dict(self.cache)
                del r[item[0]]
                #del self.cache[item[0]]
                self.cache=r

    def cache_clear(self):
        self.cache = {}

    def cache_find(self, key):
        return key in self.cache

    def check(self):

        # no queue name allowed

        if self.queue_name == None:
           self.queue_name  = 'q_' + self.broker.username + '.'
           self.queue_name += self.program_name + '.' + self.config_name 

        # we cannot have more than one instance since we 
        # need to work with a single cache.

        if self.nbr_instances != 1 :
           self.logger.warning("Only one instance allowed... set to 1")
           self.nbr_instances = 1

        # exchange must be provided 
        if self.exchange == None:
           self.logger.error("exchange (input) unset...")
           sys.exit(1)

        # by default, post_broker  is the broker
        if self.post_broker == None :
           self.post_broker = self.broker

        # post_exchange must be provided and must be different from exchange
        if self.post_exchange == None or self.post_exchange == self.exchange :
           self.logger.error("post_exchange (output) not properly set...")
           sys.exit(1)

        # no vip given... so should not matter ?
        if self.vip == None and self.interface == None :
           self.logger.info("both vip and interface missing... standalone mode")

        # bindings should be defined 

        if self.bindings == []  :
           key = self.topic_prefix + '.#'
           self.bindings.append( (self.exchange,key) )
           self.logger.debug("*** BINDINGS %s"% self.bindings)

        # accept/reject
        self.use_pattern          = self.masks != []
        self.accept_unmatch       = True

    def close(self):
        self.consumer.close()
        if self.poster : self.poster.close()

    def connect(self):

        # =============
        # create message
        # =============

        self.msg = sr_message(self)

        # =============
        # consumer
        # =============

        self.consumer          = sr_consumer(self)
        self.msg.log_publisher = self.consumer.publish_back()
        self.msg.log_exchange  = self.log_exchange
        self.msg.user          = self.broker.username

        self.logger.info("reading from to %s@%s, exchange: %s" %
               ( self.broker.username, self.broker.hostname, self.msg.exchange ) )
        self.logger.info("report back to %s@%s, exchange: %s" %
               ( self.broker.username, self.broker.hostname, self.msg.log_exchange ) )



        # =============
        # poster if post_broker different from broker
        # =============

        self.poster = None
        if self.post_broker.geturl() != self.broker.geturl() :
           self.poster            = sr_poster(self)
           self.msg.publisher     = self.poster.publisher

        # =============
        # publisher if post_broker is same as broker
        # =============

        else :
           self.publisher = Publisher(self.consumer.hc)
           self.publisher.build()
           self.msg.publisher = self.publisher
           self.logger.info("Output AMQP broker(%s) user(%s) vhost(%s)" % \
                           (self.broker.hostname,self.broker.username,self.broker.path) )

        self.msg.pub_exchange  = self.post_exchange
        self.msg.post_exchange_split  = self.post_exchange_split
        self.logger.info("Output AMQP exchange(%s)" % self.msg.pub_exchange )


    def overwrite_defaults(self):

        # default broker : manager

        self.broker      = None
        self.post_broker = None
        if hasattr(self,'manager'):
           self.broker   = self.manager

    def help(self):
        self.logger.info("Usage: %s [OPTIONS] configfile [start|stop|restart|reload|status]\n" % self.program_name )
        self.logger.info("OPTIONS:")
        self.logger.info("-b   <broker>                default manager (if configured)")
        self.logger.info("-e   <exchange>              MANDATORY")
        self.logger.info("-tp  <topic_prefix>          default v02.post")
        self.logger.info("-st  <subtopic>              default #")
        self.logger.info("-pe  <post_exchange>         MANDATORY")
        self.logger.info("DEBUG:")
        self.logger.info("-debug")

    # =============
    # __on_message__
    # =============

    def __on_message__(self):

        # invoke user defined on_message when provided

        if self.on_message : return self.on_message(self)

        return True

    # =============
    # __on_post__ posting of message
    # =============

    def __on_post__(self):

        # invoke on_post when provided

        if self.on_post :
           ok = self.on_post(self)
           if not ok: return ok

        # should always be ok

        ok = self.msg.publish( )

        return ok

    # =============
    # process message  
    # =============

    def process_message(self):

        self.logger.debug("Received %s '%s' %s  filesize: %s" % (self.msg.topic,self.msg.notice,self.msg.hdrstr,self.msg.filesize))

        #=================================
        # now message is complete : invoke __on_message__
        #=================================

        ok = self.__on_message__()
        if not ok : return ok

        # ========================================
        # cache testing/adding
        # ========================================

        key=str(self.msg.headers['filename']) + "|" + str(self.msg.block_count) + "|" +str(self.msg.checksum)

        if self.cache_find(key) :
            self.msg.log_publish(304,'Not modified')
            self.logger.debug("Ignored %s" % (self.msg.notice))
            return True

        self.logger.debug("Added %s" % (self.msg.notice))
        self.cache_add(key)

        # announcing the first and unique message

        self.__on_post__()
        self.msg.log_publish(201,'Published')

        return True


    def run(self):

        # present basic config

        self.logger.info("sr_winnow run")

        # loop/process messages

        self.connect()

        while True :
              try  :
                      #  is it sleeping ?
                      if not self.has_vip() :
                         self.logger.debug("sr_winnow does not have vip=%s, is sleeping", self.vip)
                         time.sleep(5)
                         continue
                      else:
                         self.logger.debug("sr_winnow is active on vip=%s", self.vip)

                      #  consume message
                      ok, self.msg = self.consumer.consume()
                      self.logger.debug("sr_winnow consume, ok=%s" % ok)
                      if not ok : continue

                      #  process message (ok or not... go to the next)
                      ok = self.process_message()

              except:
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

    if len(sys.argv) >= 2 : 
       action = sys.argv[-1]

    if len(sys.argv) >= 3 : 
       config = sys.argv[-2]
       args   = sys.argv[1:-2]

    winnow = sr_winnow(config,args)

    if   action == 'foreground' : winnow.foreground_parent()
    elif action == 'reload'     : winnow.reload_parent()
    elif action == 'restart'    : winnow.restart_parent()
    elif action == 'start'      : winnow.start_parent()
    elif action == 'stop'       : winnow.stop_parent()
    elif action == 'status'     : winnow.status_parent()
    else :
           winnow.logger.error("action unknown %s" % action)
           sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
