import pytest
import types

#useful for debugging tests
def pretty(*things, **named_things):
    import pprint
    for t in things:
        pprint.PrettyPrinter(indent=2, width=200).pprint(t)
    for k,v in named_things.items():
        print(str(k) + ":")
        pprint.PrettyPrinter(indent=2, width=200).pprint(v)

from sarracenia.flowcb.accept.wmotypesuffix import WmoTypeSuffix
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message(extSet = False, withRename = False):
    m = SR3Message()
    m['new_file'] = 'HavetoHaveANameHere'
    if extSet:
        m['new_file'] = 'HavetoHaveANameHere.grib'
    if withRename:
        m['rename'] = 'HavetoHaveANameHere'

    return m

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList


@pytest.mark.parametrize('input,extension', 
    [   ('G_', '.grid'),  ('IX', '.hdf'),  ('I_', '.bufr'), ('K_', '.crex'),
        ('LT', '.iwxxm'), ('L_', '.grib'), ('XW', '.txt'),  ('X_', '.cap'),
        ('D_', '.grib'),  ('H_', '.grib'), ('O_', '.grib'), ('Y_', '.grib'),
        ('E_', '.bin'),   ('P_', '.bin'),  ('Q_', '.bin'),  ('R_', '.bin'),
        ('__', '.txt'),
    ])
def test_find_type(input,extension):
    wmotypesuffix = WmoTypeSuffix(sarracenia.config.default_config())
    assert wmotypesuffix.find_type(input) == extension


@pytest.mark.depends(on=['test_find_type'])
def test_after_accept():
    #Set x
    wmotypesuffix = WmoTypeSuffix(sarracenia.config.default_config())

    worklist = make_worklist()
    worklist.incoming = [make_message(False, False), make_message(True, False), make_message(False, True)]

    wmotypesuffix.after_accept(worklist)

    assert len(worklist.incoming) == 3
    assert worklist.incoming[0]['new_file'] == 'HavetoHaveANameHere.grib'
    assert worklist.incoming[1]['new_file'] == 'HavetoHaveANameHere.grib'
    assert worklist.incoming[2]['rename'] == worklist.incoming[2]['new_file'] =='HavetoHaveANameHere.grib'



