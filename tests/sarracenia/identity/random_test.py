import pytest
import os
#from unittest.mock import Mock

import logging

import sarracenia
import sarracenia.identity.random

#useful for debugging tests
import pprint
pretty = pprint.PrettyPrinter(indent=2, width=200).pprint


logger = logging.getLogger('sarracenia')
logger.setLevel('DEBUG')

def test_registered_as():
    hash = sarracenia.identity.random.Random()
    assert hash.registered_as() == '0'

def test_set_path(tmp_path):
    path1 = str(tmp_path) + os.sep + "file1.txt"
    hash = sarracenia.identity.random.Random()
    hash.set_path(path1)
    assert True

@pytest.mark.depends(on=['test_set_path'])
def test_prop__value(tmp_path, mocker):
    path1 = str(tmp_path) + os.sep + "file1.txt"
    hash = sarracenia.identity.random.Random()
    hash.set_path(path1)
    mocker.patch('random.randint', return_value=1000)
    assert hash.value == '1000'

