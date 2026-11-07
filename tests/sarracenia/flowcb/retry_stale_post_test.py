"""Post retries must not advertise an old checksum for a replaced local file."""

import base64
import hashlib
from types import SimpleNamespace
from unittest.mock import patch

import fakeredis
import pytest

from sarracenia import Message
from sarracenia.flowcb.retry import Retry


class Options(SimpleNamespace):
    def add_option(self, name, kind, default=None):
        if not hasattr(self, name):
            setattr(self, name, default)


def make_retry(tmp_path, driver, **overrides):
    options = Options(no=1, retry_ttl=0, logLevel='DEBUG', component='sarra',
                      config='probe', batch=10, retryCountMax=0,
                      queueName='probe', retry_driver=driver, download=True,
                      housekeeping=0, pid_filename=str(tmp_path / 'probe.pid'),
                      redisqueue_serverurl='redis://localhost:6379/0')
    options.__dict__.update(overrides)
    retry = Retry(options)
    retry.on_start()
    return retry


def make_message(path, body, method='md5'):
    message = Message()
    message.update(baseUrl='http://localhost/', relPath=path.name,
                   new_path=str(path), pubTime='20261106000000', size=len(body),
                   identity={'method': method, 'value': base64.b64encode(
                       hashlib.new(method, body).digest()).decode('ascii')})
    message['_deleteOnPost'].add('new_path')
    return message


def worklist():
    return SimpleNamespace(ok=[], incoming=[], rejected=[], failed=[])


@pytest.mark.parametrize('driver', ['disk', 'redis'])
@pytest.mark.parametrize('method', ['md5', 'sha512'])
@pytest.mark.parametrize('changed', [False, True])
def test_local_post_retry_after_restart(tmp_path, driver, method, changed):
    path = tmp_path / 'latest.txt'
    old_body = b'first version\n'
    path.write_bytes(old_body)
    message = make_message(path, old_body, method)
    with patch('redis.from_url', new=fakeredis.FakeStrictRedis.from_url):
        retry = make_retry(tmp_path, driver)
        first = worklist()
        first.failed = [message]
        retry.after_post(first)
        retry.on_housekeeping()
        if driver == 'disk':
            retry.on_stop()
            retry = make_retry(tmp_path, driver)
        if changed:
            path.write_bytes(b'other version\n')
        second = worklist()
        retry.after_work(second)
        assert len(second.ok) == (0 if changed else 1)
        assert len(second.rejected) == (1 if changed else 0)
        assert len(retry.post_retry) == 0
        retry.on_stop()


def test_resized_local_post_retry_is_rejected_without_hashing(tmp_path):
    path = tmp_path / 'latest.txt'
    path.write_bytes(b'first version\n')
    message = make_message(path, b'first version\n')
    retry = make_retry(tmp_path, 'disk')
    try:
        first = worklist()
        first.failed = [message]
        retry.after_post(first)
        retry.on_housekeeping()
        path.write_bytes(b'a longer replacement body\n')
        second = worklist()
        with patch('sarracenia.flowcb.retry.Identity.factory') as factory:
            retry.after_work(second)
        factory.assert_not_called()
        assert not second.ok
        assert [m['report']['code'] for m in second.rejected] == [410]
    finally:
        retry.on_stop()


@pytest.mark.parametrize('driver', ['disk', 'redis'])
def test_unreadable_local_post_retry_stays_pending(tmp_path, driver):
    path = tmp_path / 'latest.txt'
    message = make_message(path, b'first version\n')
    with patch('redis.from_url', new=fakeredis.FakeStrictRedis.from_url):
        retry = make_retry(tmp_path, driver)
        first = worklist()
        first.failed = [message]
        retry.after_post(first)
        retry.on_housekeeping()
        second = worklist()
        retry.after_work(second)
        assert not second.ok
        assert not second.rejected
        assert len(retry.post_retry) == 1

        # The requeued notice waits for housekeeping, like any other retry,
        # so an unreadable file is not re-read on every pass.
        path.write_bytes(b'first version\n')
        third = worklist()
        retry.after_work(third)
        assert not third.ok
        assert not third.rejected

        retry.on_housekeeping()
        fourth = worklist()
        retry.after_work(fourth)
        assert [m['identity'] for m in fourth.ok] == [message['identity']]
        assert fourth.ok[0]['_isRetry'] == 2
        assert len(retry.post_retry) == 0
        retry.on_stop()


@pytest.mark.parametrize('override,extra', [
    ({'download': False}, {}),
    ({'component': 'sender'}, {}),
    ({'component': 'flow', 'flowMain': 'sender'}, {}),
    ({}, {'fileOp': {'remove': ''}}),
    ({}, {'blocks': {'method': 'inplace', 'number': 0, 'size': 10}}),
    ({}, {'identity': {'method': 'random', 'value': '1234'}}),
    ({}, {'content': {'encoding': 'utf-8', 'value': 'body'}}),
])
def test_nonlocal_or_noncontent_retry_keeps_existing_behavior(tmp_path, override, extra):
    message = make_message(tmp_path / 'absent.txt', b'body')
    message.update(extra)
    retry = make_retry(tmp_path, 'disk', **override)
    try:
        first = worklist()
        first.failed = [message]
        retry.after_post(first)
        retry.on_housekeeping()
        second = worklist()
        retry.after_work(second)
        assert second.ok == [message]
    finally:
        retry.on_stop()
