import pytest
from unittest.mock import patch
import os, types, copy

import fakeredis

#useful for debugging tests
import pprint
def pretty(*things, **named_things):
    for t in things:
        pprint.PrettyPrinter(indent=2, width=200).pprint(t)
    for k,v in named_things.items():
        print(str(k) + ":")
        pprint.PrettyPrinter(indent=2, width=200).pprint(v)

from sarracenia.flowcb.nodupe.redis import NoDupe as NoDupe_Redis
from sarracenia.flowcb.nodupe.disk import NoDupe as NoDupe_Disk
from sarracenia import Message as SR3Message

class Options:
    def __init__(self):
        self.retry_ttl = 0
        self.logLevel = "DEBUG"
        self.logFormat = ""
        self.queueName = "TEST_QUEUE_NAME"
        self.component = "sarra"
        self.nodupe_redis_serverurl = "redis://Never.Going.To.Resolve:6379/0"
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

@pytest.mark.depends(on=['sarracenia/flowcb/nodupe/disk_test.py', 'sarracenia/flowcb/nodupe/redis_test.py'])
def test_on_housekeeping(tmp_path):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        from sarracenia import nowflt
        import time

        BaseOptions = Options()
        BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.config = "test_on_housekeeping.conf"
        BaseOptions.cfg_run_dir = str(tmp_path)
        BaseOptions.no = 5
        BaseOptions.inflight = 0

        message_now = nowflt()
        message_1 = make_message()
        message_1['relPath'] = "Path/To/File/1.txt"

        message_2 = make_message()
        message_2['relPath'] = "Path/To/File/2.txt"

        #Disk
        nodupe_disk = NoDupe_Disk(BaseOptions)
        nodupe_disk.o.nodupe_ttl = 1
        nodupe_disk.now = message_now
        nodupe_disk.on_start()

        worklist_disk = copy.deepcopy(WorkList)
        worklist_disk.incoming = [message_1, message_2]

        nodupe_disk.after_accept(worklist_disk)

        #Redis
        nodupe_redis = NoDupe_Redis(BaseOptions)
        nodupe_redis.o.nodupe_ttl = 1
        nodupe_redis.now = message_now
        nodupe_redis.on_start()
        
        worklist_redis = copy.deepcopy(WorkList)
        worklist_redis.incoming = [message_1, message_2]

        nodupe_redis.after_accept(worklist_redis)

        assert len(worklist_disk.incoming) == len(worklist_redis.incoming) == 2

        time.sleep(2)

        nodupe_disk.on_housekeeping()
        worklist_disk = copy.deepcopy(WorkList)
        worklist_disk.incoming = [message_1, message_2]
        nodupe_disk.after_accept(worklist_disk)

        nodupe_redis.on_housekeeping()
        worklist_redis = copy.deepcopy(WorkList)
        worklist_redis.incoming = [message_1, message_2]
        nodupe_redis.after_accept(worklist_redis)

        assert len(worklist_disk.incoming) == len(worklist_redis.incoming) == 2

@pytest.mark.depends(on=['sarracenia/flowcb/nodupe/disk_test.py', 'sarracenia/flowcb/nodupe/redis_test.py'])
def test_restart(tmp_path):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        from sarracenia import nowflt

        BaseOptions = Options()
        BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.config = "test_restart.conf"
        BaseOptions.cfg_run_dir = str(tmp_path)
        BaseOptions.no = 5
        BaseOptions.inflight = 0

        message_now = nowflt()
        message = make_message()

        #Disk
        nodupe_disk = NoDupe_Disk(BaseOptions)
        nodupe_disk.o.nodupe_ttl = 100000
        nodupe_disk.now = message_now
        nodupe_disk.on_start()

        worklist_disk = copy.deepcopy(WorkList)
        worklist_disk.incoming = [message, message, message]

        nodupe_disk.after_accept(worklist_disk)

        #Redis
        nodupe_redis = NoDupe_Redis(BaseOptions)
        nodupe_redis.o.nodupe_ttl = 100000
        nodupe_redis.now = message_now
        nodupe_redis.on_start()
        
        worklist_redis = copy.deepcopy(WorkList)
        worklist_redis.incoming = [message, message, message]

        nodupe_redis.after_accept(worklist_redis)

        assert len(worklist_disk.incoming) == len(worklist_redis.incoming) == 1
        assert len(worklist_disk.rejected) == len(worklist_redis.rejected) == 2

        #Actual restart
        nodupe_disk.on_stop()
        nodupe_disk.on_start()
        worklist_disk = copy.deepcopy(WorkList)
        worklist_disk.incoming = [message, message, message]
        nodupe_disk.after_accept(worklist_disk)

        nodupe_redis.on_stop()
        nodupe_redis.on_start()
        worklist_redis = copy.deepcopy(WorkList)
        worklist_redis.incoming = [message, message, message]
        nodupe_redis.after_accept(worklist_redis)
        
        assert len(worklist_disk.rejected) == len(worklist_redis.rejected) == 3

@pytest.mark.depends(on=['sarracenia/flowcb/nodupe/disk_test.py', 'sarracenia/flowcb/nodupe/redis_test.py'])
def test_after_accept(tmp_path, capsys):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        from sarracenia import nowflt

        BaseOptions = Options()
        BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.config = "test_after_accept.conf"
        BaseOptions.cfg_run_dir = str(tmp_path)
        BaseOptions.no = 5
        BaseOptions.inflight = 0

        message_now = nowflt()
        message = make_message()

        #Disk
        nodupe_disk = NoDupe_Disk(BaseOptions)
        nodupe_disk.o.nodupe_ttl = 100000
        nodupe_disk.now = message_now
        nodupe_disk.on_start()

        worklist_disk = copy.deepcopy(WorkList)
        worklist_disk.incoming = [message, message, message]

        nodupe_disk.after_accept(worklist_disk)

        #Redis
        nodupe_redis = NoDupe_Redis(BaseOptions)
        nodupe_redis.o.nodupe_ttl = 100000
        nodupe_redis.now = message_now
        nodupe_redis.on_start()
        
        worklist_redis = copy.deepcopy(WorkList)
        worklist_redis.incoming = [message, message, message]

        nodupe_redis.after_accept(worklist_redis)


        assert len(worklist_disk.incoming) == len(worklist_redis.incoming) == 1
        assert len(worklist_disk.rejected) == len(worklist_redis.rejected) == 2

@pytest.mark.depends(on=['sarracenia/flowcb/nodupe/disk_test.py', 'sarracenia/flowcb/nodupe/redis_test.py'])
def test_after_accept__WithFileAges(tmp_path, capsys):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        from sarracenia import nowflt, nowstr, timeflt2str

        BaseOptions = Options()
        BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.config = "test_after_accept__WithFileAges.conf"
        BaseOptions.cfg_run_dir = str(tmp_path)
        BaseOptions.no = 5
        BaseOptions.inflight = 0

        message_now = nowflt() + 10
        message_new_mtime = timeflt2str(message_now)
        message_old_mtime = timeflt2str(message_now - 10000)

        message_old = make_message()
        message_old['mtime'] = message_old_mtime
        message_new = make_message()
        message_new['mtime'] = message_new_mtime

        #Disk
        nodupe_disk = NoDupe_Disk(BaseOptions)
        nodupe_disk.o.nodupe_ttl = 100000
        nodupe_disk.o.nodupe_fileAgeMin = 1000
        nodupe_disk.o.nodupe_fileAgeMax = 1000
        nodupe_disk.now = message_now
        nodupe_disk.on_start()

        worklist_disk = copy.deepcopy(WorkList)
        worklist_disk.incoming = [message_old, message_new]

        nodupe_disk.after_accept(worklist_disk)

        #Redis
        nodupe_redis = NoDupe_Redis(BaseOptions)
        nodupe_redis.o.nodupe_ttl = 100000
        nodupe_redis.o.nodupe_fileAgeMin = 1000
        nodupe_redis.o.nodupe_fileAgeMax = 1000
        nodupe_redis.now = message_now
        nodupe_redis.on_start()
        
        worklist_redis = copy.deepcopy(WorkList)
        worklist_redis.incoming = [message_old, message_new]

        nodupe_redis.after_accept(worklist_redis)

        assert len(worklist_disk.rejected) == len(worklist_redis.rejected) == 2
        assert worklist_disk.rejected[0]['reject'].count(message_old_mtime + " too old (nodupe check), oldest allowed") \
            == worklist_redis.rejected[0]['reject'].count(message_old_mtime + " too old (nodupe check), oldest allowed") \
            == 1
        
        assert worklist_disk.rejected[1]['reject'].count(message_new_mtime + " too new (nodupe check), newest allowed") \
            == worklist_redis.rejected[1]['reject'].count(message_new_mtime + " too new (nodupe check), newest allowed") \
            == 1

@pytest.mark.depends(on=['sarracenia/flowcb/nodupe/disk_test.py', 'sarracenia/flowcb/nodupe/redis_test.py'])
def test_after_accept__InFlight(tmp_path, capsys):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        from sarracenia import nowflt, timeflt2str

        BaseOptions = Options()
        BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.config = "test_after_accept__InFlight.conf"
        BaseOptions.cfg_run_dir = str(tmp_path)
        BaseOptions.no = 5
        BaseOptions.inflight = 1000

        message_now = nowflt() + 10
        message_new_mtime = timeflt2str(message_now)
        message_old_mtime = timeflt2str(message_now - 10000)

        message_old = make_message()
        message_old['mtime'] = message_old_mtime
        message_new = make_message()
        message_new['mtime'] = message_new_mtime

        #Redis
        nodupe_redis = NoDupe_Redis(BaseOptions)
        nodupe_redis.o.nodupe_ttl = 100000
        nodupe_redis.now = message_now
        nodupe_redis.on_start()

        worklist_redis = copy.deepcopy(WorkList)
        worklist_redis.incoming = [message_old, message_new]
        nodupe_redis.after_accept(worklist_redis)
        
        #Disk
        nodupe_disk = NoDupe_Disk(BaseOptions)
        nodupe_disk.o.nodupe_ttl = 100000
        nodupe_disk.now = message_now
        nodupe_disk.on_start()

        worklist_disk = copy.deepcopy(WorkList)
        worklist_disk.incoming = [message_old, message_new]
        nodupe_disk.after_accept(worklist_disk)

        assert len(worklist_disk.rejected) == len(worklist_redis.rejected) == 1
        assert len(worklist_disk.incoming) == len(worklist_redis.incoming) == 1
        assert worklist_disk.incoming[0]['mtime'] == worklist_redis.incoming[0]['mtime'] == message_old_mtime

        assert worklist_redis.rejected[0]['reject'].count(message_new_mtime + " too new (nodupe check), newest allowed") \
            == worklist_disk.rejected[0]['reject'].count(message_new_mtime + " too new (nodupe check), newest allowed") \
            == 1