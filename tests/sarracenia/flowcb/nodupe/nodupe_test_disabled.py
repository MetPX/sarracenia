import pytest, pprint
from unittest.mock import patch
import os, types, copy

import fakeredis, urllib.parse

pretty = pprint.PrettyPrinter(indent=2, width=200)

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
        self.config = "foobar.conf"
        self.pid_filename = "/tmp/sarracenia/diskqueue_test/pid_filename"
        self.housekeeping = float(39)
    def add_option(self, option, type, default = None):
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

def redis_setup(nodupe, vals):
    for val in vals:
        k = nodupe._rkey_base + ":" + nodupe._hash(val[0]) + ":" + nodupe._hash(val[1])
        v = str(val[2]) + "|" + str(urllib.parse.quote(val[1]))
        nodupe._redis.set(k, v, ex=nodupe.o.nodupe_ttl) #

    nodupe._redis.set(nodupe._rkey_count, len(vals))
    nodupe._last_count = len(vals)

# def test_on_start(tmp_path):

#     BaseOptions_disk = Options()
#     BaseOptions_disk.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
#     nodupe_disk = NoDupe_Disk(BaseOptions_disk)

#     BaseOptions_redis = Options()
#     BaseOptions_redis.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
#     BaseOptions_redis.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
#     BaseOptions_redis.config = "test__deriveKey.conf"
#     nodupe_redis = NoDupe_Redis(BaseOptions_redis)


#     BaseOptions = Options()
#     BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
#     BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
#     BaseOptions.config = "test_on_start.conf"
#     BaseOptions.cfg_run_dir = str(tmp_path)
#     BaseOptions.no = 5
#     nodupe = NoDupe_Redis(BaseOptions)

#     nodupe.on_start()

#     assert True

# def test_on_stop(tmp_path):
#     BaseOptions = Options()
#     BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
#     BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
#     BaseOptions.config = "test_on_stop.conf"
#     BaseOptions.cfg_run_dir = str(tmp_path)
#     BaseOptions.no = 5
#     nodupe = NoDupe_Redis(BaseOptions)

#     nodupe.on_stop()

#     assert True

# @pytest.mark.depends(on=['test_save'])
# def test_on_housekeeping(tmp_path, caplog):
#     with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
#         import time
#         from sarracenia import nowflt
#         BaseOptions = Options()
#         BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
#         BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
#         BaseOptions.config = "test_on_housekeeping.conf"
#         BaseOptions.cfg_run_dir = str(tmp_path)
#         BaseOptions.no = 5
#         nodupe = NoDupe_Redis(BaseOptions)
#         nodupe.o.nodupe_ttl = 900

#         cache = [
#             ['key1', '/some/path/to/file1.txt', float(time.time() - 300)], 
#             ['key2', '/some/path/to/file2a.txt', float(time.time() - 300)], 
#             ['key2', '/some/path/to/file2b.txt', float(time.time() - 300)], 
#             ['key3', '/some/path/to/file3.txt', float(time.time() - 3000)],
#         ]

#         redis_setup(nodupe, cache)

#         nodupe._last_time = nowflt() - 250
#         nodupe._last_count = 5

#         nodupe.on_housekeeping()

#         log_found = False
#         for record in caplog.records:
#             if "cache size was 5 items 250.00 sec ago, now saved 4 entries" in record.message:
#                 log_found = True

#         assert nodupe._last_count == 4
#         assert log_found == True


@pytest.mark.depends(on=['test__is_new'])
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
        nodupe = NoDupe_Redis(BaseOptions)
        nodupe.o.nodupe_ttl = 100000

        nodupe.now = nowflt()

        message = make_message()
        
        test_after_accept_worklist = copy.deepcopy(WorkList)
        test_after_accept_worklist.incoming = [message, message, message]

        nodupe.after_accept(test_after_accept_worklist)

        assert len(test_after_accept_worklist.incoming) == 1
        assert len(test_after_accept_worklist.rejected) == 2
        k = nodupe._rkey_base + ":" + nodupe._hash(message['relPath'] + "," + message['mtime']) + ":" + nodupe._hash(message['relPath'])
        assert nodupe._redis.get(k) == bytes(str(nodupe.now) + "|" + message['relPath'], 'utf-8')
        assert int(nodupe._redis.get(nodupe._rkey_count)) == 1

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

        nodupe = NoDupe_Redis(BaseOptions)
        nodupe.o.nodupe_ttl = 100000
        nodupe.o.nodupe_fileAgeMin = 1000
        nodupe.o.nodupe_fileAgeMax = 1000

        nodupe.now = nowflt() + 10

        message_old = make_message()
        message_old['mtime'] = timeflt2str(nodupe.now - 10000)
        message_new = make_message()
        message_new['mtime'] = nowstr()
        
        test_after_accept__WithFileAges_worklist = copy.deepcopy(WorkList)
        test_after_accept__WithFileAges_worklist.incoming = [message_old, message_new]

        nodupe.after_accept(test_after_accept__WithFileAges_worklist)

        assert len(test_after_accept__WithFileAges_worklist.rejected) == 2
        assert test_after_accept__WithFileAges_worklist.rejected[0]['reject'].count(message_old['mtime'] + " too old (nodupe check), oldest allowed")
        assert test_after_accept__WithFileAges_worklist.rejected[1]['reject'].count(message_new['mtime'] + " too new (nodupe check), newest allowed")

def test_after_accept__InFlight(tmp_path, capsys):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        from sarracenia import nowflt, nowstr, timeflt2str

        BaseOptions = Options()
        BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.config = "test_after_accept__InFlight.conf"
        BaseOptions.cfg_run_dir = str(tmp_path)
        BaseOptions.no = 5
        BaseOptions.inflight = 1000

        nodupe = NoDupe_Redis(BaseOptions)
        nodupe.o.nodupe_ttl = 100000

        nodupe.now = nowflt() + 10

        message_old = make_message()
        message_old['mtime'] = timeflt2str(nodupe.now - 10000)
        message_new = make_message()
        message_new['mtime'] = nowstr()
        
        test_after_accept__InFlight_worklist = copy.deepcopy(WorkList)
        test_after_accept__InFlight_worklist.incoming = [message_old, message_new]

        nodupe.after_accept(test_after_accept__InFlight_worklist)

        assert len(test_after_accept__InFlight_worklist.rejected) == 1
        assert len(test_after_accept__InFlight_worklist.incoming) == 1
        assert test_after_accept__InFlight_worklist.incoming[0]['mtime'] == message_old['mtime']
        assert test_after_accept__InFlight_worklist.rejected[0]['reject'].count(message_new['mtime'] + " too new (nodupe check), newest allowed")