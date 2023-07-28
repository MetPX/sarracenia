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

from sarracenia.flowcb.accept.longflow import LongFlow
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message():
    m = SR3Message()
    m['headers'] = {}

    return m

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList

def test_after_accept():
    longflow = LongFlow(sarracenia.config.default_config())
    
    worklist = make_worklist()
    worklist.incoming = [make_message(), make_message()]

    longflow.after_accept(worklist)
    assert len(worklist.incoming) == 2
    assert len(worklist.incoming[0]['headers']['toolong']) == len('1234567890ßñç' * 26)