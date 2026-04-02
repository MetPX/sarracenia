import pytest
from tests.conftest import *

import json
import logging
import urllib.parse

import sarracenia
import sarracenia.config
import sarracenia.postformat
import sarracenia.postformat.v02
import sarracenia.postformat.v03
from sarracenia.postformat import PostFormat

logger = logging.getLogger('sarracenia.postformat')
logger.setLevel('DEBUG')


def _make_options(scheme='amqp', topic_prefix=None, exchange='xpublic', topic=None):
    """Build a minimal options dict suitable for topicDerive."""
    if topic_prefix is None:
        topic_prefix = ['v03']
    return {
        'publishers': [{
            'broker': type('Broker', (), {'url': urllib.parse.urlparse(f'{scheme}://localhost')})(),
            'topicPrefix': topic_prefix,
            'exchange': exchange,
            'topic': topic,
        }],
        'publisher_index': 0,
    }


# ---------------------------------------------------------------------------
# PostFormat.content_type
# ---------------------------------------------------------------------------

def test_content_type_v02():
    ct = PostFormat.content_type('v02')
    assert ct == 'text/plain'


def test_content_type_v03():
    ct = PostFormat.content_type('v03')
    assert ct == 'application/json'


def test_content_type_unknown():
    ct = PostFormat.content_type('doesnotexist')
    assert ct is None


# ---------------------------------------------------------------------------
# PostFormat.importAny
# ---------------------------------------------------------------------------

def test_importAny_routes_to_v03():
    options = sarracenia.config.default_config()
    msg_data = {
        'pubTime': '20230101T120000.0',
        'baseUrl': 'http://example.com/',
        'relPath': '/path/file.dat',
        'size': 512,
    }
    body = json.dumps(msg_data)
    msg = PostFormat.importAny(body, {}, 'application/json', options)
    assert msg is not None
    assert msg['_format'] == 'v03'
    assert msg['size'] == 512


def test_importAny_routes_to_v02():
    options = sarracenia.config.default_config()
    body = '20230101T120000.0 http://example.com/ /obs/file.dat'
    msg = PostFormat.importAny(body, {}, 'text/plain', options)
    assert msg is not None
    assert msg['_format'] == 'v02'
    assert msg['baseUrl'] == 'http://example.com/'


def test_importAny_unknown_format_returns_none():
    options = sarracenia.config.default_config()
    # A body that no format will claim (non-JSON string with { at start fools v02 away)
    # Actually JSON content with wrong content_type: wis/swim would need to check too.
    # Provide a body and content-type that no handler matches.
    body = 'not any known format'
    # Without headers, wis/swim won't match; v02 will match plain string - use JSON to avoid v02
    # Pass a JSON body but with content_type that no handler accepts
    body = json.dumps({'pubTime': '20230101T120000.0'})
    # content_type='text/xml' won't match any handler
    msg = PostFormat.importAny(body, {}, 'text/xml', options)
    assert msg is None


# ---------------------------------------------------------------------------
# PostFormat.exportAny
# ---------------------------------------------------------------------------

def test_exportAny_v03():
    # exportAny/exportMine/topicDerive all expect options as a dict (not Config)
    options = {
        'publishers': [{
            'broker': type('Broker', (), {'url': urllib.parse.urlparse('amqp://localhost')})(),
            'topicPrefix': ['v03'],
            'exchange': 'xpublic',
            'topic': None,
        }],
        'publisher_index': 0,
    }

    msg = {
        'pubTime': '20230101T120000.0',
        'baseUrl': 'http://example.com/',
        'relPath': '/path/file.dat',
        'size': 1024,
    }
    body, headers, ct = PostFormat.exportAny(msg, 'v03', ['v03'], options)
    assert ct == 'application/json'
    assert 'topic' in headers
    parsed = json.loads(body)
    assert parsed['size'] == 1024


def test_exportAny_unknown_format_returns_none_triple():
    options = sarracenia.config.default_config()
    msg = {'pubTime': '20230101T120000.0'}
    body, headers, ct = PostFormat.exportAny(msg, 'doesnotexist', ['v03'], options)
    assert body is None
    assert headers is None
    assert ct is None


# ---------------------------------------------------------------------------
# PostFormat.topicDerive
# ---------------------------------------------------------------------------

def test_topicDerive_relpath():
    options = _make_options()
    msg = {'relPath': '/data/obs/file.dat'}
    topic = PostFormat.topicDerive(msg, options)
    assert topic == ['v03', '', 'data', 'obs']


def test_topicDerive_with_subtopic():
    options = _make_options()
    msg = {'subtopic': ['data', 'obs']}
    topic = PostFormat.topicDerive(msg, options)
    assert topic == ['v03', 'data', 'obs']


def test_topicDerive_with_msg_topic_as_list():
    options = _make_options()
    msg = {'topic': ['v03', 'post', 'data', 'obs']}
    topic = PostFormat.topicDerive(msg, options)
    assert topic == ['v03', 'post', 'data', 'obs']


def test_topicDerive_with_msg_topic_as_string():
    options = _make_options()
    msg = {'topic': 'v03.post.data.obs'}
    topic = PostFormat.topicDerive(msg, options)
    assert topic == ['v03', 'post', 'data', 'obs']


def test_topicDerive_fallback_to_prefix():
    options = _make_options()
    msg = {}
    topic = PostFormat.topicDerive(msg, options)
    assert topic == ['v03']


def test_topicDerive_amqp_uses_dot_separator():
    options = _make_options(scheme='amqp')
    msg = {'topic': 'v03.post.data.obs'}
    topic = PostFormat.topicDerive(msg, options)
    # AMQP split on '.'
    assert topic == ['v03', 'post', 'data', 'obs']
