import pytest
#from unittest.mock import Mock

import os
from base64 import b64decode
#import urllib.request
import logging
import re

import sarracenia
import sarracenia.config
import sarracenia.transfer
import sarracenia.transfer.s3

import boto3, botocore

#useful for debugging tests
import pprint
pretty = pprint.PrettyPrinter(indent=2, width=200).pprint


logger = logging.getLogger('sarracenia.config')
logger.setLevel('DEBUG')

def test___init__():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)

    assert type(transfer) is sarracenia.transfer.s3.S3
    assert transfer.entries == {}
    assert hasattr(transfer.s3_transfer_config, 'max_concurrency')
    assert hasattr(transfer.s3_client_config, 'user_agent_extra')

def test___credentials():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)

    assert True

def test_cd():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)

    assert transfer.path == ""
    assert transfer.cwd == ""

    transfer.cd("/this/Is/A/Path/")

    assert transfer.path == "this/Is/A/Path/"
    assert transfer.cwd == "/this/Is/A/Path"

def test_cd_forced():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)

    assert transfer.path == ""
    assert transfer.cwd == ""

    transfer.cd("/this/Is/A/Path/")

    assert transfer.path == "this/Is/A/Path/"
    assert transfer.cwd == "/this/Is/A/Path"

@pytest.mark.depends(on=['test_close'])
def test_check_is_connected():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    assert True

def test_chmod():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    transfer.chmod('777')
    assert True

def test_close():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    transfer.connected = True
    transfer.client = boto3.client('s3')

    transfer.close()

    assert transfer.connected == False
    assert transfer.client == None

@pytest.mark.depends(on=['test___credentials'])
def test_connect():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    assert True

def test_delete():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    assert True

def test_get():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    assert True

def test_getcwd():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    assert transfer.getcwd() == None

    transfer.client = boto3.client('s3')
    assert transfer.getcwd() == ''

def test_ls():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    assert True

def test_mkdir():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    transfer.mkdir('ThisMeansNothing')
    assert True

def test_put():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    assert True

def test_registered_as():
    #options = sarracenia.config.default_config()
    #transfer = sarracenia.transfer.s3.S3('s3', options)
    
    assert sarracenia.transfer.s3.S3.registered_as() == ['s3']

def test_rename():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    assert True

def test_rmdir():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    assert True

def test_umask():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    transfer.umask()
    assert True