from unittest.mock import MagicMock, patch

from sarracenia.moth.mqtt import MQTT


def make_publisher(timeout):
    mqtt = MQTT.__new__(MQTT)
    mqtt.client = MagicMock()
    mqtt.client.is_connected.return_value = True
    mqtt.connected = True
    mqtt.is_subscriber = False
    mqtt.pending_publishes = [17]
    mqtt.unexpected_publishes = []
    mqtt.o = {'timeout': timeout}
    return mqtt


def test_close_stops_waiting_at_timeout():
    mqtt = make_publisher(0.25)
    waits = []

    with patch('sarracenia.moth.mqtt.time.sleep', side_effect=waits.append):
        mqtt.close()

    assert waits == [0.1, 0.15]
    assert mqtt.pending_publishes == [17]
    mqtt.client.disconnect.assert_called_once_with()
    mqtt.client.loop_stop.assert_called_once_with()
    assert mqtt.connected is False


def test_close_preserves_successful_pending_publish_drain():
    mqtt = make_publisher(1)
    waits = []

    def acknowledge(wait_for):
        waits.append(wait_for)
        mqtt.pending_publishes.clear()

    with patch('sarracenia.moth.mqtt.time.sleep', side_effect=acknowledge):
        mqtt.close()

    assert waits == [0.1]
    mqtt.client.disconnect.assert_called_once_with()
    mqtt.client.loop_stop.assert_called_once_with()
    assert mqtt.connected is False
