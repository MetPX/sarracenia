import pytest
from tests.conftest import *
from unittest.mock import patch, MagicMock, PropertyMock

from sarracenia.moth.mqtt import MQTT


def make_mqtt_instance(is_subscriber=True):
    """Create a minimal MQTT instance without connecting."""
    m = MQTT.__new__(MQTT)
    m.is_subscriber = is_subscriber
    m.connected = False
    m.connect_in_progress = False
    m.subscribe_in_progress = 0
    m._stop_requested = False
    m.o = {}
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


def test_close__calls_loop_stop():
    """close() should call loop_stop() after disconnect()."""
    m = make_mqtt_instance()
    mock_client = MagicMock()
    mock_client.is_connected.return_value = True
    m.client = mock_client

    m.close()

    mock_client.disconnect.assert_called_once()
    mock_client.loop_stop.assert_called_once()


def test_close__loop_stop_after_disconnect():
    """loop_stop() must be called after disconnect()."""
    m = make_mqtt_instance()
    call_order = []
    mock_client = MagicMock()
    mock_client.is_connected.return_value = True
    mock_client.disconnect.side_effect = lambda: call_order.append('disconnect')
    mock_client.loop_stop.side_effect = lambda: call_order.append('loop_stop')
    m.client = mock_client

    m.close()

    assert call_order == ['disconnect', 'loop_stop']


def test_close__not_connected_skips_loop_stop():
    """If client is not connected, should not call disconnect or loop_stop."""
    m = make_mqtt_instance()
    mock_client = MagicMock()
    mock_client.is_connected.return_value = False
    m.client = mock_client

    m.close()

    mock_client.disconnect.assert_not_called()
    mock_client.loop_stop.assert_not_called()


def test_getSetup__stops_old_client():
    """getSetup() should stop the old client before creating a new one."""
    m = make_mqtt_instance()
    old_client = MagicMock()
    m.client = old_client

    m.o = {
        'no': 1,
        'subscription_index': 0,
        'clean_session': False,
        'subscriptions': [{
            'queue': {'name': 'q_test'},
            'broker': MagicMock(
                url=MagicMock(
                    hostname='localhost',
                    username='user',
                    password='pass',
                    scheme='mqtt',
                ),
            ),
        }],
    }
    m.next_connect_time = 0
    m.next_message = 0

    new_client = MagicMock()

    def setup_then_stop(cid):
        m._stop_requested = True
        return new_client

    with patch.object(MQTT, '_MQTT__clientSetup', side_effect=setup_then_stop):
        with patch.object(MQTT, '_MQTT__sslClientSetup', return_value=1883):
            try:
                m.getSetup()
            except Exception:
                pass

    old_client.loop_stop.assert_called_once()
    old_client.disconnect.assert_called_once()


def test_putSetup__stops_old_client():
    """putSetup() should stop the old client before creating a new one."""
    m = make_mqtt_instance(is_subscriber=False)
    old_client = MagicMock()
    m.client = old_client

    m.o = {
        'broker': MagicMock(
            url=MagicMock(
                hostname='localhost',
                username='user',
                password='pass',
                scheme='mqtt',
            ),
        ),
        'messageAgeMax': 0,
        'no': 1,
    }
    m.proto_version = 5
    m.next_connect_time = 0
    m.next_message = 0

    new_client = MagicMock()

    def client_then_stop(*args, **kwargs):
        m._stop_requested = True
        return new_client

    with patch('paho.mqtt.client.Client', side_effect=client_then_stop):
        with patch.object(MQTT, '_MQTT__sslClientSetup', return_value=1883):
            try:
                m.putSetup()
            except Exception:
                pass

    old_client.loop_stop.assert_called_once()
    old_client.disconnect.assert_called_once()
