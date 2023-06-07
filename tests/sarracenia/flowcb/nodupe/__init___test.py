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

@pytest.mark.depends(on=[   'sarracenia/flowcb/nodupe/__init___test.py::test_open__withoutfile',
                            'sarracenia/flowcb/nodupe/__init___test.py::test_open__withfile',
                            'sarracenia/flowcb/nodupe/__init___test.py::test_open__withdata'
                            ])
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


@pytest.mark.depends(on=[   'sarracenia/flowcb/nodupe/__init___test.py::test_save',
                            'sarracenia/flowcb/nodupe/__init___test.py::test_close'
                            ])
def test_on_stop(tmp_path):
    BaseOptions = Options()
    BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
    BaseOptions.cfg_run_dir = str(tmp_path)
    BaseOptions.no = 5
    nodupe = NoDupe(BaseOptions)

    nodupe.on_stop()

    assert nodupe.fp == None
    assert len(nodupe.cache_dict) == 0

@pytest.mark.depends(on=['sarracenia/flowcb/nodupe/__init___test.py::test_on_start'])
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

@pytest.mark.depends(on=['sarracenia/flowcb/nodupe/__init___test.py::test_on_start'])
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

@pytest.mark.depends(on=['sarracenia/flowcb/nodupe/__init___test.py::test_on_start'])
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

@pytest.mark.depends(on=['sarracenia/flowcb/nodupe/__init___test.py::test_on_start'])
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

@pytest.mark.depends(on=['sarracenia/flowcb/nodupe/__init___test.py::test_open__withdata'])
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

@pytest.mark.depends(on=['sarracenia/flowcb/nodupe/__init___test.py::test_open__withoutfile'])
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


@pytest.mark.depends(on=[
                        'sarracenia/flowcb/nodupe/__init___test.py::test_open__withoutfile',
                        'sarracenia/flowcb/nodupe/__init___test.py::test_clean__Persist_DelPath'
])
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

@pytest.mark.depends(on=[
                        'sarracenia/flowcb/nodupe/__init___test.py::test_open__withoutfile',
                        'sarracenia/flowcb/nodupe/__init___test.py::test_clean__Persist_DelPath'
])
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


@pytest.mark.depends(on=[
                        'sarracenia/flowcb/nodupe/__init___test.py::test_open__withoutfile',
                        'sarracenia/flowcb/nodupe/__init___test.py::test_clean__Persist_DelPath'
])
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

@pytest.mark.depends(on=[
                        'sarracenia/flowcb/nodupe/__init___test.py::test_open__withoutfile',
                        'sarracenia/flowcb/nodupe/__init___test.py::test_save'
                        ])
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

@pytest.mark.depends(on=[
                        'sarracenia/flowcb/nodupe/__init___test.py::test_open__withoutfile'
                        ])
def test__not_in_cache__Hit(tmp_path, caplog):
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
    assert nodupe.cache_hit == "/some/path/to/file3.txt"
    assert nodupe.cache_dict['key3']["/some/path/to/file3.txt"] == nodupe.now 

@pytest.mark.depends(on=[
                        'sarracenia/flowcb/nodupe/__init___test.py::test_open__withoutfile',
                        ])
def test__not_in_cache__Miss(tmp_path, caplog):
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

    assert nodupe._not_in_cache("key7", "/some/path/to/file7a.txt") == True
    assert nodupe.count == 8
    assert nodupe.cache_dict['key7']["/some/path/to/file7a.txt"] == nodupe.now

    assert nodupe._not_in_cache("key7", "/some/path/to/file7b.txt") == True
    assert nodupe.count == 9
    assert nodupe.cache_dict['key7']["/some/path/to/file7b.txt"] == nodupe.now 

# @pytest.mark.depends(on=[
#                         'sarracenia/flowcb/nodupe/__init___test.py::test__not_in_cache__Hit',
#                         'sarracenia/flowcb/nodupe/__init___test.py::test__not_in_cache__Miss',
#                         ])
# def test_check_message(tmp_path, caplog):
#     import time
#     from sarracenia import nowflt
#     BaseOptions = Options()
#     BaseOptions.pid_filename = str(tmp_path) + os.sep + "pidfilename.txt"
#     BaseOptions.cfg_run_dir = str(tmp_path)
#     BaseOptions.no = 5
#     nodupe = NoDupe(BaseOptions)
#     nodupe.o.nodupe_ttl = 100000

#     nodupe.open()
#     nodupe.now = nowflt()
#     nodupe.count = 7

#     nodupe.cache_dict = {
#         'key1': {'/some/path/to/file1.txt': float(time.time() - 1000)}, 
#         'key2': {'/some/path/to/file2.txt': float(time.time() - 1000)}, 
#         'key3': {'/some/path/to/file3.txt': float(time.time() - 1000)}, 
#         'key4': {'/some/path/to/file4.txt': float(time.time() - 1000)}, 
#         'key5': {   
#             '/some/path/to/file5a.txt': float(time.time() - 1000), 
#             '/some/path/to/file5b.txt': float(time.time() - 1000)}, 
#         'key6': {'/some/path/to/file6.txt': float(time.time() - 1000000)}}

#     msg = message.copy()
#     assert nodupe.check_message(msg) == False