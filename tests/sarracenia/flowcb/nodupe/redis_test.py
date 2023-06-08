import pytest, pprint
from unittest.mock import patch
import os, types, copy

import fakeredis, urllib.parse

pretty = pprint.PrettyPrinter(indent=2, width=200)

from sarracenia.flowcb.nodupe.redis import NoDupe_Redis
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
        nodupe._redis.set(k, v, ex=nodupe.o.nodupe_ttl)

    nodupe._redis.set(nodupe._rkey_count, len(vals))
    nodupe._last_count = len(vals)

def test__deriveKey__nodupe_override(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
    nodupe = NoDupe_Redis(BaseOptions)

    thismsg = make_message()

    thismsg['nodupe_override'] = {'key': "SomeKeyValue"}

    assert nodupe._deriveKey(thismsg) == "SomeKeyValue"

def test__deriveKey__fileOp(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
    nodupe = NoDupe_Redis(BaseOptions)

    thismsg = make_message()
    thismsg['fileOp'] = {'link': "SomeKeyValue"}
    assert nodupe._deriveKey(thismsg) == "SomeKeyValue"

    thismsg = make_message()
    thismsg['fileOp'] = {'directory': "SomeKeyValue"}
    assert nodupe._deriveKey(thismsg) == thismsg["relPath"]

def test__deriveKey__integrity(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
    nodupe = NoDupe_Redis(BaseOptions)

    thismsg = make_message()

    thismsg['integrity'] = {'method': "cod"}
    assert nodupe._deriveKey(thismsg) == thismsg["relPath"]

    thismsg['integrity'] = {'method': "method", 'value': "value\n"}
    assert nodupe._deriveKey(thismsg) == "method,value"

def test__deriveKey__NotKey(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
    nodupe = NoDupe_Redis(BaseOptions)

    thismsg = make_message()

    assert nodupe._deriveKey(thismsg) == thismsg["relPath"] + "," + thismsg["mtime"]
    thismsg['size'] = 28234
    assert nodupe._deriveKey(thismsg) == thismsg["relPath"] + "," + thismsg["mtime"] + ",28234" 
    del thismsg['mtime']
    assert nodupe._deriveKey(thismsg) == thismsg["relPath"] + "," + thismsg['pubTime'] + ",28234" 

def test_on_start(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe_Redis(BaseOptions)

    nodupe.on_start()

    assert True

def test_on_stop(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe_Redis(BaseOptions)

    nodupe.on_stop()

    assert True

@pytest.mark.depends(on=['test_save'])
def test_on_housekeeping(tmp_path, caplog):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        import time
        import urllib.parse
        from sarracenia import nowflt
        BaseOptions = Options()
        BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.cfg_run_dir = str(tmp_path)
        BaseOptions.no = 5
        nodupe = NoDupe_Redis(BaseOptions)
        nodupe.o.nodupe_ttl = 100000

        cache = [
            ['key1', '/some/path/to/file1.txt', float(time.time() - 1000)], 
            ['key2', '/some/path/to/file2.txt', float(time.time() - 1000)], 
            ['key3', '/some/path/to/file3.txt', float(time.time() - 1000)], 
            ['key4', '/some/path/to/file4.txt', float(time.time() - 1000)], 
            ['key5', '/some/path/to/file5a.txt', float(time.time() - 1000)], 
            ['key5', '/some/path/to/file5b.txt', float(time.time() - 1000)], 
            ['key6', '/some/path/to/file6.txt', float(time.time() - 1000000)],
        ]

        pprint.pprint(nodupe._redis.keys())

        redis_setup(nodupe, cache)

        nodupe.on_housekeeping()

        pprint.pprint(nodupe._redis.keys())

        # log_found = False
        # for record in caplog.records:
        #     if "sec, increased up to" in record.message:
        #         log_found = True

        # assert len(nodupe.cache_dict) == 5
        # assert nodupe.count == 6
        # #File hasn't been flushed at this point, so the number of lines 0, despite the count being 5
        # assert log_found == True

@pytest.mark.depends(on=['test__not_in_cache'])
def test__is_new(tmp_path, capsys):
    import time
    from sarracenia import nowflt
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe_Redis(BaseOptions)
    nodupe.o.nodupe_ttl = 100000

    nodupe.now = nowflt()

    nodupe.cache_dict = {
        'key1': {'/some/path/to/file1.txt': float(time.time() - 1000)}, 
        'key5': {   
            '/some/path/to/file5a.txt': float(time.time() - 1000), 
            '/some/path/to/file5b.txt': float(time.time() - 1000)}, 
        'key6': {'/some/path/to/file6.txt': float(time.time() - 1000000)}}

    message = make_message()

    assert nodupe._is_new(message) == True
    assert nodupe.cache_dict[message['relPath']+","+message['mtime']][message['relPath']] == nodupe.now

    message['nodupe_override'] = {"path": message['relPath'].split('/')[-1], "key": message['relPath'].split('/')[-1]}
    assert nodupe._is_new(message) == True
    assert nodupe.cache_dict[message['nodupe_override']['key']][message['nodupe_override']['path']] == nodupe.now
    assert nodupe.count == 6

@pytest.mark.depends(on=['test_check_message'])
def test_after_accept(tmp_path, capsys):
    from sarracenia import nowflt

    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    BaseOptions.inflight = 0
    nodupe = NoDupe_Redis(BaseOptions)
    nodupe.o.nodupe_ttl = 100000

    nodupe.now = nowflt()

    message = make_message()
    
    after_accept_worklist = copy.deepcopy(WorkList)
    after_accept_worklist.incoming = [message, message, message]

    nodupe.after_accept(after_accept_worklist)

    assert len(after_accept_worklist.incoming) == 1
    assert len(after_accept_worklist.rejected) == 2
    assert nodupe.cache_dict[message['relPath'] + "," + message['mtime']][message['relPath']] == nodupe.now
    #pretty.pprint(message)
    #pretty.pprint(nodupe.cache_dict)

@pytest.mark.depends(on=['test_check_message'])
def test_after_accept__WithFileAges(tmp_path, capsys):
    from sarracenia import nowflt, nowstr, timeflt2str

    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
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
    
    after_accept_worklist__WithFileAges = copy.deepcopy(WorkList)
    after_accept_worklist__WithFileAges.incoming = [message_old, message_new]

    nodupe.after_accept(after_accept_worklist__WithFileAges)

    #pretty.pprint(message)
    #pretty.pprint(after_accept_worklist.rejected[0]['reject'].count(message_old['mtime'] + " too old (nodupe check), oldest allowed"))
    #pretty.pprint(vars(nodupe))
    #pretty.pprint(after_accept_worklist__WithFileAges)

    assert len(after_accept_worklist__WithFileAges.rejected) == 2
    assert after_accept_worklist__WithFileAges.rejected[0]['reject'].count(message_old['mtime'] + " too old (nodupe check), oldest allowed")
    assert after_accept_worklist__WithFileAges.rejected[1]['reject'].count(message_new['mtime'] + " too new (nodupe check), newest allowed")

@pytest.mark.depends(on=['test_check_message'])
def test_after_accept__InFlight(tmp_path, capsys):
    from sarracenia import nowflt, nowstr, timeflt2str

    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
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
    
    test_after_accept__InFlight = copy.deepcopy(WorkList)
    test_after_accept__InFlight.incoming = [message_old, message_new]

    nodupe.after_accept(test_after_accept__InFlight)

    #pretty.pprint(message)
    #pretty.pprint(after_accept_worklist.rejected[0]['reject'].count(message_old['mtime'] + " too old (nodupe check), oldest allowed"))
    #pretty.pprint(vars(nodupe))
    #pretty.pprint(test_after_accept__InFlight)

    assert len(test_after_accept__InFlight.rejected) == 1
    assert len(test_after_accept__InFlight.incoming) == 1
    assert test_after_accept__InFlight.incoming[0]['mtime'] == message_old['mtime']
    assert test_after_accept__InFlight.rejected[0]['reject'].count(message_new['mtime'] + " too new (nodupe check), newest allowed")