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

from sarracenia.flowcb.accept.toclusters import ToClusters
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message(tocluster):
    m = SR3Message()
    #['to_clusters']
    m['headers'] = {'to_clusters': tocluster}

    return m

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList

def test___init__(caplog):
    options = sarracenia.config.default_config()
    options.logLevel = 'DEBUG'
    toclusters = ToClusters(options)
    assert "msgToClusters setting mandatory" in caplog.messages

def test_after_accept(caplog):

    options = sarracenia.config.default_config()
    options.logLevel = 'DEBUG'
    options.msgToClusters = ['GoodCluster', 'AnotherGoodCluster']
    toclusters = ToClusters(options)

    worklist = make_worklist()
    worklist.incoming = [make_message('GoodCluster'), make_message('AnotherGoodCluster'), make_message('BadCluster')]

    toclusters.after_accept(worklist)

    assert len(worklist.incoming) == 2
    assert len(worklist.rejected) == 1