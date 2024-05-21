import base64
import hashlib
#from unittest.mock import Mock

#import urllib.request
import logging
import os
import pprint
import pytest

import sarracenia
import sarracenia.config

import sarracenia.flowcb.filter.wmo00_accumulate 
import sarracenia.flowcb.filter.wmo00_split 

import types

#useful for debugging tests
pretty = pprint.PrettyPrinter(indent=2, width=200).pprint


logger = logging.getLogger('sarracenia.config')
logger.setLevel('DEBUG')


TEST_WMO00_SampleWMO_individual = b'''\01\r\r\n00237\r\r\nFDCN02 CWQQ 282015 AMD\r\r\nFCST BASED ON 281800 DATA VALID 290000 FOR USE 21-06\r\r\n    3000 6000    9000    12000   18000\r\r\nYXS      3124-04 2922-11 2211-17 1827-31=\r\r\nXDD 75N 110W\r\r\n    3512 3520-22 3522-26 3614-30 0611-39=\r\r\n\3'''
TEST_WMO00_SampleWMO_accumulated = b'''00000237\0\0\01\r\r\n00237\r\r\nFDCN02 CWQQ 282015 AMD\r\r\nFCST BASED ON 281800 DATA VALID 290000 FOR USE 21-06\r\r\n    3000 6000    9000    12000   18000\r\r\nYXS      3124-04 2922-11 2211-17 1827-31=\r\r\nXDD 75N 110W\r\r\n    3512 3520-22 3522-26 3614-30 0611-39=\r\r\n\3'''

def make_message():
    m = sarracenia.Message()
    m['baseUrl'] = 'file:'
    m['relPath'] = '/foo/bar'
    m['content'] = { 'encoding' : 'base64', 'value': base64.b64encode(TEST_WMO00_SampleWMO_individual) }

    return m

def make_worklist():
    # FIXME: open new worklist
    worklist = types.SimpleNamespace()
    worklist.ok = []
    worklist.incoming = []
    worklist.rejected = []
    worklist.failed = []
    worklist.directories_ok = []
    worklist.poll_catching_up = False
    return worklist

def test___init__(tmp_path):
    options = sarracenia.config.default_config()
    options.batch=50
    options.no=1
    options.hostname="hoho.mydomain.org"
    options.pid_filename= str(tmp_path) + os.sep + "myconfig_01.pid"
    options.wmo00_work_directory = str(tmp_path)
    options.wmo00_origin_CCCC = 'CYKK'

    accumulator = sarracenia.flowcb.filter.wmo00_accumulate.Wmo00_accumulate(options)

    assert type(accumulator) is sarracenia.flowcb.filter.wmo00_accumulate.Wmo00_accumulate 
    assert accumulator.sequence_first_digit in range(0,10)
    assert accumulator.sequence_second_digit in range(0,10)
    assert accumulator.o.wmo00_work_directory == str(tmp_path)
    assert accumulator.o.wmo00_origin_CCCC == 'CYKK'
    assert accumulator.o.wmo00_type_marker == 'a'
    assert accumulator.o.wmo00_encapsulate
    assert accumulator.o.wmo00_byteCountMax == 500000
    assert accumulator.thisday in range(1,32)
    assert type(accumulator.sequence_file) is str
    assert accumulator.sequence == 0

    options.batch=500
    options.no=14
    yesterday=accumulator.thisday-1 if accumulator.thisday > 1 else 31

    with open( str(tmp_path) + os.sep + f"sequence_{options.no:02d}.txt", "w" ) as sf:
        sf.write( f"{yesterday} 99999" )

    options.hostname="hoho8.mydomain.org"

    accumulator = sarracenia.flowcb.filter.wmo00_accumulate.Wmo00_accumulate(options)
    assert accumulator.sequence_first_digit == 8
    assert accumulator.sequence_second_digit == 4
    assert accumulator.thisday == yesterday
    assert accumulator.sequence == 99999

def test_open_accumulated_file(tmp_path):

    options = sarracenia.config.default_config()
    options.batch=50
    options.no=1
    options.hostname="hoho8.mydomain.org"
    options.pid_filename= str(tmp_path) + os.sep + "myconfig_01.pid"
    options.wmo00_work_directory = str(tmp_path)
    options.wmo00_origin_CCCC = 'CYKK'

    accumulator = sarracenia.flowcb.filter.wmo00_accumulate.Wmo00_accumulate(options)

    af = accumulator.open_accumulated_file()

    #assert str(type(af)) is "<class '_io.TextIOWrapper'>"
    assert accumulator.accumulated_file == str(tmp_path) + os.sep + 'CYKK81000000.a'
    assert os.path.isfile(accumulator.accumulated_file)
    assert accumulator.sequence == 1

    af.close()

    options.no=2
    accumulator = sarracenia.flowcb.filter.wmo00_accumulate.Wmo00_accumulate(options)

    accumulator.sequence=999999
    af = accumulator.open_accumulated_file()
    assert os.path.isfile(accumulator.accumulated_file)
    assert accumulator.accumulated_file == str(tmp_path) + os.sep + 'CYKK82999999.a'
    assert accumulator.sequence == 0


@pytest.mark.depends( on=[ 'test_open_accumulated_file' ])
def test_after_accept(tmp_path):

    options = sarracenia.config.default_config()
    options.batch=50
    options.no=1
    options.hostname="hoho8.mydomain.org"
    options.pid_filename= str(tmp_path) + os.sep + "myconfig_01.pid"
    options.wmo00_work_directory = str(tmp_path)
    options.wmo00_origin_CCCC = 'CYKK'

    options.post_baseUrl = 'file://'

    accumulator = sarracenia.flowcb.filter.wmo00_accumulate.Wmo00_accumulate(options)
    
    worklist = make_worklist()
    m = make_message()
    worklist.incoming = [ m ]

    accumulator.after_accept( worklist )

    assert len(worklist.incoming) == 1

    output_message = worklist.incoming[0]

    print( f" {output_message=} " )

    assert output_message['relPath'] == str(tmp_path)[1:] + os.sep + 'CYKK81000000.a'

    fname = os.sep + output_message['relPath'] 
    assert os.path.isfile( fname )

    with open(fname, 'rb' ) as af:
        afdata = af.read()

    assert afdata == TEST_WMO00_SampleWMO_accumulated

    splitter = sarracenia.flowcb.filter.wmo00_split.Wmo00_split(options)

    datahash =  hashlib.md5(TEST_WMO00_SampleWMO_individual).hexdigest()
    print(' {datahash=}' )
    splitter.after_accept( worklist )

    assert datahash == '9e87a9155b446dac46417f548a808c7a'
    assert os.path.isdir(str(tmp_path)+ os.sep + 'FD' )
    assert os.path.isdir(str(tmp_path)+ os.sep + 'FD/CWQQ'  )
    assert os.path.isdir(str(tmp_path)+ os.sep + 'FD/CWQQ/20'  )
    assert os.path.isfile(str(tmp_path)+ os.sep + f'FD/CWQQ/20/FDCN02_CWQQ_282015_AMD_9e87a9155b446dac46417f548a808c7a' )
