import pytest
from tests.conftest import *
#from unittest.mock import Mock

import sarracenia.config
import sarracenia.flowcb.v2wrapper


def test_after_work_routes_on_file_failures_to_retry():
    wrapper = object.__new__(sarracenia.flowcb.v2wrapper.V2Wrapper)
    accepted = object()
    failed = object()
    rejected_on_post = object()
    worklist = type('Worklist', (), {
        'ok': [accepted, failed, rejected_on_post],
        'failed': [],
        'rejected': [],
    })()

    def run_entry(entry_point, message):
        if entry_point == 'on_file':
            return message is not failed
        return message is not rejected_on_post

    wrapper.run_entry = run_entry

    wrapper.after_work(worklist)

    assert worklist.ok == [accepted]
    assert worklist.failed == [failed]
    assert worklist.rejected == [rejected_on_post]
