import pytest
import os

from sarracenia.flowcb.nodupe import NoDupe

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

BaseOptions = Options()


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

def test_deriveKey__nodupe_override(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    nodupe = NoDupe(BaseOptions)

    thismsg = message.copy()

    thismsg['nodupe_override'] = {'key': "SomeKeyValue"}

    assert nodupe.deriveKey(thismsg) == "SomeKeyValue"

def test_deriveKey__fileOp(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    nodupe = NoDupe(BaseOptions)

    thismsg = message.copy()
    thismsg['fileOp'] = {'link': "SomeKeyValue"}
    assert nodupe.deriveKey(thismsg) == "SomeKeyValue"

    thismsg = message.copy()
    thismsg['fileOp'] = {'directory': "SomeKeyValue"}
    assert nodupe.deriveKey(thismsg) == thismsg["relPath"]

def test_deriveKey__integrity(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    nodupe = NoDupe(BaseOptions)

    thismsg = message.copy()

    thismsg['integrity'] = {'method': "cod"}
    assert nodupe.deriveKey(thismsg) == thismsg["relPath"]

    thismsg['integrity'] = {'method': "method", 'value': "value\n"}
    assert nodupe.deriveKey(thismsg) == "method,value"

def test_deriveKey__NotKey(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    nodupe = NoDupe(BaseOptions)

    thismsg = message.copy()

    assert nodupe.deriveKey(thismsg) == thismsg["relPath"] + "," + thismsg["pubTime"]
    thismsg['size'] = 28234
    assert nodupe.deriveKey(thismsg) == thismsg["relPath"] + "," + thismsg["pubTime"] + ",28234" 
    thismsg['mtime'] = "20230118151049.356378078"
    assert nodupe.deriveKey(thismsg) == thismsg["relPath"] + "," + thismsg['mtime'] + ",28234" 

    del thismsg['size']
    assert nodupe.deriveKey(thismsg) == thismsg["relPath"] + "," + thismsg['mtime']

def test_open__withoutfile(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)

    nodupe.open()
    assert nodupe.cache_file == str(tmp_path) + os.sep + 'recent_files_005.cache'
    assert os.path.isfile(nodupe.cache_file) == True
    assert len(nodupe.cache_dict) == 0

def test_open__withfile(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)

    filepath = str(tmp_path) + os.sep + 'recent_files_005.cache'
    fp = open(filepath, 'a')
    fp.flush()

    nodupe.open(cache_file=filepath)
    assert nodupe.cache_file == str(tmp_path) + os.sep + 'recent_files_005.cache'
    assert os.path.isfile(nodupe.cache_file) == True
    assert len(nodupe.cache_dict) == 0

def test_open__withdata(tmp_path):
    import urllib, time
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)
    nodupe.o.nodupe_ttl = 100000

    fp = open(str(tmp_path) + os.sep + 'recent_files_005.cache', 'a')
    fp.write("%s %f %s\n" % ("key1", float(time.time() - 1000), urllib.parse.quote("/some/path/to/file1.txt")))
    fp.write("%s %f %s\n" % ("key2", float(time.time() - 1000), urllib.parse.quote("/some/path/to/file2.txt")))
    fp.write("%s %f %s\n" % ("key3", float(time.time() - 1000), urllib.parse.quote("/some/path/to/file3.txt")))
    fp.write("%s %f %s\n" % ("key4", float(time.time() - 1000), urllib.parse.quote("/some/path/to/file4.txt")))
    fp.write("%s %f %s\n" % ("key5", float(time.time() - 1000), urllib.parse.quote("/some/path/to/file5.txt")))
    fp.write("%s %f %s\n" % ("key5", float(time.time() - 1000), urllib.parse.quote("/some/path/to/file6.txt")))
    fp.write("%s %f %s\n" % ("key6", float(time.time() - 1000000), urllib.parse.quote("/some/path/to/file7.txt")))
    fp.write("thisisgarbage\n")
    fp.flush()

    nodupe.open()
    assert nodupe.cache_file == str(tmp_path) + os.sep + 'recent_files_005.cache'
    assert os.path.isfile(nodupe.cache_file) == True
    assert len(nodupe.cache_dict) == 5