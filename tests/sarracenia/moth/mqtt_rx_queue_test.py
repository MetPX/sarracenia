"""Tests for MQTT rx_msg_q (queue.Queue-based message reception).

Validates that the paho callback thread and main thread interact correctly
via queue.Queue, replacing the old 5-buffer rotation system.
"""
import queue
import threading
import time

import pytest
from tests.conftest import *
from unittest.mock import MagicMock, patch

import sarracenia
from sarracenia.moth.mqtt import MQTT


def make_mqtt_instance():
    """Create a minimal MQTT subscriber instance without connecting."""
    m = MQTT.__new__(MQTT)
    m.is_subscriber = True
    m.connected = True
    m.connect_in_progress = False
    m.subscribe_in_progress = 0
    m._stop_requested = False
    m.rx_msg_q = queue.Queue()
    m.o = {
        'batch': 25,
        'messageDebugDump': False,
        'subscription_index': 0,
    }
    m.metrics = {
        'rxBadCount': 0,
        'txBadCount': 0,
        'rxByteCount': 0,
        'txByteCount': 0,
        'rxGoodCount': 0,
        'txGoodCount': 0,
        'rxLast': '',
        'txLast': '',
        'connected': False,
    }
    return m


def make_message(n):
    """Create a minimal message dict matching what _msgDecode returns."""
    msg = sarracenia.Message()
    msg['baseUrl'] = 'https://example.com'
    msg['relPath'] = 'path/to/file%d' % n
    msg['pubTime'] = '20260402T120000.0'
    msg['_deleteOnPost'] = set(['ack_id'])
    msg['subscription_index'] = 0
    return msg


class Test_NewMessages:

    def test_empty_queue_returns_empty_list(self):
        m = make_mqtt_instance()
        result = m.newMessages()
        assert result == []

    def test_returns_all_messages_under_batch(self):
        m = make_mqtt_instance()
        m.o['batch'] = 10
        for i in range(5):
            m.rx_msg_q.put(make_message(i))

        result = m.newMessages()
        assert len(result) == 5

    def test_respects_batch_limit(self):
        m = make_mqtt_instance()
        m.o['batch'] = 3
        for i in range(10):
            m.rx_msg_q.put(make_message(i))

        result = m.newMessages()
        assert len(result) == 3
        # remaining 7 still in queue
        assert m.rx_msg_q.qsize() == 7

    def test_second_call_gets_remaining(self):
        m = make_mqtt_instance()
        m.o['batch'] = 3
        for i in range(5):
            m.rx_msg_q.put(make_message(i))

        first = m.newMessages()
        second = m.newMessages()
        assert len(first) == 3
        assert len(second) == 2

    def test_skips_none_messages(self):
        """_msgDecode can return None for malformed messages."""
        m = make_mqtt_instance()
        m.rx_msg_q.put(make_message(0))
        m.rx_msg_q.put(None)
        m.rx_msg_q.put(make_message(2))

        result = m.newMessages()
        assert len(result) == 2

    def test_calls_getSetup_when_disconnected(self):
        m = make_mqtt_instance()
        m.connected = False
        m.getSetup = MagicMock()

        m.newMessages()
        m.getSetup.assert_called_once()


class Test_GetNewMessage:

    def test_empty_queue_returns_none(self):
        m = make_mqtt_instance()
        result = m.getNewMessage()
        assert result is None

    def test_returns_single_message(self):
        m = make_mqtt_instance()
        m.rx_msg_q.put(make_message(1))

        result = m.getNewMessage()
        assert result is not None
        assert 'subscription_index' in result

    def test_sets_subscription_index(self):
        m = make_mqtt_instance()
        m.o['subscription_index'] = 3
        m.rx_msg_q.put(make_message(1))

        result = m.getNewMessage()
        assert result['subscription_index'] == 3

    def test_adds_subscription_index_to_deleteOnPost(self):
        m = make_mqtt_instance()
        m.rx_msg_q.put(make_message(1))

        result = m.getNewMessage()
        assert 'subscription_index' in result['_deleteOnPost']

    def test_none_message_returns_none(self):
        m = make_mqtt_instance()
        m.rx_msg_q.put(None)
        result = m.getNewMessage()
        assert result is None

    def test_calls_getSetup_when_disconnected(self):
        m = make_mqtt_instance()
        m.connected = False
        m.getSetup = MagicMock()

        m.getNewMessage()
        m.getSetup.assert_called_once()

    def test_consecutive_calls_drain_queue(self):
        m = make_mqtt_instance()
        for i in range(3):
            m.rx_msg_q.put(make_message(i))

        results = [m.getNewMessage() for _ in range(4)]
        assert results[0] is not None
        assert results[1] is not None
        assert results[2] is not None
        assert results[3] is None


class Test_SubOnMessageCallback:

    def test_put_calls_queue(self):
        """__sub_on_message should put decoded message on the queue."""
        m = make_mqtt_instance()
        mock_mqtt_msg = MagicMock()
        mock_mqtt_msg.topic = 'xpublic/v03/test'
        mock_mqtt_msg.payload = b'test payload'
        mock_mqtt_msg.mid = 1
        mock_mqtt_msg.qos = 1

        decoded = make_message(1)
        m._msgDecode = MagicMock(return_value=decoded)

        # Call the callback (it's a static method, pass m as userdata)
        MQTT._MQTT__sub_on_message(None, m, mock_mqtt_msg)

        assert m.rx_msg_q.qsize() == 1
        assert m.rx_msg_q.get_nowait() is decoded

    def test_none_decode_still_queued(self):
        """If _msgDecode returns None, it should still be queued (filtered later)."""
        m = make_mqtt_instance()
        mock_mqtt_msg = MagicMock()
        mock_mqtt_msg.topic = 'xpublic/v03/test'
        mock_mqtt_msg.payload = b'bad'
        mock_mqtt_msg.mid = 2
        mock_mqtt_msg.qos = 1

        m._msgDecode = MagicMock(return_value=None)

        MQTT._MQTT__sub_on_message(None, m, mock_mqtt_msg)

        assert m.rx_msg_q.qsize() == 1


class Test_ThreadSafety:

    def test_concurrent_put_and_get(self):
        """Simulate paho callback thread putting messages while main thread gets them."""
        m = make_mqtt_instance()
        m.o['batch'] = 10
        num_messages = 200
        received = []

        def producer():
            for i in range(num_messages):
                m.rx_msg_q.put(make_message(i))
                if i % 10 == 0:
                    time.sleep(0.001)

        producer_thread = threading.Thread(target=producer)
        producer_thread.start()

        deadline = time.time() + 5
        while len(received) < num_messages and time.time() < deadline:
            batch = m.newMessages()
            received.extend(batch)
            if not batch:
                time.sleep(0.005)

        producer_thread.join(timeout=2)

        assert len(received) == num_messages

    def test_multiple_producers(self):
        """Multiple paho callback threads (shouldn't happen, but should still be safe)."""
        m = make_mqtt_instance()
        m.o['batch'] = 50
        per_thread = 100
        num_threads = 4

        def producer(offset):
            for i in range(per_thread):
                m.rx_msg_q.put(make_message(offset + i))

        threads = [threading.Thread(target=producer, args=(t * per_thread,))
                   for t in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        total = 0
        while not m.rx_msg_q.empty():
            batch = m.newMessages()
            total += len(batch)

        assert total == per_thread * num_threads
