import pytest
import types
import os

#useful for debugging tests
def pretty(*things, **named_things):
    import pprint
    for t in things:
        pprint.PrettyPrinter(indent=2, width=200).pprint(t)
    for k,v in named_things.items():
        print(str(k) + ":")
        pprint.PrettyPrinter(indent=2, width=200).pprint(v)

from sarracenia.flowcb.accept.save import Save
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message():
    m = SR3Message()
    m['topic'] = 'message_topic'
    m["notice"] = "20180118151050.45 ftp://anonymous@localhost:2121 /sent_by_tsource2send/SXAK50_KWAL_181510___58785"
    m["headers"] = {
            "atime": "20180118151049.356378078", 
            "from_cluster": "localhost",
            "parts": "1,69,1,0,0",
            "source": "tsource",
            "to_clusters": "localhost"
        }
    return m

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList

def test___init__(tmp_path, caplog):
    options = sarracenia.config.default_config()
    options.logLevel = 'DEBUG'
    save = Save(options)
    assert 'msg_save: setting msgSaveFile setting is mandatory' in caplog.messages

    file = str(tmp_path) + os.sep + 'saveFile.json'
    options.msgSaveFile = file
    assert os.path.exists(file) == False
    save = Save(options)
    assert os.path.exists(file) == True
    assert os.path.isfile(file) == True

@pytest.mark.depends(on=['test___init__'])
def test_after_accept(tmp_path, caplog):
    file = str(tmp_path) + os.sep + 'saveFile.json'
    options = sarracenia.config.default_config()
    options.logLevel = "DEBUG"
    options.msgSaveFile = file
    save = Save(options)

    caplog.clear()
    worklist = make_worklist()
    worklist.incoming = [make_message(), make_message()]
    save.after_accept(worklist)
    assert len(worklist.incoming) == 2
    assert len(caplog.messages) == 2
    assert len(open(file, 'r').readlines()) == 2