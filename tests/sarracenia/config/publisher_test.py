import pytest
from tests.conftest import *
from unittest.mock import MagicMock

from sarracenia.config.publisher import Publisher


def make_options(**overrides):
    """Minimal options object for Publisher."""
    opts = MagicMock()
    opts.post_broker = MagicMock()
    opts.post_broker.url = MagicMock()
    opts.post_broker.url.username = 'tsource'
    opts.post_broker.url.scheme = 'amqp'
    opts.post_exchange = ['xs_tsource']
    opts.post_baseDir = '/tmp'
    opts.post_baseUrl = 'http://localhost'
    opts.post_exchangeSplit = 0

    # defaults matching config/__init__.py
    opts.post_format = None
    opts.post_topicPrefix = ['v03', 'post']

    for k, v in overrides.items():
        setattr(opts, k, v)

    return opts


def test_format_defaults_to_v03():
    """When neither post_format nor post_topicPrefix is set, default to v03."""
    opts = make_options()
    del opts.post_topicPrefix
    del opts.post_format
    pub = Publisher(opts)
    assert pub['format'] == 'v03'
    assert pub['post_format'] == 'v03'


def test_format_derived_from_v02_topicprefix():
    """post_topicPrefix v02.post should derive format v02.

    This is the bug that Peter found -- post_format defaulted to 'v03'
    which always took priority, so post_topicPrefix was never used.
    """
    opts = make_options(post_topicPrefix=['v02', 'post'])
    pub = Publisher(opts)
    assert pub['format'] == 'v02'
    assert pub['post_format'] == 'v02'


def test_format_derived_from_v03_topicprefix():
    """post_topicPrefix v03.post should derive format v03."""
    opts = make_options(post_topicPrefix=['v03', 'post'])
    pub = Publisher(opts)
    assert pub['format'] == 'v03'
    assert pub['post_format'] == 'v03'


def test_explicit_post_format_overrides_topicprefix():
    """If user explicitly sets post_format, it wins over topicPrefix."""
    opts = make_options(
        post_format='v03',
        post_topicPrefix=['v02', 'post'],
    )
    pub = Publisher(opts)
    assert pub['format'] == 'v03'
    assert pub['post_format'] == 'v03'


def test_explicit_v02_post_format():
    """If user explicitly sets post_format v02, use it."""
    opts = make_options(post_format='v02')
    pub = Publisher(opts)
    assert pub['format'] == 'v02'
    assert pub['post_format'] == 'v02'


def test_topicprefix_fallback_is_empty_list():
    """When neither post_topicPrefix nor topicPrefix is set, fallback must
    be [] (empty list), not None. Peter fixed this in bab4b9424 -- None
    causes TypeError when downstream code iterates or concatenates."""
    opts = make_options()
    del opts.post_topicPrefix
    del opts.topicPrefix
    pub = Publisher(opts)
    assert pub['topicPrefix'] == [], \
        "topicPrefix fallback must be [] not None (see commit bab4b9424)"


def test_basedir_missing_no_keyerror():
    """Publisher must not raise KeyError when baseDir is absent from the
    dict. The guard must use 'or' (short-circuit) not 'and'."""
    opts = make_options(post_baseUrl='file:/data/incoming')
    del opts.post_baseDir
    # This must not raise KeyError
    pub = Publisher(opts)
    assert pub['baseDir'] == '/data/incoming'


def test_basedir_empty_string_derives_from_url():
    """When baseDir is set but empty, it should still derive from baseUrl."""
    opts = make_options(post_baseDir='', post_baseUrl='file:/data/output')
    pub = Publisher(opts)
    assert pub['baseDir'] == '/data/output'
