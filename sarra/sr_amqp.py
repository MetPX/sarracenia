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
from amqp import AMQPError

from sarra.sr_util import *

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
        for channel in self.toclose:
            if self.use_pika:
                cid = channel.channel_number
            else:
                cid = channel.channel_id
            self.logger.debug("closing channel_id: %s" % cid)
            try:
                channel.close()
            except AMQPError as err:
                self.logger.error("unable to close channel {} with {}".format(channel, err))
                self.logger.debug('Exception details:', exc_info=True)
            except Exception as err:
                self.logger.error("Unexpected error: {}".format(err))
                self.logger.debug("Exception details:", exc_info=True)
        try:
            self.connection.close()
        except AMQPError as err:
            self.logger.error("unable to close connection {} with {}".format(self.connection, err))
            self.logger.debug('Exception details:', exc_info=True)
        except Exception as err:
            self.logger.error("Unexpected error: {}".format(err))
            self.logger.debug("Exception details:", exc_info=True)
        self.toclose = []
        self.connection = None

    def connect(self):
        """Connect to amqp broker with the amqp client library that has been chosen.
 
        :returns True if successful, False otherwise.
        """
        while True:
            try:
                self.logger.debug("Connecting %s %s (ssl %s)" % (self.host, self.user, self.ssl))
                host = self.host
                if self.port is not None:
                    host = host + ':%s' % self.port
                self.logger.debug("%s://%s:<pw>@%s%s ssl=%s" % (self.protocol, self.user, host, self.vhost, self.ssl))
                if self.use_amqp:
                    self.logger.info("Using amqp module (AMQP 0-9-1)")
                    self.connection = amqp.Connection(host, userid=self.user, password=self.password,
                                                      virtual_host=self.vhost, ssl=self.ssl)
                    if hasattr(self.connection, 'connect'):
                        # check for amqp 1.3.3 and 1.4.9 because connect doesn't exist in those older versions
                        self.connection.connect()
                elif self.use_amqplib:
                    self.logger.info("Using amqplib module (mostly AMQP 0-8)")
                    self.connection = amqplib_0_8.Connection(host, userid=self.user, password=self.password,
                                                             virtual_host=self.vhost, ssl=self.ssl)
                elif self.use_pika:
                    self.logger.info("Using pika module (AMQP 0-9-1)")
                    credentials = pika.PlainCredentials(self.user, self.password)
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
            except AMQPError as err:
                self.logger.error("AMQP cannot connect to {} with {}".format(self.host, err))
                self.logger.debug('Exception details: ', exc_info=True)

                if not self.loop:
                    self.logger.error("Could not connect to broker")
                    return False

                self.logger.error("Sleeping 5 seconds ...")
                time.sleep(5)
            except Exception as err:
                self.logger.error("Unexpected error: {}".format(err))
                self.logger.debug("Exception details:", exc_info=True)
                return False

    def exchange_declare(self, exchange, edelete=False, edurable=True):
        try:
            self.channel.exchange_declare(exchange, 'topic', auto_delete=edelete, durable=edurable)
            self.logger.info("declaring exchange %s (%s@%s)" % (exchange, self.user, self.host))
        except AMQPError as err:
            self.logger.error("could not declare exchange %s (%s@%s): %s" % (exchange, self.user, self.host, err))
            self.logger.debug('Exception details: ', exc_info=True)
        except Exception as err:
            self.logger.error("Unexpected error: {}".format(err))
            self.logger.debug("Exception details:", exc_info=True)

    def exchange_delete(self, exchange):

        # never delete basic and permanent exchanges...

        if exchange in ['xpublic', 'xs_mqtt_public', 'xreport']:
            self.logger.info("exchange %s remains" % exchange)
            return

        if exchange.startswith('xwinnow'):
            self.logger.info("exchange %s remains" % exchange)
            return

        # proceed for all others
        try:
            self.channel.exchange_delete(exchange)
            self.logger.info("deleting exchange %s (%s@%s)" % (exchange, self.user, self.host))
        except AMQPError as err:
            self.logger.error("could not delete exchange %s (%s@%s): %s" % (exchange, self.user, self.host, err))
            self.logger.debug('Exception details: ', exc_info=True)
        except Exception as err:
            self.logger.error("Unexpected error: {}".format(err))
            self.logger.debug("Exception details:", exc_info=True)

    def new_channel(self):
        channel = self.connection.channel()
        self.toclose.append(channel)
        return channel

    def queue_delete(self, queue_name):
        self.logger.info("deleting queue %s (%s@%s)" % (queue_name, self.user, self.host))
        try:
            self.channel.queue_delete(queue_name)
        except AMQPError as err:
            (stype, svalue, tb) = sys.exc_info()
            error_str = '%s' % svalue
            if 'NOT_FOUND' in error_str:
                return
            self.logger.error("could not delete queue %s (%s@%s): %s" % (queue_name, self.user, self.host, err))
            self.logger.debug('Exception details: ', exc_info=True)
        except Exception as err:
            self.logger.error("Unexpected error: {}".format(err))
            self.logger.debug("Exception details:", exc_info=True)

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
        self.prefetch = prefetch

    def build(self):
        self.logger.debug("building consumer")
        self.channel = self.hc.new_channel()
        # MG : seems important to have, but behave correctly without it
        self.channel.basic_recover(requeue=True)
        if self.prefetch != 0:
            prefetch_size = 0  # dont care
            a_global = False  # only apply here
            self.channel.basic_qos(prefetch_size, self.prefetch, a_global)

    def ack(self, msg):
        self.logger.debug("--------------> ACK")
        self.logger.debug("--------------> %s" % msg.delivery_tag)
        self.channel.basic_ack(msg.delivery_tag)

    def consume(self, queuename):

        msg = None

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
        except AMQPError as err:
            # FIXME: PAS-2019. recursion here may be dangerous when things go badly... 
            #        will stack grow without bound?
            self.logger.error("sr_amqp/consume: could not consume in queue %s: %s" % (queuename, err))
            self.logger.debug('Exception details: ', exc_info=True)
            if self.hc.loop:
                self.hc.reconnect()
                self.logger.debug("consume resume ok")
                msg = self.consume(queuename)
        except Exception as err:
            self.logger.error("Unexpected error: {}".format(err))
            self.logger.debug("Exception details:", exc_info=True)

        if msg is not None:
            msg.isRetry = False

        return msg


# ==========
# Publisher
# ==========

class Publisher:

    def __init__(self, hostconnect):
        self.hc = hostconnect
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
        if not hasattr(self, 'channel'):
            return False
        alarm_set(self.iotime)
        try:
            if self.hc.use_pika:
                self.channel.confirm_delivery()
            else:
                self.channel.tx_select()
        except AMQPError:
            alarm_cancel()
            return False
        except Exception as err:
            self.logger.error("unexpected error: {}".format(err))
            self.logger.debug("Exception details:", exc_info=True)
        alarm_cancel()
        return True

    def publish(self, exchange_name, exchange_key, message, mheaders, mexp=0):
        try:
            if self.hc.use_amqp:
                self.logger.debug("publish AMQP is used")
                if mexp:
                    expms = '%s' % mexp
                    msg = amqp.Message(message, content_type='text/plain', application_headers=mheaders,
                                       expiration=expms)
                else:
                    msg = amqp.Message(message, content_type='text/plain', application_headers=mheaders)
                self.channel.basic_publish(msg, exchange_name, exchange_key)
                self.channel.tx_commit()
            elif self.hc.use_amqplib:
                self.logger.debug("publish AMQPLIB is used")
                if mexp:
                    expms = '%s' % mexp
                    msg = amqplib_0_8.Message(message, content_type='text/plain', application_headers=mheaders,
                                              expiration=expms)
                else:
                    msg = amqplib_0_8.Message(message, content_type='text/plain', application_headers=mheaders)
                self.channel.basic_publish(msg, exchange_name, exchange_key)
                self.channel.tx_commit()
            elif self.hc.use_pika:
                self.logger.debug("publish PIKA is used")
                if mexp:
                    expms = '%s' % mexp
                    properties = pika.BasicProperties(content_type='text/plain', delivery_mode=1, headers=mheaders,
                                                      expiration=expms)
                else:
                    properties = pika.BasicProperties(content_type='text/plain', delivery_mode=1, headers=mheaders)
                self.channel.basic_publish(exchange_name, exchange_key, message, properties, True)
            else:
                self.logger.debug("Couldn't choose an AMQP client library, setting it back to default amqp")
                self.hc.use_amqp = True
                raise ConnectionError("No AMQP client library is set")
            return True
        except AMQPError as err:
            if self.hc.loop:
                self.logger.error("sr_amqp/publish: Sleeping 5 seconds ... and reconnecting")
                self.logger.debug('Exception details: ', exc_info=True)
                time.sleep(5)
                self.hc.reconnect()
                return self.publish(exchange_name, exchange_key, message, mheaders, mexp)
            else:
                self.logger.error("sr_amqp/publish: could not publish %s %s %s %s with %s"
                                  % (exchange_name, exchange_key, message, mheaders, err))
                self.logger.debug('Exception details: ', exc_info=True)
                return False
        except Exception as err:
            self.logger.error("unexpected error: {}".format(err))
            self.logger.debug("Exception details:", exc_info=True)
            return False


    def restore_clear(self):
        if self.restore_queue and self.restore_exchange:
            try:
                self.channel.queue_unbind(self.restore_queue, self.restore_exchange, '#')
            except AMQPError:
                pass
            except Exception as err:
                self.logger.error("Unexpected error: {}".format(err))
                self.logger.debug("Exception details:", exc_info=True)
            self.restore_queue = None

        if self.restore_exchange:
            try:
                self.channel.exchange_delete(self.restore_exchange)
            except AMQPError:
                pass
            except Exception as err:
                self.logger.error("Unexpected error: {}".format(err))
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
        except AMQPError as err:
            self.logger.error("sr_amqp/restore_set: restore_set exchange %s queuename %s with %s"
                              % (self.restore_exchange, self.restore_queue, err))
            self.logger.debug('Exception details: ', exc_info=True)
            os._exit(1)
        except Exception as err:
            self.logger.error("Unexpected error: {}".format(err))
            self.logger.debug("Exception details:", exc_info=True)


# ==========
# Queue
# ==========

class Queue:

    def __init__(self, hc, qname, auto_delete=False, durable=False, reset=False):

        self.hc = hc
        self.logger = self.hc.logger
        self.name = qname
        self.qname = qname
        self.channel = None
        self.auto_delete = auto_delete
        self.durable = durable
        self.reset = reset

        self.expire = 0
        self.message_ttl = 0

        self.bindings = []

        self.hc.add_build(self.build)

    def add_binding(self, exchange_name, exchange_key):
        self.bindings.append((exchange_name, exchange_key))

    def add_expire(self, expire):
        self.expire = expire

    def add_message_ttl(self, message_ttl):
        self.message_ttl = message_ttl

    def bind(self, exchange_name, exchange_key):
        self.channel.queue_bind(self.qname, exchange_name, exchange_key)

    def build(self):
        self.logger.debug("building queue %s" % self.name)
        self.channel = self.hc.new_channel()

        # reset
        if self.reset:
            try:
                self.channel.queue_delete(self.name)
            except AMQPError as err:
                self.logger.error("could not delete queue %s (%s@%s) with %s"
                                  % (self.name, self.hc.user, self.hc.host, err))
                self.logger.debug('Exception details:', exc_info=True)
            except Exception as err:
                self.logger.error("Unexpected error: {}".format(err))
                self.logger.debug("Exception details:", exc_info=True)

        # declare queue

        msg_count = self.declare()

        # something went wrong
        if msg_count == -1:
            return

        # no bindings... in declare mode

        if len(self.bindings) == 0:
            self.logger.debug("queue build done in declare mode")
            return

        # queue bindings
        last_exchange_name = ''
        bound=0
        backoff=1
        while bound < len(self.bindings):
            for exchange_name, exchange_key in self.bindings:
                self.logger.debug("binding queue to exchange=%s with key=%s" % (exchange_name, exchange_key))
                try:
                    self.bind(exchange_name, exchange_key)
                    last_exchange_name = exchange_name
                    bound += 1
                    continue
                except AMQPError as err:
                    self.logger.error("bind queue: %s to exchange: %s with key: %s failed with %s"
                                  % (self.name, exchange_name, exchange_key, err))
                    self.logger.error("Permission issue with %s@%s or exchange %s not found."
                                  % (self.hc.user, self.hc.host, exchange_name))
                    self.logger.debug('Exception details:', exc_info=True)
                except Exception as err:
                    self.logger.error("Unexpected error: {}".format(err))
                    self.logger.debug("Exception details:", exc_info=True)
                self.logger.error( "sleeping %g seconds to try binding again..." % backoff )
                time.sleep(backoff)
                if backoff < 60:
                    backoff *= 2

        # always allow pulse binding... use last exchange_name
        if last_exchange_name:
            exchange_key = 'v02.pulse.#'
            self.logger.debug("binding queue to exchange=%s with key=%s (pulse)" % (last_exchange_name, exchange_key))
            try:
                self.bind(last_exchange_name, exchange_key)
            except AMQPError as err:
                self.logger.error("bind queue: %s to exchange: %s with key: %s failed.."
                                  % (self.name, last_exchange_name, exchange_key))
                self.logger.error("Permission issue with %s@%s or exchange %s not found with %s"
                                  % (self.hc.user, self.hc.host, last_exchange_name, err))
                self.logger.debug('Exception details:', exc_info=True)
            except Exception as err:
                self.logger.error("Unexpected error: {}".format(err))
                self.logger.debug("Exception details:", exc_info=True)
        else:
            self.logger.warning("this process will not receive pulse message")

        self.logger.debug("queue build done")

    def declare(self):
        self.logger.debug("declaring queue %s" % self.name)

        # queue arguments
        args = {}
        if self.expire > 0:
            args['x-expires'] = self.expire
        if self.message_ttl > 0:
            args['x-message-ttl'] = self.message_ttl

        # create queue
        try:
            if self.hc.use_pika:
                self.logger.debug("queue_declare PIKA is used")
                q_dclr_ok = self.channel.queue_declare(self.name, passive=False, durable=self.durable,
                                                       exclusive=False, auto_delete=self.auto_delete, arguments=args)
                method = q_dclr_ok.method
                self.qname, msg_count, consumer_count = method.queue, method.message_count, method.consumer_count
            else:
                self.logger.debug("queue_declare AMQP or AMQPLIB is used")
                self.qname, msg_count, consumer_count = self.channel.queue_declare(self.name, passive=False,
                                                                                   durable=self.durable,
                                                                                   exclusive=False,
                                                                                   auto_delete=self.auto_delete,
                                                                                   nowait=False, arguments=args)
            self.logger.debug("queue declare done")
            return msg_count
        except AMQPError as err:
            self.logger.error("sr_amqp/build, queue declare: %s failed...(%s@%s) with %s"
                              % (self.name, self.hc.user, self.hc.host, err))
            self.logger.debug('Exception details: ', exc_info=True)
            return -1
        except Exception as err:
            self.logger.error("Unexpected error: {}".format(err))
            self.logger.debug("Exception details:", exc_info=True)
