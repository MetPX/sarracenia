#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, 2008-2020
#
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
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

# the real AMQP library... not this one... 
import amqp

from sarra.sr_util import *

from sarra.tmpc import TMPC
import copy


class AMQP(TMPC):

    __default_properties = { 'queue_name':None, 
               'exchange': None, 'topic_prefix':None, 'subtopic' : None,  
               'durable':True, 'expire': '5m', 'message_ttl':0, 
               'prefetch':25, 'auto_delete':False, 'vhost':'/',
               'reset':False, 'declare':True, 'bind':True, 
    }

    def default_props():
       return AMQP.__default_properties

    def __init__( self, broker ):
        """
           connect to broker, depending on message_strategy stubborness, remain connected.
           
        """
        self.logger.debug("__init__ AMQP")

        AMQP.assimilate(self)
        self.props.update(copy.deepcopy(AMQP.__default_properties))

        self.first_setup=True

        if self.props_args:
            self.props.update(copy.deepcopy(self.props_args)) 

        if self.get: #build_consumer
           self.__getSetup()
           return
        else: # publisher...
           self.__putSetup()

    def __connect(self,broker):
        """
          connect to broker. 
          returns with self.channel set to a new channel.

          Expect caller to handle errors.
        """
        host= broker.hostname 
        if broker.port:
           host += ':{}'.format(broker.port)

        self.connection = amqp.Connection(
            host=host,
            userid=broker.username, 
            password=broker.password,
            virtual_host=self.props['vhost'], 
            ssl= (broker.scheme[-1]=='s' )
        )
        if hasattr(self.connection, 'connect'):
            # check for amqp 1.3.3 and 1.4.9 because connect doesn't exist in those older versions
            self.connection.connect()

        self.channel = self.connection.channel()


    def __getSetup(self):
        """
        Setup so we can get messages.

        if message_strategy is stubborn, will loop here forever.
             connect, declare queue, apply bindings.
        """
        ebo=1
        while True:

            # It does not really matter how it fails, the recovery approach is always the same:
            # tear the whole thing down, and start over.
            try:
                # from sr_consumer.build_connection...
                self.__connect(self.broker)

                self.logger.debug('getSetup ... 1. connected to {}'.format(self.props['broker'].hostname) )

                if self.props['prefetch'] != 0 :
                    self.channel.basic_qos( 0, self.props['prefetch'], True )
           
                #FIXME: test self.first_setup and props['reset']... delete queue...
    
                # from Queue declare
                if self.props['declare']:

                    self.logger.debug('getSetup ... 1. declaring {} '.format(self.props['queue_name'] ) )
                    args={}
                    if self.props['expire']:
                        x = int(durationToSeconds(self.props['expire']) * 1000)
                        if x > 0: args['x-expires'] = x
                    if self.props['message_ttl']:
                        x = int(durationToSeconds(self.props['x-message-ttl']) * 1000 )
                        if x > 0: args['x-message-ttl'] = x
  
                    #FIXME: conver expire, message_ttl to proper units.
                    qname, msg_count, consumer_count  = self.channel.queue_declare( 
                        self.props['queue_name'], passive=False, 
                        durable=self.props['durable'], exclusive=False, 
                        auto_delete=self.props['auto_delete'], nowait=False,
                        arguments=args )
    
                if self.props['bind']:
                    self.logger.debug('getSetup ... 1. binding')
                    broker_str = self.broker.geturl().replace(':'+self.broker.password+'@','@')
                    for tup in self.props['bindings'] :          
                        prefix, exchange, values = tup
                        topic= prefix + '.' + values[0]
                        self.logger.error('Binding queue %s with key %s from exchange %s on broker %s' % \
                            ( self.props['queue_name'], topic, exchange, broker_str ) )
                        self.channel.queue_bind( self.props['queue_name'], exchange, topic )

                # Setup Successfully Complete! 
                self.logger.debug('getSetup ... Done!')
                return

            except Exception as err:
                self.logger.error("AMQP getSetup failed to {} with {}".format(self.broker.hostname, err))
                self.logger.error('Exception details: ', exc_info=True)

            if not self.props['message_strategy']['stubborn']: return

            if ebo < 60 : ebo *= 2

            self.logger.info("Sleeping {} seconds ...".format( ebo) )
            time.sleep(ebo)


    def __putSetup(self):
        ebo=1
        while True:

            # It does not really matter how it fails, the recovery approach is always the same:
            # tear the whole thing down, and start over.
            try:
                # from sr_consumer.build_connection...
                self.__connect(self.props['broker'])

                # transaction mode... confirms would be better...
                self.channel.tx_select()

                self.logger.debug('putSetup ... 1. connected to {}'.format(self.props['broker'].hostname ) )

                if self.props['declare']:

                    self.logger.debug('putSetup ... 1. declaring {}'.format(self.props['exchange']) )
                    
                    self.channel.exchange_declare(
                        self.props['exchange'], 'topic',
                        auto_delete=self.props['auto_delete'], durable=self.props['durable']  )

                    self.mttl='0'
                    if self.props['message_ttl']:
                        x = int(durationToSeconds(self.props['message_ttl']) * 1000)
                        if x > 0: self.mttl = "%d" % x 
                # Setup Successfully Complete! 
                self.logger.debug('putSetup ... Done!')
                return

            except Exception as err:
                self.logger.error("AMQP putSetup failed to {} with {}".format( 
                    self.props['broker'].hostname, err) )
                self.logger.debug('Exception details: ', exc_info=True)

            if not self.props['message_strategy']['stubborn']: return

            if ebo < 60 : ebo *= 2

            self.logger.info("Sleeping {} seconds ...".format( ebo) )
            time.sleep(ebo)

    def __putCleanUp(self):

        try: 
            self.channel.exchange_delete( self.props['exchange'] )            
        except Exception as err:
            self.logger.error("AMQP putCleanup failed to {} with {}".format( 
                self.props['broker'].hostname, err) )
            self.logger.debug('Exception details: ', exc_info=True)

    def __getCleanUp(self):

        try: 
            self.channel.queue_delete( self.props['queue_name'] )            
        except Exception as err:
            self.logger.error("AMQP putCleanup failed to {} with {}".format( 
                self.props['broker'].hostname, err) )
            self.logger.debug('Exception details: ', exc_info=True)

    @classmethod
    def assimilate(cls,obj):
        """
        Turn the calling object into 
        """
        obj.__class__ = AMQP

    def url_proto(self):
        return "amqp"


    def getNewMessage( self ):

        if not self.get: #build_consumer
            self.logger.error("getting from a publisher")
            return None

        ebo=1
        while True:
            try:
                msg = self.channel.basic_get(self.props['queue_name']) 
                return msg 
            except:
                self.logger.warning("tmpc.amqp.getNewMessage: failed %s: %s" % (queuename, err))
                self.logger.debug('Exception details: ', exc_info=True)

            if not self.props['message_strategy']['stubborn']:
                return None

            self.close()
            self.__getSetup()

            if ebo < 60 : ebo *= 2

            self.logger.info("Sleeping {} seconds ...".format( ebo) )
            time.sleep(ebo)

    def putNewMessage(self, topic, body, headers=None, content_type='application/json', exchange=None ):
        """
        put a new message out, to the configured exchange by default.
        """
        if self.get: #build_consumer
            self.logger.error("publishing from a consumer")
            return None

        ebo=1
        while True:
            try:
                if not exchange :
                    exchange=self.props['exchange']

                AMQP_Message = amqp.Message(body, content_type=content_type, 
                     application_headers=headers, expiration=self.mttl)

                self.channel.basic_publish( AMQP_Message, exchange, topic ) 

                self.channel.tx_commit()
                self.logger.info("published {} to {} ".format(body, exchange) )
                return # no failure == success :-)

            except Exception as err:
                self.logger.warning("tmpc.amqp.putNewMessage: failed %s: %s" % (exchange, err))
                self.logger.debug('Exception details: ', exc_info=True)

            if not self.props['message_strategy']['stubborn']:
                return None

            self.close()
            self.__putSetup()

            if ebo < 60 : ebo *= 2

            self.logger.info("Sleeping {} seconds ...".format( ebo) )
            time.sleep(ebo)

    def close(self):
        try:
            self.connection.close()

        except Exception as err:
            self.logger.error("sr_amqp/close 2: {}".format(err))
            self.logger.debug("sr_amqp/close 2 Exception details:", exc_info=True)
        # FIXME toclose not useful as we don't close channels anymore
        self.connection=None
