import pytest
from tests.conftest import *

import os, types, copy

from sarracenia.flowcb.gather.am import Am
import sarracenia.config 

from sarracenia import Message as SR3Message
from sarracenia.flowcb.rename.raw2bulletin import Raw2bulletin

class Options:
    def __init__(self):
        # self.o = sarracenia.config.default_config()
        self.logLevel = "DEBUG"
        self.logFormat = ""
        self.queueName = "TEST_QUEUE_NAME"
        self.component = "flow"
        self.config = "foobar_am.conf"
        self.sendTo = "am://127.0.0.1:5005"
        self.pid_filename = "/tmp/sarracenia/am_test/pid_filename"
        self.directory = "/tmp/test/directory"
        self.housekeeping = float(39)
        self.fileAgeMin = 0
        self.fileAgeMax = 0
        self.post_baseUrl = "http://localhost/"
        self.post_format = "v02"

    def add_option(self, option, type, default = None):
        if not hasattr(self, option):
            setattr(self, option, default)
    pass

def make_message():
    m = SR3Message()
    m["pubTime"] = "20180118151049.356378078"
    m["topic"] = "v02.post.sent_by_tsource2send"
    m["mtime"] = "20180118151048"
    m["identity"] = {
            "method": "md5",
            "value": "c35f14e247931c3185d5dc69c5cd543e"
         }
    m["atime"] = "201801181.51049.356378078"
    m["content"] = {"encoding":"" , "value": ""}
    m["from_cluster"] = "localhost"
    m["mode"] = "644"
    m["source"] = "tsource"
    m["sum"] =  "d,c35f14e247931c3185d5dc69c5cd543e"
    m["to_clusters"] = "localhost"
    m["baseUrl"] =  "https://NotARealURL"
    m["post_baseUrl"] =  "https://NotARealURL"
    m["relPath"] = "ThisIsAPath/To/A/File.txt"
    m["_deleteOnPost"] = set()
    return m

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList

# def test___init__():
#     BaseOptions = Options()
#     am_instance = Am(BaseOptions)
#     renamer = Raw2bulletin(BaseOptions)

def _get_bulletin_info(message):
    charset = message['content']['encoding']
    bulletin = message['content']['value']
    lines = bulletin.splitlines()
    if message['content']['encoding'] != 'base64':
        firstchars = bulletin[0:2].decode(charset)
        if list(lines[1].split()):
            station = lines[1].split()[0].decode(charset)
        else:
            station = lines[1].decode(charset)
    else:
        firstchars = "XX"
        station = "XXX"
    missing_ahl = 'CN00 CWAO'
    return bulletin, firstchars, lines, missing_ahl, station, charset

# For unit testing, we mostly want to check how the bulletins get corrected.
# We have lots of use cases where bulletin get corrected so it's important to test all of these cases


# @pytest.mark.depends(on=['test___init__'])

# Test 1: Check a regular binary bulletin. 
def test_am_binary_bulletin():
    from base64 import b64encode

    BaseOptions = Options()
    renamer = Raw2bulletin(BaseOptions)

    message_test1 = make_message()
    message_test1['content']['encoding'] = 'base64'
    message_test1['content']['value'] = b'ISAA41 CYWA 030000\nBUFR\x00\x00\xa8\x02\x00\x00\x12\x00\x006\x00\x00\x00\x00\r\r\x18\x05\x03\x00\x00\x00\x00\x00L\x00\x00\x01\x00\x01\xcc\x06\x02\x05\x02\x07\x01\x04\x01\x04\x02\x04\x03\x04\x04\x04\x05\x02\xc4\x01\xc3\x14\xd5\x14\r\x14\xce\x14\xc5\x14\x0b\x14\x01\n\x04\n3\x0c\x01\x0c\x02\x0c\x03\x0c\xc7\x08\x15\x04\x19\x0b\x0b\x0b\x0c\x04\x19\x08\x15\n4\n?\n=\r\x03\x85\x11\x00\x00\x00>\x00YWA (\x1cj6\x08I\xfa\x140\x00\xe0a@F1\x92g/\x9f6\xd0l~\xc1,hO\xfdh\x01_\xff\xfc\xf9D\xff\xc3DENSITY ALT 479FT7777\n'

    bulletin, firstchars, lines, missing_ahl, station, charset = _get_bulletin_info(message_test1)

    bulletinHeader = lines[0].decode('iso-8859-1').replace(' ', '_')
    message_test1['new_file'] = bulletinHeader + '__12345'
    message_test1['new_dir'] = BaseOptions.directory
    message_test1['content']['value'] = b64encode(message_test1['content']['value']).decode('ascii')
    message_test1["isProblem"] = False

    worklist = make_worklist()
    worklist.incoming = [message_test1]

    # Check renamer.
    renamer.after_accept(worklist)
    assert worklist.incoming[0]['new_file'] == 'ISAA41_CYWA_030000___00001'


# Test 2: Check a regular CACN bulletin
def test_cacn_regular():

    BaseOptions = Options()
    renamer = Raw2bulletin(BaseOptions)
    am_instance = Am(BaseOptions)

    message_test2 = make_message()
    message_test2['content']['encoding'] = 'iso-8859-1'
    message_test2['content']['value'] = b'CA\nWVO\n100,2024,123,1600,0,100,13.5,5.6,79.4,0.722,11.81,11.74,1.855,6.54,16.76,1544,2.344,14.26,0,375.6,375.6,375.5,375.5,0,11.58,11.24,3.709,13.89,13.16,11.22,11,9.45,11.39,5.033,79.4,0.694,-6999,41.19,5.967,5.887,5.93,6.184,5.64,5.066,5.253,-6999,7.3,0.058,0,5.715,4.569,0,0,1.942,-6999,57.4,0,0.531,-6999,1419,1604,1787,-6999,-6999,-6999,-6999,-6999,1601,-6999,-6999,6,5.921,5.956,6.177,5.643,5.07,5.256,-6999,9.53,11.22,10.09,10.61,125.4,9.1\n'

    bulletin, firstchars, lines, missing_ahl, station, charset = _get_bulletin_info(message_test2)

    bulletinHeader = lines[0].decode('iso-8859-1').replace(' ', '_')
    message_test2['new_file'] = bulletinHeader + '__12345'
    message_test2['new_dir'] = BaseOptions.directory

    # Check correcting the bulletin contents of a CACN
    new_bulletin, isProblem = am_instance.correctContents(bulletin, firstchars, lines, missing_ahl, station, charset)
    assert new_bulletin == b'CACN00 CWAO 021600\nWVO\n100,2024,123,1600,0,100,13.5,5.6,79.4,0.722,11.81,11.74,1.855,6.54,16.76,1544,2.344,14.26,0,375.6,375.6,375.5,375.5,0,11.58,11.24,3.709,13.89,13.16,11.22,11,9.45,11.39,5.033,79.4,0.694,-6999,41.19,5.967,5.887,5.93,6.184,5.64,5.066,5.253,-6999,7.3,0.058,0,5.715,4.569,0,0,1.942,-6999,57.4,0,0.531,-6999,1419,1604,1787,-6999,-6999,-6999,-6999,-6999,1601,-6999,-6999,6,5.921,5.956,6.177,5.643,5.07,5.256,-6999,9.53,11.22,10.09,10.61,125.4,9.1\n'


    # Check renamer.
    message_test2['content']['value'] = new_bulletin.decode('iso-8859-1')
    message_test2["isProblem"] = isProblem

    worklist = make_worklist()
    worklist.incoming = [message_test2]

    renamer.after_accept(worklist)
    assert worklist.incoming[0]['new_file'] == 'CACN00_CWAO_021600__WVO_00001'

# Test 3: Check an erronous CACN bulletin (missing timestamp in bulletin contents)
def test_cacn_erronous():
    import re

    BaseOptions = Options()
    renamer = Raw2bulletin(BaseOptions)
    am_instance = Am(BaseOptions)

    message_test3 = make_message()
    message_test3['content']['encoding'] = 'iso-8859-1'
    message_test3['content']['value'] = b'CA\nWPK\n0.379033,325.078,1.13338\n'

    bulletin, firstchars, lines, missing_ahl, station, charset = _get_bulletin_info(message_test3)

    bulletinHeader = lines[0].decode('iso-8859-1').replace(' ', '_')
    message_test3['new_file'] = bulletinHeader + '__12345'
    message_test3['new_dir'] = BaseOptions.directory

    # Check correcting the bulletin contents of a CACN
    new_bulletin, isProblem = am_instance.correctContents(bulletin, firstchars, lines, missing_ahl, station, charset)
    assert new_bulletin == b'CACN00 CWAO\nWPK\n0.379033,325.078,1.13338\n'

    # Check renamer.
    message_test3['content']['value'] = new_bulletin.decode('iso-8859-1')
    message_test3["isProblem"] = isProblem

    worklist = make_worklist()
    worklist.incoming = [message_test3]


    renamer.after_accept(worklist)
    assert re.match('CACN00_CWAO_......__WPK_00001_PROBLEM' , worklist.incoming[0]['new_file'])

# Test 4: Bulletin with double line separator after header (my-header\n\n)
def test_bulletin_double_linesep():

    BaseOptions = Options()
    renamer = Raw2bulletin(BaseOptions)
    am_instance = Am(BaseOptions)

    message_test4 = make_message()
    message_test4['content']['encoding'] = 'iso-8859-1'
    message_test4['content']['value'] = b'SXCN35 CWVR 021100\n\nFacility:       GVRD\nData valid at:  2024/05/02 11:00Z\n\nsome other stuff'

    bulletin, firstchars, lines, missing_ahl, station, charset = _get_bulletin_info(message_test4)

    bulletinHeader = lines[0].decode('iso-8859-1').replace(' ', '_')
    message_test4['new_file'] = bulletinHeader + '__12345'
    message_test4['new_dir'] = BaseOptions.directory

    # Check correcting the bulletin contents of the bulletin
    # Checking for b'' because this is what returns when correctContents has no problems to report correcting.
    new_bulletin, isProblem = am_instance.correctContents(bulletin, firstchars, lines, missing_ahl, station, charset)
    assert new_bulletin == b''

    # Check renamer.
    message_test4['content']['value'] = message_test4['content']['value'].decode('iso-8859-1')
    message_test4["isProblem"] = isProblem

    worklist = make_worklist()
    worklist.incoming = [message_test4]

    renamer.after_accept(worklist)
    assert message_test4['new_file'] == 'SXCN35_CWVR_021100___00001'

# Test 5: Bulletin with invalid year in timestamp (Fix: https://github.com/MetPX/sarracenia/pull/973)
def test_bulletin_invalid_timestamp(caplog):
    import re, datetime

    BaseOptions = Options()
    renamer = Raw2bulletin(BaseOptions)
    am_instance = Am(BaseOptions)    

    message_test5 = make_message()
    message_test5['content']['encoding'] = 'iso-8859-1'
    message_test5['content']['value'] = b'CA\nWVO\n100,1024,123,1600,0,100,13.5,5.6,79.4,0.722,11.81,11.74,1.855,6.54,16.76,1544,2.344,14.26,0,375.6,375.6,375.5,375.5,0,11.58,11.24,3.709,13.89,13.16,11.22,11,9.45,11.39,5.033,79.4,0.694,-6999,41.19,5.967,5.887,5.93,6.184,5.64,5.066,5.253,-6999,7.3,0.058,0,5.715,4.569,0,0,1.942,-6999,57.4,0,0.531,-6999,1419,1604,1787,-6999,-6999,-6999,-6999,-6999,1601,-6999,-6999,6,5.921,5.956,6.177,5.643,5.07,5.256,-6999,9.53,11.22,10.09,10.61,125.4,9.1\n'

    bulletin, firstchars, lines, missing_ahl, station, charset = _get_bulletin_info(message_test5)

    bulletinHeader = lines[0].decode('iso-8859-1').replace(' ', '_')
    message_test5['new_file'] = bulletinHeader + '__12345'
    message_test5['new_dir'] = BaseOptions.directory

    new_bulletin, isProblem = am_instance.correctContents(bulletin, firstchars, lines, missing_ahl, station, charset)
    assert new_bulletin == b'CACN00 CWAO\nWVO\n100,1024,123,1600,0,100,13.5,5.6,79.4,0.722,11.81,11.74,1.855,6.54,16.76,1544,2.344,14.26,0,375.6,375.6,375.5,375.5,0,11.58,11.24,3.709,13.89,13.16,11.22,11,9.45,11.39,5.033,79.4,0.694,-6999,41.19,5.967,5.887,5.93,6.184,5.64,5.066,5.253,-6999,7.3,0.058,0,5.715,4.569,0,0,1.942,-6999,57.4,0,0.531,-6999,1419,1604,1787,-6999,-6999,-6999,-6999,-6999,1601,-6999,-6999,6,5.921,5.956,6.177,5.643,5.07,5.256,-6999,9.53,11.22,10.09,10.61,125.4,9.1\n'

    message_test5['content']['value'] = message_test5['content']['value'].decode('iso-8859-1')
    message_test5["isProblem"] = isProblem

    worklist = make_worklist()
    worklist.incoming = [message_test5]

    renamer.after_accept(worklist)
    # We want to make sure the proper errors are raised from the logs
    assert 'Unable to fetch header contents. Skipping message' in caplog.text and 'Unable to verify year from julian time.' in caplog.text


# Test 6: Bulletin with trailing spaces at the end of the header (Fix: https://github.com/MetPX/sarracenia/pull/956)
def test_bulletin_header_trailing_space():

    BaseOptions = Options()
    renamer = Raw2bulletin(BaseOptions)
    am_instance = Am(BaseOptions)

    message_test6 = make_message()
    message_test6['content']['encoding'] = 'iso-8859-1'
    message_test6['content']['value'] = b'SXCN35 CWVR 021100 \n\nFacility:       GVRD\nData valid at:  2024/05/02 11:00Z\n\nsome other stuff\n'


    bulletin, firstchars, lines, missing_ahl, station, charset = _get_bulletin_info(message_test6)

    bulletinHeader = lines[0].decode('iso-8859-1').replace(' ', '_')
    message_test6['new_file'] = bulletinHeader + '__12345'
    message_test6['new_dir'] = BaseOptions.directory

    # Check correcting the bulletin contents of the bulletin
    new_bulletin, isProblem = am_instance.correctContents(bulletin, firstchars, lines, missing_ahl, station, charset)
    assert new_bulletin == b'SXCN35 CWVR 021100\n\nFacility:       GVRD\nData valid at:  2024/05/02 11:00Z\n\nsome other stuff\n'


# Test 7: Bulletin with a wrong station name (Fix: https://github.com/MetPX/sarracenia/pull/963/files)
def test_bulletin_wrong_station():

    BaseOptions = Options()
    renamer = Raw2bulletin(BaseOptions)
    am_instance = Am(BaseOptions)

    message_test7 = make_message()
    message_test7['content']['encoding'] = 'iso-8859-1'
    message_test7['content']['value'] = b'UECN99 CYCX 071200\nTTDD21 /// 5712/ 71701 NIL=\n\n\n\n' 

    bulletin, firstchars, lines, missing_ahl, station, charset = _get_bulletin_info(message_test7)

    bulletinHeader = lines[0].decode('iso-8859-1').replace(' ', '_')
    message_test7['new_file'] = bulletinHeader + '__12345'
    message_test7['new_dir'] = BaseOptions.directory

    # Check correcting the bulletin contents of the bulletin
    # Checking for b'' because this is what returns when correctContents has no problems to report correcting
    new_bulletin, isProblem = am_instance.correctContents(bulletin, firstchars, lines, missing_ahl, station, charset)
    assert new_bulletin == b''

    # Check renamer.
    message_test7['content']['value'] = message_test7['content']['value'].decode('iso-8859-1')
    message_test7["isProblem"] = isProblem

    worklist = make_worklist()
    worklist.incoming = [message_test7]

    renamer.after_accept(worklist)
    assert message_test7['new_file'] == 'UECN99_CYCX_071200___00001_PROBLEM'

# Test 8: SM Bulletin - Add station mapping + SM/SI bulletin accomodities 
def test_SM_bulletin():
    
    BaseOptions = Options()
    renamer = Raw2bulletin(BaseOptions)
    am_instance = Am(BaseOptions)

    message_test8 = make_message()
    message_test8['content']['encoding'] = 'iso-8859-1'
    message_test8['content']['value'] = b'SM 030000\n71816 11324 80313 10004 20003 30255 40318 52018 60031 77177 887//\n333 10017 20004 42001 70118 90983 93101=\n'

    bulletin, firstchars, lines, missing_ahl, station, charset = _get_bulletin_info(message_test8)

    bulletinHeader = lines[0].decode('iso-8859-1').replace(' ', '_')
    message_test8['new_file'] = bulletinHeader + '__12345'
    message_test8['new_dir'] = BaseOptions.directory

    # Check correcting the bulletin contents of the bulletin
    am_instance.o.mapStations2AHL = ['SMCN06 CWAO COLL 71816 71818 71821 71825 71827 71828 71831 71832 71834 71841 71842 71845 71850 71854']
    new_bulletin, isProblem = am_instance.correctContents(bulletin, firstchars, lines, missing_ahl, station, charset)
    assert new_bulletin == b'SMCN06 CWAO 030000\nAAXX 03004\n71816 11324 80313 10004 20003 30255 40318 52018 60031 77177 887//\n333 10017 20004 42001 70118 90983 93101=\n'

    message_test8['content']['value'] = new_bulletin.decode('iso-8859-1')
    message_test8["isProblem"] = isProblem

    worklist = make_worklist()
    worklist.incoming = [message_test8]

    renamer.after_accept(worklist)
    assert message_test8['new_file'] == 'SMCN06_CWAO_030000__71816_00001'

# Test 9: Bulletin with 5 fields in header (invalid)
def test_bulletin_header_five_fileds():

    BaseOptions = Options()
    renamer = Raw2bulletin(BaseOptions)
    am_instance = Am(BaseOptions)

    message_test9 = make_message()
    message_test9['content']['encoding'] = 'iso-8859-1'
    message_test9['content']['value'] = b'SXCN35 CWVR 021100 AAA OOPS\n\nFacility:       GVRD\nData valid at:  2024/05/02 11:00Z\n\nsome other stuff\n'

    bulletin, firstchars, lines, missing_ahl, station, charset = _get_bulletin_info(message_test9)

    bulletinHeader = lines[0].decode('iso-8859-1').replace(' ', '_')
    message_test9['new_file'] = bulletinHeader + '__12345'
    message_test9['new_dir'] = BaseOptions.directory

    # Check correcting the bulletin contents of the bulletin
    new_bulletin, isProblem = am_instance.correctContents(bulletin, firstchars, lines, missing_ahl, station, charset)
    assert new_bulletin == b'SXCN35 CWVR 021100 AAA\n\nFacility:       GVRD\nData valid at:  2024/05/02 11:00Z\n\nsome other stuff\n'

# Test 10: Bulletin with 6 fields in header (invalid)
def test_bulletin_header_six_fileds():

    BaseOptions = Options()
    renamer = Raw2bulletin(BaseOptions)
    am_instance = Am(BaseOptions)

    message_test10 = make_message()
    message_test10['content']['encoding'] = 'iso-8859-1'
    message_test10['content']['value'] = b'SXCN35 CWVR 021100 AAA OTHER OHNO\n\nFacility:       GVRD\nData valid at:  2024/05/02 11:00Z\n\nsome other stuff\n'

    bulletin, firstchars, lines, missing_ahl, station, charset = _get_bulletin_info(message_test10)

    bulletinHeader = lines[0].decode('iso-8859-1').replace(' ', '_')
    message_test10['new_file'] = bulletinHeader + '__12345'
    message_test10['new_dir'] = BaseOptions.directory

    # Check correcting the bulletin contents of the bulletin
    new_bulletin, isProblem = am_instance.correctContents(bulletin, firstchars, lines, missing_ahl, station, charset)
    assert new_bulletin == b'SXCN35 CWVR 021100 AAA OTHER\n\nFacility:       GVRD\nData valid at:  2024/05/02 11:00Z\n\nsome other stuff\n'


# Test 11: Bulletin with a timestamp (DDHHmm) bigger then 6 chars
def test_bulletin_timestamp_6chars_plus():
    BaseOptions = Options()
    renamer = Raw2bulletin(BaseOptions)
    am_instance = Am(BaseOptions)

    message_test11 = make_message()
    message_test11['content']['encoding'] = 'iso-8859-1'
    message_test11['content']['value'] = b'SXCN35 CWVR 021100Z\n\nFacility:       GVRD\nData valid at:  2024/05/02 11:00Z\n\nsome other stuff'

    bulletin, firstchars, lines, missing_ahl, station, charset = _get_bulletin_info(message_test11)

    bulletinHeader = lines[0].decode('iso-8859-1').replace(' ', '_')
    message_test11['new_file'] = bulletinHeader + '__12345'
    message_test11['new_dir'] = BaseOptions.directory

    # Check correcting the bulletin contents of the bulletin
    new_bulletin, isProblem = am_instance.correctContents(bulletin, firstchars, lines, missing_ahl, station, charset)
    assert new_bulletin == b'SXCN35 CWVR 021100\n\nFacility:       GVRD\nData valid at:  2024/05/02 11:00Z\n\nsome other stuff\n'

# Test 12: Test if BBB gets parsed properly when it's supposed to
def test_random_bulletin_with_BBB():
    BaseOptions = Options()
    renamer = Raw2bulletin(BaseOptions)
    am_instance = Am(BaseOptions)

    message_test12 = make_message()
    message_test12['content']['encoding'] = 'iso-8859-1'
    message_test12['content']['value'] = b'FXCN06 CYTR 230939 AAA\nREVISED SPECIAL AREA FORECAST FOR CFB VALCARTIER ISSUED BY THE JOINT\nMETEOROLOGICAL CENTRE AT 5:34 AM EDT THURSDAY 23 MAY 2024 FOR TODAY\nAND FRIDAY.\nTHE NEXT SCHEDULED FORECAST WILL BE ISSUED AT 4:00 PM TODAY.\n\nAMENDMENT: FORECAST AMENDED TO INCLUDE CB.\n\n1. AVIATION AREA FCST FOR 430 SQUADRON OPERATIONS WITHIN 25 NM RADIUS\n   OF CFB VALCARTIER.\n\n   NOTE. FCST ONLY VALID WHILE TAF IN EFFECT.\n         ALL HGTS ASL UNLESS NOTED.\n         HGTS ABV 10000 FT INDICATED BY XXX.\n         CB TCU AND ACC IMPLY SIG TURB AND ICE.\n         CB IMPLIES L LVL WS.\n\n   VALID 10-22Z\n\n   CLD AND WX... 20-30 BKN 80 P6SM. PTCHY -DZ BR CIGS 8-12 AGL TIL\n                 15Z. OCNL TCU XXX 3-P6SM -SHRA BR CIGS 10-15 AGL.\n                 OCNL CB XXX 2-5SM TSRAGR CIGS 4-9 AGL.\n      AFT 17Z... 40 FEW-SCT CU 70 P6SM.\n\n   ICE... NIL SIG ICE.\n\n   FZLVL... XXX.\n\n   TURB... PTCHY MOD MECH AFT 17Z.\n\n   OTLK VALID 22-04Z... VFR.\n\n2. HUMIDITY INFORMATION (IN PERCENT).\n\n   MNM TODAY... 50.\n\n   MAX TONIGHT... 100.\n\n   MNM FRIDAY... 45.\n\n3. LIGHT INFORMATION (LOCAL TIME).\n\n   A.  NEXT LAST LIGHT CIVIL 23/2102\n\n   B.  NEXT FIRST LIGHT CIVIL 24/0424\n\nEND/JMC\n'

    bulletin, firstchars, lines, missing_ahl, station, charset = _get_bulletin_info(message_test12)

    bulletinHeader = lines[0].decode('iso-8859-1').replace(' ', '_')
    message_test12['new_file'] = bulletinHeader + '__12345'
    message_test12['new_dir'] = BaseOptions.directory

    # Check correcting the bulletin contents of the bulletin
    new_bulletin, isProblem = am_instance.correctContents(bulletin, firstchars, lines, missing_ahl, station, charset)
    assert new_bulletin == b'' 

    message_test12['content']['value'] = bulletin.decode('iso-8859-1')
    message_test12["isProblem"] = isProblem

    worklist = make_worklist()
    worklist.incoming = [message_test12]

    renamer.after_accept(worklist)
    assert message_test12['new_file'] == 'FXCN06_CYTR_230939_AAA__00001'

# Test 13: SM Bulletin with BBB - Add station mapping + SM/SI bulletin accomodities + conserve BBB header
def test_SM_bulletin_with_BBB():
    
    BaseOptions = Options()
    renamer = Raw2bulletin(BaseOptions)
    am_instance = Am(BaseOptions)

    message_test13 = make_message()
    message_test13['content']['encoding'] = 'iso-8859-1'
    message_test13['content']['value'] = b'SM 030000 AAA\n71816 11324 80313 10004 20003 30255 40318 52018 60031 77177 887//\n333 10017 20004 42001 70118 90983 93101=\n'

    bulletin, firstchars, lines, missing_ahl, station, charset = _get_bulletin_info(message_test13)

    bulletinHeader = lines[0].decode('iso-8859-1').replace(' ', '_')
    message_test13['new_file'] = bulletinHeader + '__12345'
    message_test13['new_dir'] = BaseOptions.directory

    # Check correcting the bulletin contents of the bulletin
    am_instance.o.mapStations2AHL = ['SMCN06 CWAO COLL 71816 71818 71821 71825 71827 71828 71831 71832 71834 71841 71842 71845 71850 71854']
    new_bulletin, isProblem = am_instance.correctContents(bulletin, firstchars, lines, missing_ahl, station, charset)
    assert new_bulletin == b'SMCN06 CWAO 030000 AAA\nAAXX 03004\n71816 11324 80313 10004 20003 30255 40318 52018 60031 77177 887//\n333 10017 20004 42001 70118 90983 93101=\n'

    message_test13['content']['value'] = new_bulletin.decode('iso-8859-1')
    message_test13["isProblem"] = isProblem

    worklist = make_worklist()
    worklist.incoming = [message_test13]

    renamer.after_accept(worklist)
    assert message_test13['new_file'] == 'SMCN06_CWAO_030000_AAA_71816_00001'
