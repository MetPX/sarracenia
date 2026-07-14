from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import jsonpickle

import sarracenia
import sarracenia.flowcb.post.message


class Options:

    def __init__(self, publishers):
        self.post_broker = True
        self.publishers = publishers

    def dictify(self):
        return {'publishers': self.publishers}


def publisher(name):
    return {
        'broker': 'amqp://%s.example' % name,
        'exchange': ['xs_%s' % name],
        'topicPrefix': ['v03', 'post'],
        'format': 'v03',
    }


def message_for_publisher(index):
    message = sarracenia.Message()
    message['publisher_index'] = index
    message['_deleteOnPost'] = {'publisher_index'}
    return message


def worklist(message):
    return SimpleNamespace(ok=[message], failed=[])


def test_retry_follows_original_publisher_after_reorder():
    publisher_a = publisher('a')
    publisher_b = publisher('b')
    failed_b = MagicMock()
    failed_b.putNewMessage.return_value = False

    with patch('sarracenia.moth.Moth.pubFactory', side_effect=[MagicMock(), failed_b]):
        callback = sarracenia.flowcb.post.message.Message(Options([publisher_a, publisher_b]))

    message = message_for_publisher(1)
    first_attempt = worklist(message)
    callback.post(first_attempt)

    assert first_attempt.ok == []
    assert first_attempt.failed == [message]
    message = jsonpickle.decode(jsonpickle.encode(message))

    retry_b = MagicMock()
    retry_b.putNewMessage.return_value = True
    wrong_a = MagicMock()
    with patch('sarracenia.moth.Moth.pubFactory', side_effect=[retry_b, wrong_a]):
        reordered = sarracenia.flowcb.post.message.Message(Options([publisher_b, publisher_a]))

    retry = worklist(message)
    reordered.post(retry)

    retry_b.putNewMessage.assert_called_once_with(message)
    wrong_a.putNewMessage.assert_not_called()
    assert retry.ok == [message]
    assert retry.failed == []


def test_retry_stays_failed_when_original_publisher_is_removed():
    publisher_a = publisher('a')
    publisher_b = publisher('b')
    failed_b = MagicMock()
    failed_b.putNewMessage.return_value = False

    with patch('sarracenia.moth.Moth.pubFactory', side_effect=[MagicMock(), failed_b]):
        callback = sarracenia.flowcb.post.message.Message(Options([publisher_a, publisher_b]))

    message = message_for_publisher(1)
    first_attempt = worklist(message)
    callback.post(first_attempt)
    message = jsonpickle.decode(jsonpickle.encode(message))

    remaining_a = MagicMock()
    with patch('sarracenia.moth.Moth.pubFactory', return_value=remaining_a):
        reconfigured = sarracenia.flowcb.post.message.Message(Options([publisher_a]))

    retry = worklist(message)
    reconfigured.post(retry)

    remaining_a.putNewMessage.assert_not_called()
    assert retry.ok == []
    assert retry.failed == [message]
