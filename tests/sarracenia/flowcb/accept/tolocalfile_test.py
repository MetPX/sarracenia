import pytest
import types

import time

#useful for debugging tests
def pretty(*things, **named_things):
    import pprint
    for t in things:
        pprint.PrettyPrinter(indent=2, width=200).pprint(t)
    for k,v in named_things.items():
        print(str(k) + ":")
        pprint.PrettyPrinter(indent=2, width=200).pprint(v)

from sarracenia.flowcb.accept.tolocalfile import ToLocalFile
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message(relpathPrefix = '', baseUrl = 'http://NotAReal.url'):
    m = SR3Message()
    m['baseUrl'] = baseUrl 
    m['relPath'] = relpathPrefix + 'not/a/real/directory'

    return m

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList

def test___init__():
    options = sarracenia.config.default_config()
    tolocalfile = ToLocalFile(options)


def test_after_accept():
    #Set 1
    tolocalfile = ToLocalFile(sarracenia.config.default_config())
    worklist = make_worklist()
    worklist.incoming = [make_message(), make_message(baseUrl='file:')]
    tolocalfile.after_accept(worklist)
    assert len(worklist.incoming) == 1
    assert len(worklist.rejected) == 1
    assert worklist.incoming[0]['baseUrl'] == 'file:'
    assert worklist.rejected[0]['saved_baseUrl'] == 'http://NotAReal.url'


    #set 2
    options = sarracenia.config.default_config()
    options.baseDir = '//foo/bar'
    tolocalfile = ToLocalFile(options)
    worklist = make_worklist()
    worklist.incoming = [make_message('/wiggle/'), make_message('//foo/bar/')]
    tolocalfile.after_accept(worklist)
    assert len(worklist.incoming) == 1
    assert len(worklist.rejected) == 1
    assert worklist.incoming[0]['relPath'] == '//foo/bar//wiggle/not/a/real/directory'
    assert worklist.rejected[0]['relPath'] == '//foo/bar/not/a/real/directory'
