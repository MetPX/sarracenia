#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#
# sr_amqp.py : python3 utility tools from python's amqplib
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Sep 22 10:41:32 EDT 2015
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

import amqp

from sarra.sr_util import *
from urllib.parse import unquote

# ======= amqp alternative libraries ========
try:
    import amqplib.client_0_8 as amqplib_0_8
except ImportError:
    pass
try:
    import pika
except ImportError:
    pass
# ===========================================


# ===========
# HostConnect
# ===========

class HostConnect:
    def __init__(self, logger=None):

        self.loop = True

        self.connection = None
        self.channel = None
        self.ssl = False

        # FIXME propagation of root logger should be avoided we are doing it all over the sr_ code
        #  Every module should have its own logger correct usage would be self.logger = logging.getLogger(__name__)
        #  Also it have a default value of None which doesn't make sense as the execution will fails through many ways
        self.logger = logger

        self.protocol = 'amqp'
        self.host = 'localhost'
        self.vhost = None
        self.port = None
        self.user = 'guest'
        self.password = 'guest'

        self.rebuilds = []
        self.toclose = []

        # Default behavior is to use amqp and not the alternatives
        self.use_amqp = True
        self.use_amqplib = False
        self.use_pika = False

    def add_build(self, func):
        self.rebuilds.append(func)

    def close(self):
        """

         20200404-PAS FIXME
         as per: https://www.rabbitmq.com/channels.html
          "A channel only exists in the context of a connection and never on its own. 
           When a connection is closed, so are all channels on it."

         so wondering why we shut down all the channels here.
        """
        # TODO remove those commented lines
        #for channel in self.toclose:
        #    if self.use_pika:
        #        cid = channel.channel_number
        #    else:
        #        cid = channel.channel_id
        #    self.logger.debug("sr_amqp/close 0 closing channel_id: %s" % cid)
        #    try:
        #        channel.close()
        #    except Exception as err:
        #        #by default ignore.. doesn't matter... but for debugging, might be interesting...
        #        #self.logger.error("sr_amqp/close 1 unable to close channel {} with {}".format(channel, err))
        #        self.logger.debug('sr_amqp/close 1 unable to close channel {} with {} :'.format(channel,err), exc_info=True)

        try:
            self.connection.close()
        except Exception as err:
            self.logger.error("sr_amqp/close 2: {}".format(err))
            self.logger.debug("sr_amqp/close 2 Exception details:", exc_info=True)
        # FIXME toclose not useful as we don't close channels anymore
        self.toclose = []
        self.connection = None

    def connect(self):
        """Connect to amqp broker with the amqp client library that has been chosen.
 
        :returns True if successful, False otherwise.
        """
        ebo=1
        while True:
            try:
                self.logger.debug("Connecting %s %s (ssl %s)" % (self.host, self.user, self.ssl))
                host = self.host
                if self.port is not None:
                    host = host + ':%s' % self.port
                self.logger.debug("%s://%s:<pw>@%s%s ssl=%s" % (self.protocol, self.user, host, self.vhost, self.ssl))
                if self.use_amqp:
                    self.logger.info("Using amqp module (AMQP 0-9-1)")
                    self.connection = amqp.Connection(host, userid=self.user, password=unquote(self.password),
                                                      virtual_host=self.vhost, ssl=self.ssl)
                    if hasattr(self.connection, 'connect'):
                        # check for amqp 1.3.3 and 1.4.9 because connect doesn't exist in those older versions
                        self.connection.connect()
                elif self.use_amqplib:
                    self.logger.info("Using amqplib module (mostly AMQP 0-8)")
                    self.connection = amqplib_0_8.Connection(host, userid=self.user, password=unquote(self.password),
                                                             virtual_host=self.vhost, ssl=self.ssl)
                elif self.use_pika:
                    self.logger.info("Using pika module (AMQP 0-9-1)")
                    credentials = pika.PlainCredentials(self.user, unquote(self.password))
                    parameters = pika.connection.ConnectionParameters(self.host, virtual_host=self.vhost,
                                                                      credentials=credentials, ssl=self.ssl)
                    self.connection = pika.BlockingConnection(parameters)
                else:
                    self.use_amqp = True
                    raise ConnectionError("Not using any amqp client library, setting it back to default: AMQP")
                self.channel = self.new_channel()
                self.logger.debug("Connected ")
                for func in self.rebuilds:
                    func()
                return True

            except Exception as err:
                self.logger.error("AMQP cannot connect to {} with {}".format(self.host, err))
                self.logger.debug('Exception details: ', exc_info=True)

                if not self.loop:
                    self.logger.error("giving up. Failed to connect to broker")
                    return False

            if ebo < 60 : ebo *= 2
            self.logger.info("Sleeping {} seconds ...".format( ebo) )
            time.sleep(ebo)

    def exchange_declare(self, exchange, edelete=False, edurable=True):
        try:
            self.channel.exchange_declare(exchange, 'topic', auto_delete=edelete, durable=edurable)
            self.logger.info("declaring exchange %s (%s@%s)" % (exchange, self.user, self.host))
        except Exception as err:
            self.logger.error("could not declare exchange %s (%s@%s): %s" % (exchange, self.user, self.host, err))
            self.logger.debug('Exception details: ', exc_info=True)

    def exchange_delete(self, exchange):

        # never delete basic and permanent exchanges...

        if exchange in ['xpublic', 'xs_mqtt_public', 'xreport']:
            self.logger.info("exchange %s remains" % exchange)
            return

        if exchange.startswith('xwinnow'):
            self.logger.info("exchange %s remains" % exchange)
            return

        # proceed for all others, but only delete unused exchanges (no queues bound)
        try:
            self.channel.exchange_delete(exchange, if_unused=True)
            self.logger.info("deleting exchange %s (%s@%s)" % (exchange, self.user, self.host))
        except Exception as err:
            self.logger.error("could not delete exchange %s (%s@%s): %s" % (exchange, self.user, self.host, err))
            self.logger.debug('Exception details: ', exc_info=True)

    def new_channel(self):
        channel = self.connection.channel()
        self.toclose.append(channel)
        return channel

    def queue_delete(self, queue_name):
        self.logger.info("deleting queue %s (%s@%s)" % (queue_name, self.user, self.host))
        try:
            self.channel.queue_delete(queue_name)
        except Exception as err:
            (stype, svalue, tb) = sys.exc_info()
            error_str = '%s' % svalue
            if 'NOT_FOUND' in error_str:
                return
            self.logger.error("could not delete queue %s (%s@%s): %s" % (queue_name, self.user, self.host, err))
            self.logger.debug('Exception details: ', exc_info=True)

    def reconnect(self):
        self.close()
        self.connect()

    def set_url(self, url):
        self.protocol = url.scheme
        self.user = url.username
        self.password = url.password
        self.host = url.hostname
        self.port = url.port
        self.vhost = url.path

        if self.protocol == 'amqps':
            self.ssl = True
            if self.port is None:
                self.port = 5671

        if self.vhost is None:
            self.vhost = '/'
        if self.vhost == '':
            self.vhost = '/'

    def choose_amqp_alternative(self, use_amqplib=False, use_pika=False):
        # 1 alternative could be chosen there (By default 0 alternative is chosen)
        self.use_amqplib = use_amqplib
        self.use_pika = use_pika

        # Ensure that if 1 alternative is chosen we will not use the default amqp library
        self.use_amqp = not (self.use_amqplib or self.use_pika)


# ==========
# Consumer
# ==========

class Consumer:

    def __init__(self, hostconnect):

        self.hc = hostconnect
        # FIXME root logger propagation
        self.logger = self.hc.logger
        self.prefetch = 20
        self.channel = None

        self.exchange_type = 'topic'

        self.hc.add_build(self.build)

        self.retry_msg = raw_message(self.logger)

        self.for_pika_msg = None
        if self.hc.use_pika:
            self.for_pika_msg = raw_message(self.logger)

    def add_prefetch(self, prefetch):
        # FIXME confusing name: should be call set_prefetch (this looks like a setter here)
        #  add_* would 'add' some value to a list, btw why would we need a setter
        self.prefetch = prefetch

    def build(self):
        self.logger.debug("building consumer")
        self.channel = self.hc.new_channel()
        if self.prefetch != 0:
            # FIXME if we dont care and only apply here why we put it in variable
            prefetch_size = 0  # dont care
            a_global = False  # only apply here
            self.channel.basic_qos(prefetch_size, self.prefetch, a_global)

    def ack(self, msg):
        self.logger.debug("--------------> ACK")
        self.logger.debug("--------------> %s" % msg.delivery_tag)
        # TODO 1. figure out if there is a risk of delivery_tag being 0 as we ack only single messages
        #  (default mutiple=False) and zero is reserved to ack multiple messages
        # TODO 2. basic_ack may raise many type of Exception that are not handled at this level which will then be
        #  reraise from here. Ensure that it is the expected behaviour and that we document those right here. Then
        #  every caller of this method will be advised of what to handle.

        try:
            ret = self.channel.basic_ack(msg.delivery_tag)
            self.logger.debug( "basic_ack returned: %s " % ret )
        except Exception as err: # cannot recover failed ack, only applies within connection.
            self.logger.warning("sr_amqp/basic_ack could not ack in: %s" % (err) )
            self.logger.debug('Exception details: ', exc_info=True)
            self.hc.reconnect()
            self.logger.debug( "reconnected after failed basic_ack" )

    def consume(self, queuename):

        msg = None

        while True: 
            try:
                if self.hc.use_pika:
                    # self.logger.debug("consume PIKA is used")
                    method_frame, properties, body = self.channel.basic_get(queuename)
                    if method_frame and properties and body:
                        self.for_pika_msg.pika_to_amqplib(method_frame, properties, body)
                        msg = self.for_pika_msg
                else:
                    # self.logger.debug("consume AMQP or AMQPLIB is used")
                    msg = self.channel.basic_get(queuename)

                if msg is not None:
                    msg.isRetry = False
                return msg

            except Exception as err:
                # TODO Maybe provide different handling for irrecoverable vs recoverable error such:
                #  1. irrecoverable would include reconnection handling (ie hc.reconnect)
                #  2. recoverable would have a different handling which is unkown at this point
                self.logger.warning("sr_amqp/consume: could not consume in queue %s: %s" % (queuename, err))
                self.logger.debug('Exception details: ', exc_info=True)


            self.hc.reconnect()
            self.logger.debug("consume resume ok")


# ==========
# Publisher
# ==========

class Publisher:

    def __init__(self, hostconnect):
        self.hc = hostconnect
        # FIXME root logger propagation
        self.logger = self.hc.logger
        self.hc.add_build(self.build)
        self.iotime = 30
        self.restore_exchange = None
        self.restore_queue = None
        self.channel = None

    def build(self):
        self.channel = self.hc.new_channel()
        if self.hc.use_pika:
            self.channel.confirm_delivery()
        else:
            self.channel.tx_select()

    def is_alive(self):
        # FIXME: is_alive is dead code, it caused problems and so was removed.
        #  there are two is_alive's not sure which one is the problem.
        #  https://github.com/MetPX/sarracenia/issues/236
        # FIXME 2: if is_alive is dead code, why hb_pulse plugins using it and is hb_pulse used anywhere ?
        if self.channel is None:
            return False
        alarm_set(self.iotime)
        try:
            if self.hc.use_pika:
                self.channel.confirm_delivery()
            else:
                self.channel.tx_select()
        except Exception as err:
            self.logger.error("is_alive/confirm_delivery or tx_select: {}".format(err))
            self.logger.debug("Exception details:", exc_info=True)
        alarm_cancel()
        return True

    def publish(self, exchange_name, exchange_key, message, mheaders, mexp=0, persistent=True):
      """ Args:
            persistent (boolean): Whether the message should be published as persistent 
              (``True``, ``delivery_mode=2``) or non-persistent (``False``, ``delivery_mode=1``). 
              Default is ``True``. 
      """

      deliv_mode = 2 if persistent else 1
      ebo=2
      connected=True
      while True:
        if 'v03.' in exchange_key:
            ct='application/json'
        else:
            ct='text/plain'
        try:
            if self.hc.use_amqp:
                self.logger.debug("publish AMQP is used")
                if mexp:
                    expms = '%s' % mexp
                    msg = amqp.Message(message, content_type=ct, application_headers=mheaders,
                                       expiration=expms, delivery_mode=deliv_mode)
                else:
                    msg = amqp.Message(message, content_type=ct, application_headers=mheaders,
                                       delivery_mode=deliv_mode)
                self.channel.basic_publish(msg, exchange_name, exchange_key)
                self.channel.tx_commit()
            elif self.hc.use_amqplib:
                self.logger.debug("publish AMQPLIB is used")
                if mexp:
                    expms = '%s' % mexp
                    msg = amqplib_0_8.Message(message, content_type=ct, application_headers=mheaders,
                                              expiration=expms, delivery_mode=deliv_mode)
                else:
                    msg = amqplib_0_8.Message(message, content_type=ct, application_headers=mheaders,
                                              delivery_mode=deliv_mode)
                self.channel.basic_publish(msg, exchange_name, exchange_key)
                self.channel.tx_commit()
            elif self.hc.use_pika:
                self.logger.debug("publish PIKA is used")
                if mexp:
                    expms = '%s' % mexp
                    properties = pika.BasicProperties(content_type=ct, delivery_mode=deliv_mode, headers=mheaders,
                                                      expiration=expms)
                else:
                    properties = pika.BasicProperties(content_type=ct, delivery_mode=deliv_mode, headers=mheaders)
                self.channel.basic_publish(exchange_name, exchange_key, message, properties, True)
            else:
                self.logger.debug("Couldn't choose an AMQP client library, setting it back to default amqp")
                self.hc.use_amqp = True
                raise ConnectionError("No AMQP client library is set")
            return True
        except Exception as err:
                if  ebo <  65: 
                     ebo = ebo * 2 
                self.logger.error("sr_amqp/publish: Sleeping %d seconds ... and reconnecting" % ebo)
                self.logger.debug('Exception details: ', exc_info=True)
                time.sleep(ebo)
                connected=False

        if not connected:
            self.hc.reconnect()


    def restore_clear(self):
        if self.restore_queue and self.restore_exchange:
            try:
                self.channel.queue_unbind(self.restore_queue, self.restore_exchange, '#')
            except Exception as err:
                self.logger.error("08 restore/unbind: {}".format(err))
                self.logger.debug("Exception details:", exc_info=True)
            self.restore_queue = None

        if self.restore_exchange:
            try:
                self.channel.exchange_delete(self.restore_exchange, if_unused=True)
            except Exception as err:
                self.logger.error("09 exchange_delete: {}".format(err))
                self.logger.debug("Exception details:", exc_info=True)
            self.restore_exchange = None

    def restore_set(self, parent):
        try:
            self.restore_queue = parent.restore_queue
            self.restore_exchange = parent.post_exchange
            self.restore_exchange += '.%s.%s.restore.' % (parent.program_name, parent.config_name)
            self.restore_exchange += str(random.randint(0, 100000000)).zfill(8)
            self.channel.exchange_declare(self.restore_exchange, 'topic', auto_delete=True, durable=False)
            self.channel.queue_bind(self.restore_queue, self.restore_exchange, '#')
        except Exception as err:
            self.logger.error("sr_amqp/restore_set: restore_set exchange %s queuename %s with %s"
                              % (self.restore_exchange, self.restore_queue, err))
            self.logger.debug('Exception details: ', exc_info=True)
            os._exit(1)


# ==========
# Queue
# ==========

class Queue:

    __default_queue_properties = { 'auto_delete':False, 'durable':False, 'reset':False, \
        'expire':0, 'message_ttl':0, 'declare':True, 'bind':True }
    # FIXME using mutable default argument is not recommended, this is an anti-pattern
    #  https://docs.quantifiedcode.com/python-anti-patterns/correctness/mutable_default_value_as_argument.html
    #  why not declaring every named argument as we would do normally ? This would improve:
    #  1. READABILITY: keep a good readability when someone want to declare a queue and want to change a default value
    #     which would be easy at first sight, this procedure obfuscate args we might want to change
    #  2. CORRECTNESS: avoid the risk of a catastrophic change that would include a list (maybe bindings) in the args
    #     which we only shallow copy and where values would be shared among all instances
    def __init__(self, hc, qname, prop_arg=__default_queue_properties ):

        # have arguments override defaults.
        properties=Queue.__default_queue_properties.copy()
        properties.update(prop_arg)

        self.hc = hc
        # FIXME root logger propagation
        self.logger = self.hc.logger
        self.name = qname
        self.qname = qname
        self.channel = None
        self.properties=properties

        if (properties['expire'] == None): properties['expire'] = 0
        if (properties['message_ttl'] == None): properties['message_ttl'] = 0

        self.bindings = []

        self.hc.add_build(self.build)

    def add_binding(self, exchange_name, exchange_key):
        self.bindings.append((exchange_name, exchange_key))

    def bind(self, exchange_name, exchange_key):
        # FIXME why does this method exist (it is only called by Queue.build), no external calls (ie like from
        #  sr_consumer the setter methods)
        self.channel.queue_bind(self.qname, exchange_name, exchange_key)

    def build(self):
        # TODO Too many reponsabilities in that single method, should consider breaking it
        #  down into reset(delete), bind and/or bind pulse with error handling encapsulated in each part.
        self.logger.debug("building queue %s" % self.name)
        self.channel = self.hc.new_channel()

        ebo=1
        while self.properties['declare']:
            try:
                # reset
                if self.properties['reset']:
                    try:
                        self.channel.queue_delete(self.name)
                    except Exception as err:
                        self.logger.error("could not delete queue %s (%s@%s) with %s"
                                          % (self.name, self.hc.user, self.hc.host, err))
                        self.logger.debug('Exception details:', exc_info=True)
    
                # declare queue
                self.declare()
                self.logger.info("declared queue %s (%s@%s) " % (self.name, self.hc.user, self.hc.host))
                break

            except Exception as err:
                self.logger.error("sr_amqp/build could not declare queue %s (%s@%s) with %s"
                                  % (self.name, self.hc.user, self.hc.host, err))
                self.logger.debug('Exception details:', exc_info=True)

            if ebo < 64: ebo *= 2 
            self.logger.info("sr_amqp/build sleeping {} seconds ...".format( ebo) )
            time.sleep(ebo)


        if not self.properties['bind']:
            return

        # no bindings... in declare mode

        if len(self.bindings) == 0:
            self.logger.debug("queue build done in declare mode")
            return

        # queue bindings
        last_exchange_name = ''
        bound=0
        backoff=1
        # FIXME bad loop: There is a loophole here...
        #  What if it has 6 bindings and the first 5 fails multiple times, we got unlucky and we then loop several
        #  times binding the same last one 6 times. Not only we fail binding the five first but we falsely think
        #  we did bind everything and also induce very poor performance because of the backoff sleep time
        while bound < len(self.bindings):
            for exchange_name, exchange_key in self.bindings:
                self.logger.debug("binding queue to exchange=%s with key=%s" % (exchange_name, exchange_key))
                try:
                    self.bind(exchange_name, exchange_key)
                    last_exchange_name = exchange_name
                    bound += 1
                    continue
                except Exception as err:
                    self.logger.error("bind queue: %s to exchange: %s with key: %s failed with %s"
                                  % (self.name, exchange_name, exchange_key, err))
                    # FIXME unsuitable error msg: The exception is too broad to conclude this is a permission issue
                    self.logger.error("Permission issue with %s@%s or exchange %s not found."
                                  % (self.hc.user, self.hc.host, exchange_name))
                    self.logger.debug('Exception details:', exc_info=True)
                self.logger.error( "sleeping %g seconds to try binding again..." % backoff )
                time.sleep(backoff)
                if backoff < 60:
                    backoff *= 2

        self.logger.debug("queue build done")

    def declare(self):
        self.logger.debug("declaring queue %s" % self.name)

        # queue arguments
        args = {}
        if self.properties['expire'] > 0:
            args['x-expires'] = self.properties['expire']
        if self.properties['message_ttl'] > 0:
            args['x-message-ttl'] = self.properties['message_ttl']

        # create queue
        if self.hc.use_pika:
                self.logger.debug("queue_declare PIKA is used")
                q_dclr_ok = self.channel.queue_declare(self.name, passive=False, durable=self.properties['durable'],
                                                       exclusive=False, auto_delete=self.properties['auto_delete'], arguments=args)
                # FIXME confusing variable naming: This is not a method but a namedtuple returned by the queue_declare
                method = q_dclr_ok.method
                self.qname, msg_count, consumer_count = method.queue, method.message_count, method.consumer_count
        else:
                self.logger.debug("queue_declare AMQP or AMQPLIB is used")
                self.qname, msg_count, consumer_count = self.channel.queue_declare(self.name, passive=False,
                                                                                   durable=self.properties['durable'],
                                                                                   exclusive=False,
                                                                                   auto_delete=self.properties['auto_delete'],
                                                                                   nowait=False, arguments=args)
        self.logger.debug("queue declare done: qname:{}, msg_count:{}, consumer_count:{}".format(self.qname, msg_count,
                                                                                                 consumer_count))
        return msg_count
