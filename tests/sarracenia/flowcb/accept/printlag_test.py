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

from sarracenia.flowcb.accept.printlag import PrintLag
from sarracenia import Message as SR3Message
import sarracenia.config



def make_message():
    m = SR3Message()
    m['new_file'] = '/foo/bar/NewFile.txt'
    m['pubTime'] = '20180118T151049.356378078'
    return m

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList

def test_after_accept(caplog, mocker):
    options = sarracenia.config.default_config()
    options.logLevel = 'DEBUG'
    printlag = PrintLag(options)
    
    message = make_message()
    worklist = make_worklist()
    worklist.incoming = [message]

    now = sarracenia.nowflt()
    message['pubTime'] = sarracenia.timeflt2str(now - 100)
    mocker.patch('sarracenia.nowflt', return_value=now)
    printlag.after_accept(worklist)
    assert len(worklist.incoming) == 1 
    log = "print_lag, posted: %s, lag: %.2f sec. to deliver: %s, " % (message['pubTime'], 100, message['new_file'])
    assert log in caplog.messages