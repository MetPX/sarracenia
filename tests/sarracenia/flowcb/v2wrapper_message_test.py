import pytest
from tests.conftest import *

import sarracenia
from sarracenia.flowcb.v2wrapper import Message


def make_plain_dict_message():
    """Create a plain dict (not sarracenia.Message) with minimum v02 fields.

    This simulates what happens after dict(message) shallow copy in
    putNewMessage -- the sarracenia.Message class is lost.
    """
    return {
        'pubTime': '20180118T151049.356378078',
        'baseUrl': 'https://example.com',
        'relPath': '/data/observations/test.txt',
        'identity': {
            'method': 'md5',
            'value': 'CY9rzUYh03PK3k6DJie09g==',
        },
        '_format': 'v02',
        '_deleteOnPost': set(),
    }


def make_sr3_message():
    """Create a sarracenia.Message (dict subclass with isRetry method)."""
    m = sarracenia.Message()
    m['pubTime'] = '20180118T151049.356378078'
    m['baseUrl'] = 'https://example.com'
    m['relPath'] = '/data/observations/test.txt'
    m['identity'] = {
        'method': 'md5',
        'value': 'CY9rzUYh03PK3k6DJie09g==',
    }
    m['_format'] = 'v02'
    m['_deleteOnPost'] = set()
    return m


def test_v2wrapper_message_from_plain_dict():
    """v2wrapper.Message must work with a plain dict, not just sarracenia.Message.

    Regression test for PR #1604: dict(message) shallow copy strips the
    Message class, so v2wrapper.Message.__init__ must not call h.isRetry().
    """
    d = make_plain_dict_message()
    msg = Message(d)
    assert msg.isRetry is False


def test_v2wrapper_message_from_plain_dict_with_retry():
    """Plain dict with _isRetry flag should set isRetry=True."""
    d = make_plain_dict_message()
    d['_isRetry'] = True
    msg = Message(d)
    assert msg.isRetry is True


def test_v2wrapper_message_from_plain_dict_with_retry_count():
    """Plain dict with _isRetry as int (retry count) should be truthy."""
    d = make_plain_dict_message()
    d['_isRetry'] = 3
    msg = Message(d)
    assert msg.isRetry is True


def test_v2wrapper_message_from_sr3_message():
    """sarracenia.Message (dict subclass) should still work."""
    m = make_sr3_message()
    msg = Message(m)
    assert msg.isRetry is False


def test_v2wrapper_message_from_sr3_message_with_retry():
    """sarracenia.Message with _isRetry should set isRetry=True."""
    m = make_sr3_message()
    m['_isRetry'] = True
    msg = Message(m)
    assert msg.isRetry is True
