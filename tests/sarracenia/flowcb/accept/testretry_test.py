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

from sarracenia.flowcb.accept.testretry import TestRetry
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message(isRetry = False):
    m = SR3Message()
    m['baseUrl'] = 'http://NotAReal.url'
    m['relPath'] = 'a/rel/Path/file.txt'
    m['pubTime'] = '20180118151049.356378078'
    if isRetry:
        m['isRetry'] = True

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
    options.logLevel = 'DEBUG'
    #options.pxClient = 'meadow,foobar'
    testretry = TestRetry(options)
    assert testretry.sendTo == testretry.msg_baseUrl_good == testretry.details_bad== None

@pytest.mark.depends(on=['test___init__'])
def test_after_accept(caplog, mocker):
    #Set 1 - When random is True, with a message having isRetry
    caplog.clear()
    options = sarracenia.config.default_config()
    options.sendTo = 'http://options.sendTo.url'
    options.logLevel = 'DEBUG'
    worklist = make_worklist()
    worklist.incoming = [make_message()]
    mocker.patch('random.randint', return_value=0)
    testretry = TestRetry(options)
    testretry.after_accept(worklist)
    assert len(worklist.incoming) == 0
    assert "return from testretry after_accept" in caplog.messages


    #Set 2 - When random is True, with a message having isRetry
    caplog.clear()
    options = sarracenia.config.default_config()
    options.sendTo = 'http://options.sendTo.url'
    options.logLevel = 'DEBUG'
    testretry = TestRetry(options)
    testretry.sendTo = 'http://testretry.sendTo.url'
    testretry.msg_baseUrl_good = 'http://testretry.msg_baseUrl_good.url'
    message_isRetry = make_message(isRetry=True)
    worklist = make_worklist()
    worklist.incoming = [message_isRetry]
    testretry.after_accept(worklist)
    assert len(worklist.incoming) == 0
    assert options.sendTo == 'http://testretry.sendTo.url'
    assert options.details.url.netloc == 'testretry.sendTo.url'


    #Set 3 - When random is False, there's nothing that gets retried
    caplog.clear()
    options = sarracenia.config.default_config()
    options.sendTo = 'https://TestUsername:TestPassword@options.sendTo.url/Path/File.txt'
    options.component = 'watch'
    options.logLevel = 'DEBUG'
    testretry = TestRetry(options)
    message = make_message()
    worklist = make_worklist()
    worklist.incoming = [message]
    mocker.patch('random.randint', return_value=1)
    testretry.after_accept(worklist)
    assert len(worklist.incoming) == 0
    assert testretry.msg_baseUrl_bad == message['baseUrl']
    assert testretry.sendTo == options.sendTo
    assert options.details.url.username == 'TestUsername'
    assert "making it bad 1" in caplog.messages


    #Set 4 - When random is True, without a message having isRetry, and component is watch
    caplog.clear()
    options = sarracenia.config.default_config()
    options.sendTo = 'https://TestUsername:TestPassword@options.sendTo.url/Path/File.txt'
    options.component = 'sender'
    options.logLevel = 'DEBUG'
    testretry = TestRetry(options)
    mocker.patch('random.randint', return_value=1)
    message = make_message()
    worklist = make_worklist()
    worklist.incoming = [message]
    testretry.after_accept(worklist)
    assert len(worklist.incoming) == 0
    assert options.details.url.username == 'ruser'
    assert "making it bad 2" in caplog.messages

