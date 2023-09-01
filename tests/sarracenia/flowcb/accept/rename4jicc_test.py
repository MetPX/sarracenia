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

from sarracenia.flowcb.accept.rename4jicc import Rename4Jicc
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message(has_ccstn = False):
    m = SR3Message()
    if has_ccstn:
        m["new_file"] = '20160302/MSC-CMC/METADATA/ccstn.dat:pull-ccstn:NCP:JICC:5:Codecon:20160302212706'
    else:
        m["new_file"] = '20160302/MSC-CMC/METADATA/pull-ccstn:NCP:JICC:5:Codecon:20160302212706'

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
    rename4jicc = Rename4Jicc(options)

@pytest.mark.depends(on=['test___init__'])
def test_after_accept(mocker):
    localtime = time.localtime()
    mocker.patch('time.localtime', return_value=localtime)

    options = sarracenia.config.default_config()
    options.logLevel = "DEBUG"
    rename4jicc = Rename4Jicc(options)

    worklist = make_worklist()
    worklist.incoming = [make_message(), make_message(True)]
    rename4jicc.after_accept(worklist)
    assert len(worklist.incoming) == 2
    assert worklist.incoming[0]['new_file'] == '20160302/MSC-CMC/METADATA/pull-ccstn:NCP:JICC:5:Codecon:20160302212706'
    assert worklist.incoming[1]['new_file'] == '20160302/MSC-CMC/METADATA/jicc.' + time.strftime('%Y%m%d%H%M', localtime) + '.ccstn.dat:pull-ccstn:NCP:JICC:5:Codecon:20160302212706'
