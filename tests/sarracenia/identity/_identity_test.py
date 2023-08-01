import pytest
import os
#from unittest.mock import Mock

import logging

import sarracenia
import sarracenia.identity

#useful for debugging tests
import pprint
pretty = pprint.PrettyPrinter(indent=2, width=200).pprint


def test_factory():
    identity = sarracenia.identity.Identity().factory('foobar')
    assert identity == None

    identity = sarracenia.identity.Identity().factory()
    assert identity.registered_as() == 's'

def test_get_method():
    identity = sarracenia.identity.Identity().factory()
    assert identity.get_method() == 'sha512'


def test_update_file(tmp_path):
    path1 = str(tmp_path) + os.sep + "file1.txt"
    open(path1, 'a').write('randomstring')
    identity = sarracenia.identity.Identity().factory()
    identity.update_file(path1)

    assert identity.filehash.name == "sha512"

@pytest.mark.depends(on=['test_update_file'])
def test___Property_value(tmp_path):
    path1 = str(tmp_path) + os.sep + "file1.txt"
    open(path1, 'a').write('randomstring')
    identity = sarracenia.identity.Identity().factory()
    identity.update_file(path1)

    assert identity.value == 'kkUPxxKfR72my8noS5yekWcdFnmIJSvDJIvtSF7uTyvnhtm0saERCXReIcNDAk2B7gET3o+tQY3gTbd36ynoDA=='