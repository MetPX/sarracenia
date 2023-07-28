import pytest
import types, re

#useful for debugging tests
def pretty(*things, **named_things):
    import pprint
    for t in things:
        pprint.PrettyPrinter(indent=2, width=200).pprint(t)
    for k,v in named_things.items():
        print(str(k) + ":")
        pprint.PrettyPrinter(indent=2, width=200).pprint(v)

from sarracenia.flowcb.accept.trim_legacy_fields import Trim_legacy_fields
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message():
    m = SR3Message()
    m['SomethingGood'] = 'SomethingGood__value'
    m['atime'] = 'atime__value'
    m['filename'] = 'filename__value'
    m['from_cluster'] = 'from_cluster__value'
    m['mtime'] = 'mtime__value'
    m['source'] = 'source__value'
    m['to_clusters' ] = 'to_clusters__value'

    return m

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList

def test_after_accept(caplog):

    trim_legacy_fields = Trim_legacy_fields(sarracenia.config.default_config())

    worklist = make_worklist()
    worklist.incoming = [make_message()]

    trim_legacy_fields.after_accept(worklist)

    assert len(worklist.incoming) == 1
    assert 'SomethingGood' in worklist.incoming[0]
    assert 'atime' not in worklist.incoming[0]