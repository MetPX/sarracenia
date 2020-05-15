""" This file is part of metpx-sarracenia.

metpx-sarracenia
Documentation: https://github.com/MetPX/sarracenia

sr_amqp_unit_test.py : test utility tool used for sr_amqp


Code contributed by:
 Benoit Lapointe - Shared Services Canada
"""
import amqp
import re
import json
import logging
import os
import unittest
import urllib.parse

from io import StringIO
from unittest.mock import Mock, call, patch, DEFAULT

from amqp.connection import SSLError

try:
    from amqplib import client_0_8
except ImportError:
    pass
from amqp import AMQPError, RecoverableConnectionError, ResourceError, PreconditionFailed
from sarra.sr_amqp import HostConnect, Publisher, Consumer, Queue


class SrAmqpBaseCase(unittest.TestCase):
    xname = 'q_anonymous_exchange'
    qname = 'q_anonymous_queue'

    @classmethod
    def setUpClass(cls) -> None:
        logformat = '%(asctime)s [%(levelname)s] %(message)s at %(name)s.%(funcName)s:%(lineno)s'
        logging.basicConfig(format=logformat)
        logginglevel = logging.CRITICAL
        loggingHandler = logging.StreamHandler()
        loggingHandler.setLevel(logginglevel)
        logging.getLogger().handlers[0] = loggingHandler
        cls.assertLoggingLevel = logging.WARNING

    def setUp(self) -> None:
        self.log_stream = StringIO()
        self.assertHandler = logging.StreamHandler(self.log_stream)
        self.assertHandler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
        self.assertHandler.setLevel(self.assertLoggingLevel)
        self.AMQPError_msg = 'Generic AMQP error stub'
        self.Exception_msg = 'Generic Python error stub'

    def assertErrorInLog(self, msg_regex=r'ERROR'):
        self.assertRegex(self.log_stream.getvalue(), msg_regex)

    def assertNoErrorInLog(self):
        self.assertNotRegex(self.log_stream.getvalue(), r'ERROR')

    def find_in_log(self, pattern):
        p = re.compile(pattern)
        return re.findall(p, self.log_stream.getvalue())


class HostConnectBaseCase(SrAmqpBaseCase):
    def setUp(self) -> None:
        super(HostConnectBaseCase, self).setUp()
        self.hc = HostConnect()
        self.hc.logger = logging.getLogger(self.__class__.__name__)
        self.hc.logger.addHandler(self.assertHandler)
        self.amqp_channel_assert_msg = 'amqp.Channel mocked calls'
        self.hc_assert_msg = 'hc mocked calls'
        self.sleep_assert_msg = 'time.sleep mocked calls'

    def tearDown(self) -> None:
        self.hc.logger.removeHandler(self.assertHandler)


class HcNoAmqpCase(HostConnectBaseCase):
    def test_add_build(self):
        # Execute test
        self.hc.add_build(self.test_add_build)
        # Evaluate results
        self.assertIn(self.test_add_build, self.hc.rebuilds)

    def test_choose_amqp(self):
        # Execute test
        self.hc.choose_amqp_alternative()
        # Evaluate results
        self.assertTrue(self.hc.use_amqp)
        self.assertFalse(self.hc.use_amqplib)
        self.assertFalse(self.hc.use_pika)

    def test_choose_pika(self):
        # Execute test
        self.hc.choose_amqp_alternative(use_pika=True)
        # Evaluate results
        self.assertFalse(self.hc.use_amqp)
        self.assertFalse(self.hc.use_amqplib)
        self.assertTrue(self.hc.use_pika)

    def test_choose_amqplib(self):
        # Execute test
        self.hc.choose_amqp_alternative(use_amqplib=True)
        # Evaluate results
        self.assertFalse(self.hc.use_amqp)
        self.assertTrue(self.hc.use_amqplib)
        self.assertFalse(self.hc.use_pika)

    def test_set_url(self):
        # Prepare test
        url = urllib.parse.urlparse('amqps://john:doe@dd.weather.gc.ca')
        # Execute test
        self.hc.set_url(url)
        # Evaluate results
        self.assertEqual('amqps', self.hc.protocol)
        self.assertEqual('john', self.hc.user)
        self.assertEqual('doe', self.hc.password)
        self.assertEqual('dd.weather.gc.ca', self.hc.host)
        self.assertEqual(5671, self.hc.port)
        self.assertEqual('/', self.hc.vhost)
        self.assertTrue(self.hc.ssl)


@patch('amqp.Connection')
@patch('amqp.Channel')
class HcAmqpCase(HostConnectBaseCase):
    def setUp(self) -> None:
        super(HcAmqpCase, self).setUp()
        self.amqp_connection_assert_msg = 'amqp.Connection mocked calls'
        self.hc.host = 'my.domain.com'
        self.hc.user = 'anonymous'
        self.hc.password = 'anonymous'
        self.hc.vhost = '/'

    def test_close(self, chan, conn):
        # Prepare test
        self.hc.connection = conn
        chan.channel_id = 1
        self.hc.toclose = [chan]
        # Execute test
        self.hc.close()
        # Evaluate results
        expected = [call.close()]
        self.assertEqual(expected, conn.mock_calls, self.amqp_connection_assert_msg)
        self.assertEqual(0, len(self.hc.toclose))
        self.assertIsNone(self.hc.connection)
        self.assertNoErrorInLog()

    def test_close_connection_lost(self, chan, conn):
        # Prepare test
        conn.close.side_effect = RecoverableConnectionError('Connection already closed.')
        self.hc.connection = conn
        # Execute test
        self.hc.close()
        # Evaluate results
        expected = [call.close()]
        self.assertEqual(expected, conn.mock_calls, self.amqp_connection_assert_msg)
        self.assertEqual(0, len(self.hc.toclose))
        self.assertIsNone(self.hc.connection)
        self.assertErrorInLog()

    def test_close_connection_Exception(self, chan, conn):
        # Prepare test
        conn.close.side_effect = Exception(self.Exception_msg)
        self.hc.connection = conn
        # Execute test
        self.hc.close()
        # Evaluate results
        self.assertEqual(0, len(self.hc.toclose))
        self.assertIsNone(self.hc.connection)
        self.assertErrorInLog()

    def test_connect(self, chan, conn):
        # Execute test
        ok = self.hc.connect()
        # Evaluate results
        expected = [call(self.hc.host, userid=self.hc.user, password=self.hc.password, virtual_host=self.hc.vhost,
                         ssl=self.hc.ssl), call().connect(), call().channel()]
        self.assertEqual(expected, conn.mock_calls, self.amqp_connection_assert_msg)
        self.assertTrue(ok)
        self.assertIsNotNone(self.hc.connection)
        self.assertIsNotNone(self.hc.channel)
        self.assertEqual(1, len(self.hc.toclose))
        self.assertNoErrorInLog()

    def test_connect__port(self, chan, conn):
        # Prepare test
        self.hc.port = 1234
        # Execute test
        ok = self.hc.connect()
        # Evaluate results
        expected = [call("{}:{}".format(self.hc.host, self.hc.port), userid=self.hc.user, password=self.hc.password,
                         virtual_host=self.hc.vhost, ssl=self.hc.ssl), call().connect(), call().channel()]
        self.assertEqual(expected, conn.mock_calls, self.amqp_connection_assert_msg)
        self.assertTrue(ok)
        self.assertIsNotNone(self.hc.connection)
        self.assertIsNotNone(self.hc.channel)
        self.assertEqual(1, len(self.hc.toclose))
        self.assertNoErrorInLog()

    @patch('time.sleep')
    def test_connect__multiple_amqp_init_errors(self, sleep, chan, conn):
        # Prepare test
        conn.side_effect = [
            RecoverableConnectionError('connection already closed'),
            ValueError("Must supply authentication or userid/password"),
            ValueError("Invalid login method", 'login_method'),
            DEFAULT
        ]
        # Execute test
        ok = self.hc.connect()
        # Evaluate results
        expected = [call(self.hc.host, userid=self.hc.user, password=self.hc.password, virtual_host=self.hc.vhost,
                         ssl=self.hc.ssl)]*4 + [call().connect(), call().channel()]
        self.assertEqual(expected, conn.mock_calls, self.amqp_connection_assert_msg)
        expected = [call(2), call(4), call(8)]
        self.assertEqual(expected, sleep.mock_calls)
        self.assertTrue(ok)
        self.assertIsNotNone(self.hc.connection)
        self.assertIsNotNone(self.hc.channel)
        self.assertEqual(1, len(self.hc.toclose))
        self.assertErrorInLog()

    @patch('time.sleep')
    def test_connect__multiple_amqp_connect_errors(self, sleep, chan, conn):
        # Prepare test
        conn.return_value = conn
        conn.connect.side_effect = [
            AMQPError(self.AMQPError_msg),
            SSLError('SSLError stub'),
            IOError('IOError stub'),
            OSError('OSError stub'),
            Exception(self.Exception_msg),
            DEFAULT
        ]
        # Execute test
        ok = self.hc.connect()
        # Evaluate results
        expected = [call(self.hc.host, userid=self.hc.user, password=self.hc.password, virtual_host=self.hc.vhost,
                         ssl=self.hc.ssl), call.connect()]*6 + [call.channel()]
        self.assertEqual(expected, conn.mock_calls, self.amqp_connection_assert_msg)
        expected = [call(2), call(4), call(8), call(16), call(32)]
        self.assertEqual(expected, sleep.mock_calls, self.sleep_assert_msg)
        self.assertTrue(ok)
        self.assertIsNotNone(self.hc.connection)
        self.assertIsNotNone(self.hc.channel)
        self.assertEqual(1, len(self.hc.toclose))
        self.assertErrorInLog()

    @patch('time.sleep')
    def test_connect__multiple_new_channel_errors(self, sleep, chan, conn):
        # Prepare test
        self.hc.new_channel = Mock()
        self.hc.new_channel.side_effect = [
            RecoverableConnectionError('Connection already closed.'),
            ConnectionError('Channel %r already open' % (1,)),
            ResourceError('No free channel ids, current={0}, channel_max={1}'.format(101, 100), (20, 10)),
            IOError('Socket closed'),
            IOError('Server unexpectedly closed connection'),
            OSError('Socket timeout related error'), chan]
        # Execute test
        ok = self.hc.connect()
        # Evaluate results
        expected = [call(self.hc.host, userid=self.hc.user, password=self.hc.password, virtual_host=self.hc.vhost,
                         ssl=self.hc.ssl), call().connect()]*7
        self.assertEqual(expected, conn.mock_calls, self.amqp_connection_assert_msg)
        expected = [call(2), call(4), call(8), call(16), call(32), call(64)]
        self.assertEqual(expected, sleep.mock_calls, self.sleep_assert_msg)
        self.assertTrue(ok)
        self.assertIsNotNone(self.hc.connection)
        self.assertIsNotNone(self.hc.channel)
        self.assertErrorInLog()

    def test_exchange_declare(self, chan, conn):
        # Prepare test
        self.hc.channel = chan
        # Execute test
        self.hc.exchange_declare(self.xname)
        # Evaluate results
        expected = [call.exchange_declare(self.xname, 'topic', auto_delete=False, durable=True)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertNoErrorInLog()

    def test_exchange_declare_AMQPError(self, chan, conn):
        # Prepare test
        self.hc.channel = chan
        self.hc.channel.exchange_declare.side_effect = AMQPError(self.AMQPError_msg)
        # Execute test
        self.hc.exchange_declare(self.xname)
        # Evaluate results
        expected = [call.exchange_declare(self.xname, 'topic', auto_delete=False, durable=True)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertErrorInLog()

    def test_exchange_declare_Exception(self, chan, conn):
        # Prepare test
        self.hc.channel = chan
        self.hc.channel.exchange_declare.side_effect = Exception(self.Exception_msg)
        # Execute test
        self.hc.exchange_declare(self.xname)
        # Evaluate results
        expected = [call.exchange_declare(self.xname, 'topic', auto_delete=False, durable=True)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertErrorInLog()

    def test_exchange_delete(self, chan, conn):
        # Prepare test
        self.hc.channel = chan
        # Execute test
        self.hc.exchange_delete(self.xname)
        # Evaluate results
        expected = [call.exchange_delete(self.xname)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertNoErrorInLog()

    def test_exchange_delete_AMQPError(self, chan, conn):
        # Prepare test
        self.hc.channel = chan
        self.hc.channel.exchange_delete.side_effect = AMQPError(self.AMQPError_msg)
        # Execute test
        self.hc.exchange_delete(self.xname)
        # Evaluate results
        expected = [call.exchange_delete(self.xname)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertErrorInLog()

    def test_exchange_delete_Exception(self, chan, conn):
        # Prepare test
        self.hc.channel = chan
        self.hc.channel.exchange_delete.side_effect = Exception(self.Exception_msg)
        # Execute test
        self.hc.exchange_delete(self.xname)
        # Evaluate results
        expected = [call.exchange_delete(self.xname)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertErrorInLog()

    def test_new_channel(self, chan, conn):
        # Prepare test
        self.hc.connection = chan
        # Execute test
        self.hc.new_channel()
        self.assertEqual(1, len(self.hc.toclose))
        # Evaluate results
        expected = [call.channel()]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertNoErrorInLog()

    def test_queue_delete(self, chan, conn):
        # Prepare test
        self.hc.channel = chan
        # Execute test
        self.hc.queue_delete(self.qname)
        # Evaluate results
        expected = [call.queue_delete(self.qname)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertNoErrorInLog()

    def test_queue_delete_AMQPError(self, chan, conn):
        # Prepare test
        chan.queue_delete.side_effect = AMQPError(self.AMQPError_msg)
        self.hc.channel = chan
        # Execute test
        self.hc.queue_delete(self.qname)
        # Evaluate results
        expected = [call.queue_delete(self.qname)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertErrorInLog()

    def test_queue_delete_AMQPError_NOT_FOUND(self, chan, conn):
        # Prepare test
        chan.queue_delete.side_effect = AMQPError('NOT_FOUND')
        self.hc.channel = chan
        # Execute test
        self.hc.queue_delete(self.qname)
        # Evaluate results
        expected = [call.queue_delete(self.qname)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertNoErrorInLog()

    def test_queue_delete_Exception(self, chan, conn):
        # Prepare test
        chan.side_effect = Exception(self.Exception_msg)
        self.hc.channel = chan
        # Execute test
        self.hc.queue_delete(self.qname)
        # Evaluate results
        expected = [call.queue_delete(self.qname)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertNoErrorInLog()

    def test_reconnect(self, chan, conn):
        # Prepare test
        self.hc.connection = conn
        self.hc.channel = chan
        # Execute test
        self.hc.reconnect()
        # Evaluate results
        self.assertIsNotNone(self.hc.connection)
        self.assertIsNotNone(self.hc.channel)
        self.assertNotEqual(conn, self.hc.connection)
        self.assertNotEqual(chan, self.hc.channel)
        self.assertNoErrorInLog()


@patch('amqp.Channel')
@patch('sarra.sr_amqp.HostConnect')
class ConsumerCase(HostConnectBaseCase):
    def setUp(self) -> None:
        super(ConsumerCase, self).setUp()
        self.consumer = Consumer(self.hc)
        self.consumer.logger = logging.getLogger(self.__class__.__name__)
        self.consumer.logger.addHandler(self.assertHandler)

    def tearDown(self) -> None:
        self.consumer.logger.removeHandler(self.assertHandler)

    @patch('sarra.sr_util.raw_message')
    def test_ack(self, msg, hc, chan):
        # Prepare test
        msg.delivery_tag = 1
        self.consumer.channel = chan
        # Execute test
        self.consumer.ack(msg)
        # Evaluate results
        expected = [call.basic_ack(msg.delivery_tag)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertNoErrorInLog()

    def test_add_prefetch(self, hc, chan):
        # Prepare test
        new_prefetch = 10
        # Execute test
        self.consumer.add_prefetch(new_prefetch)
        # Evaluate results
        self.assertEqual(new_prefetch, self.consumer.prefetch)

    def test_build(self, hc, chan):
        # Prepare test
        hc.new_channel.return_value = chan
        self.consumer.hc = hc
        # Execute test
        self.consumer.build()
        # Evaluate results
        expected = [call.basic_qos(0, 20, False)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertNoErrorInLog()

    def test_build_no_prefetch(self, hc, chan):
        # Prepare test
        hc.new_channel.return_value = chan
        self.consumer.hc = hc
        self.consumer.prefetch = 0
        # Execute test
        self.consumer.build()
        # Evaluate results
        expected = [call.new_channel()]
        self.assertEqual(expected, hc.mock_calls, self.hc_assert_msg)
        expected = []
        self.assertEqual(expected, chan.mock_calls, self.hc_assert_msg)
        self.assertNoErrorInLog()

    @patch('amqp.Message')
    def test_consume(self, msg, hc, chan):
        # Prepare test
        hc.use_pika = False
        self.consumer.hc = hc
        chan.basic_get.return_value = msg
        self.consumer.channel = chan
        # Execute test
        msg_returned = self.consumer.consume(self.qname)
        # Evaluate results
        self.assertEqual(msg, msg_returned)

    @patch('sarra.sr_util.raw_message')
    def test_consume__IrrecoverabeChannelError(self, msg, hc, chan):
        """ If a wrong delivery tag is provided, the next basic get will fail with PRECONDITION_FAILED error

        This is an irrecoverable error and the process must create a new connection to amqp
        """
        # Prepare test
        msg.delivery_tag = 1
        errmsg = 'Basic.ack: (406) PRECONDITION_FAILED - unknown delivery tag {}'.format(msg.delivery_tag)
        chan.basic_get.side_effect = [PreconditionFailed(errmsg), msg]
        self.consumer.channel = chan
        self.consumer.hc = hc
        hc.use_pika = False
        # Execute test
        self.consumer.consume(self.qname)
        # Evaluate results
        expected = [call.basic_get(self.qname), call.basic_get(self.qname)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        expected = [call.reconnect()]
        self.assertEqual(expected, hc.mock_calls, self.hc_assert_msg)
        self.assertErrorInLog(re.escape(errmsg))


@patch('amqp.Channel')
@patch('sarra.sr_amqp.HostConnect')
class PublisherCase(HostConnectBaseCase):
    def setUp(self) -> None:
        super(PublisherCase, self).setUp()
        self.pub = Publisher(self.hc)
        self.pub.logger = logging.getLogger(self.__class__.__name__)
        self.pub.logger.addHandler(self.assertHandler)
        self.pubkey = "test_publish"

    def tearDown(self) -> None:
        self.pub.logger.removeHandler(self.assertHandler)

    def test_build(self, hc, chan):
        # Prepare test
        self.pub.hc = hc
        self.pub.hc.new_channel.return_value = chan
        # Execute test
        self.pub.build()
        # Evaluate results
        expected = [call.new_channel(), call.use_pika.__bool__()]
        self.assertEqual(expected, hc.mock_calls, self.hc_assert_msg)
        expected = [call.confirm_delivery()]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertIsNotNone(self.pub.channel)
        self.assertNoErrorInLog()

    def test_is_alive(self, hc, chan):
        # Prepare test
        hc.use_pika = False
        self.pub.hc = hc
        self.pub.channel = chan
        # Execute test
        alive = self.pub.is_alive()
        # Evaluate results
        expected = [call.tx_select()]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertTrue(alive)
        self.assertNoErrorInLog()

    def test_is_alive_channel_none(self, hc, chan):
        # Prepare test
        self.pub.hc = hc
        self.assertIsNone(self.pub.channel)
        # Execute test
        alive = self.pub.is_alive()
        # Evaluate results
        self.assertFalse(alive, 'Wrong is_alive information when channel is None')
        self.assertNoErrorInLog()

    def test_publish(self, hc, chan):
        # Prepare test
        self.pub.channel = chan
        msg = json.dumps({'sr_amqp test': 'test publish msg'})
        # Execute test
        ok = self.pub.publish(self.xname, self.pubkey, msg, None)
        # Evaluate results
        expected = r'call.basic_publish.*amqp.basic_message.Message.*{}.*{}'.format(self.xname, self.pubkey)
        self.assertRegex(str(chan.mock_calls[0]), expected, 'chan.basic_publish mocked call')
        expected = [call.tx_commit()]
        self.assertEqual(expected, chan.mock_calls[1:], 'chan.tx_commit mocked call')
        self.assertTrue(ok)
        self.assertNoErrorInLog()

    def test_restore_clear(self, hc, chan):
        # Prepare test
        self.pub.channel = chan
        self.pub.restore_queue = self.qname
        self.pub.restore_exchange = self.xname
        # Execute test
        self.pub.restore_clear()
        # Evaluate results
        expected = [call.queue_unbind(self.qname, self.xname, '#'), call.exchange_delete(self.xname)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertIsNone(self.pub.restore_queue)
        self.assertIsNone(self.pub.restore_exchange)
        self.assertNoErrorInLog()

    def test_restore_clear_AMQPError(self, hc, chan):
        # Prepare test
        chan.queue_unbind.side_effect = AMQPError(self.AMQPError_msg)
        chan.exchange_delete.side_effect = AMQPError(self.AMQPError_msg)
        self.pub.channel = chan
        self.pub.restore_queue = self.qname
        self.pub.restore_exchange = self.xname
        # Execute test
        self.pub.restore_clear()
        # Evaluate results
        expected = [call.queue_unbind(self.qname, self.xname, '#'), call.exchange_delete(self.xname)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertIsNone(self.pub.restore_queue)
        self.assertIsNone(self.pub.restore_exchange)
        self.assertErrorInLog()
        self.find_in_log(r'{}'.format(self.AMQPError_msg))

    def test_restore_clear_Exception(self, hc, chan):
        # Prepare test
        chan.queue_unbind.side_effect = Exception(self.Exception_msg)
        chan.exchange_delete.side_effect = Exception(self.Exception_msg)
        self.pub.restore_queue = self.qname
        self.pub.restore_exchange = self.xname
        self.pub.channel = chan
        # Execute test
        self.pub.restore_clear()
        # Evaluate results
        expected = [call.queue_unbind(self.qname, self.xname, '#'), call.exchange_delete(self.xname)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertIsNone(self.pub.restore_queue)
        self.assertIsNone(self.pub.restore_exchange)
        self.assertErrorInLog()

    def test_restore_clear_no_queue(self, hc, chan):
        # Prepare test
        self.pub.restore_exchange = self.xname
        self.pub.channel = chan
        # Execute test
        self.pub.restore_clear()
        # Evaluate results
        expected = [call.exchange_delete(self.xname)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertIsNone(self.pub.restore_queue)
        self.assertIsNone(self.pub.restore_exchange)
        self.assertNoErrorInLog()

    def test_restore_clear_noop(self, hc, chan):
        # Prepare test
        self.pub.channel = chan
        # Execute test
        self.pub.restore_clear()
        # Evaluate results
        expected = []
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertNoErrorInLog()

    def test_restore_set(self, hc, chan):
        # Prepare test
        self.pub.channel = chan
        self.restore_queue = self.qname
        self.post_exchange = self.xname
        self.program_name = str(self.__class__.__name__.lower())
        self.config_name = "myconfig"
        ex = os._exit
        os._exit = self.pub.logger.error
        # Execute test
        self.pub.restore_set(self)
        os._exit = ex
        # Evaluate results
        expected = [call.exchange_declare(self.pub.restore_exchange, 'topic', auto_delete=True, durable=False),
                    call.queue_bind(self.restore_queue, self.pub.restore_exchange, '#')]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertEqual(self.restore_queue, self.pub.restore_queue)
        regex = r'{}.{}.{}.restore.\d+'.format(self.xname, self.program_name, self.config_name)
        self.assertRegex(self.pub.restore_exchange, regex)
        self.assertNoErrorInLog()

    def test_restore_set_exchange_declare_AMQPError(self, hc, chan):
        # Prepare test
        chan.exchange_declare.side_effect = AMQPError(self.AMQPError_msg)
        self.pub.channel = chan
        self.restore_queue = self.qname
        self.post_exchange = self.xname
        self.program_name = str(self.__class__.__name__.lower())
        self.config_name = "myconfig"
        ex = os._exit
        os._exit = self.pub.logger.error
        # Execute test
        self.pub.restore_set(self)
        os._exit = ex
        # Evaluate results
        expected = [call.exchange_declare(self.pub.restore_exchange, 'topic', auto_delete=True, durable=False)]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertEqual(self.restore_queue, self.pub.restore_queue)
        regex = r'{}.{}.{}.restore.\d+'.format(self.xname, self.program_name, self.config_name)
        self.assertRegex(self.pub.restore_exchange, regex)
        self.assertErrorInLog()

    def test_restore_set_queue_bind_Exception(self, hc, chan):
        # Prepare test
        ex = os._exit
        os._exit = self.pub.logger.error
        chan.queue_bind.side_effect = Exception(self.Exception_msg)
        self.pub.channel = chan
        self.restore_queue = self.qname
        self.post_exchange = self.xname
        self.program_name = str(self.__class__.__name__.lower())
        self.config_name = "myconfig"
        # Execute test
        self.pub.restore_set(self)
        os._exit = ex
        # Evaluate results
        expected = [call.exchange_declare(self.pub.restore_exchange, 'topic', auto_delete=True, durable=False),
                    call.queue_bind(self.restore_queue, self.pub.restore_exchange, '#')]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertEqual(self.restore_queue, self.pub.restore_queue)
        regex = r'{}.{}.{}.restore.\d+'.format(self.xname, self.program_name, self.config_name)
        self.assertRegex(self.pub.restore_exchange, regex)
        self.assertErrorInLog()


@patch('amqp.Channel')
class QueueCase(HostConnectBaseCase):
    def setUp(self) -> None:
        super(QueueCase, self).setUp()
        self.q = Queue(self.hc, self.qname)
        self.q.logger = logging.getLogger(self.__class__.__name__)
        self.q.logger.addHandler(self.assertHandler)
        self.msg_count = 1
        self.xname_fmt = '{}_xname'
        self.xkey_fmt = '{}_xkey'
        self.pulse_key = 'v02.pulse.#'
        self.queue_assert_msg = 'Queue mocked call'

    def tearDown(self) -> None:
        self.q.logger.removeHandler(self.assertHandler)

    def test_init__mutable_args_are_evil(self, chan):
        Queue.__init__.__defaults__[0]['a'] = []
        a = Queue(self.hc, self.qname)
        b = Queue(self.hc, self.qname)
        a.properties['a'].append(1)
        self.assertIn(1, b.properties['a'])

    def test_init__defaults_contains_mutable(self, chan):
        defaults_copy = Queue.__init__.__defaults__[0].copy()
        for v1, v2 in zip(Queue.__init__.__defaults__[0].values(), defaults_copy.values()):
            if type(v1) not in [bool, int, float, tuple, str, frozenset]:
                self.assertNotEqual(id(v1), id(v2), '{} is mutable'.format(v1))

    def test_add_binding(self, chan):
        # Prepare test
        xname = self.xname_fmt.format(self.test_add_binding.__name__)
        xkey = self.xkey_fmt.format(self.test_add_binding.__name__)
        # Execute test
        self.q.add_binding(xname, xkey)
        # Evaluate results
        self.assertEqual((xname, xkey), self.q.bindings[0])

    def test_bind(self, chan):
        # Prepare test
        self.q.channel = chan
        xname = self.xname_fmt.format(self.test_bind.__name__)
        xkey = self.xkey_fmt.format(self.test_bind.__name__)
        # Execute test
        self.q.bind(xname, xkey)
        # Evaluate results
        expected = [call(self.q.name, xname, xkey)]
        self.assertEqual(expected, chan.queue_bind.mock_calls, 'amqp.Channel.queue_bind mocked calls')
        self.assertNoErrorInLog()

    @patch('sarra.sr_amqp.HostConnect')
    def test_build(self, hc, chan):
        # Prepare test
        xname = self.xname_fmt.format(self.test_build.__name__)
        xkey = self.xkey_fmt.format(self.test_build.__name__)
        self.q.bindings.append((xname, xkey))
        hc.new_channel.return_value = chan
        hc.user = '{}_user'.format(self.test_build.__name__)
        hc.host = '{}_host'.format(self.test_build.__name__)
        self.q.hc = hc
        self.q.declare = Mock(return_value=self.msg_count)
        # Execute test
        self.q.build()
        # Evaluate results
        expected = [call.new_channel()]
        self.assertEqual(expected, hc.mock_calls, self.hc_assert_msg)
        expected = [call.queue_bind(self.q.name, xname, xkey)
                    # ,call.queue_bind(self.q.name, xname, self.pulse_key)
                    ]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertNoErrorInLog()

    @patch('sarra.sr_amqp.HostConnect')
    def test_build__new_channel_Exception(self, hc, chan):
        """ Build is expected to be called at startup then the expected behaviour is to fail fast on exception

        This is why new_channel exceptions should not be handled, so analysts starting processes would be instantly
        aware of build problems.
        """
        # Prepare test
        xname = '{}_xname'.format(self.test_build.__name__)
        xkey = '{}_xkey'.format(self.test_build.__name__)
        self.q.bindings.append((xname, xkey))
        hc.new_channel.side_effect = Exception('AMQP failed to create a new channel')
        hc.user = '{}_user'.format(self.test_build.__name__)
        hc.host = '{}_host'.format(self.test_build.__name__)
        self.q.hc = hc
        self.q.declare = Mock(return_value=self.msg_count)
        # Execute test
        try:
            self.q.build()
        except Exception:
            # Evaluate results
            expected = [call.new_channel()]
            self.assertEqual(expected, hc.mock_calls, self.hc_assert_msg)
            expected = []
            self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
            self.assertNoErrorInLog()

    @patch('sarra.sr_amqp.HostConnect')
    def test_build__reset__queue_delete_Exception(self, hc, chan):
        # Prepare test
        self.q.properties['reset'] = True
        xname = '{}_xname'.format(self.test_build.__name__)
        xkey = '{}_xkey'.format(self.test_build.__name__)
        self.q.bindings.append((xname, xkey))
        chan.queue_delete.side_effect = Exception(self.Exception_msg)
        hc.new_channel.return_value = chan
        hc.user = '{}_user'.format(self.test_build.__name__)
        hc.host = '{}_host'.format(self.test_build.__name__)
        self.q.hc = hc
        self.q.declare = Mock(return_value=self.msg_count)
        # Execute test
        self.q.build()
        # Evaluate results
        expected = [call.new_channel()]
        self.assertEqual(expected, hc.mock_calls, self.hc_assert_msg)
        expected = [
            call.queue_delete(self.qname),
            call.queue_bind(self.qname, xname, xkey)
        ]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertErrorInLog()

    @patch('sarra.sr_amqp.HostConnect')
    def test_build__declare_failure(self, hc, chan):
        # Prepare test
        xname = '{}_xname'.format(self.test_build.__name__)
        xkey = '{}_xkey'.format(self.test_build.__name__)
        self.q.bindings.append((xname, xkey))
        hc.new_channel.return_value = chan
        hc.user = '{}_user'.format(self.test_build.__name__)
        hc.host = '{}_host'.format(self.test_build.__name__)
        self.q.hc = hc
        self.q.declare = Mock(name='declare', return_value=-1)
        # Execute test
        self.q.build()
        # Evaluate results
        expected = [call.new_channel()]
        self.assertEqual(expected, hc.mock_calls, self.hc_assert_msg)
        self.assertTrue(self.q.declare.called, self.queue_assert_msg)
        self.assertNoErrorInLog()

    @patch('sarra.sr_amqp.HostConnect')
    def test_build__no_bindings(self, hc, chan):
        # Prepare test
        hc.new_channel.return_value = chan
        hc.user = '{}_user'.format(self.test_build.__name__)
        hc.host = '{}_host'.format(self.test_build.__name__)
        self.q.hc = hc
        self.q.declare = Mock(name='declare', return_value=-1)
        # Execute test
        self.q.build()
        # Evaluate results
        expected = [call.new_channel()]
        self.assertEqual(expected, hc.mock_calls, self.hc_assert_msg)
        self.assertTrue(self.q.declare.called, self.queue_assert_msg)
        self.assertNoErrorInLog()

    @patch('sarra.sr_amqp.HostConnect')
    def test_build__bind_Exception(self, hc, chan):
        # Prepare test
        xname = self.xname_fmt.format(self.test_build.__name__)
        xkey = self.xkey_fmt.format(self.test_build.__name__)
        self.q.bindings.append((xname, xkey))
        chan.queue_bind.side_effect = [Exception(self.Exception_msg), DEFAULT]
        hc.new_channel.return_value = chan
        hc.user = '{}_user'.format(self.test_build.__name__)
        hc.host = '{}_host'.format(self.test_build.__name__)
        self.q.hc = hc
        self.q.declare = Mock(return_value=self.msg_count)
        # Execute test
        self.q.build()
        # Evaluate results
        expected = [call.new_channel()]
        self.assertEqual(expected, hc.mock_calls, self.hc_assert_msg)
        expected = [call.queue_bind(self.q.name, xname, xkey),
                    call.queue_bind(self.q.name, xname, xkey)
                    # ,call.queue_bind(self.q.name, xname, self.pulse_key)
                    ]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertErrorInLog()

    @patch('sarra.sr_amqp.HostConnect')
    def test_build__multiple_bindings(self, hc, chan):
        # Prepare test
        xname = self.xname_fmt.format(self.test_build.__name__)
        xkey = self.xkey_fmt.format(self.test_build.__name__)
        self.q.bindings.append((xname, xkey))
        self.q.bindings.append((xname + '_1', xkey + '_1'))
        hc.new_channel.return_value = chan
        hc.user = '{}_user'.format(self.test_build.__name__)
        hc.host = '{}_host'.format(self.test_build.__name__)
        self.q.hc = hc
        self.q.declare = Mock(return_value=self.msg_count)
        # Execute test
        self.q.build()
        # Evaluate results
        expected = [call.new_channel()]
        self.assertEqual(expected, hc.mock_calls, self.hc_assert_msg)
        expected = [call.queue_bind(self.q.name, xname, xkey),
                    call.queue_bind(self.q.name, xname + '_1', xkey + '_1')
                    # ,call.queue_bind(self.q.name, xname + '_1', self.pulse_key)
                    ]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        self.assertNoErrorInLog()

    @patch('sarra.sr_amqp.HostConnect')
    @patch('time.sleep')
    def test_build__multiple_bindings__bind_Exception_loophole(self, sleep, hc, chan):
        # Prepare test
        xname = self.xname_fmt.format(self.test_build.__name__)
        xkey = self.xkey_fmt.format(self.test_build.__name__)
        self.q.bindings.append((xname, xkey))
        self.q.bindings.append((xname + '_1', xkey + '_1'))
        chan.queue_bind.side_effect = [AMQPError(self.AMQPError_msg), AMQPError(self.AMQPError_msg),  # both bindings fail
                                       AMQPError(self.AMQPError_msg), DEFAULT,  # xname fails, xname_1 succeeds
                                       # DEFAULT  # this is for pulse
                                       ]*2
        hc.new_channel.return_value = chan
        self.q.declare = Mock(return_value=self.msg_count)
        hc.user = 'test_user'
        hc.host = 'test_host'
        self.q.hc = hc
        # Execute test
        self.q.build()
        # Evaluate results
        expected = [call.new_channel()]
        self.assertEqual(expected, hc.mock_calls, self.hc_assert_msg)
        expected = [call.queue_bind(self.q.name, xname, xkey),
                    call.queue_bind(self.q.name, xname + '_1', xkey + '_1')
                    # ,call.queue_bind(self.q.name, xname + '_1', self.pulse_key)
                    ]*4
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
        expected = [call(1), call(2), call(4), call(8), call(16), call(32)]
        self.assertEqual(expected, sleep.mock_calls, self.sleep_assert_msg)
        self.assertErrorInLog()
        matched = self.find_in_log(r'ERROR bind queue.*?{} '.format(xname))
        self.assertLess(4, len(matched), 'bind to {} failed'.format(xname))

    def test_declare(self, chan):
        # Prepare test
        chan.queue_declare.return_value = self.qname, self.msg_count, 1
        self.q.channel = chan
        # Execute test
        self.q.declare()
        # Evaluate results
        expected = [call.queue_declare(self.q.name, passive=False, durable=self.q.properties['durable'],
                                       exclusive=False, auto_delete=self.q.properties['auto_delete'], nowait=False,
                                       arguments={})]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)

    def test_declare__Exception(self, chan):
        # Prepare test
        chan.queue_declare.side_effect = Exception(self.Exception_msg)
        self.q.channel = chan
        # Execute test
        try:
            self.q.declare()
        except:
            # Evaluate results
            expected = [call.queue_declare(self.q.name, passive=False, durable=self.q.properties['durable'],
                                           exclusive=False, auto_delete=self.q.properties['auto_delete'], nowait=False,
                                           arguments={})]
            self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)
            self.assertNoErrorInLog()

    def test_declare__expire_gt_0(self, chan):
        # Prepare test
        chan.queue_declare.return_value = self.qname, self.msg_count, 1
        self.q.channel = chan
        self.q.properties['expire'] = 1
        # Execute test
        self.q.declare()
        # Evaluate results
        expected = [call.queue_declare(self.q.name, passive=False, durable=self.q.properties['durable'],
                                       exclusive=False, auto_delete=self.q.properties['auto_delete'], nowait=False,
                                       arguments={'x-expires': 1})]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)

    def test_declare__message_ttl_gt_0(self, chan):
        # Prepare test
        chan.queue_declare.return_value = self.qname, self.msg_count, 1
        self.q.channel = chan
        self.q.properties['message_ttl'] = 1
        # Execute test
        self.q.declare()
        # Evaluate results
        expected = [call.queue_declare(self.q.name, passive=False, durable=self.q.properties['durable'],
                                       exclusive=False, auto_delete=self.q.properties['auto_delete'], nowait=False,
                                       arguments={'x-message-ttl': 1})]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)

    def test_declare__expire_message_ttl_gt_0(self, chan):
        # Prepare test
        chan.queue_declare.return_value = self.qname, self.msg_count, 1
        self.q.channel = chan
        self.q.properties['expire'] = 1
        self.q.properties['message_ttl'] = 1
        # Execute test
        self.q.declare()
        # Evaluate results
        expected = [call.queue_declare(self.q.name, passive=False, durable=self.q.properties['durable'],
                                       exclusive=False, auto_delete=self.q.properties['auto_delete'], nowait=False,
                                       arguments={'x-expires': 1, 'x-message-ttl': 1})]
        self.assertEqual(expected, chan.mock_calls, self.amqp_channel_assert_msg)


class RabbitMqAmqpCase(unittest.TestCase):
    def setUp(self) -> None:
        self.conn_admin = amqp.Connection('localhost', 'bunnymaster', 'ZTI0MjFmZGM0YzM3YmQwOWJlNjhlNjMz')
        self.conn_admin.connect()
        self.chan_admin = self.conn_admin.channel()
        self.conn_user = amqp.Connection('localhost', 'anonymous', 'anonymous')
        self.conn_user.connect()
        self.chan_user = self.conn_user.channel()
        self.qname_fmt = 'q_{}'
        self.xname_fmt = 'x_{}'
        self.xkey_fmt = 'k_{}'
        self.l = []

    def tearDown(self) -> None:
        self.conn_admin.close()
        self.conn_user.close()

    def test_close(self):
        self.conn_admin.close()
        self.assertFalse(self.chan_admin.is_open)

    def test_queue_declare(self):
        qname = self.qname_fmt.format(self.test_queue_declare.__name__)
        result = self.chan_admin.queue_declare(qname, passive=False, durable=False,
                                                       exclusive=False, auto_delete=False)
        self.assertEqual((qname, 0, 0), (result.queue, result.message_count, result.consumer_count))
        self.chan_admin.queue_delete(self.qname_fmt.format(self.test_queue_declare.__name__))

    def test_multiple_queue_bind(self):
        qname = self.qname_fmt.format(self.test_multiple_queue_bind.__name__)
        xname = self.xname_fmt.format(self.test_multiple_queue_bind.__name__)
        xkey = self.xkey_fmt.format(self.test_multiple_queue_bind.__name__)
        declare_result = self.chan_admin.queue_declare(qname)
        self.chan_admin.queue_bind(qname, 'amq.topic', xkey)
        self.chan_admin.queue_bind(qname, 'amq.topic', xkey)
        delete_result = self.chan_admin.queue_delete(qname)

    def test_sr_amqp__Queue__build_sequence(self):
        qname = self.qname_fmt.format(self.test_sr_amqp__Queue__build_sequence.__name__)
        xname = self.xname_fmt.format(self.test_sr_amqp__Queue__build_sequence.__name__)
        xkey = self.xkey_fmt.format(self.test_sr_amqp__Queue__build_sequence.__name__)
        delete_result = self.chan_admin.queue_delete(qname)
        declare_result = self.chan_admin.queue_declare(qname)
        self.chan_admin.queue_bind(qname, 'amq.topic', xkey)

    def test_tx_publish(self):
        xname = self.xname_fmt.format(self.test_tx_publish.__name__)
        qname = self.qname_fmt.format('anonymous_{}'.format(self.test_tx_publish.__name__))
        self.chan_admin.tx_select()
        self.chan_admin.exchange_declare(xname, 'topic')
        self.chan_user.queue_declare(qname)
        self.chan_admin.queue_bind(qname, xname)
        for i in range(2000):
            msg = amqp.Message('message{}'.format(i))
            self.chan_admin.basic_publish(msg, exchange=xname)
            self.chan_admin.tx_commit()
        self.chan_admin.exchange_delete(xname)
        self.chan_admin.queue_delete(qname)

    def test_confirm_publish_ack(self):
        xname = self.xname_fmt.format(self.test_confirm_publish_ack.__name__)
        qname = self.qname_fmt.format('anonymous_{}'.format(self.test_confirm_publish_ack.__name__))
        self.chan_admin.confirm_select()
        self.chan_admin.events['basic_ack'].add(self.ack_handling)
        self.chan_admin.events['basic_nack'].add(self.nack_handling)
        self.chan_admin.exchange_declare(xname, 'topic')
        self.chan_user.queue_declare(qname)
        self.chan_admin.queue_bind(qname, xname)
        for i in range(2000):
            msg = amqp.Message('message{}'.format(i))
            self.chan_admin.basic_publish(msg, xname)
        self.chan_admin.exchange_delete(xname)
        self.chan_admin.queue_delete(qname)
        self.assertEqual(2000, self.l[0])

    def test_confirm_publish_nack(self):
        # # self.chan_admin.exchange_delete(xname)
        # self.chan_admin.queue_delete(qname)
        # for i in range(5):
        #     msg = amqp.Message('message{}'.format(i+50000))
        #     try:
        #         self.chan_admin.basic_publish(msg, xname)
        #     except Exception as err:
        #         print(err)
        pass

    def test_ack__wrong_delivery_tag(self):
        xname = self.xname_fmt.format(self.test_ack__wrong_delivery_tag.__name__)
        qname = self.qname_fmt.format('anonymous_{}'.format(self.test_ack__wrong_delivery_tag.__name__))
        self.chan_admin.tx_select()
        self.chan_admin.exchange_declare(xname, 'topic')
        self.chan_user.queue_declare(qname)
        self.chan_admin.queue_bind(qname, xname)
        for i in range(3):
            msg = amqp.Message('message'+str(i))
            self.chan_admin.basic_publish(msg, xname)
            self.chan_admin.tx_commit()
            self.chan_user.basic_get(qname)
            self.chan_user.basic_ack(i+1)
        self.chan_user.basic_ack(4)
        try:
            msg = self.chan_user.basic_get(qname)
            self.fail('this must fails, something is wrong with this channel: {}'.format(self.chan_user))
        except PreconditionFailed as err:
            pass
        self.chan_admin.queue_delete(qname)
        self.chan_admin.exchange_delete(xname)

    def nack_handling(self, delivery_tag, multiple):
        self.l = delivery_tag, multiple

    def ack_handling(self, delivery_tag, multiple):
        self.l = delivery_tag, multiple


class RabbitMqAmqplibCase(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = client_0_8.Connection('localhost', 'bunnymaster', 'ZTI0MjFmZGM0YzM3YmQwOWJlNjhlNjMz')
        self.chan = self.conn.channel()
        self.qname_fmt = 'q_{}'
        self.xname_fmt = 'x_{}'
        self.xkey_fmt = 'k_{}'

    def test_close(self):
        self.conn.close()
        self.assertFalse(self.chan.is_open)

def suite():
    """ Create the test suite that include all sr_amqp test cases

    :return: sr_amqp test suite
    """
    sr_amqp_suite = unittest.TestSuite()
    sr_amqp_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(HcAmqpCase))
    sr_amqp_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(HcNoAmqpCase))
    sr_amqp_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(PublisherCase))
    sr_amqp_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(ConsumerCase))
    sr_amqp_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(QueueCase))
    return sr_amqp_suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
