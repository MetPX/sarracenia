import pytest
import types
import os
import time

#useful for debugging tests
def pretty(*things, **named_things):
    import pprint
    for t in things:
        pprint.PrettyPrinter(indent=2, width=200).pprint(t)
    for k,v in named_things.items():
        print(str(k) + ":")
        pprint.PrettyPrinter(indent=2, width=200).pprint(v)

from sarracenia.flowcb.accept.sundewpxroute import SundewPxRoute
from sarracenia import Message as SR3Message
import sarracenia.config

def write_pxroute_config(path):
    with open(path, "w") as w:
        w.write("""\
#comment_WithoutLeadingSpace_WithoutAfterSpace
#comment WithoutLeadingSpace WithAfterSpace
# Comment_WithLeadingSpace_WithoutAfterSpace
# Comment WithLeadingSpace WithAfterSpace
#empty line below

garbage line that means nothing with spaces
garbage line that means nothing, with comma
garbageLineThatMeansNothing_NoSpaces
garbageLineThatMeansNothing,withComma

clientAlias IIIIPPP iiiippp,bbb-bulletins,progressive-slip
clientAlias meadow zz-meadow,zz-meadow-sulphur-mt,sulphur,sulphur-bufr,sulphur-abc-test,sulphur-test,national-meadow
key AACN11_CWLW foo,mushroom,grip,orientation,familiar-19,familiar,romantic,cathedral,HARDWARE,energy,test, 3
key WXYZ07_RUHB foo,meadow,mushroom,grip,orientation,familiar-19,familiar,romantic,cathedral,HARDWARE,test,wmomntr 5
key ABCD11_CYQX STRUGGLE_NERVOUS 3
key QBAABC_CWVR STAIRCASE NO_DISTRIBUTION 5
key INAX13_EUMS Objective_FOR_Lorem,IIIIPPP 5""")
    

def make_message(new_file):
    m = SR3Message()
    m['new_file'] = new_file
    return m

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList


def test___init__(caplog, tmp_path):
    config_file = str(tmp_path) + os.sep + 'pxRouting.conf'
    options = sarracenia.config.default_config()
    options.logLevel = 'DEBUG'
    #options.pxClient = 'meadow,foobar'
    sundewpxroute = SundewPxRoute(options)
    
    assert len(caplog.messages) == 1
    assert 'sundew_pxroute pxRouting file not defined' in caplog.messages

    caplog.clear()
    options.pxRouting = config_file
    sundewpxroute = SundewPxRoute(options)
    #pretty(caplog.messages)
    assert len(caplog.messages) == 1
    assert f'sundew_pxroute pxRouting file ({config_file}) not found' in caplog.messages

    caplog.clear()
    write_pxroute_config(config_file)
    options.pxClient = 'grip,STRUGGLE_NERVOUS,progressive-slip'
    sundewpxroute = SundewPxRoute(options)
    assert sundewpxroute.ahls_to_route == {'AACN11_CWLW': True, 'ABCD11_CYQX': True, 'INAX13_EUMS': True, 'WXYZ07_RUHB': True}
    assert len(caplog.messages) == 3

@pytest.mark.depends(on=['test___init__'])
def test_after_accept(caplog, tmp_path):
    config_file = str(tmp_path) + os.sep + 'pxRouting.conf'
    write_pxroute_config(config_file)
    options = sarracenia.config.default_config()
    options.pxRouting = config_file
    options.pxClient = 'grip,STRUGGLE_NERVOUS,progressive-slip'
    options.logLevel = 'DEBUG'

    sundewpxroute = SundewPxRoute(options)

    caplog.clear()
    worklist = make_worklist()
    worklist.incoming = [
        make_message('/Some/Random/Path/That/Doesnt/Matter/TooShort'),                  # too short
        make_message('/Some/Random/Path/That/Doesnt/Matter/LongEnoughButNo_AtPos6'),    # doesn't have _ in pos 6
        make_message('/Some/Random/Path/That/Doesnt/Matter/ABCD07_RUHB'),               # right length, and has _, but not found in ahl keys
        make_message('/Some/Random/Path/That/Doesnt/Matter/WXYZ07_RUHB'),               # right length, and has _, found in ahl keys
        ]
    sundewpxroute.after_accept(worklist)
    assert len(worklist.rejected) == 3
    assert len(worklist.incoming) == 1
    assert len(caplog.messages) == 4
    assert 'sundew_pxroute not an AHL: LongEnoughB' in caplog.messages
    assert 'sundew_pxroute no, do not deliver: ABCD07_RUHB' in caplog.messages
    assert 'sundew_pxroute yes, deliver: WXYZ07_RUHB' in caplog.messages