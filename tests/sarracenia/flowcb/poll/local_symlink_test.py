import os

import pytest

import sarracenia
import sarracenia.config
from sarracenia.flowcb.poll import Poll


def make_poll(base_dir, follow_symlinks):
    options = sarracenia.config.no_file_config()
    options.post_baseUrl = 'file:'
    options.publishers = [{'baseUrl': 'file:', 'baseDir': str(base_dir)}]
    options.follow_symlinks = follow_symlinks
    options.fileEvents = ['create', 'modify', 'link']
    options.identity_method = 'random'

    poll = Poll.__new__(Poll)
    poll.o = options
    return poll


@pytest.mark.parametrize('follow_symlinks', [False, True])
def test_poll_file_post_returns_local_symlink_message(tmp_path, follow_symlinks):
    target = tmp_path / 'target.dat'
    target.write_bytes(b'weather data')
    link = tmp_path / 'product.dat'
    link.symlink_to(target.name)
    poll = make_poll(tmp_path, follow_symlinks)

    messages = poll.poll_file_post(None, str(tmp_path), link.name)

    assert len(messages) == 1
    assert isinstance(messages[0], sarracenia.Message)
    assert 'size' not in messages[0]
    if follow_symlinks:
        assert 'fileOp' not in messages[0]
        assert 'identity' in messages[0]
    else:
        assert messages[0]['fileOp'] == {'link': os.readlink(link)}
        assert 'identity' not in messages[0]
