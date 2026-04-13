import pytest
from tests.conftest import *
from unittest.mock import patch, MagicMock

import sarracenia.config
import sarracenia.moth
import sarracenia.moth.amqp


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
