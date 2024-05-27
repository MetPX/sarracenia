import pytest
from tests.conftest import *
#from unittest.mock import Mock

import os
import logging

import sarracenia
import sarracenia.identity.arbitrary

def test___init__():
    hash = sarracenia.identity.arbitrary.Arbitrary()
    assert hash._value == 'None'


def test_registered_as():
    # Set 1
    hash = sarracenia.identity.arbitrary.Arbitrary()
    assert hash.registered_as() == 'a'

def test_set_path(tmp_path):
    path1 = str(tmp_path) + os.sep + "file1.txt"
    hash = sarracenia.identity.arbitrary.Arbitrary()
    hash.set_path(path1)
    assert True


def test_update():
    hash = sarracenia.identity.arbitrary.Arbitrary()
    hash.update('randomstring')
    assert True

@pytest.mark.depends()
def test___Property_value():
    sarracenia.identity.arbitrary.set_default_value('default')
    
    hash = sarracenia.identity.arbitrary.Arbitrary()
    assert hash.value == 'default'

    # test the setter
    hash.value = 'new'
    assert hash.value == 'new'

