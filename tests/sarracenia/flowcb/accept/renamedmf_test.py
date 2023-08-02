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

from sarracenia.flowcb.accept.renamedmf import RenameDMF
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message():
    m = SR3Message()
    m['rename'] = 'fooBarBaz:20081008190602'
    m['new_file'] = 'fooBarBaz:20081008190602'

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
    renamedmf = RenameDMF(options)


def test_after_accept(mocker):

    localtime = time.localtime()

    mocker.patch('time.localtime', return_value=localtime)
    renamedmf = RenameDMF(sarracenia.config.default_config())

    #Set 1 - option.new_dir doesn't exists
    worklist = make_worklist()
    worklist.incoming = [make_message()]
    renamedmf.after_accept(worklist)
    assert len(worklist.incoming) == 1
    assert worklist.incoming[0]['rename'] == 'fooBarBaz:20081008190602' + time.strftime(':%Y%m%d%H%M%S', localtime)
    assert worklist.incoming[0]['new_file'] == 'fooBarBaz:20081008190602' + time.strftime(':%Y%m%d%H%M%S', localtime)
