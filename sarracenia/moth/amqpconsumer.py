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

import time
import queue
import threading

logger = logging.getLogger(__name__)

class AMQPConsumer(AMQP):
    """
        Extension of the existing AMQP implementation, replacing basic_get with a consumer.
        https://github.com/celery/py-amqp#quick-overview

        Set amqp_consumer True in the config to use this instead of the regular AMQP class.

        TODO: 
          - how does this work with the batch and prefetch options? 
    """

    def __init__(self, props, is_subscriber) -> None:
        super().__init__(props, is_subscriber)
        self._raw_msg_q = queue.Queue() # Queue is thread safe
        self._consumer_thread = None
        self._thread_please_stop = False

        # control log level in config file:
        # set sarracenia.moth.amqpconsumer.AMQPConsumer.logLevel debug
        me = "%s.%s" % (__class__.__module__, __class__.__name__)
        if ('settings' in self.o) and (me in self.o['settings']):
            for s in self.o['settings'][me]:
                self.o[s] = self.o['settings'][me][s]
            if 'logLevel' in self.o['settings'][me]:
                logger.setLevel(self.o['logLevel'].upper())

    def __consumer_setup(self) -> None:
        """ Start consuming from the queue.
        """
        if not self.connection:
            self.getSetup()
        # docs.celeryq.dev/projects/amqp/en/latest/reference/amqp.channel.html#amqp.channel.Channel.basic_consume
        self.channel.basic_consume(self.o['queueName'], no_ack=False, callback=self.__get_on_message)
        self.__stop_thread() # make sure it's not already running
        self._consumer_thread = threading.Thread(target=self.__drain_events)
        self._consumer_thread.start()

    def __drain_events(self):
        """ Calls drain_events on the connection until told to stop.
        """
        logger.debug("thread starting")
        while not self._thread_please_stop:
            # This blocks until there's an event to deal with
            try:
                self.connection.drain_events(timeout=2) # TODO configurable timeout?
            except TimeoutError:
                pass
            except Exception as e:
                logger.error(f"exception occurred: {e}")
                logger.debug('Exception details: ', exc_info=True)
        logger.debug("thread stopping")
        self._consumer_thread = None

    def __get_on_message(self, msg):
        """ Callback for AMQP basic_consume, called when the broker sends a new message.
        """
        logger.debug(f"new message pushed from broker: {msg.body}")
        # This will block until the msg can be put in the queue
        self._raw_msg_q.put(msg)

    def __stop_thread(self):
        # need to stop consuming - tell the thread to stop, then join it and wait
        self._thread_please_stop = True
        if self._consumer_thread:
            self._consumer_thread.join()
        self._consumer_thread = None
        self._thread_please_stop = False # if True, the thread won't start again

    def _amqp_setup_signal_handler(self, signum, stack):
        logger.info("ok, asked to stop")
        self.please_stop=True
        self.__stop_thread()

    def getCleanUp(self) -> None:
        self.__stop_thread()
        super().getCleanUp()

    def getNewMessage(self) -> sarracenia.Message:
        """ Mostly a copy of moth.amqp.AMQP's getNewMessage.
        """

        if not self.is_subscriber:  #build_consumer
            logger.error("getting from a publisher")
            return None

        try:
            if not self.connection:
                self.getSetup()

            if not self._consumer_thread:
                self.__consumer_setup()

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
        try: 
            self.__stop_thread()
        except:
            pass
        super().close()
