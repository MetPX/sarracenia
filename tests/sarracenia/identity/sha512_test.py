import pytest
from tests.conftest import *
#from unittest.mock import Mock

import os
import logging

import sarracenia
import sarracenia.identity.sha512


def test_registered_as():
    # Set 1
    hash = sarracenia.identity.sha512.Sha512()
    assert hash.registered_as() == 's'

def test_set_path(tmp_path):
    path1 = str(tmp_path) + os.sep + "file1.txt"
    hash = sarracenia.identity.sha512.Sha512()
    hash.set_path(path1)
    assert hash.filehash.name == "sha512"

@pytest.mark.depends(on=['test_set_path'])
def test_update(tmp_path):
    path1 = str(tmp_path) + os.sep + "file1.txt"
    # Set 1
    hash = sarracenia.identity.sha512.Sha512()
    hash.set_path(path1)
    hash.update('randomstring')
    assert hash.value == 'kkUPxxKfR72my8noS5yekWcdFnmIJSvDJIvtSF7uTyvnhtm0saERCXReIcNDAk2B7gET3o+tQY3gTbd36ynoDA=='
    hash.update(b'randombytes')
    assert hash.value == 'pPhNwHi6/lnnslx41G9BZ/5bEwpE+GbPTf9+6Rj7j76UeO7wT0c+Dlc2VioFI9Fy66G0pCszFkB/8cfrBFBRRw=='

