import pytest
from tests.conftest import *

import json
import logging
import urllib.parse

import sarracenia
import sarracenia.config
import sarracenia.postformat.v03
from sarracenia.postformat.v03 import V03

logger = logging.getLogger('sarracenia.postformat.v03')
logger.setLevel('DEBUG')


def _options():
    return sarracenia.config.default_config()


def _export_options():
    """Build a minimal dict-based options object for exportMine/topicDerive.

    topicDerive accesses options via dict-style indexing (options['publishers']),
    so a plain dict is required rather than a sarracenia.config.Config instance.
    """
    return {
        'publishers': [{
            'broker': type('Broker', (), {'url': urllib.parse.urlparse('amqp://localhost')})(),
            'topicPrefix': ['v03'],
            'exchange': 'xpublic',
            'topic': None,
        }],
        'publisher_index': 0,
    }


# ---------------------------------------------------------------------------
# V03.content_type
# ---------------------------------------------------------------------------

def test_content_type():
    assert V03.content_type() == 'application/json'


# ---------------------------------------------------------------------------
# V03.mine – detection logic
# ---------------------------------------------------------------------------

def test_mine_application_json():
    assert V03.mine('{}', {}, 'application/json', _options()) is True


def test_mine_other_content_type_returns_false():
    assert V03.mine('{}', {}, 'text/plain', _options()) is False


def test_mine_no_content_type_returns_false():
    assert V03.mine('{}', {}, '', _options()) is False


# ---------------------------------------------------------------------------
# V03.importMine – basic JSON parsing
# ---------------------------------------------------------------------------

def test_importMine_basic():
    msg_data = {
        'pubTime': '20230101T120000.0',
        'baseUrl': 'http://example.com/',
        'relPath': '/path/file.dat',
        'size': 1024,
    }
    msg = V03.importMine(json.dumps(msg_data), {}, _options())
    assert msg is not None
    assert msg['_format'] == 'v03'
    assert msg['pubTime'] == '20230101T120000.0'
    assert msg['baseUrl'] == 'http://example.com/'
    assert msg['relPath'] == '/path/file.dat'
    assert msg['size'] == 1024


def test_importMine_invalid_json_returns_none():
    msg = V03.importMine('this is not json', {}, _options())
    assert msg is None


def test_importMine_empty_json_object():
    msg = V03.importMine('{}', {}, _options())
    assert msg is not None
    assert msg['_format'] == 'v03'


def test_importMine_headers_not_used():
    # V03 reads entirely from body, headers are ignored
    msg_data = {'pubTime': '20230101T120000.0', 'size': 512}
    msg = V03.importMine(json.dumps(msg_data), {'extra_header': 'value'}, _options())
    assert msg is not None
    assert msg['size'] == 512


# ---------------------------------------------------------------------------
# V03.importMine – legacy field migrations (Postel's Robustness Principle)
# ---------------------------------------------------------------------------

def test_importMine_retPath_migrated_to_retrievePath():
    msg_data = {
        'pubTime': '20230101T120000.0',
        'baseUrl': 'http://example.com/',
        'retPath': '/retrieve/path/file.dat',
    }
    msg = V03.importMine(json.dumps(msg_data), {}, _options())
    assert msg['retrievePath'] == '/retrieve/path/file.dat'
    assert 'retPath' not in msg


def test_importMine_integrity_renamed_to_identity():
    msg_data = {
        'pubTime': '20230101T120000.0',
        'integrity': {'method': 'sha512', 'value': 'abc123def456'},
    }
    msg = V03.importMine(json.dumps(msg_data), {}, _options())
    assert msg['identity'] == {'method': 'sha512', 'value': 'abc123def456'}
    assert 'integrity' not in msg


# ---------------------------------------------------------------------------
# V03.importMine – 'parts' field normalization (v2 bug in v03 messages)
# ---------------------------------------------------------------------------

def test_importMine_parts_style_1_converts_to_size():
    msg_data = {'pubTime': '20230101T120000.0', 'parts': '1,8192,1,0,0'}
    msg = V03.importMine(json.dumps(msg_data), {}, _options())
    assert msg['size'] == 8192
    assert 'parts' not in msg


def test_importMine_parts_style_i_creates_blocks():
    msg_data = {'pubTime': '20230101T120000.0', 'parts': 'i,4096,10,200,0'}
    msg = V03.importMine(json.dumps(msg_data), {}, _options())
    assert 'blocks' in msg
    assert msg['blocks']['method'] == 'inplace'
    assert msg['blocks']['size'] == 4096
    assert msg['blocks']['count'] == 10
    assert msg['blocks']['remainder'] == 200
    assert msg['blocks']['number'] == 0
    assert 'parts' not in msg


def test_importMine_parts_style_p_creates_blocks():
    msg_data = {'pubTime': '20230101T120000.0', 'parts': 'p,2048,5,100,2'}
    msg = V03.importMine(json.dumps(msg_data), {}, _options())
    assert msg['blocks']['method'] == 'partitioned'
    assert msg['blocks']['size'] == 2048
    assert msg['blocks']['count'] == 5
    assert msg['blocks']['remainder'] == 100
    assert msg['blocks']['number'] == 2
    assert 'parts' not in msg


# ---------------------------------------------------------------------------
# V03.importMine – size as string type coercion
# ---------------------------------------------------------------------------

def test_importMine_size_as_string_converted_to_int():
    msg_data = {'pubTime': '20230101T120000.0', 'size': '2048'}
    msg = V03.importMine(json.dumps(msg_data), {}, _options())
    assert msg['size'] == 2048
    assert type(msg['size']) is int


# ---------------------------------------------------------------------------
# V03.importMine – blocks manifest key normalization
# ---------------------------------------------------------------------------

def test_importMine_manifest_string_keys_normalized_to_int():
    # When JSON round-trips numeric dict keys, they become strings
    msg_data = {
        'pubTime': '20230101T120000.0',
        'blocks': {
            'method': 'inplace',
            'size': 4096,
            'count': 3,
            'remainder': 100,
            'number': 0,
            'manifest': {'0': 'block0_checksum', '1': 'block1_checksum', '2': 'block2_checksum'},
        },
    }
    msg = V03.importMine(json.dumps(msg_data), {}, _options())
    manifest = msg['blocks']['manifest']
    assert all(type(k) is int for k in manifest.keys())
    assert manifest[0] == 'block0_checksum'
    assert manifest[1] == 'block1_checksum'
    assert manifest[2] == 'block2_checksum'


def test_importMine_manifest_int_keys_unchanged():
    # If keys are already ints, they should remain ints
    msg_data = {
        'pubTime': '20230101T120000.0',
        'blocks': {
            'method': 'inplace',
            'size': 4096,
            'count': 2,
            'remainder': 0,
            'number': 0,
            'manifest': {0: 'block0', 1: 'block1'},
        },
    }
    # json.dumps will convert int keys to strings, so importMine must normalize them back
    msg = V03.importMine(json.dumps(msg_data), {}, _options())
    manifest = msg['blocks']['manifest']
    assert all(type(k) is int for k in manifest.keys())


def test_importMine_blocks_without_manifest():
    msg_data = {
        'pubTime': '20230101T120000.0',
        'blocks': {
            'method': 'inplace',
            'size': 4096,
            'count': 3,
            'remainder': 100,
            'number': 0,
        },
    }
    msg = V03.importMine(json.dumps(msg_data), {}, _options())
    assert 'blocks' in msg
    assert 'manifest' not in msg['blocks']


# ---------------------------------------------------------------------------
# V03.exportMine
# ---------------------------------------------------------------------------

def test_exportMine_returns_json_content_type():
    options = _export_options()
    msg = {
        'pubTime': '20230101T120000.0',
        'baseUrl': 'http://example.com/',
        'relPath': '/path/file.dat',
        'size': 1024,
    }
    body, headers, ct = V03.exportMine(msg, options)
    assert ct == 'application/json'


def test_exportMine_body_is_valid_json():
    options = _export_options()
    msg = {
        'pubTime': '20230101T120000.0',
        'baseUrl': 'http://example.com/',
        'relPath': '/data/obs/file.dat',
        'size': 512,
    }
    body, headers, ct = V03.exportMine(msg, options)
    parsed = json.loads(body)
    assert parsed['size'] == 512
    assert parsed['relPath'] == '/data/obs/file.dat'


def test_exportMine_topic_in_headers():
    options = _export_options()
    msg = {'pubTime': '20230101T120000.0', 'relPath': '/data/obs/file.dat'}
    body, headers, ct = V03.exportMine(msg, options)
    assert 'topic' in headers
    assert isinstance(headers['topic'], list)
