import pytest
import types

#useful for debugging tests
def pretty(*things, **named_things):
    import pprint
    for t in things:
        pprint.PrettyPrinter(indent=2, width=200).pprint(t)
    for k,v in named_things.items():
        print(str(k) + ":")
        pprint.PrettyPrinter(indent=2, width=200).pprint(v)

from sarracenia.flowcb.accept.postoverride import PostOverride
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message(withOverrideDel = False):
    m = SR3Message()
    m['headers'] = {'toOverride': 'overriden__origvalue'}
    if withOverrideDel:
        m['headers']['toDelete'] = 'toDelete__value'

    return m

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList

def test___init__(caplog):
    #Set 1 - If neither o.baseDir, or o.toHttpRoot are set, CB creation throws an error
    options = sarracenia.config.default_config()
    options.postOverride = ['Foo Bar']
    postoverride = PostOverride(options)
    assert len(caplog.messages) == 1
    assert "postOverride settings: ['Foo Bar']" in caplog.messages


def test_after_accept():
    #Set 1
    options = sarracenia.config.default_config()
    options.logLevel = 'DEBUG'
    options.postOverride = ['toOverride Bar']
    options.postOverrideDel = ['toDelete']
    worklist = make_worklist()
    worklist.incoming = [make_message(), make_message(True)]
    postoverride = PostOverride(options)
    postoverride.after_accept(worklist)
    assert len(worklist.incoming) == 3
    assert worklist.incoming[0]['headers']['toOverride'] == worklist.incoming[1]['headers']['toOverride'] == 'Bar'
    assert worklist.incoming[1]['headers']['toDelete'] == 'toDelete__value'
    assert 'toDelete' not in worklist.incoming[2]['headers']



