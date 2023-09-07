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

from sarracenia.flowcb.accept.pathreplace import Pathreplace
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message():
    m = SR3Message()
    m["new_file"] = 's0000684_fileReplace_f.xml'
    m["new_dir"] = '/Some/dirReplace/Path'
    m['fileOp'] = {'rename':'fileOp_rename', 'hlink':'fileOp_hlink', 'link':'fileOp_link'}

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
    pathreplace = Pathreplace(options)

@pytest.mark.depends(on=['test___init__'])
def test_on_start(caplog):

    options = sarracenia.config.default_config()
    options.logLevel = "DEBUG"
    pathreplace = Pathreplace(options)
    caplog.clear()
    pathreplace.on_start()
    assert len(caplog.messages) == 1 or len(caplog.messages) == 3
    assert "pathReplace setting mandatory" in caplog.messages

    caplog.clear()
    options.pathReplace = ['before1,after1', 'before2,after2']
    options.pathReplaceFields = set(['dir','file'])
    pathreplace = Pathreplace(options)
    pathreplace.on_start()
    assert len(caplog.messages) == 1 or len(caplog.messages) == 3
    assert "pathReplace is ['before1,after1', 'before2,after2'] " in caplog.messages



@pytest.mark.depends(on=['test___init__'])
def test_after_accept():
    options = sarracenia.config.default_config()
    options.pathReplace = ['fileReplace,file_foo_Replace', 'dirReplace,dir_foo_Replace', 'fileOp_rename,fileOp_foo_rename', 'fileOp_hlink,fileOp_foo_hlink', 'fileOp_link,fileOp_foo_link']
    #options.pathReplaceFields = set(['dir','file'])
    options.logLevel = "DEBUG"
    pathreplace = Pathreplace(options)
    
    worklist = make_worklist()
    worklist.incoming = [make_message(), make_message()]
    options.post_broker = "foobar"
    pathreplace.after_accept(worklist)
    assert len(worklist.incoming) == 2
    assert worklist.incoming[0]['new_relPath'] == '/Some/dir_foo_Replace/Path' + os.sep + 's0000684_file_foo_Replace_f.xml'
    assert worklist.incoming[1]['fileOp']['rename'] == 'fileOp_foo_rename'
    assert worklist.incoming[1]['fileOp']['hlink'] == 'fileOp_foo_hlink'
    assert worklist.incoming[1]['fileOp']['link'] == 'fileOp_foo_link'

    worklist = make_worklist()
    worklist.incoming = [make_message(), make_message()]
    del(worklist.incoming[0]['fileOp'])
    options.pathReplaceFields = set()
    options.post_baseDir = '/Some'
    pathreplace = Pathreplace(options)
    pathreplace.after_accept(worklist)
    assert len(worklist.incoming) == 2
    assert worklist.incoming[0]['new_relPath'] == '/dirReplace/Path' + os.sep + 's0000684_fileReplace_f.xml'
    assert worklist.incoming[1]['fileOp']['rename'] == 'fileOp_rename'

    del(pathreplace.o.pathReplace)
    worklist = make_worklist()
    worklist.incoming = [make_message(), make_message()]
    options.pathReplaceFields = set()
    #options.pathReplace = ['fileReplace,file_foo_Replace']
    pathreplace = Pathreplace(options)
    pathreplace.after_accept(worklist)
    assert len(worklist.incoming) == 2
    assert worklist.incoming[1]['fileOp']['rename'] == 'fileOp_rename'
    assert 'new_relPath' not in worklist.incoming[0]
