import pytest
import types
import os
import time

#useful for debugging tests
def pretty(*things, **named_things):
    import pprint
    for t in things:
        pprint.PrettyPrinter(indent=2, width=200).pprint(t)
    for k,v in named_things.items():
        print(str(k) + ":")
        pprint.PrettyPrinter(indent=2, width=200).pprint(v)

from sarracenia.flowcb.accept.speedo import Speedo
from sarracenia import Message as SR3Message
import sarracenia.config

from sarracenia import timestr2flt, timeflt2str, nowflt, naturalSize, naturalTime

def make_message(pubtimeflt):
    m = SR3Message()
    m['topic'] = 'message_topic'
    m["notice"] = "20180118151050.45 ftp://anonymous@localhost:2121 /sent_by_tsource2send/SXAK50_KWAL_181510___58785"
    m["partstr"] = "foo,1000,baz,bar,boz"
    m["headers"] = {
            "atime": "20180118151049.356378078", 
            "from_cluster": "localhost",
            "mode": "644",
            "parts": "1,69,1,0,0",
            "source": "tsource",
            "sum": "d,c35f14e247931c3185d5dc69c5cd543e",
            "to_clusters": "localhost"
        }
    m['pubTime'] = timeflt2str(pubtimeflt)
    return m

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList

def test___init__(mocker):
    nowtime = time.time()
    mocker.patch('time.time', return_value=nowtime)

    options = sarracenia.config.default_config()
    options.logLevel = 'DEBUG'
    speedo = Speedo(options)

    assert speedo.msg_speedo_last == nowflt()
    assert speedo.msg_speedo_bytecount == speedo.msg_speedo_msgcount == 0

@pytest.mark.depends(on=['test___init__'])
def test_after_accept(mocker, caplog):
    nowtime = time.time()
    nowtime_flt = nowflt()

    options = sarracenia.config.default_config()
    options.logLevel = 'DEBUG'

    #make speedo.msg_speedo_last be in the past
    mocker.patch('time.time', return_value=nowtime - 300)
    speedo = Speedo(options)

    mocker.patch('time.time', return_value=nowtime)
    
    caplog.clear()
    worklist = make_worklist()
    worklist.incoming = [make_message(nowtime_flt - 10)]
    speedo.after_accept(worklist)
    assert len(worklist.incoming) == 1
    assert len(caplog.messages) == 1
    assert 'speedo:   1 messages received: 0.0033 msg/s, 3.33 bytes/s, lag:   10 s' in caplog.messages

    caplog.clear()
    worklist.incoming = [make_message(nowtime_flt - 300)]
    speedo.msg_speedo_last = nowflt() - 300
    speedo.after_accept(worklist)
    assert len(worklist.incoming) == 1
    assert len(caplog.messages) == 2
    assert 'speedo:   1 messages received: 0.0033 msg/s, 3.33 bytes/s, lag:  300 s' in caplog.messages
    assert 'speedo: Excessive lag! Messages posted  300 s ago' in caplog.messages

    caplog.clear()
    speedo.after_accept(worklist)
    assert len(caplog.messages) == 0