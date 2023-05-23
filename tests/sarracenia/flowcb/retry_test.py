import pytest
from unittest.mock import patch

import os, types

#from sarracenia.flowcb import FlowCB
from sarracenia.flowcb.retry import Retry

import fakeredis

class Options:
    retry_driver = 'disk'
    redisqueue_serverurl = ''
    no = 1
    retry_ttl = 0
    batch = 8
    logLevel = "DEBUG"
    queueName = "TEST_QUEUE_NAME"
    component = "sarra"
    config = "foobar.conf"
    pid_filename = "NotARealPath"
    housekeeping = float(0)
    def add_option(self, option, type, default = None):
        pass
    pass



WorkList = types.SimpleNamespace()
WorkList.ok = []
WorkList.incoming = []
WorkList.rejected = []
WorkList.failed = []
WorkList.directories_ok = []

message = {
    "pubTime": "20180118151049.356378078",
    "topic": "v02.post.sent_by_tsource2send",
    "headers": {
        "atime": "20180118151049.356378078", 
        "from_cluster": "localhost",
        "mode": "644",
        "mtime": "20180118151048",
        "parts": "1,69,1,0,0",
        "source": "tsource",
        "sum": "d,c35f14e247931c3185d5dc69c5cd543e",
        "to_clusters": "localhost"
    },
    "baseUrl": "https://NotARealURL",
    "relPath": "ThisIsAPath/To/A/File.txt",
    "notice": "20180118151050.45 ftp://anonymous@localhost:2121 /sent_by_tsource2send/SXAK50_KWAL_181510___58785"
}

@pytest.mark.bug("DiskQueue.py doesn't cleanup properly")
def test_cleanup(tmp_path):
    
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions_disk = Options()
        BaseOptions_disk.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
        retry_disk = Retry(BaseOptions_disk)


        BaseOptions_redis = Options()
        BaseOptions_redis.retry_driver = 'redis'
        BaseOptions_redis.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions_redis.queueName = "test_cleanup"
        retry_redis = Retry(BaseOptions_redis)

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

        retry_disk.download_retry.put([message, message, message])
        retry_disk.post_retry.put([message, message, message])

        retry_redis.download_retry.put([message, message, message])
        retry_redis.post_retry.put([message, message, message])

        metrics_disk = retry_disk.metricsReport()

        metrics_redis = retry_redis.metricsReport()

        assert metrics_disk['msgs_in_download_retry'] == metrics_redis['msgs_in_download_retry'] == 3
        assert metrics_disk['msgs_in_post_retry'] == metrics_redis['msgs_in_post_retry'] == 3

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

        after_post_worklist_disk = WorkList
        after_post_worklist_disk.failed = [message, message, message]
        retry_disk.after_post(after_post_worklist_disk)

        after_post_worklist_redis = WorkList
        after_post_worklist_redis.failed = [message, message, message]
        retry_redis.after_post(after_post_worklist_redis)

        assert len(retry_disk.post_retry) == len(retry_redis.post_retry) == 3

def test_after_work__WLFailed(tmp_path):
    # -- DiskQueue
    BaseOptions = Options()
    BaseOptions.retry_driver = 'disk'
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    after_work_worklist = WorkList
    after_work_worklist.failed = [message, message, message]

    retry.after_work(after_work_worklist)

    assert len(retry.download_retry) == 3
    assert len(after_work_worklist.failed) == 0

    # -- RedisQueue
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_after_work__WLFailed"
        retry = Retry(BaseOptions)

        after_work_worklist = WorkList
        after_work_worklist.failed = [message, message, message]

        retry.after_work(after_work_worklist)

        assert len(retry.download_retry) == 3
        assert len(after_work_worklist.failed) == 0

def test_after_work__SmallQty(tmp_path):
    # -- DiskQueue
    BaseOptions = Options()
    BaseOptions.retry_driver = 'disk'
    BaseOptions.batch = 2
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    after_work_worklist = WorkList
    after_work_worklist.ok = [message, message, message]

    retry.after_work(after_work_worklist)

    assert len(retry.download_retry) == 0
    assert len(after_work_worklist.ok) == 3

    # -- RedisQueue
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.batch = 2
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_after_work__SmallQty"
        retry = Retry(BaseOptions)

        after_work_worklist = WorkList
        after_work_worklist.ok = [message, message, message]

        retry.after_work(after_work_worklist)

        assert len(retry.download_retry) == 0
        assert len(after_work_worklist.ok) == 3

def test_after_work(tmp_path):
    # -- DiskQueue
    BaseOptions = Options()
    BaseOptions.retry_driver = 'disk'
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    after_work_worklist = WorkList
    after_work_worklist.ok = [message, message, message]
    retry.post_retry.put([message, message, message])
    retry.on_housekeeping()

    retry.after_work(after_work_worklist)

    assert len(retry.download_retry) == 0
    assert len(after_work_worklist.ok) == 4

    # -- RedisQueue
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_after_work"
        retry = Retry(BaseOptions)

        after_work_worklist = WorkList
        after_work_worklist.ok = [message, message, message]
        retry.post_retry.put([message, message, message])
        retry.on_housekeeping()

        retry.after_work(after_work_worklist)

        assert len(retry.download_retry) == 0
        assert len(after_work_worklist.ok) == 4

def test_after_accept__SmallQty(tmp_path):
    # -- DiskQueue
    BaseOptions = Options()
    BaseOptions.retry_driver = 'disk'
    BaseOptions.batch = 2
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    after_accept_worklist = WorkList
    after_accept_worklist.incoming = [message, message, message]

    retry.after_accept(after_accept_worklist)

    assert len(retry.download_retry) == 0
    assert len(after_accept_worklist.incoming) == 3

    # -- RedisQueue
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.batch = 2
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_after_accept__SmallQty"
        retry = Retry(BaseOptions)

        after_accept_worklist = WorkList
        after_accept_worklist.incoming = [message, message, message]

        retry.after_accept(after_accept_worklist)

        assert len(retry.download_retry) == 0
        assert len(after_accept_worklist.incoming) == 3

def test_after_accept(tmp_path):
    # -- DiskQueue
    BaseOptions = Options()
    BaseOptions.retry_driver = 'disk'
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    retry.download_retry.put([message, message, message])
    retry.on_housekeeping()

    after_accept_worklist = WorkList
    after_accept_worklist.incoming = [message, message, message]

    retry.after_accept(after_accept_worklist)

    assert len(retry.download_retry) == 0
    assert len(after_accept_worklist.incoming) == 4

    # -- RedisQueue
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_after_accept"
        retry = Retry(BaseOptions)

        after_accept_worklist = WorkList
        after_accept_worklist.incoming = [message, message, message]
        retry.download_retry.put([message, message, message])
        retry.on_housekeeping()

        retry.after_accept(after_accept_worklist)

        assert len(retry.download_retry) == 0
        assert len(after_accept_worklist.incoming) == 4

def test_on_housekeeping(tmp_path, caplog):
    # -- DiskQueue
    BaseOptions = Options()
    BaseOptions.retry_driver = 'disk'
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    retry = Retry(BaseOptions)

    retry.download_retry.put([message, message, message])
    retry.post_retry.put([message, message, message])

    assert len(retry.download_retry) == 3
    assert len(retry.post_retry) == 3

    retry.on_housekeeping()

    log_found_hk_elapse = False
    for record in caplog.records:
        if "on_housekeeping elapse" in record.message:
            log_found_hk_elapse = True

    assert log_found_hk_elapse == True

    # -- RedisQueue
    caplog.clear()
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.retry_driver = 'redis'
        BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
        BaseOptions.queueName = "test_on_housekeeping"
        retry = Retry(BaseOptions)

        #server_test_on_housekeeping = fakeredis.FakeServer()
        #retry.download_retry.redis = fakeredis.FakeStrictRedis(server=server_test_on_housekeeping)
        #retry.post_retry.redis = fakeredis.FakeStrictRedis(server=server_test_on_housekeeping)

        retry.download_retry.put([message, message, message])
        retry.post_retry.put([message, message, message])

        assert len(retry.download_retry) == 3
        assert len(retry.post_retry) == 3

        retry.on_housekeeping()

        log_found_hk_elapse = False
        for record in caplog.records:
            if "on_housekeeping elapse" in record.message:
                log_found_hk_elapse = True

        assert log_found_hk_elapse == True