import pytest
from tests.conftest import *

import types, re

from sarracenia.flowcb.accept.dateappend import Dateappend
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message():
    m = SR3Message()
    m["new_file"] = './SK/s0000684_f.xml'

    return m

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList

def test_after_accept():
    dateappend = Dateappend(sarracenia.config.default_config())
    
    worklist = make_worklist()
    worklist.incoming = [make_message(), make_message()]

    dateappend.after_accept(worklist)

    assert len(worklist.incoming) == 2
    assert bool(re.match(r'./SK/s0000684_f.xml_\d{12}', worklist.incoming[0]['new_file'])) == True
    assert bool(re.match(r'./SK/s0000684_f.xml_\d{12}', worklist.incoming[1]['new_file'])) == True