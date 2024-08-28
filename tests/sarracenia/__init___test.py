import pytest
from tests.conftest import *
#from unittest.mock import Mock

import os
from base64 import b64decode
#import urllib.request
import logging

import sarracenia
import sarracenia.config

logger = logging.getLogger('sarracenia')
logger.setLevel('DEBUG')

def test_baseUrlParse():
    parsed = sarracenia.baseUrlParse('http://hostname.com/a/deep/path/file.txt?query=val')
    assert parsed.scheme == "http"
    assert parsed.query == "query=val"

    parsed = sarracenia.baseUrlParse('file:////opt/foobar/file.txt')
    assert parsed.scheme == "file"
    assert parsed.path == "/opt/foobar/file.txt"


def test_timev2tov3str():
    assert sarracenia.timev2tov3str('20230710T120000.123') == '20230710T120000.123'
    assert sarracenia.timev2tov3str('20230710120000.123') == '20230710T120000.123'


def test_durationToSeconds():
    assert sarracenia.durationToSeconds('none') == sarracenia.durationToSeconds('off') == sarracenia.durationToSeconds('false') == 0.0
    assert sarracenia.durationToSeconds('on', default=10) == sarracenia.durationToSeconds('true', default=10) == 10.0

    assert sarracenia.durationToSeconds('1s') == sarracenia.durationToSeconds('1S') == 1.0
    assert sarracenia.durationToSeconds('2m') == sarracenia.durationToSeconds('2M') == 120.0
    assert sarracenia.durationToSeconds('3h') == sarracenia.durationToSeconds('3H') == 10800.0
    assert sarracenia.durationToSeconds('4d') == sarracenia.durationToSeconds('4D') == 345600.0
    assert sarracenia.durationToSeconds('1w') == sarracenia.durationToSeconds('1W') == 604800.0
    assert sarracenia.durationToSeconds('0.5h') == sarracenia.durationToSeconds('0.5H') == 1800.0

    assert sarracenia.durationToSeconds('invalid') == 0.0
    assert sarracenia.durationToSeconds(b'5') == 0.0
    assert sarracenia.durationToSeconds([5]) == 5.0

    assert sarracenia.durationToSeconds(2.5) == 2.5
    assert sarracenia.durationToSeconds('1s', default=None) == 1.0
    assert sarracenia.durationToSeconds('1y') == 1.0
    assert sarracenia.durationToSeconds('-1s') == -1.0
    assert sarracenia.durationToSeconds('-1.5h') == -5400.0
    assert sarracenia.durationToSeconds('2h2m') == 7320
    assert sarracenia.durationToSeconds('3m2s') == 182

def test_durationToString():
    assert sarracenia.durationToString( 3600 ) == '1h'
    assert sarracenia.durationToString( 1800 ) == '30m'
    assert sarracenia.durationToString( 600 ) == '10m'
    assert sarracenia.durationToString( 6*3600 ) == '6h'
    assert sarracenia.durationToString( 6*3600+120 ) == '6h2m'
    assert sarracenia.durationToString( 26*3600+120 ) == '1d2h'

def test_timeValidate():
    assert sarracenia.timeValidate('20230710120000') == True
    assert sarracenia.timeValidate('2023-07-10T12:00:00') == False
    assert sarracenia.timeValidate('2023-07-10T12:00:00.') == False
    assert sarracenia.timeValidate('20230710120000.123') == True
    assert sarracenia.timeValidate('2023-07-10T12:00:00.123') == False
    assert sarracenia.timeValidate('2023-07-10T12:00:00Z') == False
    assert sarracenia.timeValidate('2023-07-10T12:00:00.123Z') == False
    assert sarracenia.timeValidate('20230710120000Z') == False

    assert sarracenia.timeValidate('20230710T10:11:00000') == False
    assert sarracenia.timeValidate('!0230710120000') == False

    assert sarracenia.timeValidate('') == False
    assert sarracenia.timeValidate('2023-07-10T12:00:00.1234') == False
    assert sarracenia.timeValidate('2023-07-10T12:00:00.123Za') == False
    assert sarracenia.timeValidate('2023-07-10T12:00:00.!@#$%') == False
    assert sarracenia.timeValidate('2023-07-10T12:00:00.   ') == False


def test_timeflt2str():
    assert sarracenia.timeflt2str(1632180811.123456) == '20210920T233331.123456001'
    assert sarracenia.timeflt2str(1632180811.00123) == '20210920T233331.00123000145'
    assert sarracenia.timeflt2str(1632180811) == '20210920T233331'
    assert sarracenia.timeflt2str(0) == '19700101T000000'
    assert sarracenia.timeflt2str(1234567890.123) == '20090213T233130.122999907'
    assert sarracenia.timeflt2str(1625452800.5) == '20210705T024000.5'


def test_timestr2flt():
    assert sarracenia.timestr2flt('20210920T233331.123456') == 1632180811.123456
    assert sarracenia.timestr2flt('20210920T233331.00123') == 1632180811.00123
    assert sarracenia.timestr2flt('20210920T233331') == 1632180811.0
    assert sarracenia.timestr2flt('19700101T000000') == 0.0
    assert sarracenia.timestr2flt('19700101000000') == 0.0
    assert sarracenia.timestr2flt('20090213T233130.123') == 1234567890.123
    assert sarracenia.timestr2flt('20210705T024000.5') == 1625452800.5


@pytest.mark.depends(on=['test_timestr2flt'])
def test_nowstr():
    import time
    assert time.time() - sarracenia.timestr2flt(sarracenia.nowstr()) < 0.001


@pytest.mark.depends(on=['test_nowstr'])
def test_nowflt():
    import time
    assert time.time() - sarracenia.nowflt() < 0.001

# def test_naturalSize():
#     if sarracenia.features['humanize']['present'] == True:
#         assert sarracenia.naturalSize(1024) == '1.0 KiB'
#     elif sarracenia.features['humanize']['present'] == False:
#         assert sarracenia.naturalSize(1024) == '1024'

# def test_naturalTime():
#     if sarracenia.features['humanize']['present'] == True:
#         assert sarracenia.naturalTime(1024) == '17 minutes ago'
#     elif sarracenia.features['humanize']['present'] == False:
#         assert sarracenia.naturalTime(1024) == '1024'

@pytest.fixture
def message():
    msg = sarracenia.Message()
    msg['_format'] = 'v03'
    msg['baseUrl'] = 'https://example.com'
    msg['relPath'] = 'path/to/file.txt'
    return msg


class Test_Message():

    def test_computeIdentity(self, tmp_path, mocker, caplog):
        # Set 1
        path1 = str(tmp_path) + os.sep + "file1.txt"
        open(path1, 'a').close()
        options = sarracenia.config.default_config()
        msg = sarracenia.Message()
        msg['mtime'] = sarracenia.nowstr()
        msg['size'] = 0
        #msg['mtime'] = sarracenia.timeflt2str(sarracenia.timestr2flt(msg['mtime']) + 1000)
        msg.computeIdentity(path1, options)
        assert msg['identity']['method'] == options.identity_method

        # Set 2
        path2 = str(tmp_path) + os.sep + "file2.txt"
        open(path2, 'a').close()
        options = sarracenia.config.default_config()
        options.randomize = True
        msg = sarracenia.Message()
        msg['mtime'] = sarracenia.nowstr()
        msg['size'] = 0
        mocker.patch('random.choice', return_value=None)
        msg.computeIdentity(path2, options)
        assert 'identity' not in msg

        # Set 3 - tests random, and algorithm == None
        path3 = str(tmp_path) + os.sep + "file3.txt"
        open(path3, 'a').close()
        options = sarracenia.config.default_config()
        options.randomize = True
        msg = sarracenia.Message()
        msg['mtime'] = sarracenia.nowstr()
        msg['size'] = 0
        mocker.patch('random.choice', return_value=None)
        msg.computeIdentity(path3, options)
        assert 'identity' not in msg

        # Set 4 - abitrary method
        path4 = str(tmp_path) + os.sep + "file6.txt"
        open(path4, 'a').close()
        options = sarracenia.config.default_config()
        options.identity_method = 'arbitrary'
        options.identity_arbitrary_value = "identity_arbitrary_value"
        msg = sarracenia.Message()
        msg['mtime'] = sarracenia.nowstr()
        msg['size'] = 0
        msg.computeIdentity(path4, options)
        assert msg['identity']['value'] == 'identity_arbitrary_value'

        # Set 4a - random 
        options.identity = 'random'
        options.identity_method = 'random'
        del(msg['identity'])
        msg.computeIdentity(path4, options)
        assert msg['identity']['method'] == 'random'

        # Set 4b - 'cod,*' method
        options.identity = 'cod,testname'
        options.identity_method = 'cod,testname'
        del(msg['identity'])
        msg.computeIdentity(path4, options)
        assert msg['identity'] == 'cod,testname'

        try:
            import xattr

            # Set 5 - with identity/mtime xattrs *and* old mtime
            path5 = str(tmp_path) + os.sep + "file5.txt"
            open(path5, 'a').close()
            xattr_mtime = sarracenia.timeflt2str(sarracenia.nowflt() - 1000)
            xattr.setxattr(path5, b'user.sr_identity', b'xattr_identity_value')
            xattr.setxattr(path5, b'user.sr_mtime', bytes(xattr_mtime, 'utf-8'))
            options = sarracenia.config.default_config()
            msg = sarracenia.Message()
            msg['mtime'] = sarracenia.nowstr()
            msg['size'] = 0
            msg.computeIdentity(path5, options)
            assert msg['identity']['method'] == options.identity_method
            assert xattr.getxattr(path5, b'user.sr_mtime').decode('utf-8') == msg['mtime']
            # Set 5a - Cover cases where the identity on disk is different than what's configured
            options.identity = 'md5name'
            options.identity_method = 'md5name'
            msg.computeIdentity(path5, options)
            found_log_set5 = False
            for record in caplog.records:
                if "xattr different method than on disk" in record.message:
                    found_log_set5 = True
            assert found_log_set5 == True

            # Set 6 - with identity/mtime xattrs
            path6 = str(tmp_path) + os.sep + "file4.txt"
            open(path6, 'a').close()
            msg_time = sarracenia.nowstr()
            xattr.setxattr(path6, b'user.sr_identity', b'{"method": "sha512", "value": "xattr_identity_value"}')
            xattr.setxattr(path6, b'user.sr_mtime', bytes(msg_time, 'utf-8'))
            options = sarracenia.config.default_config()
            msg = sarracenia.Message()
            msg['mtime'] = msg_time
            msg['size'] = 0
            msg.computeIdentity(path6, options)
            assert msg['identity']['value'] == 'xattr_identity_value'
        except:
            pass


    @pytest.mark.depends(on=['test_fromFileInfo'])
    def test_fromFileData(self, tmp_path):
        path = str(tmp_path) + os.sep + "file.txt"
        pathlink = str(tmp_path) + os.sep + "link.txt"
        open(path, 'a').close()
        os.symlink(path, pathlink)
        o = sarracenia.config.default_config()

        # Test regular file
        msg1 = sarracenia.Message.fromFileData(path, o, os.lstat(path))
        assert msg1['_format'] == 'v03'
        assert len(msg1['_deleteOnPost']) == 10
        assert msg1['local_offset'] == 0

        msg2 = sarracenia.Message.fromFileData(str(tmp_path), o, os.lstat(str(tmp_path)))
        assert msg2['contentType'] == 'text/directory'

        msg3 = sarracenia.Message.fromFileData(pathlink, o, os.lstat(pathlink))
        assert msg3['contentType'] == 'text/link'

        msg4 = sarracenia.Message.fromFileData('/dev/null', o, os.lstat('/dev/null'))
        assert msg4['size'] == 0

        msg5 = sarracenia.Message.fromFileData('/dev/null', o)
        assert "size" not in msg5.keys()


    def test_fromFileInfo(self, tmp_path):
        # Set 1
        path = str(tmp_path) + os.sep + "file1.txt"
        open(path, 'a').close()
        options = sarracenia.config.default_config()
        
        msg = sarracenia.Message.fromFileInfo(path, options, None)
        assert msg['_format'] == 'v03'
        assert len(msg['_deleteOnPost']) == 10
        assert msg['local_offset'] == 0
        
        # Set 2
        path = str(tmp_path) + os.sep + "file2.txt"
        open(path, 'a').close()
        options = sarracenia.config.default_config()
        options.permCopy = True
        options.timeCopy = False
        options.to_clusters = "to_clusters"
        options.cluster = "from_cluster"
        options.source = "source"
        options.identity_method = ''
        delattr(options, 'post_format')
        msg = sarracenia.Message.fromFileInfo(path, options, os.lstat(path))
        assert msg['to_clusters'] == 'to_clusters'
        assert msg['from_cluster'] == 'from_cluster'
        assert msg['source'] == 'source'
        assert msg['_format'] == 'v03'

        # Set 3
        options = sarracenia.config.default_config()
        options.strip = 1
        options.identity_method = 'random'
        options.post_format = 'post_format'
        options.exchange = ''
        options.post_exchange = 'post_exchange'
        msg = sarracenia.Message.fromFileInfo(str(tmp_path), options, os.lstat(tmp_path))
        assert msg['rename'] == os.sep + os.path.relpath(tmp_path, '/tmp')
        assert msg['_format'] == 'post_format'
        assert msg['exchange'] == 'post_exchange'
        assert msg['identity']['method'] == 'random'

        # Set 4
        path = str(tmp_path) + os.sep + "file4.txt"
        open(path, 'a').close()
        options = sarracenia.config.default_config()
        options.strip = 20
        options.identity_method = 'cod,identityValue'
        delattr(options, 'post_format')
        options.post_topicPrefix = ['v02']
        msg = sarracenia.Message.fromFileInfo(path, options, os.lstat(path))
        assert msg['rename'] == "/"
        assert msg['_format'] == "v02"
        assert msg['identity'] == {'method': 'cod', 'value': 'identityValue' }

        #Set 5
        path = str(tmp_path) + os.sep + "file5.txt"
        open(path, 'a').close()
        options = sarracenia.config.default_config()
        options.rename = str(tmp_path) + os.sep + "file4a.txt"
        with pytest.raises(KeyError):
            msg = sarracenia.Message.fromFileInfo(path, options, os.lstat(path))


    @pytest.mark.depends(on=['test_fromFileData'])
    def test_fromStream(self, tmp_path):
        path = str(tmp_path) + os.sep + "file.txt"
        open(path, 'a').close()
        o = sarracenia.config.default_config()

        data = b"Hello, World!"

        # Test fromStream method
        msg = sarracenia.Message.fromStream(path, o, data)
        assert msg['_format'] == 'v03'
        assert len(msg['_deleteOnPost']) == 10
        assert msg['local_offset'] == 0

        # Test with chmod
        o.chmod = 0o700
        msg = sarracenia.Message.fromStream(path, o, data)
        assert oct(os.stat(path).st_mode)[-3:] == '700'


    @pytest.mark.depends(on=['sarracenia/__init___test.py::test_baseUrlParse'])
    def test_updatePaths(self, tmp_path, mocker):
        path = str(tmp_path) + os.sep + "file.txt"
        open(path, 'a').close()
        new_file = "newfile.txt"
        new_dir = str(tmp_path) + os.sep + "new"
        
        #Test set 1
        options = sarracenia.config.default_config()
        msg = sarracenia.Message()
        # this was a behaviour changed in https://github.com/MetPX/sarracenia/pull/1034
        #with pytest.raises(Exception):
        #    msg.updatePaths(options)

        msg = sarracenia.Message()
        msg.updatePaths(options, new_dir, new_file)
        assert msg['_deleteOnPost'] == set([
            'new_dir', 'new_file', 'new_relPath', 'new_baseUrl', 'new_subtopic', 'post_format', '_format', 'subtopic'
        ])
        assert msg['new_dir'] == new_dir
        assert msg['new_file'] == new_file

        #Test set 2
        options = sarracenia.config.default_config()
        options.post_baseUrl = 'https://post_baseurl.com'
        options.fixed_headers = {'fixed_headers__Key1': 'fixed_headers__Val1'}
        msg.updatePaths(options, new_dir, new_file)
        assert msg['fixed_headers__Key1'] == 'fixed_headers__Val1'
        assert msg['post_format'] == 'v03'

        #Test set 3
        options = sarracenia.config.default_config()
        options.post_format = ''
        options.post_topicPrefix  = 'post_topicPrefix'
        options.post_baseDir = str(tmp_path)
        msg = sarracenia.Message()
        msg['baseUrl'] = 'baseUrl'
        msg.updatePaths(options, new_dir, new_file)
        assert msg['new_baseUrl'] == 'baseUrl'
        assert msg['post_format'] == 'p'

        #Test set 4
        options = sarracenia.config.default_config()
        options.post_format = ''
        options.post_topicPrefix  = ''
        options.topicPrefix = 'topicPrefix'
        options.post_baseDir = 'post_baseDir'
        msg = sarracenia.Message()
        msg['baseUrl'] = 'baseUrl'
        msg.updatePaths(options, new_dir, new_file)
        assert msg['post_format'] == 't'

        #Test set 5
        options = sarracenia.config.default_config()
        options.post_format = ''
        options.post_topicPrefix  = ''
        options.topicPrefix = msg['_format']
        options.post_baseDir = 'post_baseDir'
        msg = sarracenia.Message()
        msg['baseUrl'] = '/this/is/a/path'
        msg.updatePaths(options, '/this/is/a/path/new', new_file)
        assert msg['new_baseUrl'] == '/this/is/a/path'
        assert msg['post_format'] == msg['_format']

        # Test set 6
        options = sarracenia.config.default_config()
        options.post_baseUrl = 'https://post_baseurl.com'
        msg = sarracenia.Message()
        mocker.patch('sys.platform', 'win32')
        msg.updatePaths(options, '\\this\\is\\a\\path\\new', new_file)
        assert msg['new_relPath'] == '/this/is/a/path/new/newfile.txt'
        options.currentDir = 'Z:'
        msg.updatePaths(options, '\\this\\is\\a\\path\\new', new_file)
        assert msg['new_relPath'] == 'this/is/a/path/new/newfile.txt'


    def test_setReport(self):
        msg = sarracenia.Message()

        # Test setReport method
        msg.setReport(201, "Download successful")
        assert 'report' in msg
        assert msg['report']['code'] == 201
        assert msg['report']['message'] == "Download successful"

        msg.setReport(304)
        assert msg['report']['message'] == sarracenia.known_report_codes[304]

        msg.setReport(418)
        assert msg['report']['message'] == "unknown disposition"

        msg.setReport(418, "I'm a teapot")
        assert msg['report']['message'] == "I'm a teapot"

        # Add more assertions for other fields in the message


    @pytest.mark.depends(on=['sarracenia/__init___test.py::test_timeValidate'])
    def test_validate(self, message):
        
        assert sarracenia.Message.validate('string') == False

        with pytest.raises(KeyError):
            assert sarracenia.Message.validate(message) == False

        message['pubTime'] = ''
        assert sarracenia.Message.validate(message) == False

        message['pubTime'] = '20230710120000'
        assert sarracenia.Message.validate(message) == True

    
    def test_getContent(self, mocker):
        msg = sarracenia.Message()

        msg['content'] = {
            'encoding': '',
            'value': "sarracenia/_version.py"
        }
        assert msg.getContent() == b"sarracenia/_version.py"

        msg['content'] = {
            'encoding': 'base64',
            'value': 'c2FycmFjZW5pYS9fdmVyc2lvbi5weQ=='
        }
        # Test getContent method with inlined/embedded content
        assert msg.getContent() == b"sarracenia/_version.py"

        expected_content = "sarracenia/_version.py"
        import io
        mocker.patch('urllib.request.urlopen', return_value=io.StringIO(expected_content))
        msg = sarracenia.Message()
        msg['baseUrl'] = "https://NotARealURL.123"
        msg['retrievePath'] = "MetPX/sarracenia/main/VERSION.txt"
        assert msg.getContent() == expected_content

        
    def test_copyDict(self, message):
        message.copyDict(None)
        assert message['_format'] == 'v03'

        message.copyDict({'foobar': 'baz'})
        assert message['foobar'] == 'baz'


    def test_dumps(self, message):
        # Test dumps method
        assert message.dumps() == "{  '_deleteOnPost':'{'_format'}', '_format':'v03', 'baseUrl':'https://example.com', 'relPath':'path/to/file.txt' }"

        assert sarracenia.Message.dumps(None) == ''

        message['_format'] = 'v04'
        message['properties'] = {'prop1': 'propval1'}
        assert message.dumps() == "{  '_deleteOnPost':'{'_format'}', '_format':'v04', 'baseUrl':'https://example.com', 'properties':'https://example.com 'prop1':'propval1'', 'relPath':'path/to/file.txt' }"

        message['id'] = "id111"
        del message['properties']
        assert message.dumps() == "{  '_deleteOnPost':'{'_format'}', '_format':'v04', 'baseUrl':'https://example.com', 'relPath':'path/to/file.txt' }"

        message['_format'] = 'Wis'
        del message['id']
        assert message.dumps() == "{ 'geometry': None, 'properties':{  '_deleteOnPost':'{'_format'}', '_format':'Wis', 'baseUrl':'https://example.com', 'relPath':'path/to/file.txt', } }"

        message['id'] = "id111"
        message['geometry'] = "geometry111"
        message['testdict'] = {'key1': 'val1', 'key2': 'val2'}
        assert message.dumps() == "{ { 'id': 'id111', 'type':'Feature', 'geometry':geometry111 'properties':{  '_deleteOnPost':'{'_format'}', '_format':'Wis', 'baseUrl':'https://example.com', 'geometry':'geometry111', 'id':'id111', 'relPath':'path/to/file.txt', 'testdict':'{  'key1':'val1', 'key2':'val2' }', } }"

        message['longfield'] = "hacskmbeponlfkfcmxxasoxjgrodcmovxbkzgnfxqimkmxshaztwsptqbulazgszjyiqoqasyukgjejtbrbeufvfdrxlurglhlszdehigvctczjtleadkpeycunthwzwdbxybhbewgcclljkebtwueldbhximikfbtgapiklmqzceyqlilebchekrxmvhfflaclqjddfrhicdttaabkfkhbwylnzyneattcjsgpordersenmbzyjeaybtyyahsde"
        assert message.dumps() == "{ { 'id': 'id111', 'type':'Feature', 'geometry':geometry111 'properties':{  '_deleteOnPost':'{'_format'}', '_format':'Wis', 'baseUrl':'https://example.com', 'geometry':'geometry111', 'id':'id111', 'longfield':'hacskmbeponlfkfcmxxasoxjgrodcmovxbkzgnfxqimkmxshaztwsptqbulazgszjyiqoqasyukgjejtbrbeufvfdrxlurglhlszdehigvctczjtleadkpeycunthwzwdbxybhbewgcclljkebtwueldbhximikfbtgapiklmqzceyqlilebchekrxmvhfflaclqjddfrhicdttaabkfkhbwylnzyneattcjsgpordersenmbzyjeaybtyy...', 'relPath':'path/to/file.txt', 'testdict':'{  'key1':'val1', 'key2':'val2' }', } }"

        message['longfield'] = "{hacskmbeponlfkfcmxxasoxjgrodcmovxbkzgnfxqimkmxshaztwsptqbulazgszjyiqoqasyukgjejtbrbeufvfdrxlurglhlszdehigvctczjtleadkpeycunthwzwdbxybhbewgcclljkebtwueldbhximikfbtgapiklmqzceyqlilebchekrxmvhfflaclqjddfrhicdttaabkfkhbwylnzyneattcjsgpordersenmbzyjeaybtyyahsde}"
        assert message.dumps() == "{ { 'id': 'id111', 'type':'Feature', 'geometry':geometry111 'properties':{  '_deleteOnPost':'{'_format'}', '_format':'Wis', 'baseUrl':'https://example.com', 'geometry':'geometry111', 'id':'id111', 'longfield':'{hacskmbeponlfkfcmxxasoxjgrodcmovxbkzgnfxqimkmxshaztwsptqbulazgszjyiqoqasyukgjejtbrbeufvfdrxlurglhlszdehigvctczjtleadkpeycunthwzwdbxybhbewgcclljkebtwueldbhximikfbtgapiklmqzceyqlilebchekrxmvhfflaclqjddfrhicdttaabkfkhbwylnzyneattcjsgpordersenmbzyjeaybty...}', 'relPath':'path/to/file.txt', 'testdict':'{  'key1':'val1', 'key2':'val2' }', } }"





