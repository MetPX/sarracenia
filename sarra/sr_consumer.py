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
# sr_consumer.py : python3 wraps consumer queue binding accept/reject
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  first shot     : Dec 11 10:26:22 EST 2015
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

import os,json,sys,random,time

try :    
         from sr_amqp           import *
         from sr_config         import *
         from sr_message        import *
         from sr_retry          import *
         from sr_util           import *
except : 
         from sarra.sr_amqp     import *
         from sarra.sr_config   import *
         from sarra.sr_message  import *
         from sarra.sr_retry    import *
         from sarra.sr_util     import *

# class sr_consumer

class sr_consumer:

    def __init__(self, parent, admin=False, loop=True ):
        self.logger         = parent.logger
        self.logger.debug("sr_consumer __init__")
        self.parent         = parent
        self.broker         = parent.broker

        self.hc              = None
        self.retry           = sr_retry(parent)
        self.raw_msg         = None
        self.last_msg_failed = False

        reporting = self.isReporting()

        if admin : return

        self.use_pattern    = parent.masks != []
        self.accept_unmatch = parent.accept_unmatch
        self.save = False

        self.iotime = 30
        if self.parent.timeout : self.iotime = int(self.parent.timeout)

        # truncated exponential backoff for consume...

        self.sleep_max = 10
        self.sleep_min = 0.01
        self.sleep_now = self.sleep_min

        self.build_connection(loop=loop)
        self.build_consumer()
        self.build_queue()
        self.get_message()

    def build_connection(self,loop=True):
        self.logger.debug("sr_consumer build_broker")

        self.logger.info("AMQP  broker(%s) user(%s) vhost(%s)" % \
                        (self.broker.hostname,self.broker.username,self.broker.path) )

        self.hc = HostConnect( logger = self.logger )
        self.hc.choose_amqp_alternative(self.parent.use_amqplib, self.parent.use_pika)
        self.hc.set_url(self.broker)
        self.hc.loop=loop
        return self.hc.connect()

    def build_consumer(self):
        self.logger.debug("sr_consumer build_consumer")

        self.consumer = Consumer(self.hc)

        if self.parent.prefetch > 0 :
            self.consumer.add_prefetch(self.parent.prefetch)

        self.consumer.build()

        self.retry_msg = self.retry.message

    def build_queue(self):
        self.logger.debug("sr_consumer build_queue")

        self.bindings    = self.parent.bindings

        self.broker_str  = self.broker.geturl().replace(':'+self.broker.password+'@','@')

        # queue name 
        self.queue_declare(build=False)

        # queue bindings 

        for tup in self.bindings :
            exchange, key = tup
            self.logger.info('Binding queue %s with key %s from exchange %s on broker %s' % \
		            ( self.queue_name, key, exchange, self.broker_str ) )
            self.msg_queue.add_binding( exchange, key )

        # queue creation 
        self.msg_queue.build()

    def close(self):
        if self.hc :
           self.hc.close()
           self.hc = None
        self.retry.close()

    def consume(self):

        # acknowledge last message... we are done with it since asking for a new one
        if self.raw_msg != None and not self.raw_msg.isRetry : self.consumer.ack(self.raw_msg)

        # consume a new one
        self.get_message()
        self.raw_msg = self.consumer.consume(self.queue_name)

        # if no message from queue, perhaps we have message to retry

        if self.raw_msg == None : self.raw_msg = self.retry.get()

        # when no message sleep for 1 sec. (value taken from old metpx)
        # *** value 0.01 was tested and would simply raise cpu usage of broker
        # to unacceptable level with very fews processes (~20) trying to consume messages
        # remember that instances and broker sharing messages add up to a lot of consumers

        should_sleep = False

        if   self.raw_msg == None                          : should_sleep = True
        elif self.raw_msg.isRetry and self.last_msg_failed : should_sleep = True

        if should_sleep :
           #self.logger.debug("sleeping %f" % self.sleep_now)
           time.sleep(self.sleep_now)
           self.sleep_now = self.sleep_now * 2
           if self.sleep_now > self.sleep_max : 
                  self.sleep_now = self.sleep_max

        if self.raw_msg == None: return False, self.msg

        # make use it as a sr_message
        # dont bother with retry... 
        try :
                 self.msg.from_amqplib(self.raw_msg)
                 self.logger.debug("notice %s " % self.msg.notice)
                 if self.msg.urlstr:
                    self.logger.debug("urlstr %s " % self.msg.urlstr)
        except :
                 self.logger.error("sr_consumer/consume malformed message %s" % vars(self.raw_msg))
                 self.logger.debug('Exception details: ', exc_info=True)
                 return None, None

        # special case : pulse

        if self.msg.isPulse :
           self.parent.pulse_count += 1
           return True,self.msg

        # we have a message, reset timer (original or retry)

        if not should_sleep : self.sleep_now = self.sleep_min 

        # normal message

        if not self.raw_msg.isRetry : self.parent.message_count += 1

        # make use of accept/reject
        # dont bother with retry... were good to be kept
        if self.use_pattern :

           # Adjust url to account for sundew extension if present, and files do not already include the names.
           if urllib.parse.urlparse(self.msg.urlstr).path.count(":") < 1 and 'sundew_extension' in self.msg.headers.keys() :
              urlstr=self.msg.urlstr + ':' + self.msg.headers[ 'sundew_extension' ]
           else:
              urlstr=self.msg.urlstr

           self.logger.debug("sr_consumer, path being matched: %s " % ( urlstr )  ) 

           if not self.parent.isMatchingPattern(self.msg.urlstr,self.accept_unmatch) :
              self.logger.debug("Rejected by accept/reject options")
              return False,self.msg

        elif not self.accept_unmatch :
              return False,self.msg

        # note that it is a retry or not in sr_message

        return True,self.msg

    def get_message(self):
        #self.logger.debug("sr_consumer get_message")

        if not hasattr(self.parent,'msg'):
           self.parent.msg = sr_message(self.parent)

        self.raw_msg  = None
        self.msg      = self.parent.msg
        self.msg.user = self.broker.username

    def isAlive(self):
        if not hasattr(self,'consumer') : return False
        if self.consumer.channel == None: return False
        alarm_set(self.iotime)
        try   : self.consumer.channel.basic_qos(0,self.consumer.prefetch,False)
        except: 
                alarm_cancel()
                return False
        alarm_cancel()
        return True

    def isReporting(self):
        self.logger.debug("sr_consumer isReporting")

        self.report_exchange = None
        self.report_manage   = False

        if not self.parent.reportback : return False

        self.report_exchange = self.parent.report_exchange

        # user has power to create exchanges

        user           = self.broker.username
        self.users     = self.parent.users

        self.isAllowed = user             in self.users    and \
                         self.users[user] in ['admin','feeder','manager']

        # default report_exchange if unset

        if self.report_exchange == None :
           self.report_exchange = 'xs_' + user
           if self.isAllowed :
              self.report_exchange = 'xreport'
           self.parent.report_exchange = self.report_exchange

        return True

    def msg_to_retry(self):
        self.last_msg_failed = True

        if self.raw_msg == None : return

        if self.raw_msg.isRetry : self.retry.add_msg_to_state_file(self.raw_msg)
        else                    : self.retry.add_msg_to_new_file  (self.raw_msg)

        self.logger.info("appended to retry list file %s" % self.raw_msg.body)

    def msg_worked(self):
        self.last_msg_failed = False

        if self.raw_msg == None or not self.raw_msg.isRetry : return

        self.retry.add_msg_to_state_file(self.raw_msg,done=True)

        self.logger.debug("confirmed removed from the retry process %s" % self.raw_msg.body)

    def publish_back(self):
        self.logger.debug("sr_consumer publish_back")

        self.publisher = Publisher(self.hc)
        self.publisher.build()

        return self.publisher

    def queue_declare(self,build=False):
        self.logger.debug("sr_consumer queue_declare")

        self.durable     = self.parent.durable
        self.reset       = self.parent.reset
        self.expire      = self.parent.expire
        self.message_ttl = self.parent.message_ttl

        # queue name 
        self.set_queue_name()

        # queue settings
        self.msg_queue   = Queue(self.hc,self.queue_name,durable=self.durable,reset=self.reset)

        if self.expire != None :
           self.msg_queue.add_expire(self.expire)

        if self.message_ttl != None :
           self.msg_queue.add_message_ttl(self.message_ttl)

        # queue creation if needed
        if build :
           self.logger.info("declaring queue %s on %s" % (self.queue_name,self.broker.hostname))
           self.msg_queue.build()

    #def random_queue_name(self) :
    def set_queue_name(self):

        # queue file : fix it 

        queuefile  = self.parent.program_name
        if self.parent.config_name :
           queuefile += '.' + self.parent.config_name
        queuefile += '.' + self.broker.username

        # queue path

        self.queuepath = self.parent.user_cache_dir + os.sep + queuefile + '.qname'

        # ====================================================
        # FIXME get rid of this code in 2018 (after release 2.17.11a1)
        # transition old queuepath to new queuepath...

        self.old_queuepath = self.parent.user_cache_dir + os.sep + queuefile
        if os.path.isfile(self.old_queuepath) and not os.path.isfile(self.queuepath) :
           # hardlink (copy of old)
           os.link(self.old_queuepath,self.queuepath)
           # during the transition both should be available is we go back

        # get rid up to the next line
        # ====================================================

        if os.path.isfile(self.queuepath) :
           f = open(self.queuepath)
           self.queue_name = f.read()
           f.close()
           return
        
        self.queue_prefix = 'q_'+ self.broker.username
        self.queue_name   = self.parent.queue_name

        if self.queue_name :
           if not self.queue_prefix in self.queue_name : 
               self.logger.warning("non standard queue name %s" % self.queue_name )
               #self.queue_name = self.queue_prefix + '.'+ self.queue_name

        else:
           self.queue_name  = self.queue_prefix 
           self.queue_name += '.'  + self.parent.program_name

           if self.parent.config_name : self.queue_name += '.'  + self.parent.config_name
           if self.parent.queue_suffix: self.queue_name += '.'  + self.parent.queue_suffix

           self.queue_name += '.'  + str(random.randint(0,100000000)).zfill(8)
           self.queue_name += '.'  + str(random.randint(0,100000000)).zfill(8)

        f = open(self.queuepath,'w')
        f.write(self.queue_name)
        f.close()

        #self.random_queue_name()

    def cleanup(self):
        self.logger.debug("sr_consume cleanup")
        self.set_queue_name()

        if self.build_connection(loop=False):
            self.hc.queue_delete(self.queue_name)
            if self.report_manage :
                self.hc.exchange_delete(self.report_exchange)

        try    :
                 if hasattr(self,'queuepath') :
                    os.unlink(self.queuepath)
        except : pass

        self.retry.cleanup()


    def declare(self):
        self.logger.debug("sr_consume declare")

        if self.build_connection(loop=False):
            self.queue_declare(build=True)
            if self.report_manage :
               self.hc.exchange_declare(self.report_exchange)
                  
    def setup(self):
        self.logger.debug("sr_consume setup")
        if self.build_connection(loop=False):
            self.build_queue()
            if self.report_manage :
               self.hc.exchange_declare(self.report_exchange)

