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

from sarracenia.flowcb.accept.tohttp import ToHttp
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message():
    m = SR3Message()
    m['baseUrl'] = 'http://NotAReal.url'
    m['relPath'] = 'a/rel/Path/file.txt'
    m['pubTime'] = '20180118151049.356378078'
    m['urlstr'] = 'file://fake/path'
    m['savedurl'] = '/new/fake/path'

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
    with pytest.raises(TypeError):
        tohttp = ToHttp(options)


def test_after_accept():
    #Set 1 - using o.baseDir
    options = sarracenia.config.default_config()
    options.baseDir = "/fake/path"
    worklist = make_worklist()
    message = make_message()
    worklist.incoming = [message]
    tohttp = ToHttp(options)
    tohttp.after_accept(worklist)
    assert len(worklist.incoming) == 1
    assert worklist.incoming[0]['urlstr'] == '/new/fake/path'
    assert worklist.incoming[0]['set_notice'] == '%s %s %s' % (message['pubTime'], 'file:', message['relPath'])

    #Set 2 - using o.toHttpRoot
    options = sarracenia.config.default_config()
    options.toHttpRoot = ["/fake/path"]
    message = make_message()
    worklist = make_worklist()
    worklist.incoming = [message]
    tohttp = ToHttp(options)
    tohttp.after_accept(worklist)
    assert len(worklist.incoming) == 1
    assert worklist.incoming[0]['urlstr'] == '/new/fake/path'
    assert worklist.incoming[0]['set_notice'] == '%s %s %s' % (message['pubTime'], 'file:', message['relPath'])



