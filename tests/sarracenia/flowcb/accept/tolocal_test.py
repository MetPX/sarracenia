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

from sarracenia.flowcb.accept.tolocal import ToLocal
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message():
    m = SR3Message()
    m['baseUrl'] = 'http://NotAReal.url'
    m['urlstr'] = 'http://NotAReal.url/20230804141101/Some/Directory/file.txt'

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
    #Set 1 - If neither o.baseDir, or o.toHttpRoot are set it throws an error
    options = sarracenia.config.default_config()
    tolocal = ToLocal(options)
    assert tolocal.o.ldocroot == None

    options.toLocalRoot = ['/var/www/html']
    tolocal = ToLocal(options)
    assert tolocal.o.ldocroot == '/var/www/html'

    options.toLocalUrl = ['/var/www/html']
    tolocal = ToLocal(options)
    assert tolocal.o.lurlre.pattern == '/var/www/html'


def test_after_accept():
    #Set 1 - using o.baseDir
    options = sarracenia.config.default_config()
    options.baseDir = "/fake/path"
    worklist = make_worklist()
    message = make_message()
    worklist.incoming = [message]
    tolocal = ToLocal(options)
    tolocal.after_accept(worklist)
    assert len(worklist.incoming) == 1
    assert worklist.incoming[0]['savedurl'] == 'http://NotAReal.url/'
    assert worklist.incoming[0]['urlstr'] == 'file://fake/path/20230804141101/Some/Directory/file.txt'




