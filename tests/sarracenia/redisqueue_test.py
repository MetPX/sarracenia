import pytest
from unittest.mock import patch

from sarracenia.redisqueue import RedisQueue

import fakeredis

class Empty:
    def add_option(self, option, type):
        pass
    pass

BaseOptions = Empty()

BaseOptions.retry_ttl = 0
BaseOptions.logLevel = "INFO"
BaseOptions.queueName = "TEST_QUEUE_NAME"
BaseOptions.component = "sarra"
BaseOptions.config = "foobar.conf"
BaseOptions.redisqueue_serverurl = "redis://Never.Going.To.Resolve:6379/0"
BaseOptions.housekeeping = float(39)

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

def test__len_():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        download_retry = RedisQueue(BaseOptions, 'work_retry')
        download_retry.redis.lpush(download_retry.key_name, "first")
        assert len(download_retry) == 1
        download_retry.redis.lpush(download_retry.key_name_new, "second")
        assert len(download_retry) == 2
        download_retry.redis.lpush(download_retry.key_name_hk, "third")
        assert len(download_retry) == 2

def test__in_cache():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        download_retry = RedisQueue(BaseOptions, 'work_retry')

        download_retry.retry_cache = {}

        assert download_retry._in_cache(message) == False
        # Checking if it's there actually adds it, so checking it again right after should return True
        assert download_retry._in_cache(message) == True

def test__is_exired__TooSoon():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions.retry_ttl = 100000
        download_retry = RedisQueue(BaseOptions, 'work_retry')

        assert download_retry._is_expired(message) == True

def test__is_exired__TooLate():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions.retry_ttl = 1
        download_retry = RedisQueue(BaseOptions, 'work_retry')

        import sarracenia
        message["pubTime"] = sarracenia.nowstr()

        assert download_retry._is_expired(message) == False

def test__needs_requeuing():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        download_retry = RedisQueue(BaseOptions, 'work_retry')

        download_retry.retry_cache = {}

        assert download_retry._needs_requeuing(message) == True
        assert download_retry._needs_requeuing(message) == False
        download_retry.o.retry_ttl = 1000000
        assert download_retry._needs_requeuing(message) == False

def test__msgFromJSON():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        download_retry = RedisQueue(BaseOptions, 'work_retry')

        import jsonpickle
        assert message == download_retry._msgFromJSON(jsonpickle.encode(message))

def test__msgToJSON():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        download_retry = RedisQueue(BaseOptions, 'work_retry')

        import jsonpickle
        assert jsonpickle.encode(message) == download_retry._msgToJSON(message)

def test__lpop():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        download_retry = RedisQueue(BaseOptions, 'work_retry')
        server_test__lpop = fakeredis.FakeServer()
        download_retry.redis = fakeredis.FakeStrictRedis(server=server_test__lpop)

        download_retry.put([message])
        assert download_retry.redis.llen(download_retry.key_name_new) == 1 
        assert message == download_retry._lpop(download_retry.key_name_new)
    
def test_put__Single():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        download_retry = RedisQueue(BaseOptions, 'work_retry')

        server_test_put_single = fakeredis.FakeServer()
        download_retry.redis = fakeredis.FakeStrictRedis(server=server_test_put_single)

        download_retry.put([message])
        assert download_retry.redis.llen(download_retry.key_name_new) == 1

def test_put__Multi():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        download_retry = RedisQueue(BaseOptions, 'work_retry')

        server_test_put_multi = fakeredis.FakeServer()
        download_retry.redis = fakeredis.FakeStrictRedis(server=server_test_put_multi)

        download_retry.put([message, message, message, message])
        assert download_retry.redis.llen(download_retry.key_name_new) == 4

def test_cleanup():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        
        download_retry = RedisQueue(BaseOptions, 'work_retry')

        server_test_cleanup = fakeredis.FakeServer()
        download_retry.redis = fakeredis.FakeStrictRedis(server=server_test_cleanup)

        download_retry.redis.lpush(download_retry.key_name_lasthk, "data")
        download_retry.redis.lpush(download_retry.key_name_new, "data")
        download_retry.redis.lpush(download_retry.key_name_hk, "data")
        download_retry.redis.lpush(download_retry.key_name, "data")

        #download_retry.redis_lock.acquire()
        #download_retry.redis.lpush("lock:" + download_retry.key_name, "data")

        assert len(download_retry.redis.keys()) == 4

        download_retry.cleanup()

        print(download_retry.redis.keys())

        assert len(download_retry.redis.keys()) == 0

def test_get__NotLocked_Single():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):

        download_retry = RedisQueue(BaseOptions, 'work_retry')

        server_test_get__NotLocked = fakeredis.FakeServer()
        download_retry.redis = fakeredis.FakeStrictRedis(server=server_test_get__NotLocked)

        import jsonpickle

        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))

        gotten = download_retry.get()

        assert len(gotten) == 1
        assert gotten == [message]

def test_get__NotLocked_Multi():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):

        download_retry = RedisQueue(BaseOptions, 'work_retry')

        server_test_get__NotLocked = fakeredis.FakeServer()
        download_retry.redis = fakeredis.FakeStrictRedis(server=server_test_get__NotLocked)

        import jsonpickle

        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))
        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))
        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))
        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))

        #with patch(target="redis_lock.Lock.locked", new=lambda foo: False):

        gotten = download_retry.get(2)

        assert len(gotten) == 2
        assert gotten == [message, message]

def test_get__Locked():
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):

        download_retry = RedisQueue(BaseOptions, 'work_retry')

        server_test_get__NotLocked = fakeredis.FakeServer()
        download_retry.redis = fakeredis.FakeStrictRedis(server=server_test_get__NotLocked)

        import jsonpickle

        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))

        download_retry.redis_lock.acquire()

        gotten = download_retry.get()

        assert len(gotten) == 0
        assert gotten == []

def test_on_housekeeping__TooSoon(caplog):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        download_retry = RedisQueue(BaseOptions, 'work_retry')

        server_test_on_housekeeping__TooSoon = fakeredis.FakeServer()
        download_retry.redis = fakeredis.FakeStrictRedis(server=server_test_on_housekeeping__TooSoon)

        download_retry.redis.set(download_retry.key_name_lasthk, download_retry.now)
        hk_out = download_retry.on_housekeeping()

        assert hk_out == None

        import re

        for record in caplog.records:
            if re.search("^Housekeeping ran less than .*", record.message):
                assert record.message == ("Housekeeping ran less than %ds ago; not running " % (download_retry.o.housekeeping))

@pytest.mark.skip("No need to check if we're locked, per Peter")
def test_on_housekeeping__Locked(caplog):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        download_retry = RedisQueue(BaseOptions, 'work_retry')

        server_test_on_housekeeping__Locked = fakeredis.FakeServer()
        download_retry.redis = fakeredis.FakeStrictRedis(server=server_test_on_housekeeping__Locked)

        #import jsonpickle

        #download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))

        #with patch(target="redis_lock.Lock.locked", new=lambda foo: True):

        download_retry.redis.set(download_retry.key_name_lasthk, download_retry.now - download_retry.o.housekeeping - 100)
        download_retry.redis_lock.acquire()

        hk_out = download_retry.on_housekeeping()

        assert hk_out == None

        import re
        for record in caplog.records:
            if re.search("^Another instance has lock on.*", record.message):
                assert record.message == ("Another instance has lock on %s" % (download_retry.key_name_hk))

def test_on_housekeeping__FinishRetry(caplog):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions.queueName = "test_on_housekeeping__FinishRetry"
        download_retry = RedisQueue(BaseOptions, 'work_retry')

        server_test_on_housekeeping__FinishRetry = fakeredis.FakeServer()
        download_retry.redis = fakeredis.FakeStrictRedis(server=server_test_on_housekeeping__FinishRetry)

        import jsonpickle

        #with patch(target="redis_lock.Lock.locked", new=lambda foo: True):

        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))
        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))
        download_retry.redis.lpush(download_retry.key_name, jsonpickle.encode(message))
        download_retry.redis.set(download_retry.key_name_lasthk, download_retry.now - download_retry.o.housekeeping - 100)

        hk_out = download_retry.on_housekeeping()

        assert hk_out == None

        import re
        for record in caplog.records:
            if re.search("^have not finished retry list.*", record.message):
                assert record.message == ("have not finished retry list; resuming retries from %s" % (download_retry.key_name))

def test_on_housekeeping(caplog):
    with patch(target="redis.from_url", new=fakeredis.FakeStrictRedis.from_url, ):
        BaseOptions.queueName = "test_on_housekeeping"
        download_retry = RedisQueue(BaseOptions, 'work_retry')

        server_test_on_housekeeping = fakeredis.FakeServer()
        download_retry.redis = fakeredis.FakeStrictRedis(server=server_test_on_housekeeping)

        import jsonpickle

        #with patch(target="redis_lock.Lock.locked", new=lambda foo: True):

        download_retry.redis.lpush(download_retry.key_name_new, jsonpickle.encode(message))
        download_retry.redis.lpush(download_retry.key_name_new, jsonpickle.encode(message))
        download_retry.redis.lpush(download_retry.key_name_new, jsonpickle.encode(message))

        download_retry.redis.set(download_retry.key_name_lasthk, download_retry.now - download_retry.o.housekeeping - 100)

        hk_out = download_retry.on_housekeeping()

        assert hk_out == None
        assert download_retry.redis.exists(download_retry.key_name_hk) == False

        import re
        for record in caplog.records:
            if "released redis_lock" in record.message:
                assert "released redis_lock" in record.message
            if "on_housekeeping elapse" in record.message:
                assert "on_housekeeping elapse" in record.message