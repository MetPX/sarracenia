#import pytest
import os

from sarracenia.diskqueue import DiskQueue


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
BaseOptions.pid_filename = "/tmp/sarracenia/diskqueue_test/pid_filename"

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

def test_encode_decode(tmp_path):

    BaseOptions.pid_filename = str(tmp_path) + os.pathsep + "pidfilename.txt"

    download_retry = DiskQueue(BaseOptions, 'work_retry')

    json = download_retry.msgToJSON (message)

    assert message == download_retry.msgFromJSON(json)

def test__is_exired__tooSoon(tmp_path):

    BaseOptions.pid_filename = str(tmp_path) + os.pathsep + "pidfilename.txt"
    BaseOptions.retry_ttl = 100000
    download_retry = DiskQueue(BaseOptions, 'work_retry')

    assert download_retry.is_expired(message) == True

def test__is_exired__tooLate(tmp_path):

    BaseOptions.pid_filename = str(tmp_path) + os.pathsep + "pidfilename.txt"
    BaseOptions.retry_ttl = 1
    download_retry = DiskQueue(BaseOptions, 'work_retry')

    import sarracenia
    message["pubTime"] = sarracenia.nowstr()

    assert download_retry.is_expired(message) == False
