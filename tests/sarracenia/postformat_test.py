from sarracenia.postformat import PostFormat
from sarracenia.postformat.v02 import V02
from sarracenia.postformat.wis import Wis

V03_BODY = (
    '{ "pubTime" : "20261027T214338.392", '
    '"baseUrl" : "https://hpfx.collab.science.gc.ca", '
    '"relPath" : "/20261027/WXO-DD/bulletins/alphanumeric/20261027/SR/KWAL/21/SRCN40_KWAL_272142___49052", '
    '"identity" : { "method" : "md5", "value" : "wyhJIr05KUV+tc39J/hWBg==" }, '
    '"source" : "WXO-DD", "size" : "248", "mode" : "644" }'
)


def test_importAny_none_headers_v03():
    """A v03 JSON body with no AMQP headers must still decode. See issue #183."""
    msg = PostFormat.importAny(V03_BODY, None, 'application/json', {})
    assert msg is not None
    assert msg['_format'] == 'v03'
    assert msg['source'] == 'WXO-DD'


def test_importAny_none_headers_no_match():
    """Unrecognized content with no headers returns None, not an exception."""
    assert PostFormat.importAny('{"a": 1}', None, None, {}) is None


def test_v02_mine_none_headers():
    """v02.mine must answer False for missing headers, not raise."""
    assert V02.mine('{"a": 1}', None, None, {}) is False


def test_wis_mine_none_headers():
    """wis.mine must answer False for missing headers, not raise."""
    assert Wis.mine('{"id":"x"}', None, 'application/json', {}) is False
