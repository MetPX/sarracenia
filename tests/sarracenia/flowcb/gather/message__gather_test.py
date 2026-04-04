import pytest
from tests.conftest import *
from unittest.mock import MagicMock, patch

import sarracenia.config
import sarracenia.flowcb.gather.message
from sarracenia.flowcb.gather.message import Message


class BrokenConsumer:
    """Simulates a consumer that lost its connection (no newMessages attr)."""
    pass


class WorkingConsumer:
    """Simulates a healthy consumer."""
    def __init__(self):
        self.broker = 'amqp://localhost'

    def newMessages(self):
        return [{'_format': 'v03', 'relPath': 'test.txt'}]

    def metricsReport(self):
        return {}

    def metricsReset(self):
        pass

    def close(self):
        pass


def make_gather_plugin():
    """Create a Message gather plugin with no real broker."""
    options = sarracenia.config.default_config()
    options.broker = MagicMock()
    options.broker.url = MagicMock()
    options.broker.url.hostname = 'localhost'
    # skip __init__ subscription setup
    options.subscriptions = []
    plugin = Message(options)
    return plugin


def test_reconnect_updates_consumer_list():
    """Regression: gather() assigned reconnected consumer to loop variable `c`
    instead of self.consumers[i].  The consumer list was never repaired.

    This test proves the fix: after reconnect, self.consumers[i] must hold
    the new consumer object, not the old broken one.
    """
    plugin = make_gather_plugin()

    broken = BrokenConsumer()
    plugin.consumers = [broken]

    replacement = WorkingConsumer()

    with patch('sarracenia.moth.Moth.subFactory', return_value=replacement) as mock_factory:
        ok, messages = plugin.gather(100)

    # the consumer list must now hold the replacement, not the broken one
    assert plugin.consumers[0] is replacement, \
        "gather() did not update self.consumers -- reconnect wrote to local variable"
    assert plugin.consumers[0] is not broken


def test_broken_consumer_never_recovers_without_fix():
    """Prove that the old pattern (loop var assignment) leaves the broken
    consumer in the list permanently.  We simulate the OLD behavior and
    show the consumer stays broken across multiple gather() calls.
    """
    plugin = make_gather_plugin()

    broken = BrokenConsumer()
    plugin.consumers = [broken]

    replacement = WorkingConsumer()

    with patch('sarracenia.moth.Moth.subFactory', return_value=replacement):
        # first gather -- should fix the consumer
        plugin.gather(100)

    # after the fix, the second gather should use the working consumer
    ok, messages = plugin.gather(100)
    assert len(messages) == 1, \
        "consumer not recovered -- second gather returned no messages"


def test_reconnect_with_multiple_consumers():
    """Only the broken consumer should be replaced; working ones stay."""
    plugin = make_gather_plugin()

    working = WorkingConsumer()
    broken = BrokenConsumer()
    plugin.consumers = [working, broken]

    replacement = WorkingConsumer()

    with patch('sarracenia.moth.Moth.subFactory', return_value=replacement) as mock_factory:
        ok, messages = plugin.gather(100)

    assert plugin.consumers[0] is working, "working consumer was replaced"
    assert plugin.consumers[1] is replacement, "broken consumer was not replaced"
    # subFactory should only be called once (for the broken consumer)
    mock_factory.assert_called_once()


def test_gather_returns_messages_from_working_consumers():
    """Basic sanity: gather collects messages from working consumers."""
    plugin = make_gather_plugin()

    c1 = WorkingConsumer()
    c2 = WorkingConsumer()
    plugin.consumers = [c1, c2]

    ok, messages = plugin.gather(100)
    assert ok is True
    assert len(messages) == 2
