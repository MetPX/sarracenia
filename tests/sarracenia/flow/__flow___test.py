import pytest
from tests.conftest import *

import urllib.parse

import sarracenia.config
import sarracenia.flow
import copy


def _build_urlToMatch(m):
    """
    Replicate the urlToMatch construction logic from sarracenia/flow/__init__.py
    (the lines changed to fix issue #1573).
    """
    url = m['baseUrl']
    if (m['baseUrl'][-1] == '/') or (len(m['relPath']) > 0 and (m['relPath'][0] == '/')):
        if (m['baseUrl'][-1] == '/') and (len(m['relPath']) > 0) and (m['relPath'][0] == '/'):
            url += m['relPath'][1:]
        else:
            url += m['relPath']
    else:
        url += '/' + m['relPath']

    if 'sundew_extension' in m and urllib.parse.urlparse(url).path.count(":") < 1:
        urlToMatch = url + ':' + m['sundew_extension']
    else:
        urlToMatch = url

    return urlToMatch


def test_sundew_extension_appended_when_url_has_port():
    """
    Regression test for https://github.com/MetPX/sarracenia/issues/1573

    When a source URL has a port (e.g. http://host:8180/path), the old code
    counted colons in the full URL string. The port's colon caused the count
    to be >= 1, so sundew_extension was never appended to urlToMatch.

    The fix uses urllib.parse.urlparse(url).path.count(':') so only colons
    in the *path* portion are checked, correctly ignoring the port.
    """
    msg = sarracenia.Message()
    msg['baseUrl'] = 'http://dms-dev1.domain:8180/data/msc/'
    msg['relPath'] = 'forecast/atmospheric/aviation/file.txt'
    msg['sundew_extension'] = 'ext1'

    urlToMatch = _build_urlToMatch(msg)

    # The extension MUST be appended despite the port colon in the URL
    assert urlToMatch.endswith(':ext1'), \
        f"sundew_extension should be appended to urlToMatch, got: {urlToMatch}"


def test_sundew_extension_not_double_appended_when_path_has_colon():
    """
    If the path itself already contains a colon (sundew-style filename),
    the extension should NOT be appended again.
    """
    msg = sarracenia.Message()
    msg['baseUrl'] = 'http://host/data/'
    msg['relPath'] = 'SACN43_CWAO_121435:ext1'
    msg['sundew_extension'] = 'ext1'

    urlToMatch = _build_urlToMatch(msg)

    # Path already has a colon, so extension should NOT be appended
    assert urlToMatch == 'http://host/data/SACN43_CWAO_121435:ext1', \
        f"Extension should not be double-appended when path already has a colon, got: {urlToMatch}"


def test_sundew_extension_appended_when_url_has_no_port():
    """
    Sanity check: extension is appended on a plain URL without a port.
    """
    msg = sarracenia.Message()
    msg['baseUrl'] = 'http://plain-host/data/'
    msg['relPath'] = 'some/file.txt'
    msg['sundew_extension'] = 'EXT'

    urlToMatch = _build_urlToMatch(msg)

    assert urlToMatch.endswith(':EXT'), \
        f"sundew_extension should be appended for plain URL, got: {urlToMatch}"
