import pytest
from tests.conftest import *
from unittest.mock import patch

from sarracenia.redisqueue import RedisQueue
from sarracenia import Message as SR3Message

import fakeredis

import jsonpickle

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
        self.pid_filename = "/tmp/sarracenia/diskqueue_test/pid_filename"
        self.housekeeping = float(39)
        self.batch = 0
    def add_option(self, option, type, default = None):
        if not hasattr(self, option):
            setattr(self, option, default)

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

def test___len__():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        download_retry = RedisQueue(BaseOptions, 'test___len__')
        download_retry.redis.lpush(download_retry.key_name, "first")
        assert len(download_retry) == 1
        download_retry.redis.lpush(download_retry.key_name_new, "second")
        assert len(download_retry) == 2
        download_retry.redis.lpush(download_retry.key_name_hk, "third")
        assert len(download_retry) == 2

def test__in_cache():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        download_retry = RedisQueue(BaseOptions, 'test__in_cache')

        message = make_message()
        download_retry.retry_cache = {}

        assert download_retry._in_cache(message) == False
        # Checking if it's there actually adds it, so checking it again right after should return True
        assert download_retry._in_cache(message) == True

def test__is_exired__TooSoon():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.retry_ttl = 100000
        download_retry = RedisQueue(BaseOptions, 'test__is_exired__TooSoon')

        message = make_message()

        assert download_retry._is_expired(message) == True

def test__is_exired__TooLate():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.retry_ttl = 1
        download_retry = RedisQueue(BaseOptions, 'test__is_exired__TooLate')

        import sarracenia
        message = make_message()
        message["pubTime"] = sarracenia.nowstr()

        assert download_retry._is_expired(message) == False

def test__needs_requeuing():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        download_retry = RedisQueue(BaseOptions, 'test__needs_requeuing')

        message = make_message()
        download_retry.retry_cache = {}

        assert download_retry._needs_requeuing(message) == True
        assert download_retry._needs_requeuing(message) == False
        download_retry.o.retry_ttl = 1000000
        assert download_retry._needs_requeuing(message) == False

def test__msgFromJSON():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        download_retry = RedisQueue(BaseOptions, 'test__msgFromJSON')

        message = make_message()

        assert message == download_retry._msgFromJSON(jsonpickle.encode(message))

def test__msgToJSON():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        download_retry = RedisQueue(BaseOptions, 'test__msgToJSON')

        message = make_message()

        assert jsonpickle.encode(message) == download_retry._msgToJSON(message)

def test__lpop():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        download_retry = RedisQueue(BaseOptions, 'test__lpop')

        message = make_message()

        download_retry.put([message])
        assert download_retry.redis.llen(download_retry.key_name_new) == 1 
        assert message == download_retry._lpop(download_retry.key_name_new)
    
def test_put__Single():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        download_retry = RedisQueue(BaseOptions, 'test_put__Single')

        message = make_message()

        download_retry.put([message])
        assert download_retry.redis.llen(download_retry.key_name_new) == 1

def test_put__Multi():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        download_retry = RedisQueue(BaseOptions, 'test_put__Multi')

        message = make_message()

        download_retry.put([message, message, message, message])
        assert download_retry.redis.llen(download_retry.key_name_new) == 4

def test_cleanup():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        download_retry = RedisQueue(BaseOptions, 'test_cleanup')

        download_retry.redis.set(download_retry.key_name_lasthk, "data")
        download_retry.redis.lpush(download_retry.key_name_new, "data")
        download_retry.redis.lpush(download_retry.key_name_hk, "data")
        download_retry.redis.lpush(download_retry.key_name, "data")

        assert len(download_retry.redis.keys(download_retry.key_name + "*")) == 3
        assert len(download_retry.redis.keys(download_retry.key_name_lasthk)) == 1

        download_retry.cleanup()

        assert len(download_retry.redis.keys(download_retry.key_name + "*")) == 0
        assert len(download_retry.redis.keys(download_retry.key_name_lasthk)) == 0

def test_get__NotLocked_Single():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        download_retry = RedisQueue(BaseOptions, 'test_get__NotLocked_Single')

        message = make_message()

        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))

        gotten = download_retry.get()

        assert len(gotten) == 1
        assert gotten == [message]

def test_get__NotLocked_Multi():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        download_retry = RedisQueue(BaseOptions, 'test_get__NotLocked_Multi')

        message = make_message()

        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))
        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))
        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))
        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))

        gotten = download_retry.get(2)

        assert len(gotten) == 2
        assert gotten == [message, message]

def test_get__Locked():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        download_retry = RedisQueue(BaseOptions, 'test_get__Locked')

        message = make_message()

        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))

        download_retry.redis_lock.acquire()

        gotten = download_retry.get()

        assert len(gotten) == 0
        assert gotten == []

def test_on_housekeeping__TooSoon(caplog):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        download_retry = RedisQueue(BaseOptions, 'test_on_housekeeping__TooSoon')

        download_retry.redis.set(download_retry.key_name_lasthk, download_retry.now)
        hk_out = download_retry.on_housekeeping()

        assert hk_out == None

        for record in caplog.records:
            if "Housekeeping ran less than " in record.message:
                assert "Housekeeping ran less than " in record.message

def test_on_housekeeping__FinishRetry(caplog):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.queueName = "test_on_housekeeping__FinishRetry"
        download_retry = RedisQueue(BaseOptions, 'test_on_housekeeping__FinishRetry')

        message = make_message()

        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))
        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))
        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))
        download_retry.redis.set(download_retry.key_name_lasthk, download_retry.now - download_retry.o.housekeeping - 100)

        hk_out = download_retry.on_housekeeping()

        assert hk_out == None

        log_found_notFinished = False

        for record in caplog.records:
            if "have not finished retry list" in record.message:
                log_found_notFinished = True
    
        assert log_found_notFinished == True

def test_on_housekeeping(caplog):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions = Options()
        BaseOptions.queueName = "test_on_housekeeping"
        download_retry = RedisQueue(BaseOptions, 'test_on_housekeeping')

        message = make_message()

        download_retry.redis.lpush(download_retry.key_name_new, jsonpickle.encode(message))
        download_retry.redis.lpush(download_retry.key_name_new, jsonpickle.encode(message))
        download_retry.redis.lpush(download_retry.key_name_new, jsonpickle.encode(message))

        download_retry.redis.set(download_retry.key_name_lasthk, download_retry.now - download_retry.o.housekeeping - 100)

        hk_out = download_retry.on_housekeeping()

        assert hk_out == None
        assert download_retry.redis.exists(download_retry.key_name_hk) == False

        log_found_LockReleased = log_found_Elapsed = False

        for record in caplog.records:
            if "released redis_lock" in record.message:
                log_found_LockReleased = True
            if "on_housekeeping elapse" in record.message:
                log_found_Elapsed = True

        assert log_found_LockReleased == True
        assert log_found_Elapsed == True