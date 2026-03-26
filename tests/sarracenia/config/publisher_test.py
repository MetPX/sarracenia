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


def test_format_derived_from_v02_topicprefix():
    """post_topicPrefix v02.post should derive format v02.

    This is the bug that Peter found -- post_format defaulted to 'v03'
    which always took priority, so post_topicPrefix was never used.
    """
    opts = make_options(post_topicPrefix=['v02', 'post'])
    pub = Publisher(opts)
    assert pub['format'] == 'v02'


def test_format_derived_from_v03_topicprefix():
    """post_topicPrefix v03.post should derive format v03."""
    opts = make_options(post_topicPrefix=['v03', 'post'])
    pub = Publisher(opts)
    assert pub['format'] == 'v03'


def test_explicit_post_format_overrides_topicprefix():
    """If user explicitly sets post_format, it wins over topicPrefix."""
    opts = make_options(
        post_format='v03',
        post_topicPrefix=['v02', 'post'],
    )
    pub = Publisher(opts)
    assert pub['format'] == 'v03'


def test_explicit_v02_post_format():
    """If user explicitly sets post_format v02, use it."""
    opts = make_options(post_format='v02')
    pub = Publisher(opts)
    assert pub['format'] == 'v02'
