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

import v2wrapper

from sarra.tmpc import TMPC
import copy

logger = logging.getLogger( __name__ )

class AMQP(TMPC):

    # length of an AMQP short string (used for headers and many properties)
    amqp_ss_maxlen = 255  

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

        AMQP.assimilate(self)
        self.props.update(copy.deepcopy(AMQP.__default_properties))

        self.first_setup=True

        if self.props_args:
            self.props.update(copy.deepcopy(self.props_args)) 

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

                logger.info('getSetup ... 1. connected to {}'.format(self.props['broker'].hostname) )

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

    def getNewMessage( self ):

        if not self.is_subscriber: #build_consumer
            logger.error("getting from a publisher")
            return None

        ebo=1
        while True:
            try:
                raw_msg = self.channel.basic_get(self.props['queue_name']) 
                #logger.info("msg varlist: %s" % raw_msg.__dict__ )
                if raw_msg is not None:
                    if raw_msg.properties['content_type'] == 'application/json':
                        msg = json.loads( raw_msg.body )
                        msg['topic'] = raw_msg.delivery_info['routing_key']
                    else:
                        msg = sarra.v2wrapper.v02tov03message( 
                            raw_msg.body, raw_message.headers, raw_msg.delivery_info['routing_key'] )
                else:
                    msg = None
                return msg 
            except:
                logger.warning("tmpc.amqp.getNewMessage: failed %s: %s" % (queuename, err))
                logger.debug('Exception details: ', exc_info=True)

            if not self.props['message_strategy']['stubborn']:
                return None

            self.close()
            self.__getSetup()

            if ebo < 60 : ebo *= 2

            logger.info("Sleeping {} seconds ...".format( ebo) )
            time.sleep(ebo)

    def v03tov02message( h ):

        v02main=h["pubTime"].replace("T","") + ' ' + h["baseURL" ] + ' ' + h["relPath"]
        del h["pubTime"]
        del h["baseURL"]
        del h["relPath"]

        #FIXME: ensure headers are < 255 chars.
        for k in [ 'mtime', 'atime' ]:
            h[ k ] = h[k].replace("T","")

        #FIXME: sum header encoding.
        if 'size' in h:
            h[ 'parts' ] = '1,%d,1,0,0' % h['size']
            del h['size']

        if 'blocks' in h:
            if h['parts'] == 'inplace': 
                m='i'
            else: 
                m='p'
            p=h['blocks']
            h[ 'parts' ] = '%s,%d,%d,%d,%d' % ( m, p['size'], p['count'], 
                  p['remainder'], p['number'] )
            del h['blocks']

        if 'content' in h:  #v02 does not support inlining
            del h['content']

        if 'integrity' in h:
            sum_algo_v3tov2 = { "arbitrary":"a", "md5":"d", "sha512":"s", 
                "md5name":"n", "random":"0", "link":"L", "remove":"R", "cod":"z" }
            sa = sum_algo_v3tov2[ self.headers[ "integrity" ][ "method" ] ]

            # transform sum value
            if sa in [ '0' ]:
                sv = self.headers[ "integrity" ][ "value" ]
            elif sa in [ 'z' ]:
                sv = sum_algo_v3tov2[ self.headers[ "integrity" ][ "value" ] ]
            else:
                sv = encode( decode( self.headers[ "integrity" ][ "value" ].encode('utf-8'), "base64" ), 'hex' )
            
            h[ "sum" ] = sa + ',' + sv
            del self.headers['integrity']

        return ( v02main, h)
                       


    def putNewMessage(self, body, content_type='application/json', exchange=None ):
        """
        put a new message out, to the configured exchange by default.
        """
        if self.is_subscriber: #build_consumer
            logger.error("publishing from a consumer")
            return None

        topic = body['topic']
        del body['topic']
        topic = topic.replace('#','%23')
        topic = topic.replace('#','%23')
        if len(topic) >= 255: # ensure topic is <= 255 characters
           logger.error("message topic too long, truncating")
           mxlen=amqp_ss_maxlen
           while( topic.encode("utf8")[mxlen-1] & 0xc0 == 0xc0 ):
               mxlen -= 1
           topic = topic.encode("utf8")[0:mxlen].decode("utf8")


        if not exchange :
            exchange=self.props['exchange']
 
        if self.props['message_ttl']:
           ttl = "%d" * int(durationToSeconds(self.props['message_ttl']) * 1000 )
        else:
           ttl = "0"   

        if topic.startswith('v02'): #unless explicitly otherwise
           v2m = sarra.v2wrapper.Message(body) 
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

                for x in exchange:
                    self.channel.basic_publish( AMQP_Message, x, topic ) 
                    self.channel.tx_commit()
                    logger.info("published {} to {} ".format(body, exchange) )

                return # no failure == success :-)

            except Exception as err:
                logger.warning("tmpc.amqp.putNewMessage: failed %s: %s" % (exchange, err))
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
            self.connection.close()

        except Exception as err:
            logger.error("sr_amqp/close 2: {}".format(err))
            logger.debug("sr_amqp/close 2 Exception details:", exc_info=True)
        # FIXME toclose not useful as we don't close channels anymore
        self.connection=None
