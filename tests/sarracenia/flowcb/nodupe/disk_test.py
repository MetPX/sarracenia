import pytest
import os, types, copy

#useful for debugging tests
import pprint
def pretty(*things, **named_things):
    for t in things:
        pprint.PrettyPrinter(indent=2, width=200).pprint(t)
    for k,v in named_things.items():
        print(str(k) + ":")
        pprint.PrettyPrinter(indent=2, width=200).pprint(v)

from sarracenia.flowcb.nodupe.disk import NoDupe
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
        if not hasattr(self, option):
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

def test_deriveKey(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    nodupe = NoDupe(BaseOptions)

    thismsg = make_message()
    thismsg['nodupe_override'] = {'key': "SomeKeyValue"}
    assert nodupe.deriveKey(thismsg) == "SomeKeyValue"

    thismsg = make_message()
    thismsg['fileOp'] = {'link': "SomeKeyValue"}
    assert nodupe.deriveKey(thismsg) == "SomeKeyValue"

    thismsg = make_message()
    thismsg['fileOp'] = {'directory': "SomeKeyValue"}
    assert nodupe.deriveKey(thismsg) == thismsg["relPath"]

    thismsg = make_message()
    thismsg['identity'] = {'method': "cod"}
    assert nodupe.deriveKey(thismsg) == thismsg["relPath"]
    thismsg['identity'] = {'method': "method", 'value': "value\n"}
    assert nodupe.deriveKey(thismsg) == "method,value"

    thismsg = make_message()
    assert nodupe.deriveKey(thismsg) == thismsg["relPath"] + "," + thismsg["mtime"]
    thismsg['size'] = 28234
    assert nodupe.deriveKey(thismsg) == thismsg["relPath"] + "," + thismsg["mtime"] + ",28234" 
    del thismsg['mtime']
    assert nodupe.deriveKey(thismsg) == thismsg["relPath"] + "," + thismsg['pubTime'] + ",28234" 

def test_open__WithoutFile(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)

    nodupe.open()
    assert nodupe.cache_file == str(tmp_path) + os.sep + 'recent_files_005.cache'
    assert os.path.isfile(nodupe.cache_file) == True
    assert len(nodupe.cache_dict) == 0

def test_open__WithFile(tmp_path):
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

def test_open__WithData(tmp_path, caplog):
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

    # Should be able to catch the exception thrown, but it's not working, so falling back on checking the log output
    # https://docs.pytest.org/en/stable/reference/reference.html#pytest.raises
    log_found_loadcorrupted = False
    for record in caplog.records:
        if "load corrupted: lineno" in record.message:
            log_found_loadcorrupted = True

    assert nodupe.cache_file == str(tmp_path) + os.sep + 'recent_files_005.cache'
    assert os.path.isfile(nodupe.cache_file) == True
    assert len(nodupe.cache_dict) == 5
    assert log_found_loadcorrupted == True

@pytest.mark.depends(on=['test_open__WithoutFile', 'test_open__WithFile', 'test_open__WithData'])
def test_on_start(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)

    nodupe.on_start()

    assert nodupe.cache_file == str(tmp_path) + os.sep + 'recent_files_005.cache'
    assert os.path.isfile(nodupe.cache_file) == True
    assert len(nodupe.cache_dict) == 0


@pytest.mark.depends(on=['test_save', 'test_close'])
def test_on_stop(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)

    nodupe.on_stop()

    assert nodupe.fp == None
    assert len(nodupe.cache_dict) == 0

@pytest.mark.depends(on=['test_on_start'])
def test_close(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)

    nodupe.on_start()

    nodupe.close()
    assert nodupe.fp == None
    assert nodupe.cache_dict == {}
    assert nodupe.count == 0

@pytest.mark.depends(on=['test_on_start'])
def test_close__ErrorThrown(tmp_path, caplog):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)

    nodupe.on_start()

    nodupe.fp.close()

    # Should be able to catch the exception thrown, but it's not working, so falling back on checking the log output
    # https://docs.pytest.org/en/stable/reference/reference.html#pytest.raises
    nodupe.close()

    log_found_notclose = False
    for record in caplog.records:
        if "did not close" in record.message:
            log_found_notclose = True

    assert nodupe.fp == None
    assert nodupe.cache_dict == {}
    assert nodupe.count == 0
    assert log_found_notclose == True

@pytest.mark.depends(on=['test_on_start'])
def test_close__Unlink(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)

    nodupe.on_start()

    nodupe.close(unlink=True)
    assert nodupe.fp == None
    assert nodupe.cache_dict == {}
    assert nodupe.count == 0
    assert os.path.isfile(nodupe.cache_file) == False

@pytest.mark.depends(on=['test_on_start'])
def test_close__Unlink_ErrorThrown(tmp_path, caplog):
    
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)

    nodupe.on_start()

    os.unlink(nodupe.cache_file)
    assert os.path.isfile(nodupe.cache_file) == False

    # Should be able to catch the exception thrown, but it's not working, so falling back on checking the log output
    # https://docs.pytest.org/en/stable/reference/reference.html#pytest.raises
    nodupe.close(unlink=True)

    log_found_notunlink = False
    for record in caplog.records:
        if "did not unlink" in record.message:
            log_found_notunlink = True
    
    assert nodupe.fp == None
    assert nodupe.cache_dict == {}
    assert nodupe.count == 0
    assert log_found_notunlink == True

#@pytest.mark.depends(on=['test_open__WithoutFile'])
def test_clean(tmp_path, capsys):
    import time
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)
    nodupe.o.nodupe_ttl = 100000

    nodupe.cache_dict = {
        'key1': {'/some/path/to/file1.txt': float(time.time() - 1000)}, 
        'key2': {'/some/path/to/file2.txt': float(time.time() - 1000)}, 
        'key3': {'/some/path/to/file3.txt': float(time.time() - 1000)}, 
        'key4': {'/some/path/to/file4.txt': float(time.time() - 1000)}, 
        'key5': {   
            '/some/path/to/file5a.txt': float(time.time() - 1000), 
            '/some/path/to/file5b.txt': float(time.time() - 1000)}, 
        'key6': {'/some/path/to/file6.txt': float(time.time() - 1000000)}}
    nodupe.clean()

    assert len(nodupe.cache_dict) == 5
    assert nodupe.count == 6

@pytest.mark.depends(on=['test_open__WithoutFile'])
def test_clean__Persist_DelPath(tmp_path, capsys):
    import time
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)
    nodupe.o.nodupe_ttl = 100000

    nodupe.open()

    nodupe.cache_dict = {
        'key1': {'/some/path/to/file1.txt': float(time.time() - 1000)}, 
        'key2': {'/some/path/to/file2.txt': float(time.time() - 1000)}, 
        'key3': {'/some/path/to/file3.txt': float(time.time() - 1000)}, 
        'key4': {'/some/path/to/file4.txt': float(time.time() - 1000)}, 
        'key5': {   
            '/some/path/to/file5a.txt': float(time.time() - 1000), 
            '/some/path/to/file5b.txt': float(time.time() - 1000)}, 
        'key6': {'/some/path/to/file6.txt': float(time.time() - 1000000)}}

    nodupe.clean(persist=True, delpath="/some/path/to/file1.txt")

    assert len(nodupe.cache_dict) == 4
    assert nodupe.count == 5
    #File hasn't been flushed at this point, so the number of lines 0, despite the count being 5
    assert len(open(str(tmp_path) + os.sep + 'recent_files_005.cache').readlines()) == 0


@pytest.mark.depends(on=['test_open__WithoutFile', 'test_clean__Persist_DelPath'])
def test_save(tmp_path, capsys):
    import time
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)
    nodupe.o.nodupe_ttl = 100000

    nodupe.open()

    nodupe.cache_dict = {
        'key1': {'/some/path/to/file1.txt': float(time.time() - 1000)}, 
        'key2': {'/some/path/to/file2.txt': float(time.time() - 1000)}, 
        'key3': {'/some/path/to/file3.txt': float(time.time() - 1000)}, 
        'key4': {'/some/path/to/file4.txt': float(time.time() - 1000)}, 
        'key5': {   
            '/some/path/to/file5a.txt': float(time.time() - 1000), 
            '/some/path/to/file5b.txt': float(time.time() - 1000)}, 
        'key6': {'/some/path/to/file6.txt': float(time.time() - 1000000)}}

    nodupe.save()

    assert len(nodupe.cache_dict) == 5
    assert nodupe.count == 6
    #File hasn't been flushed at this point, so the number of lines 0, despite the count being 5
    assert len(open(str(tmp_path) + os.sep + 'recent_files_005.cache').readlines()) == 0

@pytest.mark.depends(on=['test_open__WithoutFile', 'test_clean__Persist_DelPath'])
def test_save__Unlink_Error(tmp_path, caplog):
    import time
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)
    nodupe.o.nodupe_ttl = 100000

    nodupe.open()

    nodupe.cache_dict = {
        'key1': {'/some/path/to/file1.txt': float(time.time() - 1000)}, 
        'key2': {'/some/path/to/file2.txt': float(time.time() - 1000)}, 
        'key3': {'/some/path/to/file3.txt': float(time.time() - 1000)}, 
        'key4': {'/some/path/to/file4.txt': float(time.time() - 1000)}, 
        'key5': {   
            '/some/path/to/file5a.txt': float(time.time() - 1000), 
            '/some/path/to/file5b.txt': float(time.time() - 1000)}, 
        'key6': {'/some/path/to/file6.txt': float(time.time() - 1000000)}}

    os.unlink(nodupe.cache_file)
    nodupe.save()

    log_found_notunlink = False
    for record in caplog.records:
        if "did not unlink: cache_file" in record.message:
            log_found_notunlink = True

    assert len(nodupe.cache_dict) == 5
    assert nodupe.count == 6
    #File hasn't been flushed at this point, so the number of lines 0, despite the count being 5
    assert len(open(str(tmp_path) + os.sep + 'recent_files_005.cache').readlines()) == 0
    assert log_found_notunlink == True


@pytest.mark.depends(on=['test_open__WithoutFile', 'test_clean__Persist_DelPath'])
def test_save__Open_Error(tmp_path, caplog):
    import time
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)
    nodupe.o.nodupe_ttl = 100000

    nodupe.open()

    nodupe.cache_dict = {
        'key1': {'/some/path/to/file1.txt': float(time.time() - 1000)}, 
        'key2': {'/some/path/to/file2.txt': float(time.time() - 1000)}, 
        'key3': {'/some/path/to/file3.txt': float(time.time() - 1000)}, 
        'key4': {'/some/path/to/file4.txt': float(time.time() - 1000)}, 
        'key5': {   
            '/some/path/to/file5a.txt': float(time.time() - 1000), 
            '/some/path/to/file5b.txt': float(time.time() - 1000)}, 
        'key6': {'/some/path/to/file6.txt': float(time.time() - 1000000)}}

    nodupe.cache_file = "/root/foobar.cache"
    nodupe.save()

    log_found_notopen = False
    for record in caplog.records:
        if "did not clean: cache_file" in record.message:
            log_found_notopen = True

    assert len(nodupe.cache_dict) == 6
    #File hasn't been flushed at this point, so the number of lines 0, despite the count being 5
    assert log_found_notopen == True

@pytest.mark.depends(on=['test_save'])
def test_on_housekeeping(tmp_path, caplog):
    import time
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)
    nodupe.o.nodupe_ttl = 100000

    nodupe.open()

    nodupe.cache_dict = {
        'key1': {'/some/path/to/file1.txt': float(time.time() - 1000)}, 
        'key2': {'/some/path/to/file2.txt': float(time.time() - 1000)}, 
        'key3': {'/some/path/to/file3.txt': float(time.time() - 1000)}, 
        'key4': {'/some/path/to/file4.txt': float(time.time() - 1000)}, 
        'key5': {   
            '/some/path/to/file5a.txt': float(time.time() - 1000), 
            '/some/path/to/file5b.txt': float(time.time() - 1000)}, 
        'key6': {'/some/path/to/file6.txt': float(time.time() - 1000000)}}

    nodupe.on_housekeeping()

    log_found = False
    for record in caplog.records:
        if "sec, increased up to" in record.message:
            log_found = True

    assert len(nodupe.cache_dict) == 5
    assert nodupe.count == 6
    #File hasn't been flushed at this point, so the number of lines 0, despite the count being 5
    assert log_found == True

@pytest.mark.depends(on=['test_open__WithoutFile'])
def test__not_in_cache(tmp_path, caplog):
    import time
    from sarracenia import nowflt
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)
    nodupe.o.nodupe_ttl = 100000

    nodupe.open()
    nodupe.now = nowflt()
    nodupe.count = 7

    nodupe.cache_dict = {
        'key1': {'/some/path/to/file1.txt': float(time.time() - 1000)}, 
        'key2': {'/some/path/to/file2.txt': float(time.time() - 1000)}, 
        'key3': {'/some/path/to/file3.txt': float(time.time() - 1000)}, 
        'key4': {'/some/path/to/file4.txt': float(time.time() - 1000)}, 
        'key5': {   
            '/some/path/to/file5a.txt': float(time.time() - 1000), 
            '/some/path/to/file5b.txt': float(time.time() - 1000)}, 
        'key6': {'/some/path/to/file6.txt': float(time.time() - 1000000)}}

    assert nodupe._not_in_cache("key3", "/some/path/to/file3.txt") == False
    assert nodupe.count == 8
    assert nodupe.cache_hit == "/some/path/to/file3.txt"
    assert nodupe.cache_dict['key3']["/some/path/to/file3.txt"] == nodupe.now 

    assert nodupe._not_in_cache("key7", "/some/path/to/file7a.txt") == True
    assert nodupe.count == 9
    assert nodupe.cache_dict['key7']["/some/path/to/file7a.txt"] == nodupe.now

    assert nodupe._not_in_cache("key7", "/some/path/to/file7b.txt") == True
    assert nodupe.count == 10
    assert nodupe.cache_dict['key7']["/some/path/to/file7b.txt"] == nodupe.now 

@pytest.mark.depends(on=['test__not_in_cache'])
def test_check_message(tmp_path, capsys):
    import time
    from sarracenia import nowflt
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)
    nodupe.o.nodupe_ttl = 100000

    nodupe.open()
    nodupe.now = nowflt()
    nodupe.count = 4

    nodupe.cache_dict = {
        'key1': {'/some/path/to/file1.txt': float(time.time() - 1000)}, 
        'key5': {   
            '/some/path/to/file5a.txt': float(time.time() - 1000), 
            '/some/path/to/file5b.txt': float(time.time() - 1000)}, 
        'key6': {'/some/path/to/file6.txt': float(time.time() - 1000000)}}

    message = make_message()

    assert nodupe.check_message(message) == True
    assert nodupe.cache_dict[message['relPath']+","+message['mtime']][message['relPath']] == nodupe.now

    message['nodupe_override'] = {"path": message['relPath'].split('/')[-1], "key": message['relPath'].split('/')[-1]}
    assert nodupe.check_message(message) == True
    assert nodupe.cache_dict[message['nodupe_override']['key']][message['nodupe_override']['path']] == nodupe.now
    assert nodupe.count == 6

@pytest.mark.depends(on=['test_check_message'])
def test_after_accept(tmp_path, capsys):
    from sarracenia import nowflt

    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    BaseOptions.inflight = 0
    nodupe = NoDupe(BaseOptions)
    nodupe.o.nodupe_ttl = 100000

    nodupe.open()
    nodupe.now = nowflt()

    message = make_message()
    
    after_accept_worklist = copy.deepcopy(WorkList)
    after_accept_worklist.incoming = [message, message, message]

    nodupe.after_accept(after_accept_worklist)

    assert len(after_accept_worklist.incoming) == 1
    assert len(after_accept_worklist.rejected) == 2
    assert nodupe.cache_dict[message['relPath'] + "," + message['mtime']][message['relPath']] == nodupe.now

@pytest.mark.depends(on=['test_check_message'])
def test_after_accept__WithFileAges(tmp_path, capsys):
    from sarracenia import nowflt, nowstr, timeflt2str

    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    BaseOptions.inflight = 0

    nodupe = NoDupe(BaseOptions)
    nodupe.o.nodupe_ttl = 100000
    nodupe.o.nodupe_fileAgeMin = 1000
    nodupe.o.nodupe_fileAgeMax = 1000

    nodupe.open()
    nodupe.now = nowflt() + 10

    message_old = make_message()
    message_old['mtime'] = timeflt2str(nodupe.now - 10000)
    message_new = make_message()
    message_new['mtime'] = nowstr()
    
    after_accept_worklist__WithFileAges = copy.deepcopy(WorkList)
    after_accept_worklist__WithFileAges.incoming = [message_old, message_new]

    nodupe.after_accept(after_accept_worklist__WithFileAges)

    assert len(after_accept_worklist__WithFileAges.rejected) == 2
    assert after_accept_worklist__WithFileAges.rejected[0]['reject'].count(message_old['mtime'] + " too old (nodupe check), oldest allowed")
    assert after_accept_worklist__WithFileAges.rejected[1]['reject'].count(message_new['mtime'] + " too new (nodupe check), newest allowed")

@pytest.mark.depends(on=['test_check_message'])
def test_after_accept__InFlight(tmp_path, capsys):
    from sarracenia import nowflt, nowstr, timeflt2str

    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    BaseOptions.inflight = 1000

    nodupe = NoDupe(BaseOptions)
    nodupe.o.nodupe_ttl = 100000

    nodupe.open()
    nodupe.now = nowflt() + 10

    message_old = make_message()
    message_old['mtime'] = timeflt2str(nodupe.now - 10000)
    message_new = make_message()
    message_new['mtime'] = nowstr()
    
    test_after_accept__InFlight = copy.deepcopy(WorkList)
    test_after_accept__InFlight.incoming = [message_old, message_new]

    nodupe.after_accept(test_after_accept__InFlight)

    assert len(test_after_accept__InFlight.rejected) == 1
    assert len(test_after_accept__InFlight.incoming) == 1
    assert test_after_accept__InFlight.incoming[0]['mtime'] == message_old['mtime']
    assert test_after_accept__InFlight.rejected[0]['reject'].count(message_new['mtime'] + " too new (nodupe check), newest allowed")