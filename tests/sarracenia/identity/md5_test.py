import pytest
import os
#from unittest.mock import Mock

import logging

import sarracenia
import sarracenia.identity.md5

#useful for debugging tests
import pprint
pretty = pprint.PrettyPrinter(indent=2, width=200).pprint


def test_registered_as():
    # Set 1
    hash = sarracenia.identity.md5.Md5()
    assert hash.registered_as() == 'd'

def test_set_path(tmp_path):
    path1 = str(tmp_path) + os.sep + "file1.txt"
    hash = sarracenia.identity.md5.Md5()
    hash.set_path(path1)
    assert hash.filehash.name == "md5"

@pytest.mark.depends(on=['test_set_path'])
def test_update(tmp_path):
    path1 = str(tmp_path) + os.sep + "file1.txt"
    # Set 1
    hash = sarracenia.identity.md5.Md5()
    hash.set_path(path1)
    hash.update('randomstring')
    assert hash.value == 'tpDC1B4RAL5h8WAs1C1OFg=='
    hash.update(b'randombytes')
    assert hash.value == '+sILUpRAJFq9hB7p8kx1xA=='

