import pytest
from unittest.mock import patch

import os, types

#useful for debugging tests
import pprint
def pretty(*things, **named_things):
    for t in things:
        pprint.PrettyPrinter(indent=2, width=200).pprint(t)
    for k,v in named_things.items():
        print(str(k) + ":")
        pprint.PrettyPrinter(indent=2, width=200).pprint(v)

#from sarracenia.flowcb import FlowCB
from sarracenia.flowcb.retry import Retry
from sarracenia import Message as SR3Message

import fakeredis

class Options:
    def __init__(self):
        self.no = 1
        self.retry_ttl = 0
        self.logLevel = "DEBUG"
        self.logFormat = ""
        self.queueName = "TEST_QUEUE_NAME"
        self.component = "sarra"
        self.retry_driver = 'disk'
        self.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        self.config = "foobar.conf"
        self.pid_filename = "/tmp/sarracenia/retyqueue_test/pid_filename"
        self.housekeeping = float(0)
        self.batch = 0
    def add_option(self, option, type, default = None):
        if not hasattr(self, option):
            setattr(self, option, default)

WorkList = types.SimpleNamespace()
WorkList.ok = []
WorkList.incoming = []
WorkList.rejected = []
WorkList.failed = []
WorkList.directories_ok = []

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


@pytest.mark.bug("DiskQueue.py doesn't cleanup properly")
@pytest.mark.depends(on=['sarracenia/diskqueue_test.py', 'sarracenia/redisqueue_test.py'])
def test_cleanup(tmp_path):
    
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions_disk = Options()
        BaseOptions_disk.retry_driver = 'disk'
        BaseOptions_disk.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        retry_disk = Retry(BaseOptions_disk)


        BaseOptions_redis = Options()
        BaseOptions_redis.retry_driver = 'redis'
        BaseOptions_redis.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions_redis.queueName = "test_cleanup"
        retry_redis = Retry(BaseOptions_redis)

        message = make_message()

        retry_disk.download_retry.put([message, message, message])
        retry_disk.post_retry.put([message, message, message])

        retry_redis.download_retry.put([message, message, message])
        retry_redis.post_retry.put([message, message, message])

        assert len(retry_disk.download_retry) == len(retry_redis.download_retry) == 3
        assert len(retry_disk.post_retry) == len(retry_redis.post_retry) == 3
    
        retry_disk.cleanup()
        retry_redis.cleanup()

        #These should both return 0, but with the current DiskQueue, cleanup doesn't work properly.
        assert len(retry_disk.download_retry) == len(retry_redis.download_retry) == 0
        assert len(retry_disk.post_retry) == len(retry_redis.post_retry) == 0


@pytest.mark.depends(on=['sarracenia/diskqueue_test.py', 'sarracenia/redisqueue_test.py'])
def test_metricsReport(tmp_path):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions_disk = Options()
        BaseOptions_disk.retry_driver = 'disk'
        BaseOptions_disk.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        retry_disk = Retry(BaseOptions_disk)

        BaseOptions_redis = Options()
        BaseOptions_redis.retry_driver = 'redis'
        BaseOptions_redis.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions_redis.queueName = "test_metricsReport"
        retry_redis = Retry(BaseOptions_redis)

        message = make_message()

        retry_disk.download_retry.put([message, message, message])
        retry_disk.post_retry.put([message, message, message])
        metrics_disk = retry_disk.metricsReport()

        retry_redis.download_retry.put([message, message, message])
        retry_redis.post_retry.put([message, message, message])
        metrics_redis = retry_redis.metricsReport()

        assert metrics_disk['msgs_in_download_retry'] == metrics_redis['msgs_in_download_retry'] == 3
        assert metrics_disk['msgs_in_post_retry'] == metrics_redis['msgs_in_post_retry'] == 3

@pytest.mark.depends(on=['sarracenia/diskqueue_test.py', 'sarracenia/redisqueue_test.py'])
def test_after_post(tmp_path):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions_disk = Options()
        BaseOptions_disk.retry_driver = 'disk'
        BaseOptions_disk.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        retry_disk = Retry(BaseOptions_disk)

        BaseOptions_redis = Options()
        BaseOptions_redis.retry_driver = 'redis'
        BaseOptions_redis.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions_redis.queueName = "test_after_post"
        retry_redis = Retry(BaseOptions_redis)

        message = make_message()

        after_post_worklist_disk.failed = [message, message, message]
        retry_disk.after_post(after_post_worklist_disk)

        after_post_worklist_redis = WorkList
        after_post_worklist_redis.failed = [message, message, message]
        retry_redis.after_post(after_post_worklist_redis)

        assert len(retry_disk.post_retry) == len(retry_redis.post_retry) == 3

@pytest.mark.depends(on=['sarracenia/diskqueue_test.py', 'sarracenia/redisqueue_test.py'])
def test_after_work__WLFailed(tmp_path):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions_disk = Options()
        BaseOptions_disk.retry_driver = 'disk'
        BaseOptions_disk.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        retry_disk = Retry(BaseOptions_disk)

        BaseOptions_redis = Options()
        BaseOptions_redis.retry_driver = 'redis'
        BaseOptions_redis.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions_redis.queueName = "test_after_work__WLFailed"
        retry_redis = Retry(BaseOptions_redis)

        message = make_message()

        after_work_worklist_disk.failed = [message, message, message]
        retry_disk.after_work(after_work_worklist_disk)

        after_work_worklist_redis = WorkList
        after_work_worklist_redis.failed = [message, message, message]
        retry_redis.after_work(after_work_worklist_redis)

        assert len(retry_disk.download_retry) == len(retry_redis.download_retry) == 3
        assert len(after_work_worklist_disk.failed) == len(after_work_worklist_redis.failed) == 0

@pytest.mark.depends(on=['sarracenia/diskqueue_test.py', 'sarracenia/redisqueue_test.py'])
def test_after_work__SmallQty(tmp_path):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions_disk = Options()
        BaseOptions_disk.retry_driver = 'disk'
        BaseOptions_disk.batch = 2
        BaseOptions_disk.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        retry_disk = Retry(BaseOptions_disk)

        BaseOptions_redis = Options()
        BaseOptions_redis.batch = 2
        BaseOptions_redis.retry_driver = 'redis'
        BaseOptions_redis.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions_redis.queueName = "test_after_work__SmallQty"
        retry_redis = Retry(BaseOptions_redis)

        message = make_message()

        after_work_worklist_disk.ok = [message, message, message]
        retry_disk.after_work(after_work_worklist_disk)

        after_work_worklist_redis = WorkList
        after_work_worklist_redis.ok = [message, message, message]
        retry_redis.after_work(after_work_worklist_redis)

        assert len(retry_disk.download_retry) == len(retry_redis.download_retry) == 0
        assert len(after_work_worklist_disk.ok) == len(after_work_worklist_redis.ok) == 3


@pytest.mark.depends(on=['sarracenia/diskqueue_test.py', 'sarracenia/redisqueue_test.py'])
def test_after_work(tmp_path):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions_disk = Options()
        BaseOptions_disk.retry_driver = 'disk'
        BaseOptions_disk.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        retry_disk = Retry(BaseOptions_disk)

        BaseOptions_redis = Options()
        BaseOptions_redis.retry_driver = 'redis'
        BaseOptions_redis.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions_redis.queueName = "test_after_work"
        retry_redis = Retry(BaseOptions_redis)

        message = make_message()

        after_work_worklist_disk.ok = [message, message, message]
        retry_disk.post_retry.put([message, message, message])
        retry_disk.on_housekeeping()
        retry_disk.after_work(after_work_worklist_disk)

        after_work_worklist_redis = WorkList
        after_work_worklist_redis.ok = [message, message, message]
        retry_redis.post_retry.put([message, message, message])
        retry_redis.on_housekeeping()
        retry_redis.after_work(after_work_worklist_redis)

        assert len(retry_disk.download_retry) == len(retry_redis.download_retry) == 0
        assert len(after_work_worklist_disk.ok) == len(after_work_worklist_redis.ok) == 4

@pytest.mark.depends(on=['sarracenia/diskqueue_test.py', 'sarracenia/redisqueue_test.py'])
def test_after_accept__SmallQty(tmp_path):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions_disk = Options()
        BaseOptions_disk.retry_driver = 'disk'
        BaseOptions_disk.batch = 2
        BaseOptions_disk.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        retry_disk = Retry(BaseOptions_disk)

        BaseOptions_redis = Options()
        BaseOptions_redis.batch = 2
        BaseOptions_redis.retry_driver = 'redis'
        BaseOptions_redis.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions_redis.queueName = "test_after_accept__SmallQty"
        retry_redis = Retry(BaseOptions_redis)

        message = make_message()

        after_work_worklist_disk.incoming = [message, message, message]
        retry_disk.after_accept(after_work_worklist_disk)

        after_work_worklist_redis = WorkList
        after_work_worklist_redis.incoming = [message, message, message]
        retry_redis.after_accept(after_work_worklist_redis)

        assert len(retry_disk.download_retry) == len(retry_redis.download_retry) == 0
        assert len(after_work_worklist_disk.incoming) == len(after_work_worklist_redis.incoming) == 3

@pytest.mark.depends(on=['sarracenia/diskqueue_test.py', 'sarracenia/redisqueue_test.py'])
def test_after_accept(tmp_path):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions_disk = Options()
        BaseOptions_disk.retry_driver = 'disk'
        BaseOptions_disk.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        retry_disk = Retry(BaseOptions_disk)

        BaseOptions_redis = Options()
        BaseOptions_redis.retry_driver = 'redis'
        BaseOptions_redis.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions_redis.queueName = "test_after_accept"
        retry_redis = Retry(BaseOptions_redis)

        message = make_message()

        after_work_worklist_disk.incoming = [message, message, message]
        retry_disk.download_retry.put([message, message, message])
        retry_disk.on_housekeeping()
        retry_disk.after_accept(after_work_worklist_disk)

        after_work_worklist_redis = WorkList
        after_work_worklist_redis.incoming = [message, message, message]
        retry_redis.download_retry.put([message, message, message])
        retry_redis.on_housekeeping()
        retry_redis.after_accept(after_work_worklist_redis)

        assert len(retry_disk.download_retry) == len(retry_redis.download_retry) == 0
        assert len(after_work_worklist_disk.incoming) == len(after_work_worklist_redis.incoming) == 4

@pytest.mark.depends(on=['sarracenia/diskqueue_test.py', 'sarracenia/redisqueue_test.py'])
def test_on_housekeeping(tmp_path, caplog):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions_disk = Options()
        BaseOptions_disk.retry_driver = 'disk'
        BaseOptions_disk.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        retry_disk = Retry(BaseOptions_disk)

        BaseOptions_redis = Options()
        BaseOptions_redis.retry_driver = 'redis'
        BaseOptions_redis.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions_redis.queueName = "test_on_housekeeping"
        retry_redis = Retry(BaseOptions_redis)

        message = make_message()

        retry_disk.download_retry.put([message, message, message])
        retry_disk.post_retry.put([message, message, message])

        retry_redis.download_retry.put([message, message, message])
        retry_redis.post_retry.put([message, message, message])

        assert len(retry_disk.download_retry) == len(retry_redis.download_retry) == 3
        assert len(retry_disk.post_retry) == len(retry_redis.post_retry) == 3

        log_found_hk_elapse_disk = log_found_hk_elapse_redis = False

        retry_disk.on_housekeeping()
        for record in caplog.records:
            if "on_housekeeping elapse" in record.message:
                log_found_hk_elapse_disk = True

        caplog.clear()
    
        retry_redis.on_housekeeping()
        for record in caplog.records:
            if "on_housekeeping elapse" in record.message:
                log_found_hk_elapse_redis = True

        assert log_found_hk_elapse_disk == log_found_hk_elapse_redis == True