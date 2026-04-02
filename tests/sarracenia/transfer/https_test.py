import pytest
from tests.conftest import *

import logging
import ssl
import urllib.parse
import urllib.request
from unittest.mock import MagicMock, patch

import sarracenia
import sarracenia.config
import sarracenia.transfer
import sarracenia.transfer.https
from sarracenia.transfer.https import Https, HTTPRedirectHandlerSameMethod

logger = logging.getLogger('sarracenia.transfer.https')
logger.setLevel('DEBUG')


def _options(sendTo='http://example.com'):
    o = sarracenia.config.default_config()
    o.sendTo = sendTo
    return o


def _connected_transfer(sendTo='http://example.com'):
    t = Https('https', _options(sendTo))
    t.connect()
    return t


class FakeHTTPResponse:
    """Minimal fake for a urllib response object returned by opener.open()."""
    def __init__(self, status=200, content_length=None, last_modified=None, body=b''):
        self._status = status
        self._headers = {}
        if content_length is not None:
            self._headers['Content-Length'] = str(content_length)
        if last_modified is not None:
            self._headers['Last-Modified'] = last_modified
        self._body = body
        self._pos = 0

    def geturl(self):
        return 'http://example.com/data/file.dat'

    def getcode(self):
        return self._status

    def getheader(self, name):
        return self._headers.get(name)

    def info(self):
        return ' , '.join(f'{k}: {v}' for k, v in self._headers.items())

    def read(self, size=-1):
        if size == -1:
            chunk = self._body[self._pos:]
            self._pos = len(self._body)
        else:
            chunk = self._body[self._pos:self._pos + size]
            self._pos += len(chunk)
        return chunk


# ---------------------------------------------------------------------------
# registered_as
# ---------------------------------------------------------------------------

def test_registered_as():
    assert Https.registered_as() == ['http', 'https']


# ---------------------------------------------------------------------------
# __init__ / TLS rigour options
# ---------------------------------------------------------------------------

def test_init_default():
    t = Https('https', _options())
    assert not t.connected
    assert t.opener is None
    assert t.head_opener is None


def test_init_tls_lax():
    o = _options()
    o.add_option('tlsRigour', 'str', 'lax')
    o.tlsRigour = 'lax'
    t = Https('https', o)
    assert t.tlsctx.check_hostname is False
    assert t.tlsctx.verify_mode == ssl.CERT_NONE


def test_init_tls_strict():
    o = _options()
    o.add_option('tlsRigour', 'str', 'strict')
    o.tlsRigour = 'strict'
    t = Https('https', o)
    assert t.tlsctx.check_hostname is True
    assert t.tlsctx.verify_mode == ssl.CERT_REQUIRED


def test_init_tls_normal_is_default_context():
    o = _options()
    o.add_option('tlsRigour', 'str', 'normal')
    o.tlsRigour = 'normal'
    t = Https('https', o)
    # 'normal' leaves the context at its default — just ensure no exception
    assert t.tlsctx is not None


# ---------------------------------------------------------------------------
# cd
# ---------------------------------------------------------------------------

def test_cd_sets_path_and_cwd():
    t = Https('https', _options())
    t.cd('/data/obs/file.dat')
    assert t.path == '/data/obs/file.dat'
    assert t.cwd == '/data/obs'


def test_cd_root_file():
    t = Https('https', _options())
    t.cd('/file.dat')
    assert t.path == '/file.dat'
    assert t.cwd == '/'


# ---------------------------------------------------------------------------
# connect / close / check_is_connected
# ---------------------------------------------------------------------------

def test_connect_creates_openers():
    t = Https('https', _options())
    result = t.connect()
    assert result is True
    assert t.connected is True
    assert t.opener is not None
    assert t.head_opener is not None
    assert t.password_mgr is not None


def test_connect_with_basic_auth_credentials():
    o = _options('http://user:secret@example.com')
    o.credentials._parse('http://user:secret@example.com')
    t = Https('https', o)
    result = t.connect()
    assert result is True
    assert t.user == 'user'
    assert t.password == 'secret'


def test_close_resets_state():
    t = _connected_transfer()
    assert t.connected is True
    t.close()
    assert t.connected is False
    assert t.opener is None
    assert t.head_opener is None
    assert t.http is None


def test_check_is_connected_before_connect():
    t = Https('https', _options())
    assert t.check_is_connected() is False


def test_check_is_connected_after_connect():
    t = _connected_transfer()
    assert t.check_is_connected() is True


def test_check_is_connected_sendto_mismatch_disconnects():
    t = _connected_transfer('http://example.com')
    # Change the options sendTo to a different URL
    t.o.sendTo = 'http://other.example.com'
    result = t.check_is_connected()
    assert result is False
    assert t.connected is False


def test_check_is_connected_no_opener():
    t = _connected_transfer()
    t.opener = None
    assert t.check_is_connected() is False


# ---------------------------------------------------------------------------
# HTTPRedirectHandlerSameMethod
# ---------------------------------------------------------------------------

def test_redirect_handler_preserves_method():
    handler = HTTPRedirectHandlerSameMethod()
    # POST + 302: base class would normally change POST to GET on 302 redirect,
    # but HTTPRedirectHandlerSameMethod preserves the original method.
    original_req = urllib.request.Request('http://example.com/old', method='POST')

    import io, http.client
    fake_fp = io.BytesIO(b'')
    fake_headers = http.client.HTTPMessage()

    new_req = handler.redirect_request(original_req, fake_fp, 302, 'Found', fake_headers, 'http://example.com/new')
    assert new_req.get_method() == 'POST'
    assert new_req.get_full_url() == 'http://example.com/new'


def test_redirect_handler_preserves_get():
    handler = HTTPRedirectHandlerSameMethod()
    original_req = urllib.request.Request('http://example.com/old', method='GET')

    import io, http.client
    fake_fp = io.BytesIO(b'')
    fake_headers = http.client.HTTPMessage()

    new_req = handler.redirect_request(original_req, fake_fp, 302, 'Found', fake_headers, 'http://example.com/new')
    assert new_req.get_method() == 'GET'


# ---------------------------------------------------------------------------
# __open__ URL normalisation (double-slash removal)
# ---------------------------------------------------------------------------

def test_open_normalises_double_slash_http():
    t = _connected_transfer()
    fake_response = FakeHTTPResponse()
    t.opener.open = MagicMock(return_value=fake_response)
    t.head_opener.open = MagicMock(return_value=fake_response)

    t.__open__('http://example.com//data//file.dat')
    assert '//' not in t.urlstr[7:]  # no double-slash after 'http://' (7 chars)


def test_open_normalises_double_slash_https():
    t = _connected_transfer()
    fake_response = FakeHTTPResponse()
    t.opener.open = MagicMock(return_value=fake_response)
    t.head_opener.open = MagicMock(return_value=fake_response)

    t.__open__('https://example.com//path//to//file.dat')
    assert '//' not in t.urlstr[8:]  # no double-slash after 'https://' (8 chars)


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

def test_get_with_retrieve_path():
    t = _connected_transfer()
    with patch.object(t, '__open__', return_value=True) as mock_open, \
         patch.object(t, 'read_writelocal', return_value=100) as mock_rw:
        t.http = MagicMock()
        msg = {'retrievePath': 'data/obs/file.dat'}
        result = t.get(msg, 'file.dat', '/tmp/output.dat')
        assert result == 100
        url_used = mock_open.call_args[0][0]
        assert url_used == 'http://example.com/data/obs/file.dat'


def test_get_without_retrieve_path():
    t = _connected_transfer()
    t.path = '/data/'
    with patch.object(t, '__open__', return_value=True) as mock_open, \
         patch.object(t, 'read_writelocal', return_value=50) as mock_rw:
        t.http = MagicMock()
        msg = {}
        result = t.get(msg, 'file.dat', '/tmp/output.dat')
        assert result == 50
        url_used = mock_open.call_args[0][0]
        assert 'file.dat' in url_used


def test_get_returns_false_when_open_fails():
    t = _connected_transfer()
    with patch.object(t, '__open__', return_value=False):
        msg = {}
        result = t.get(msg, 'file.dat', '/tmp/output.dat')
        assert result is False


# ---------------------------------------------------------------------------
# getAccelerated
# ---------------------------------------------------------------------------

def test_get_accelerated_returns_length_on_success():
    t = Https('https', _options())
    msg = {'baseUrl': 'http://example.com/', 'relPath': '/data/file.dat'}

    with patch('sarracenia.transfer.https.subprocess.Popen') as mock_popen:
        proc = MagicMock()
        proc.returncode = 0
        mock_popen.return_value = proc

        result = t.getAccelerated(msg, 'file.dat', '/tmp/file.dat', 1024)
        assert result == 1024


def test_get_accelerated_returns_minus_one_on_failure():
    t = Https('https', _options())
    msg = {'baseUrl': 'http://example.com/', 'relPath': '/data/file.dat'}

    with patch('sarracenia.transfer.https.subprocess.Popen') as mock_popen:
        proc = MagicMock()
        proc.returncode = 1
        mock_popen.return_value = proc

        result = t.getAccelerated(msg, 'file.dat', '/tmp/file.dat', 1024)
        assert result == -1


def test_get_accelerated_with_exact_length_includes_range_header():
    t = Https('https', _options())
    msg = {'baseUrl': 'http://example.com/', 'relPath': '/data/file.dat'}

    with patch('sarracenia.transfer.https.subprocess.Popen') as mock_popen:
        proc = MagicMock()
        proc.returncode = 0
        mock_popen.return_value = proc

        t.getAccelerated(msg, 'file.dat', '/tmp/file.dat', 1024, remote_offset=0, exactLength=True)
        cmd = mock_popen.call_args[0][0]
        assert any('Range' in arg for arg in cmd)


# ---------------------------------------------------------------------------
# stat
# ---------------------------------------------------------------------------

def test_stat_returns_fmdstat_with_metadata():
    t = _connected_transfer()
    t.path = '/data/'

    fake_response = FakeHTTPResponse(
        status=200,
        content_length=9659,
        last_modified='Thu, 22 Aug 2024 20:37:53 GMT',
    )

    with patch.object(t, '__open__', return_value=True):
        t.http = fake_response
        msg = {'baseUrl': 'http://example.com/'}
        st = t.stat('file.dat', msg)

    assert st is not None
    assert st.st_size == 9659
    assert st.st_mtime > 0
    assert st.st_atime > 0


def test_stat_returns_none_when_open_fails():
    t = _connected_transfer()
    t.path = '/data/'

    with patch.object(t, '__open__', return_value=False):
        msg = {'baseUrl': 'http://example.com/'}
        st = t.stat('file.dat', msg)

    assert st is None


def test_stat_returns_none_when_non_200_status():
    t = _connected_transfer()
    t.path = '/data/'

    fake_response = FakeHTTPResponse(status=404)

    with patch.object(t, '__open__', return_value=True):
        t.http = fake_response
        msg = {'baseUrl': 'http://example.com/'}
        st = t.stat('file.dat', msg)

    assert st is None


def test_stat_returns_fmdstat_with_content_length_only():
    t = _connected_transfer()
    t.path = '/data/'

    # Only Content-Length header, no Last-Modified
    fake_response = FakeHTTPResponse(status=200, content_length=512)

    with patch.object(t, '__open__', return_value=True):
        t.http = fake_response
        msg = {'baseUrl': 'http://example.com/'}
        st = t.stat('file.dat', msg)

    assert st is not None
    assert st.st_size == 512


def test_stat_returns_none_when_no_metadata():
    t = _connected_transfer()
    t.path = '/data/'

    # Response with no Content-Length and no Last-Modified
    fake_response = FakeHTTPResponse(status=200)

    with patch.object(t, '__open__', return_value=True):
        t.http = fake_response
        msg = {'baseUrl': 'http://example.com/'}
        st = t.stat('file.dat', msg)

    assert st is None
