import pytest
from tests.conftest import *
from datetime import timedelta
from unittest.mock import patch

import flufl.lock

import sarracenia.config
import sarracenia.flowcb.block_reassembly


class TestMessage(dict):

    def setReport(self, code, message):
        self.report = (code, message)


def test_short_block_fails_without_holding_reassembly_lock(tmp_path):
    options = sarracenia.config.default_config()
    options.inflight = None
    options.bufSize = 2
    callback = sarracenia.flowcb.block_reassembly.Block_reassembly(options)
    part_name = 'result§block_0,4_§'
    part_path = tmp_path / part_name
    part_path.write_bytes(b'ab')
    message = TestMessage({
        'blocks': {
            'manifest': {0: {'size': 4}},
            'number': 0,
            'size': 4,
        },
        'new_dir': str(tmp_path),
        'new_file': part_name,
        'relPath': part_name,
    })
    worklist = type('Worklist', (), {
        'ok': [message],
        'failed': [],
        'rejected': [],
    })()

    with patch('sarracenia.flowcb.block_reassembly.humanfriendly.parse_size', return_value=4):
        callback.after_work(worklist)

    assert worklist.ok == []
    assert worklist.failed == [message]
    assert worklist.rejected == []
    assert part_path.read_bytes() == b'ab'

    lock = flufl.lock.Lock(str(tmp_path / 'result.flufl_lock'))
    lock.lock(timeout=timedelta(seconds=1))
    lock.unlock()
