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

from sarracenia.flowcb.accept.posthourtree import Posthourtree
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message():
    m = SR3Message()
    m['new_dir'] = '/foo/bar'

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
    posthourtree = Posthourtree(sarracenia.config.default_config())
    
    worklist = make_worklist()
    worklist.incoming = [make_message()]

    posthourtree.after_accept(worklist)
    assert len(worklist.incoming) == 1
    assert bool(re.match(r"/foo/bar/\d{2}", worklist.incoming[0]['new_dir'])) == True