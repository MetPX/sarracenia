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

import logging

import sarracenia
from sarracenia.moth.amqp import AMQP, amqp_ss_maxlen, default_options

import socket
import time
import queue

logger = logging.getLogger(__name__)

class AMQPConsumer(AMQP):
    """
        Extension of the existing AMQP implementation, replacing basic_get with a consumer.
        https://github.com/celery/py-amqp#quick-overview

        Set amqp_consumer True in the config to use this instead of the regular AMQP class.

        TODO: 
          - how does this work with the batch and prefetch options? 
          - set our own consumer tag
          - make timeout configurable?
    """

    def __init__(self, props, is_subscriber) -> None:
        super().__init__(props, is_subscriber)
        self._raw_msg_q = None 
        # "The consumer tag is local to a connection, so two clients can use the same consumer tags. 
        #  If this field is empty the server will generate a unique tag."
        self._request_consumer_tag = '' # TODO set to something useful
        self._active_consumer_tag = None

        # control log level in config file:
        # set sarracenia.moth.amqpconsumer.AMQPConsumer.logLevel debug
        me = "%s.%s" % (__class__.__module__, __class__.__name__)
        if ('settings' in self.o) and (me in self.o['settings']):
            for s in self.o['settings'][me]:
                self.o[s] = self.o['settings'][me][s]
            if 'logLevel' in self.o['settings'][me]:
                logger.setLevel(self.o['logLevel'].upper())

    def __get_on_message(self, msg):
        """ Callback for AMQP basic_consume, called when the broker sends a new message.
        """
        logger.debug(f"new message pushed from broker: {msg.body}")
        # This will block until the msg can be put in the queue
        self._raw_msg_q.put(msg)

    def getSetup(self) -> None:
        super().getSetup()
        # (re)create queue. Anything in the queue is invalid after re-creating a connection.
        self._raw_msg_q = queue.Queue() 
        self._active_consumer_tag = self.channel.basic_consume(queue=self.o['queueName'], 
                                                               consumer_tag=self._request_consumer_tag,
                                                               no_ack=False, 
                                                               callback=self.__get_on_message)
        logger.info(f"registered consumer with tag {self._active_consumer_tag}")
        if self._request_consumer_tag != '' and self._request_consumer_tag != self._active_consumer_tag:
            logger.warning(f"active consumer tag {self._active_consumer_tag} is different than " + 
                           f"requested consumer tag {self._request_consumer_tag}")

    def getNewMessage(self) -> sarracenia.Message:
        """ Mostly a copy of moth.amqp.AMQP's getNewMessage.
        """

        if not self.is_subscriber:  #build_consumer
            logger.error("getting from a publisher")
            return None

        try:
            if not self.connection:
                self.getSetup()

            # trigger incoming event processing
            try:
                self.connection.drain_events(timeout=0.1) # TODO configurable timeout?
            except TimeoutError:
                pass
            # In newer Python versions, socket.timeout is "a deprecated alias of TimeoutError", but it's not on
            # older versions (3.6) and needs to be handled separately
            except socket.timeout:
                pass

            try:
                # don't block waiting for the queue to be available, better to just try again later
                raw_msg = self._raw_msg_q.get_nowait()
            except queue.Empty:
                raw_msg = None
            
            if (raw_msg is None) and (self.connection.connected):
                return None
            else:
                self.metrics['rxByteCount'] += len(raw_msg.body)
                try: 
                    msg = self._msgRawToDict(raw_msg)
                except Exception as err:
                    logger.error("message decode failed. raw message: %s" % raw_msg.body )
                    logger.debug('Exception details: ', exc_info=True)
                    msg = None
                if msg is None:
                    self.metrics['rxBadCount'] += 1
                    return None
                else:
                    self.metrics['rxGoodCount'] += 1
                if hasattr(self.o, 'fixed_headers'):
                    for k in self.o.fixed_headers:
                        msg[k] = self.o.fixed_headers[k]
                logger.debug("new msg: %s" % msg)
                return msg
        except Exception as err:
            logger.warning("failed %s: %s" %
                           (self.o['queueName'], err))
            logger.debug('Exception details: ', exc_info=True)

        if not self.o['message_strategy']['stubborn']:
            return None

        logger.warning('lost connection to broker')
        self.close()
        time.sleep(1)
        return None

    def close(self) -> None:
        # TODO cancel consumer with basic_cancel(consumer_tag)?
        if self._active_consumer_tag:
            try:
                self.channel.basic_cancel(self._active_consumer_tag)
                logger.info(f"cancelled consumer with tag {self._active_consumer_tag}")
            except Exception as e:
                logger.warning(f"failed to cancel consumer with tag {self._active_consumer_tag} {e}")
                logger.debug("Exception details:", exc_info=True)
        self._active_consumer_tag = None
        super().close()

