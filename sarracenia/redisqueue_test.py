import unittest
from unittest.mock import patch

from sarracenia.redisqueue import RedisQueue

from fakeredis import FakeStrictRedis

class Empty:
    def add_option(self, option, type):
        pass
    pass

BaseOptions = Empty()

BaseOptions.retry_ttl = 0
BaseOptions.logLevel = "DEBUG"
BaseOptions.queueName = "TEST_QUEUE_NAME"
BaseOptions.component = "sarra"
BaseOptions.config = "foobar.conf"
BaseOptions.redisqueue_serverurl = "redis://glajlkajsdlaksjdf:6379/0"

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
    "notice": "20180118151050.45 ftp://anonymous@localhost:2121 /sent_by_tsource2send/SXAK50_KWAL_181510___58785"
}
# message = Empty()
# message.pubTime = "20180118151049.356378078"
# message.topic = "v02.post.sent_by_tsource2send"
# message.headers = Empty()
# message.headers.atime = "20180118151049.356378078"
# message.headers.from_cluster = "localhost"
# message.headers.mode = "644"
# message.headers.mtime = "20180118151048"
# message.headers.parts = "1,69,1,0,0"
# message.headers.source = "tsource"
# message.headers.sum = "d,c35f14e247931c3185d5dc69c5cd543e"
# message.headers.to_clusters = "localhost"
# message.notice = "20180118151050.45 ftp://anonymous@localhost:2121 /sent_by_tsource2send/SXAK50_KWAL_181510___58785"

class TestRedisQueue(unittest.TestCase):
    def test_encode_decode(self):

        with patch(
            target="redis.from_url",
            new=FakeStrictRedis.from_url,
        ):
            download_retry = RedisQueue(BaseOptions, 'work_retry')

            json = download_retry._msgToJSON(message)

            self.assertEqual(message, download_retry._msgFromJSON(json))

    def test_is_exired_tooSoon(self):
        with patch(
            target="redis.from_url",
            new=FakeStrictRedis.from_url,
        ):
            o = BaseOptions
            o.retry_ttl = 100000
            download_retry = RedisQueue(o, 'work_retry')

            self.assertTrue(download_retry._is_expired(message))
    
    def test_is_exired_tooLate(self):
        with patch(
            target="redis.from_url",
            new=FakeStrictRedis.from_url,
        ):
            o = BaseOptions
            o.retry_ttl = 1
            download_retry = RedisQueue(o, 'work_retry')

            self.assertFalse(download_retry._is_expired(message))
    
    def test__lpop(self):
        with patch(
            target="redis.from_url",
            new=FakeStrictRedis.from_url,
        ):
            download_retry = RedisQueue(BaseOptions, 'work_retry')

            download_retry.put([message])
            self.assertEqual(1, len(download_retry))
            self.assertEqual(message, download_retry._lpop(download_retry.key_name_new))
        
    def test_get(self):
        with patch(
            target="redis.from_url",
            new=FakeStrictRedis.from_url,
        ):
            o = BaseOptions
            o.retry_ttl = 10000000000000000000000000000
            download_retry = RedisQueue(o, 'work_retry')

            download_retry.put([message])
            print("get", download_retry.get())
            self.assertEqual(1, len(download_retry))
            #self.assertEqual(message, )


if __name__ == '__main__':
    unittest.main()