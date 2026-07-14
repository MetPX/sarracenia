from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import sarracenia.moth.amqp


def malformed_json_delivery(channel):
    return SimpleNamespace(
        body=b'1',
        properties={'content_type': 'application/json'},
        headers={},
        delivery_info={'delivery_tag': 41, 'routing_key': 'v03.post.test', 'exchange': 'xpublic'},
        channel=channel,
    )


def test_getNewMessage_acknowledges_decoder_exception():
    props = {
        'broker': MagicMock(),
        'subscriptions': [{'queue': {'name': 'q_test'}}],
        'subscription_index': 0,
        'message_strategy': {'stubborn': False},
    }
    moth = sarracenia.moth.amqp.AMQP(props, is_subscriber=True)
    moth.connection = SimpleNamespace(connected=True)
    moth.channel = MagicMock()
    moth.channel.basic_get.return_value = malformed_json_delivery(moth.channel)

    assert moth.getNewMessage() is None
    moth.channel.basic_ack.assert_called_once_with(41)
    assert moth.metrics['rxBadCount'] == 1


class Test_AMQPDefaultOptions:
    """Test that AMQP inherits tlsRigour from parent Moth defaults.

    Regression test for https://github.com/MetPX/sarracenia/issues/1591
    When sr3 declare creates an AMQP instance with minimal props (no tlsRigour),
    __connect would raise KeyError: 'tlsRigour'.
    """

    @patch('sarracenia.moth.amqp.amqp')
    def test_tlsRigour_present_with_minimal_props(self, mock_amqp_lib):
        """AMQP init with minimal props (like sr3 declare) must still have tlsRigour."""
        minimal_props = {
            'broker': MagicMock(),
            'dry_run': False,
            'exchange': 'xpublic',
            'message_strategy': {'stubborn': True},
        }
        instance = sarracenia.moth.amqp.AMQP(minimal_props, is_subscriber=False)
        assert 'tlsRigour' in instance.o
        assert instance.o['tlsRigour'] == 'normal'

    @patch('sarracenia.moth.amqp.amqp')
    def test_tlsRigour_override_preserved(self, mock_amqp_lib):
        """When props explicitly set tlsRigour, the value must be kept."""
        props = {
            'broker': MagicMock(),
            'dry_run': False,
            'exchange': 'xpublic',
            'message_strategy': {'stubborn': True},
            'tlsRigour': 'lax',
        }
        instance = sarracenia.moth.amqp.AMQP(props, is_subscriber=False)
        assert instance.o['tlsRigour'] == 'lax'

    @patch('sarracenia.moth.amqp.amqp')
    def test_amqp_specific_defaults_still_applied(self, mock_amqp_lib):
        """AMQP-specific defaults (e.g. vhost, exchangeDeclare) must still be set."""
        minimal_props = {
            'broker': MagicMock(),
            'dry_run': False,
            'exchange': 'xpublic',
            'message_strategy': {'stubborn': True},
        }
        instance = sarracenia.moth.amqp.AMQP(minimal_props, is_subscriber=False)
        assert instance.o['vhost'] == '/'
        assert instance.o['exchangeDeclare'] is True
        assert instance.o['durable'] is True
