import queue
from types import SimpleNamespace
from unittest.mock import MagicMock

import sarracenia.moth.amqpconsumer


def test_getNewMessage_acknowledges_decoder_exception():
    props = {
        'broker': MagicMock(),
        'subscriptions': [{'queue': {'name': 'q_test'}}],
        'subscription_index': 0,
        'message_strategy': {'stubborn': False},
    }
    moth = sarracenia.moth.amqpconsumer.AMQPConsumer(props, is_subscriber=True)
    moth.connection = MagicMock(connected=True)
    moth.channel = MagicMock()
    moth._raw_msg_q = queue.Queue()
    raw_message = SimpleNamespace(
        body=b'1',
        properties={'content_type': 'application/json'},
        headers={},
        delivery_info={'delivery_tag': 42, 'routing_key': 'v03.post.test', 'exchange': 'xpublic'},
        channel=moth.channel,
    )
    moth._raw_msg_q.put(raw_message)

    assert moth.getNewMessage() is None
    moth.channel.basic_ack.assert_called_once_with(42)
    assert moth.metrics['rxBadCount'] == 1
