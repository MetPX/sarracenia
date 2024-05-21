import pytest
from tests.conftest import *
import os, types, copy

from sarracenia.flowcb.nodupe.name import Name
from sarracenia import Message as SR3Message

class Options:
    def __init__(self):
        self.retry_ttl = 0
        self.logLevel = "DEBUG"
        self.logFormat = ""
        self.queueName = "TEST_QUEUE_NAME"
        self.component = "sarra"
        self.config = "foobar.conf"
        self.pid_filename = "/tmp/sarracenia/diskqueue_test/pid_filename"
        self.housekeeping = float(39)
    def add_option(self, option, type, default = None):
        if not hasattr(self, option):
            setattr(self, option, default)
    pass

def make_message():
    m = SR3Message()
    m["pubTime"] = "20180118151049.356378078"
    m["topic"] = "v02.post.sent_by_tsource2send"
    m["mtime"] = "20180118151048"
    m["headers"] = {
            "atime": "20180118151049.356378078", 
            "from_cluster": "localhost",
            "mode": "644",
            "parts": "1,69,1,0,0",
            "source": "tsource",
            "sum": "d,c35f14e247931c3185d5dc69c5cd543e",
            "to_clusters": "localhost"
        }
    m["baseUrl"] =  "https://NotARealURL"
    m["relPath"] = "ThisIsAPath/To/A/File.txt"
    m["notice"] = "20180118151050.45 ftp://anonymous@localhost:2121 /sent_by_tsource2send/SXAK50_KWAL_181510___58785"
    m["_deleteOnPost"] = set()
    return m

WorkList = types.SimpleNamespace()
WorkList.ok = []
WorkList.incoming = []
WorkList.rejected = []
WorkList.failed = []
WorkList.directories_ok = []

def test_after_accept(tmp_path, capsys):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    BaseOptions.inflight = 0
    nodupe = Name(BaseOptions)

    message_with_nodupe = make_message()
    message_with_nodupe['nodupe_override'] = {}

    message_without_nodupe = make_message()
    
    wl_test_after_accept = copy.deepcopy(WorkList)
    wl_test_after_accept.incoming = [message_with_nodupe, message_without_nodupe]

    nodupe.after_accept(wl_test_after_accept)

    assert len(wl_test_after_accept.incoming) == 2
    assert wl_test_after_accept.incoming[0]['nodupe_override'] == {'key': 'File.txt', 'path': 'File.txt'}
    assert 'nodupe_override' in wl_test_after_accept.incoming[1]['_deleteOnPost']