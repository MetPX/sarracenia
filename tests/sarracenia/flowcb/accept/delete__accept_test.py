import pytest
from tests.conftest import *
import types
import os


from sarracenia.flowcb.accept.delete import Delete
from sarracenia import Message as SR3Message
import sarracenia.config

class dummy_consumer:
    def __init__(self):
        self.sleep_now = 10
        self.sleep_min = 0

    def msg_to_retry(self):
        pass

def make_message(dir, file):
    m = SR3Message()
    m['new_dir'] = dir
    m['new_file'] = file
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
    deletecb = Delete(options)
    

@pytest.mark.depends(on=['test___init__'])
def test_after_accept(tmp_path, caplog):
    file = str(tmp_path) + os.sep + 'cfr/file.txt'
    file_c = str(tmp_path) + os.sep + 'cfile/file.txt'
    #os.mkdir(str(tmp_path) + os.sep + 'cfr')
    #os.mkdir(str(tmp_path) + os.sep + 'cfile')

    options = sarracenia.config.default_config()
    options.logLevel = "DEBUG"
    options.consumer = dummy_consumer()
    deletecb = Delete(options)

    caplog.clear()
    worklist = make_worklist()
    worklist.incoming = [make_message(str(tmp_path), 'cfr/file.txt')]
    # Should be able to catch that it's raising an error, but no matter what error I tell it's suppose to raise, it doesn't match
    #with pytest.raises(FileNotFoundError):
    deletecb.after_accept(worklist)
    assert len(caplog.messages) == 2
    assert len(worklist.incoming) == 0
    assert len(worklist.rejected) == 1
    assert f'could not unlink {file}: [Errno 2] No such file or directory: \'{file}\'' in caplog.messages

    caplog.clear()
    worklist = make_worklist()
    worklist.incoming = [make_message(str(tmp_path), 'cfr/file.txt')]
    os.mkdir(str(tmp_path) + os.sep + 'cfr')
    os.mkdir(str(tmp_path) + os.sep + 'cfile')
    open(file, 'a').close()
    open(file_c, 'a').close()
    deletecb.after_accept(worklist)
    assert len(worklist.incoming) == 1
    assert f'deleted: {file} and the cfile version.' in caplog.messages
