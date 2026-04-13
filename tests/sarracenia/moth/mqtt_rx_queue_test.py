"""Tests for MQTT rx_msg_q (queue.Queue-based message reception).

Validates that the paho callback thread and main thread interact correctly
via queue.Queue, replacing the old 5-buffer rotation system.
Raw MQTT messages are queued by the callback and decoded on the main thread.
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
    m.broker = MagicMock()
    m.client = MagicMock()
    m.o = {
        'batch': 25,
        'messageDebugDump': False,
        'subscription_index': 0,
        'exchange': None,
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


def make_raw_mqtt_msg(n):
    """Create a mock paho MQTT message (raw, not decoded)."""
    msg = MagicMock()
    msg.topic = 'xpublic/v03/test/file%d' % n
    msg.payload = b'{"test": %d}' % n
    msg.mid = n
    msg.qos = 1
    return msg


def make_decoded_message(n):
    """Create a minimal decoded sarracenia message."""
    msg = sarracenia.Message()
    msg['baseUrl'] = 'https://example.com'
    msg['relPath'] = 'path/to/file%d' % n
    msg['pubTime'] = '20260402T120000.0'
    msg['_deleteOnPost'] = set(['ack_id'])
    msg['subscription_index'] = 0
    return msg


def make_mqtt_with_decode(decode_returns_none=False):
    """Create an MQTT instance with _msgDecode mocked."""
    m = make_mqtt_instance()
    counter = [0]

    def mock_decode(raw_msg):
        if decode_returns_none:
            return None
        counter[0] += 1
        return make_decoded_message(counter[0])

    m._msgDecode = MagicMock(side_effect=mock_decode)
    return m


class Test_NewMessages:

    def test_empty_queue_returns_empty_list(self):
        m = make_mqtt_with_decode()
        result = m.newMessages()
        assert result == []

    def test_returns_all_messages_under_batch(self):
        m = make_mqtt_with_decode()
        m.o['batch'] = 10
        for i in range(5):
            m.rx_msg_q.put(make_raw_mqtt_msg(i))

        result = m.newMessages()
        assert len(result) == 5
        assert m._msgDecode.call_count == 5

    def test_respects_batch_limit(self):
        m = make_mqtt_with_decode()
        m.o['batch'] = 3
        for i in range(10):
            m.rx_msg_q.put(make_raw_mqtt_msg(i))

        result = m.newMessages()
        assert len(result) == 3
        # remaining 7 still in queue
        assert m.rx_msg_q.qsize() == 7

    def test_second_call_gets_remaining(self):
        m = make_mqtt_with_decode()
        m.o['batch'] = 3
        for i in range(5):
            m.rx_msg_q.put(make_raw_mqtt_msg(i))

        first = m.newMessages()
        second = m.newMessages()
        assert len(first) == 3
        assert len(second) == 2

    def test_skips_none_decoded_messages(self):
        """_msgDecode returns None for malformed messages."""
        m = make_mqtt_with_decode()
        call_count = [0]

        def decode_some_none(raw_msg):
            call_count[0] += 1
            if call_count[0] == 2:
                return None
            return make_decoded_message(call_count[0])

        m._msgDecode = MagicMock(side_effect=decode_some_none)
        for i in range(3):
            m.rx_msg_q.put(make_raw_mqtt_msg(i))

        result = m.newMessages()
        assert len(result) == 2

    def test_calls_getSetup_when_disconnected(self):
        m = make_mqtt_with_decode()
        m.connected = False
        m.getSetup = MagicMock()

        m.newMessages()
        m.getSetup.assert_called_once()


class Test_GetNewMessage:

    def test_empty_queue_returns_none(self):
        m = make_mqtt_with_decode()
        result = m.getNewMessage()
        assert result is None

    def test_returns_single_message(self):
        m = make_mqtt_with_decode()
        m.rx_msg_q.put(make_raw_mqtt_msg(1))

        result = m.getNewMessage()
        assert result is not None
        assert 'subscription_index' in result

    def test_sets_subscription_index(self):
        m = make_mqtt_with_decode()
        m.o['subscription_index'] = 3
        m.rx_msg_q.put(make_raw_mqtt_msg(1))

        result = m.getNewMessage()
        assert result['subscription_index'] == 3

    def test_adds_subscription_index_to_deleteOnPost(self):
        m = make_mqtt_with_decode()
        m.rx_msg_q.put(make_raw_mqtt_msg(1))

        result = m.getNewMessage()
        assert 'subscription_index' in result['_deleteOnPost']

    def test_none_decode_returns_none(self):
        m = make_mqtt_with_decode(decode_returns_none=True)
        m.rx_msg_q.put(make_raw_mqtt_msg(1))
        result = m.getNewMessage()
        assert result is None

    def test_calls_getSetup_when_disconnected(self):
        m = make_mqtt_with_decode()
        m.connected = False
        m.getSetup = MagicMock()

        m.getNewMessage()
        m.getSetup.assert_called_once()

    def test_consecutive_calls_drain_queue(self):
        m = make_mqtt_with_decode()
        for i in range(3):
            m.rx_msg_q.put(make_raw_mqtt_msg(i))

        results = [m.getNewMessage() for _ in range(4)]
        assert results[0] is not None
        assert results[1] is not None
        assert results[2] is not None
        assert results[3] is None


class Test_SubOnMessageCallback:

    def test_queues_raw_message(self):
        """__sub_on_message should put raw MQTT message on the queue (not decoded)."""
        m = make_mqtt_instance()
        raw_msg = make_raw_mqtt_msg(1)

        MQTT._MQTT__sub_on_message(None, m, raw_msg)

        assert m.rx_msg_q.qsize() == 1
        assert m.rx_msg_q.get_nowait() is raw_msg

    def test_does_not_call_msgDecode(self):
        """Callback should not decode -- decoding happens on the main thread."""
        m = make_mqtt_instance()
        m._msgDecode = MagicMock()
        raw_msg = make_raw_mqtt_msg(1)

        MQTT._MQTT__sub_on_message(None, m, raw_msg)

        m._msgDecode.assert_not_called()


class Test_ThreadSafety:

    def test_concurrent_put_and_get(self):
        """Simulate paho callback thread putting raw messages while main thread gets them."""
        m = make_mqtt_with_decode()
        m.o['batch'] = 10
        num_messages = 200
        received = []

        def producer():
            for i in range(num_messages):
                m.rx_msg_q.put(make_raw_mqtt_msg(i))
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
        m = make_mqtt_with_decode()
        m.o['batch'] = 50
        per_thread = 100
        num_threads = 4

        def producer(offset):
            for i in range(per_thread):
                m.rx_msg_q.put(make_raw_mqtt_msg(offset + i))

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
