import pytest
from tests.conftest import *

import logging

import sarracenia
import sarracenia.config
import sarracenia.postformat.v02
from sarracenia.postformat.v02 import V02

logger = logging.getLogger('sarracenia.postformat.v02')
logger.setLevel('DEBUG')


def _options():
    return sarracenia.config.default_config()


# ---------------------------------------------------------------------------
# V02.content_type
# ---------------------------------------------------------------------------

def test_content_type():
    assert V02.content_type() == 'text/plain'


# ---------------------------------------------------------------------------
# V02.mine – detection logic
# ---------------------------------------------------------------------------

def test_mine_text_plain_content_type():
    assert V02.mine('anything', {}, 'text/plain', _options()) is True


def test_mine_str_payload_not_json():
    # Plain string without '{' in first 5 chars → v02
    body = '20230101T120000.0 http://example.com/ /file.dat'
    assert V02.mine(body, {}, 'unknown/type', _options()) is True


def test_mine_json_payload_not_claimed():
    # JSON string (starts with '{') → NOT v02
    body = '{"pubTime":"20230101T120000.0"}'
    assert V02.mine(body, {}, 'unknown/type', _options()) is False


def test_mine_v02_topic_in_headers():
    assert V02.mine(b'binary', {'topic': 'v02.post.data'}, 'binary/data', _options()) is True


def test_mine_returns_false_for_json_content_type():
    assert V02.mine('{}', {}, 'application/json', _options()) is False


# ---------------------------------------------------------------------------
# V02.importMine – basic fields
# ---------------------------------------------------------------------------

def test_importMine_basic():
    body = '20230101T120000.0 http://example.com/data/ /obs/file.dat'
    msg = V02.importMine(body, {}, _options())
    assert msg is not None
    assert msg['_format'] == 'v02'
    assert msg['baseUrl'] == 'http://example.com/data/'
    assert msg['relPath'] == '/obs/file.dat'
    assert msg['pubTime'] == '20230101T120000.0'
    assert msg['to_clusters'] == 'ALL'


def test_importMine_sets_subtopic():
    body = '20230101T120000.0 http://example.com/ /a/b/c/file.dat'
    msg = V02.importMine(body, {}, _options())
    assert msg['subtopic'] == ['', 'a', 'b', 'c', 'file.dat']


def test_importMine_subtopic_marked_for_deletion():
    body = '20230101T120000.0 http://example.com/ /obs/file.dat'
    msg = V02.importMine(body, {}, _options())
    assert 'subtopic' in msg['_deleteOnPost']


def test_importMine_url_decode_baseurl_space():
    body = '20230101T120000.0 http://example.com/dir%20with%20space/ /file.dat'
    msg = V02.importMine(body, {}, _options())
    assert msg['baseUrl'] == 'http://example.com/dir with space/'


def test_importMine_url_decode_baseurl_hash():
    body = '20230101T120000.0 http://example.com/dir%23hash/ /file.dat'
    msg = V02.importMine(body, {}, _options())
    assert msg['baseUrl'] == 'http://example.com/dir#hash/'


def test_importMine_malformed_body_returns_none():
    body = 'only_one_field'
    msg = V02.importMine(body, {}, _options())
    assert msg is None


def test_importMine_malformed_body_two_fields_returns_none():
    body = 'field1 field2'
    msg = V02.importMine(body, {}, _options())
    assert msg is None


def test_importMine_headers_copied():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'source': 'myserver'}
    msg = V02.importMine(body, headers, _options())
    assert msg['source'] == 'myserver'
    # to_clusters is always forced to 'ALL' by the v02 parser
    assert msg['to_clusters'] == 'ALL'


# ---------------------------------------------------------------------------
# V02.importMine – integrity/identity field rename
# ---------------------------------------------------------------------------

def test_importMine_integrity_renamed_to_identity():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'integrity': {'method': 'sha512', 'value': 'abc123'}}
    msg = V02.importMine(body, headers, _options())
    assert msg.get('identity') == {'method': 'sha512', 'value': 'abc123'}
    assert 'integrity' not in msg


# ---------------------------------------------------------------------------
# V02.importMine – sum field (checksum/file-operation decoding)
# ---------------------------------------------------------------------------

def test_importMine_sum_sha512():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'sum': 's,aabbccdd11223344'}
    msg = V02.importMine(body, headers, _options())
    assert msg['identity']['method'] == 'sha512'
    assert msg['identity']['value'] != ''
    assert 'sum' not in msg


def test_importMine_sum_md5():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    # MD5 hex value must be even-length (32 hex chars = 16 bytes)
    headers = {'sum': 'd,deadbeefdeadbeefdeadbeefdeadbeef'}
    msg = V02.importMine(body, headers, _options())
    assert msg['identity']['method'] == 'md5'
    assert 'sum' not in msg


def test_importMine_sum_random():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'sum': '0,some-random-value'}
    msg = V02.importMine(body, headers, _options())
    assert msg['identity'] == {'method': 'random', 'value': 'some-random-value'}


def test_importMine_sum_arbitrary():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'sum': 'a,myarbitraryvalue'}
    msg = V02.importMine(body, headers, _options())
    assert msg['identity'] == {'method': 'arbitrary', 'value': 'myarbitraryvalue'}


def test_importMine_sum_remove():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'sum': 'R,'}
    msg = V02.importMine(body, headers, _options())
    assert msg['fileOp'] == {'remove': ''}
    assert 'identity' not in msg


def test_importMine_sum_mkdir():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'sum': 'm,'}
    msg = V02.importMine(body, headers, _options())
    assert msg['fileOp'] == {'directory': ''}


def test_importMine_sum_rmdir():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'sum': 'r,'}
    msg = V02.importMine(body, headers, _options())
    assert msg['fileOp'] == {'remove': '', 'directory': ''}


def test_importMine_sum_link():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'sum': 'L,deadbeef', 'link': '/path/to/target'}
    msg = V02.importMine(body, headers, _options())
    assert msg['fileOp'] == {'link': '/path/to/target'}
    assert 'link' not in msg


def test_importMine_sum_rename_via_oldname():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    # Use a valid even-length hex value for md5 (32 hex chars = 16 bytes)
    headers = {'sum': 'd,deadbeefdeadbeefdeadbeefdeadbeef', 'oldname': '/old/path/file.dat'}
    msg = V02.importMine(body, headers, _options())
    assert msg['fileOp']['rename'] == '/old/path/file.dat'
    assert 'oldname' not in msg


def test_importMine_corrupt_sum_handled_gracefully():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'sum': 'TOTALLY_INVALID'}
    msg = V02.importMine(body, headers, _options())
    # Should return a valid msg (sum field is just dropped/ignored)
    assert msg is not None
    assert msg['relPath'] == '/file.dat'


# ---------------------------------------------------------------------------
# V02.importMine – parts field (chunked transfer)
# ---------------------------------------------------------------------------

def test_importMine_parts_style_1_sets_size():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'parts': '1,4096,1,0,0'}
    msg = V02.importMine(body, headers, _options())
    assert msg['size'] == 4096
    assert 'parts' not in msg


def test_importMine_parts_style_i_logs_error_and_returns():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'parts': 'i,4096,10,200,0'}
    msg = V02.importMine(body, headers, _options())
    # 'inplace' is not supported; no 'size' or 'blocks' should be set
    assert msg is not None
    assert 'size' not in msg
    assert 'blocks' not in msg


def test_importMine_corrupt_parts_handled_gracefully():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'parts': 'not,a,valid,parts,field,at,all'}
    msg = V02.importMine(body, headers, _options())
    assert msg is not None
    assert msg['relPath'] == '/file.dat'


# ---------------------------------------------------------------------------
# V02.importMine – time field conversion
# ---------------------------------------------------------------------------

def test_importMine_mtime_converted():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'mtime': '20230101120000.0'}
    msg = V02.importMine(body, headers, _options())
    # v2 format '20230101120000.0' → v3 format '20230101T120000.0'
    assert msg['mtime'] == '20230101T120000.0'


def test_importMine_atime_converted():
    body = '20230101T120000.0 http://example.com/ /file.dat'
    headers = {'atime': '20230101120000.0'}
    msg = V02.importMine(body, headers, _options())
    assert msg['atime'] == '20230101T120000.0'
