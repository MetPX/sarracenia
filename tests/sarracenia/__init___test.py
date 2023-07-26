import pytest

import os
from base64 import b64decode
import urllib.request

import sarracenia
import sarracenia.config

#useful for debugging tests
import pprint
pretty = pprint.PrettyPrinter(indent=2, width=200).pprint

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


#def test_naturalSize():
#    sarracenia.naturalSize()


@pytest.fixture
def message():
    msg = sarracenia.Message()
    msg['_format'] = 'v03'
    msg['baseUrl'] = 'https://example.com'
    msg['relPath'] = 'path/to/file.txt'
    return msg



class Test_Message():

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
        path = str(tmp_path) + os.sep + "file.txt"
        open(path, 'a').close()
        o = sarracenia.config.default_config()

        # Test regular file
        lstat = os.lstat(path)
        msg = sarracenia.Message.fromFileInfo(path, o, lstat)
        assert msg['_format'] == 'v03'
        assert len(msg['_deleteOnPost']) == 10
        assert msg['local_offset'] == 0

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

    def test_updatePaths(self, tmp_path):
        path = str(tmp_path) + os.sep + "file.txt"
        open(path, 'a').close()
        options = sarracenia.config.default_config()

        msg = sarracenia.Message()
        new_file = "newfile.txt"
        new_dir = str(tmp_path) + os.sep + "new"

        # Test updatePaths method
        msg.updatePaths(options, new_dir, new_file)
        assert msg['_deleteOnPost'] == set([
            'new_dir', 'new_file', 'new_relPath', 'new_baseUrl', 'new_subtopic', 'post_format', '_format'
        ])
        assert msg['new_dir'] == new_dir
        assert msg['new_file'] == new_file

        # Add more assertions for other fields in the message

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


    def test_getContent(self):
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

        # Test getContent method with external file
        url = "https://raw.githubusercontent.com/MetPX/sarracenia/main/VERSION.txt"  # Replace with a real URL
        with urllib.request.urlopen(url) as response:
            expected_content = response.read()

        msg = sarracenia.Message()
        msg['baseUrl'] = "https://raw.githubusercontent.com"
        msg['retrievePath'] = "MetPX/sarracenia/main/VERSION.txt"
        assert msg.getContent() == expected_content

        msg = sarracenia.Message()
        msg['baseUrl'] = "https://raw.githubusercontent.com"
        msg['relPath'] = "MetPX/sarracenia/main/VERSION.txt"
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





