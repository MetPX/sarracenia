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

def make_message(scheme='https'):
    m = SR3Message()
    m['baseUrl'] = scheme + '://NotAReal.url/Or/A/RealPath'
    m['relPath'] = 'a/rel/Path/file.txt'
    m['pubTime'] = '20180118151049.356378078'
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
    tohttp = ToHttp(options)
    assert tohttp._ldocroot == None

    options.baseDir = 'baseDir_val'
    tohttp = ToHttp(options)
    assert tohttp._ldocroot == 'baseDir_val'

    options.toHttpRoot = 'toHttpRoot_val'
    tohttp = ToHttp(options)
    assert tohttp._ldocroot == 'toHttpRoot_val'

@pytest.mark.depends(on=['test___init__'])
def test_after_accept():

    #Set 1 - not using either config option
    options = sarracenia.config.default_config()
    worklist = make_worklist()
    message = make_message()
    worklist.incoming = [message]
    tohttp = ToHttp(options)
    tohttp.after_accept(worklist)
    assert len(worklist.incoming) == 1
    assert worklist.incoming[0]['baseUrl'] == 'http://NotAReal.url/Or/A/RealPath'

    #Set 2 - using o.baseDir
    options = sarracenia.config.default_config()
    options.baseDir = "/fake/path/baseDir"
    worklist = make_worklist()
    message = make_message()
    worklist.incoming = [message]
    tohttp = ToHttp(options)
    tohttp.after_accept(worklist)
    assert len(worklist.incoming) == 1
    assert worklist.incoming[0]['baseUrl'] == 'http://NotAReal.url/fake/path/baseDir/Or/A/RealPath'

    #Set 3 - using o.toHttpRoot
    options = sarracenia.config.default_config()
    options.toHttpRoot = "/fake/path/toHttpRoot"
    message = make_message('sftp')
    worklist = make_worklist()
    worklist.incoming = [message]
    tohttp = ToHttp(options)
    tohttp.after_accept(worklist)
    assert len(worklist.incoming) == 1
    assert worklist.incoming[0]['baseUrl'] == 'http://NotAReal.url/fake/path/toHttpRoot/Or/A/RealPath'
    assert worklist.incoming[0]['relPath'] == message['relPath']



