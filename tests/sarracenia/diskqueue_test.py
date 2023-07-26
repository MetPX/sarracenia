import pytest, jsonpickle
import os

#useful for debugging tests
import pprint
def pretty(*things, **named_things):
    for t in things:
        pprint.PrettyPrinter(indent=2, width=200).pprint(t)
    for k,v in named_things.items():
        print(str(k) + ":")
        pprint.PrettyPrinter(indent=2, width=200).pprint(v)

from sarracenia.diskqueue import DiskQueue
from sarracenia import Message as SR3Message

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

def test_msgFromJSON(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    download_retry = DiskQueue(BaseOptions, 'work_retry')

    message = make_message()

    assert message == download_retry.msgFromJSON(jsonpickle.encode(message))

def test_msgToJSON(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    download_retry = DiskQueue(BaseOptions, 'work_retry')

    message = make_message()

    assert jsonpickle.encode(message) + '\n' == download_retry.msgToJSON(message)

def test__is_exired__TooSoon(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.retry_ttl = 100000
    download_retry = DiskQueue(BaseOptions, 'work_retry')

    message = make_message()

    assert download_retry.is_expired(message) == True

def test__is_exired__TooLate(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.retry_ttl = 1
    download_retry = DiskQueue(BaseOptions, 'work_retry')

    import sarracenia
    message = make_message()
    message["pubTime"] = sarracenia.nowstr()

    assert download_retry.is_expired(message) == False

def test___len__(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    download_retry = DiskQueue(BaseOptions, 'work_retry')

    # fp = open(download_retry.queue_file, 'a')
    # fp_new = open(download_retry.new_path, 'a')
    # fp_hk = open(download_retry.housekeeping_path, 'a')
    
    # fp_new.write(download_retry.msgToJSON(message))
    download_retry.msg_count += 1
    assert len(download_retry) == 1

    download_retry.msg_count_new += 1
    assert len(download_retry) == 2

def test_in_cache(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    download_retry = DiskQueue(BaseOptions, 'work_retry')

    message = make_message()
    download_retry.retry_cache = {}

    assert download_retry.in_cache(message) == False

    # Checking if it's there actually adds it, so checking it again right after should return True
    assert download_retry.in_cache(message) == True

def test_needs_requeuing(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    download_retry = DiskQueue(BaseOptions, 'work_retry')

    message = make_message()
    download_retry.retry_cache = {}

    assert download_retry.needs_requeuing(message) == True
    assert download_retry.needs_requeuing(message) == False

    download_retry.o.retry_ttl = 1000000

    assert download_retry.needs_requeuing(message) == False
    
def test_put__Single(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    download_retry = DiskQueue(BaseOptions, 'test_put__Single')

    message = make_message()
    download_retry.put([message])
    assert download_retry.msg_count_new == 1

    line = jsonpickle.encode(message) + '\n'

    assert open(download_retry.new_path, 'r').read() == line

def test_put__Multi(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    download_retry = DiskQueue(BaseOptions, 'test_put__Multi')

    message = make_message()
    download_retry.put([message, message, message])
    assert download_retry.msg_count_new == 3

    line = jsonpickle.encode(message) + '\n'

    contents = open(download_retry.new_path, 'r').read()

    assert contents == line + line + line

def test_cleanup(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    download_retry = DiskQueue(BaseOptions, 'test_cleanup')

    message = make_message()
    fp = open(download_retry.queue_file, 'a')
    fp.write(jsonpickle.encode(message) + '\n')
    download_retry.msg_count = 1

    assert os.path.exists(download_retry.queue_file) == True
    assert download_retry.msg_count == 1

    download_retry.cleanup()

    assert os.path.exists(download_retry.queue_file) == False
    assert download_retry.msg_count == 0

def test_msg_get_from_file__NoLine(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    download_retry = DiskQueue(BaseOptions, 'test_msg_get_from_file__NoLine')

    fp_new, msg = download_retry.msg_get_from_file(None, download_retry.queue_file)

    assert fp_new == None
    assert msg == None

def test_msg_get_from_file(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    download_retry = DiskQueue(BaseOptions, 'test_msg_get_from_file')

    message = make_message()

    fp = open(download_retry.queue_file, 'a')
    fp.write(jsonpickle.encode(message) + '\n')
    fp.flush()
    fp.close()

    fp_new, msg = download_retry.msg_get_from_file(None, download_retry.queue_file)

    import io
    assert isinstance(fp_new, io.TextIOWrapper) == True
    assert msg == message

def test_get__Single(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    download_retry = DiskQueue(BaseOptions, 'test_get__Single')

    message = make_message()

    fp = open(download_retry.queue_file, 'a')
    line = jsonpickle.encode(message) + '\n'
    fp.write(line)
    fp.flush()
    fp.close()

    gotten = download_retry.get()

    assert len(gotten) == 1
    assert gotten == [message]

def test_get__Multi(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    download_retry = DiskQueue(BaseOptions, 'test_get__Multi')

    message = make_message()

    fp = open(download_retry.queue_file, 'a')
    line = jsonpickle.encode(message) + '\n'
    fp.write(line + line)
    fp.flush()
    fp.close()

    gotten = download_retry.get(2)

    assert len(gotten) == 2
    assert gotten == [message, message]

def test_on_housekeeping__FinishRetry(tmp_path, caplog):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    download_retry = DiskQueue(BaseOptions, 'test_on_housekeeping__FinishRetry')

    message = make_message()

    download_retry.queue_fp = open(download_retry.queue_file, 'a')
    line = jsonpickle.encode(message) + '\n'
    download_retry.queue_fp.write(line + line)
    download_retry.queue_fp.flush()

    hk_out = download_retry.on_housekeeping()

    assert hk_out == None

    for record in caplog.records:
        if "have not finished retry list" in record.message:
            assert "have not finished retry list" in record.message

def test_on_housekeeping(tmp_path, caplog):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    download_retry = DiskQueue(BaseOptions, 'test_on_housekeeping')

    message = make_message()

    download_retry.new_fp = open(download_retry.new_path, 'a')
    line = jsonpickle.encode(message) + '\n'
    download_retry.new_fp.write(line + line)
    download_retry.new_fp.flush()

    hk_out = download_retry.on_housekeeping()

    assert hk_out == None
    assert os.path.exists(download_retry.queue_file) == True
    assert os.path.exists(download_retry.new_path) == False

    for record in caplog.records:
        if "has queue" in record.message:
            assert "has queue" in record.message
        if "Number of messages in retry list" in record.message:
            assert "Number of messages in retry list" in record.message
        if "on_housekeeping elapse" in record.message:
            assert "on_housekeeping elapse" in record.message