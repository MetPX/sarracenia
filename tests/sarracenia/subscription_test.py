import pytest
from tests.conftest import *

from sarracenia.config.subscription import Subscriptions, normalize_subscription


class _FakeUrl:
    def __init__(self, scheme):
        self.scheme = scheme


class _FakeBroker:
    def __init__(self, scheme):
        self.url = _FakeUrl(scheme)

    def __str__(self):
        return f"{self.url.scheme}://fake"


def _amqp_sub():
    return {
        'broker': _FakeBroker('amqps'),
        'bindings': [{'exchange': 'xpublic', 'prefix': ['v02', 'post'], 'sub': ['#']}],
        'queue': {'name': 'q_anonymous_test_host_abc'},
    }


def _mqtt_sub():
    return {
        'broker': _FakeBroker('mqtts'),
        'bindings': [{'prefix': ['v02', 'post'], 'sub': ['#']}],
        'queue': {'name': 'q_test'},
    }


def test_normalize_subscription_amqp_joins_with_dot():
    s = _amqp_sub()
    normalize_subscription(s)
    b = s['bindings'][0]
    assert b['topic'] == 'v02.post.#'
    assert b['exchange'] == 'xpublic'
    assert 'sub' not in b and 'prefix' not in b


def test_normalize_subscription_mqtt_joins_with_slash_and_shares():
    s = _mqtt_sub()
    normalize_subscription(s)
    b = s['bindings'][0]
    assert b['topic'] == '$share/q_test/v02/post/#'
    assert 'sub' not in b and 'prefix' not in b


def test_normalize_subscription_is_idempotent():
    s = _amqp_sub()
    normalize_subscription(s)
    before = dict(s['bindings'][0])
    normalize_subscription(s)
    assert s['bindings'][0] == before


def test_normalize_subscription_leaves_existing_topic_alone():
    s = {
        'broker': _FakeBroker('amqp'),
        'bindings': [{'exchange': 'xpublic', 'topic': 'already.set.#'}],
        'queue': {'name': 'q'},
    }
    normalize_subscription(s)
    assert s['bindings'][0]['topic'] == 'already.set.#'


def test_normalize_subscription_strips_stale_sub_when_topic_present():
    # A binding that somehow has both: topic wins, leftovers cleared.
    s = {
        'broker': _FakeBroker('amqp'),
        'bindings': [{'exchange': 'xpublic', 'topic': 'already.set.#',
                      'prefix': ['v02'], 'sub': ['#']}],
        'queue': {'name': 'q'},
    }
    normalize_subscription(s)
    b = s['bindings'][0]
    assert b['topic'] == 'already.set.#'
    assert 'sub' not in b and 'prefix' not in b


def test_normalize_subscription_no_queue():
    # Publisher-side subscription dicts may not carry a queue. Should not crash.
    s = {
        'broker': _FakeBroker('amqp'),
        'bindings': [{'exchange': 'xpublic', 'prefix': ['v02', 'post'], 'sub': ['#']}],
    }
    normalize_subscription(s)
    assert s['bindings'][0]['topic'] == 'v02.post.#'


def test_normalize_subscription_scalar_prefix_and_sub():
    s = {
        'broker': _FakeBroker('amqp'),
        'bindings': [{'exchange': 'xpublic', 'prefix': 'v02', 'sub': '#'}],
        'queue': {'name': 'q'},
    }
    normalize_subscription(s)
    assert s['bindings'][0]['topic'] == 'v02.#'


def test_subscriptions_init_normalizes_amqp():
    # This is the regression case for issue #5: in-memory construction via
    # Subscriptions([...]) previously left bindings as prefix+sub, and
    # moth/amqp.py raised KeyError: 'topic' on use.
    subs = Subscriptions([_amqp_sub()])
    assert subs[0]['bindings'][0]['topic'] == 'v02.post.#'
    assert 'sub' not in subs[0]['bindings'][0]


def test_subscriptions_init_normalizes_mqtt():
    subs = Subscriptions([_mqtt_sub()])
    assert subs[0]['bindings'][0]['topic'] == '$share/q_test/v02/post/#'


def test_subscriptions_init_empty():
    subs = Subscriptions()
    assert len(subs) == 0
    subs2 = Subscriptions(None)
    assert len(subs2) == 0
    subs3 = Subscriptions([])
    assert len(subs3) == 0


def test_subscriptions_add_normalizes():
    subs = Subscriptions()
    subs.add(_amqp_sub())
    assert subs[0]['bindings'][0]['topic'] == 'v02.post.#'


def test_normalize_subscription_defaults_bindings_to_remove():
    # moth/amqp.py:432 iterates subscription['bindings_to_remove'] directly.
    # In-memory subs never carry that key, which produced a second KeyError
    # after the 'topic' fix. Normalize must default it to [].
    s = _amqp_sub()
    assert 'bindings_to_remove' not in s
    normalize_subscription(s)
    assert s['bindings_to_remove'] == []


def test_subscriptions_init_defaults_bindings_to_remove():
    subs = Subscriptions([_amqp_sub()])
    assert subs[0]['bindings_to_remove'] == []


def test_subscriptions_add_merges_new_binding():
    subs = Subscriptions([_amqp_sub()])
    # Second subscription, same broker+queue, different binding in pre-3.02 shape.
    second = {
        'broker': _FakeBroker('amqps'),
        'bindings': [{'exchange': 'xpublic', 'prefix': ['v03'], 'sub': ['post.#']}],
        'queue': {'name': 'q_anonymous_test_host_abc'},
    }
    subs.add(second)
    # Must have merged into the first entry as a second binding, with topic computed.
    assert len(subs) == 1
    topics = [b['topic'] for b in subs[0]['bindings']]
    assert 'v02.post.#' in topics
    assert 'v03.post.#' in topics
