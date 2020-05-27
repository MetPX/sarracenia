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

import logging

from sarra.sr_util import *

from sarra.plugin import v2wrapper 

from sarra.moth import Moth
import copy

logger = logging.getLogger( __name__ )

"""
amqp_ss_maxlen 

the maximum length of a "short string", as per AMQP protocol, in bytes.

"""
amqp_ss_maxlen = 255

default_options = { 'queue_name':None, 
               'exchange': None, 'topic_prefix':'v03.post', 'subtopic' : None,  
               'durable':True, 'expire': '5m', 'message_ttl':0, 
               'logLevel':'info',
               'prefetch':25, 'auto_delete':False, 'vhost':'/',
               'reset':False, 'declare':True, 'bind':True, 
}



def _msgRawToDict( raw_msg ):
    if raw_msg is not None:
        if raw_msg.properties['content_type'] == 'application/json':
            msg = json.loads( raw_msg.body )
            if ('size' in msg): 
                 if (type(msg['size']) is str):
                     msg['size'] = int(msg['size']) 
        else:
            msg = v2wrapper.v02tov03message( 
                raw_msg.body, raw_msg.headers, raw_msg.delivery_info['routing_key'] )

        msg['exchange'] = raw_msg.delivery_info['exchange']
        msg['topic'] = raw_msg.delivery_info['routing_key']
        msg['delivery_tag'] = raw_msg.delivery_info['delivery_tag']
        msg['_deleteOnPost'] = [ 'exchange', 'topic', 'delivery_tag' ]
    else:
        msg = None
    return msg


class AMQP(Moth):

    # length of an AMQP short string (used for headers and many properties)
    amqp_ss_maxlen = 255  

    def __init__( self, broker, props ):
        """
           connect to broker, depending on message_strategy stubborness, remain connected.
           
        """
        AMQP.assimilate(self)

        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s' )

        self.props=copy.deepcopy(default_options)
        self.props.update(props)

        self.first_setup=True

        me='sarra.moth.amqp.AMQP'

        if ( 'settings' in self.props ) and ( me in self.props['settings'] ):
            logger.debug('props[%s] = %s ' % ( me, self.props['settings'][me] ) )
            for s in self.props['settings'][me]:
                self.props[s] = self.props['settings'][me][s]

        logging.basicConfig( format=self.props['logFormat'], level=getattr(logging, self.props['logLevel'].upper()) )

        logger.debug( '%s logLevel set to: %s ' % ( me, self.props['logLevel'] ) )
        if self.is_subscriber: #build_consumer
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
        if broker.port is None:
            if (broker.scheme[-1]=='s' ):
                host += ':5671'
            else:
                host += ':5672'
        else:
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

                logger.info('getSetup connected to {}'.format(self.props['broker'].hostname) )

                if self.props['prefetch'] != 0 :
                    self.channel.basic_qos( 0, self.props['prefetch'], True )
           
                #FIXME: test self.first_setup and props['reset']... delete queue...
                broker_str = self.broker.geturl().replace(':'+self.broker.password+'@','@')
    
                # from Queue declare
                if self.props['declare']:

                    logger.debug('getSetup ... 1. declaring {} '.format(self.props['queue_name'] ) )
                    args={}
                    if self.props['expire']:
                        x = int(durationToSeconds(self.props['expire']) * 1000)
                        if x > 0: args['x-expires'] = x
                    if self.props['message_ttl']:
                        x = int(durationToSeconds(self.props['message_ttl']) * 1000 )
                        if x > 0: args['x-message-ttl'] = x
  
                    #FIXME: conver expire, message_ttl to proper units.
                    qname, msg_count, consumer_count  = self.channel.queue_declare( 
                        self.props['queue_name'], passive=False, 
                        durable=self.props['durable'], exclusive=False, 
                        auto_delete=self.props['auto_delete'], nowait=False,
                        arguments=args )
                    logger.info('queue declared %s (as: %s) ' % ( self.props['queue_name'], broker_str ) )
    
                if self.props['bind']:
                    logger.info('getSetup ... 1. binding')
                    for tup in self.props['bindings'] :          
                        prefix, exchange, values = tup
                        topic= prefix + '.' + values[0]
                        logger.info('binding %s with %s to %s (as: %s)' % \
                            ( self.props['queue_name'], topic, exchange, broker_str ) )
                        self.channel.queue_bind( self.props['queue_name'], exchange, topic )

                # Setup Successfully Complete! 
                logger.debug('getSetup ... Done!')
                return

            except Exception as err:
                logger.error("AMQP getSetup failed to {} with {}".format(self.broker.hostname, err))
                logger.error('Exception details: ', exc_info=True)

            if not self.props['message_strategy']['stubborn']: return

            if ebo < 60 : ebo *= 2

            logger.info("Sleeping {} seconds ...".format( ebo) )
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
                broker_str = self.broker.geturl().replace(':'+self.broker.password+'@','@')

                logger.debug('putSetup ... 1. connected to {}'.format(broker_str ) )

                if self.props['declare']:
                    logger.debug('putSetup ... 1. declaring {}'.format(self.props['exchange']) )
                    if type(self.props['exchange']) is not list:
                        self.props['exchange'] = [ self.props['exchange'] ] 
                    for x in self.props['exchange']:
                        self.channel.exchange_declare( x, 'topic', 
                             auto_delete=self.props['auto_delete'], durable=self.props['durable']  )
                        logger.info('exchange declared: %s (as: %s) ' % ( x, broker_str ) )

                # Setup Successfully Complete! 
                logger.debug('putSetup ... Done!')
                return

            except Exception as err:
                logger.error("AMQP putSetup failed to {} with {}".format( 
                    self.props['broker'].hostname, err) )
                logger.debug('Exception details: ', exc_info=True)

            if not self.props['message_strategy']['stubborn']: return

            if ebo < 60 : ebo *= 2

            logger.info("Sleeping {} seconds ...".format( ebo) )
            time.sleep(ebo)

    def putCleanUp(self):

        try: 
            self.channel.exchange_delete( self.props['exchange'] )            
        except Exception as err:
            logger.error("AMQP putCleanup failed on {} with {}".format( 
                self.props['broker'].hostname, err) )
            logger.debug('Exception details: ', exc_info=True)

    def getCleanUp(self):

        try: 
            self.channel.queue_delete( self.props['queue_name'] )            
        except Exception as err:
            logger.error("AMQP putCleanup failed to {} with {}".format( 
                self.props['broker'].hostname, err) )
            logger.debug('Exception details: ', exc_info=True)

    @classmethod
    def assimilate(cls,obj):
        """
        Turn the calling object into 
        """
        obj.__class__ = AMQP

    def url_proto(self):
        return "amqp"

    def newMessages( self ):

        if not self.is_subscriber: #build_consumer
            logger.error("getting from a publisher")
            return None

        ml=[]
        m=self.getNewMessage()
        if m is not None:
            fetched=1
            ml.append(m)
            while fetched < self.props['prefetch']:
                m=self.getNewMessage()
                if m is None:
                    break
                ml.append(m)
                fetched += 1

        logger.debug("got (%d) done." % len(ml) )
        return ml

    def getNewMessage( self ):

        if not self.is_subscriber: #build_consumer
            logger.error("getting from a publisher")
            return None

        ebo=1
        while True:
            try:
                raw_msg = self.channel.basic_get(self.props['queue_name']) 

                if (raw_msg is None) and (self.connection.connected):
                    return None
                else:
                    msg = _msgRawToDict( raw_msg ) 
                    logger.info("new msg: %s" % msg )
                    return msg
            except Exception as err:
                logger.warning("moth.amqp.getNewMessage: failed %s: %s" % (self.props['queue_name'], err))
                logger.debug('Exception details: ', exc_info=True)

            if not self.props['message_strategy']['stubborn']:
                return None

            logger.warning( 'lost connection to broker' )
            self.close()
            self.__getSetup()

            if ebo < 60 : ebo *= 2

            logger.info("Sleeping {} seconds ...".format( ebo) )
            time.sleep(ebo)

    def ack( self, m ):
        """
           do what you need to acknowledge that processing of a message is done.
        """
        if not self.is_subscriber: #build_consumer
            logger.error("getting from a publisher")
            return 

        if not 'delivery_tag' in m:
            logger.warning("cannot acknowledge message without a delivery_tag: %s " % m['relPath'] )
            return 

        self.channel.basic_ack( m['delivery_tag'] )

    def putNewMessage(self, body, content_type='application/json', exchange=None ):
        """
        put a new message out, to the configured exchange by default.
        """

        if self.is_subscriber: #build_consumer
            logger.error("publishing from a consumer")
            return None

        #body = copy.deepcopy(bd)
        topic = body['topic']
        topic = topic.replace('#','%23')
        topic = topic.replace('#','%23')

        if len(topic) >= 255: # ensure topic is <= 255 characters
            logger.error("message topic too long, truncating")
            mxlen=amqp_ss_maxlen
            while( topic.encode("utf8")[mxlen-1] & 0xc0 == 0xc0 ):
                mxlen -= 1
            topic = topic.encode("utf8")[0:mxlen].decode("utf8")

        if '_deleteOnPost' in body:
            for k in body['_deleteOnPost']:
               del body[k]
            del body['_deleteOnPost']      

        if not exchange :
            if (type(self.props['exchange']) is list):
                if ( len(self.props['exchange']) > 1 ):
                    if 'post_exchange_split' in self.props:
                        # FIXME: assert ( len(self.props['exchange']) == self.props['post_exchange_split'] )
                        #        if that isn't true... then there is something wrong... should we check ?
                        idx = sum( bytearray(body['integrity']['value'], 'ascii')) % len(self.props['exchange'])
                        exchange=self.props['exchange'][idx]
                    else:
                        logger.error('do not know which exchange to publish to: %s' % self.props['exchange'] )
                        return
                else:
                    exchange=self.props['exchange'][0]
            else:
                exchange=self.props['exchange']
 
        if self.props['message_ttl']:
            ttl = "%d" * int(durationToSeconds(self.props['message_ttl']) * 1000 )
        else:
            ttl = "0"   

        if topic.startswith('v02'): #unless explicitly otherwise
            v2m = v2wrapper.Message(body) 

            # v2wrapp
            for h in [ 'pubTime', 'baseUrl', 'relPath', 'size', 'blocks', 'content', 'integrity' ]:
                if h in v2m.headers:
                    del v2m.headers[h]

            for k in v2m.headers:
                if len(v2m.headers[k]) >= amqp_ss_maxlen:
                    logger.error("message header %s too long, dropping" % k )
                    return
            AMQP_Message = amqp.Message(v2m.notice, content_type='text/plain', 
                application_headers=v2m.headers, expire=ttl )
        else: #assume v03

            raw_body=json.dumps(body)
            AMQP_Message = amqp.Message(raw_body, content_type='application/json', 
                application_headers=None, expire=ttl )

        ebo=1
        while True:
            try:
                    self.channel.basic_publish( AMQP_Message, exchange, topic ) 
                    self.channel.tx_commit()
                    logger.info("published {} to {} under: {} ".format(body, exchange, topic) )
                    return # no failure == success :-)

            except Exception as err:
                logger.warning("moth.amqp.putNewMessage: failed %s: %s" % (exchange, err))
                logger.debug('Exception details: ', exc_info=True)

            if not self.props['message_strategy']['stubborn']:
                return None

            self.close()
            self.__putSetup()

            if ebo < 60 : ebo *= 2

            logger.info("Sleeping {} seconds ...".format( ebo) )
            time.sleep(ebo)


    def close(self):
        try:
            self.connection.collect()
            self.connection.close()

        except Exception as err:
            logger.error("sr_amqp/close 2: {}".format(err))
            logger.debug("sr_amqp/close 2 Exception details:", exc_info=True)
        # FIXME toclose not useful as we don't close channels anymore
        self.connection=None
