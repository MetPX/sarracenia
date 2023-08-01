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

from sarracenia.flowcb.accept.httptohttps import HttpToHttps
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message(scheme):
    m = SR3Message()
    m['baseUrl'] = scheme + '://NotAReal.url'
    m['relPath'] = 'a/rel/Path/file.txt'
    m['pubTime'] = '20180118151049.356378078'

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
    httptohttps = HttpToHttps(sarracenia.config.default_config())
    
    message_http = make_message('http')
    message_https = make_message('https')
    message_sftp = make_message('sftp')

    worklist = make_worklist()
    worklist.incoming = [message_http, message_https, message_sftp]

    httptohttps.after_accept(worklist)
    assert len(worklist.incoming) == 3
    assert worklist.incoming[0]['baseUrl'] == 'https://NotAReal.url'
    assert worklist.incoming[0]['baseUrl'] == message_http['relPath']
    assert worklist.incoming[2]['baseUrl'] == 'sftp://NotAReal.url'
    #assert 'set_notice' not in worklist.incoming[2]
