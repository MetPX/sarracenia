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

from moto import mock_aws
import base64
import json
import stat

#useful for debugging tests
import pprint
pretty = pprint.PrettyPrinter(indent=2, width=200).pprint


logger = logging.getLogger('sarracenia.config')
logger.setLevel('DEBUG')


TEST_BUCKET_NAME = 'notarealbucket'
TEST_BUCKET_KEYS = {
    'RootFile.txt': {
        'value': 'Lorem ipsum',
        'meta': json.dumps({'mtime': '20240402T161825', 'identity': {'method': 'cod', 'value': 'sha512'}})},
    'Folder1/NestedFile.jpg': {
        'value': base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdjuG8t/x8ABW8COSh+5hMAAAAASUVORK5CYII='),
        'meta': json.dumps({'mtime': '20240401T161825', 'identity': {'method': 'cod', 'value': 'sha512'}})},
    'Folder1/NestedFolder/DoubleNestedFile.txt': {
        'value': 'This is the contents of DoubleNestedFile.txt',
        'meta': json.dumps({ 'mtime': '20240404T181822', 'identity': {'method': 'cod', 'value': 'sha512'}})},
    'Folder2/AlsoNestedFile.dat': {
        'value': 'o28934ua;loifgja908024hf;oiau4fhj298yao;uih43wap98w4fiuaghw3oufiywag3fhjklawgv2873RTY23ILUGHli&tyl&uiGHUU',
        'meta': json.dumps({'mtime': '20240404T181822', 'identity': {'method': 'cod', 'value': 'sha512'}})},
    'FolderToDelete/ThisFileWillBeGone.txt': {
        'value': 'ThisIsNotTheFileYouAreLookingFor',
        'meta': json.dumps({ 'mtime': '20240404T181822', 'identity': {'method': 'cod', 'value': 'sha512'}})},
    'FileToRename.txt': {
        'value': 'This file used to be called FileToRename.txt',
        'meta': json.dumps({ 'mtime': '20240404T181822', 'identity': {'method': 'cod', 'value': 'sha512'}})},
}

@pytest.fixture(scope="function")
def build_client():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=TEST_BUCKET_NAME)
        for key, details in TEST_BUCKET_KEYS.items():
            client.put_object(Bucket=TEST_BUCKET_NAME, Key=key, Body=details['value'], Metadata={'sarracenia_v3': details['meta']})
        
        yield client

def _list_keys(client):
    return [item['Key'] for item in client.list_objects_v2(Bucket=TEST_BUCKET_NAME)['Contents']]

def test___init__():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)

    assert type(transfer) is sarracenia.transfer.s3.S3
    assert transfer.entries == {}
    assert hasattr(transfer.s3_transfer_config, 'max_concurrency')
    assert hasattr(transfer.s3_client_config, 'user_agent_extra')

def test___credentials():
    transfer = sarracenia.transfer.s3.S3('s3', sarracenia.config.default_config())

    #simple path
    transfer.o.credentials._parse('s3://testing_simple_bucket_creds')
    transfer.sendTo = 's3://testing_simple_bucket_creds'
    transfer._S3__credentials()
    assert transfer.bucket == 'testing_simple_bucket_creds'
    assert transfer.client_args == {
            'aws_access_key_id': None,
            'aws_secret_access_key': None,
            'aws_session_token': None,
            'endpoint_url': None
            }

    #Complex, with all options/details
    transfer = sarracenia.transfer.s3.S3('s3', sarracenia.config.default_config())
    transfer.o.credentials._parse('s3://testing__access_key_id:testing__secret_access_key@testing_full_bucket_creds s3_session_token=testing_session_token,s3_endpoint=https://testing_endpoint:5000')
    transfer.sendTo = 's3://testing_full_bucket_creds'
    transfer._S3__credentials()
    assert transfer.bucket == 'testing_full_bucket_creds'
    assert transfer.client_args == {
            'aws_access_key_id': 'testing__access_key_id',
            'aws_secret_access_key': 'testing__secret_access_key',
            'aws_session_token': 'testing_session_token',
            'endpoint_url': 'https://testing_endpoint:5000'
            }

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

    transfer.cd_forced('777', "/this/Is/A/Path/")

    assert transfer.path == "this/Is/A/Path/"
    assert transfer.cwd == "/this/Is/A/Path"

@pytest.mark.depends(on=['test_close'])
def test_check_is_connected():
    options = sarracenia.config.default_config()
    options.sendTo = 's3://foobar'
    transfer = sarracenia.transfer.s3.S3('s3', options)

    assert transfer.check_is_connected() == False
    assert transfer.connected == False

    # This will still return False because of the sendto checks
    transfer.connected = True
    assert transfer.check_is_connected() == False

    transfer.connected = True
    transfer.sendTo = options.sendTo
    assert transfer.check_is_connected() == True

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
def test_connect(build_client):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)

    transfer.o.credentials._parse('s3://testing_simple_bucket_creds')
    transfer.o.sendTo = 's3://testing_simple_bucket_creds'

    assert transfer.connect() == False

    transfer.o.sendTo = 's3://' + TEST_BUCKET_NAME
    assert transfer.connect() == True

    # Probably need to test exception handling here, but... that sounds like a lot of work.

def test_delete(build_client):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)

    transfer.client = build_client
    transfer.bucket = TEST_BUCKET_NAME

    assert 'RootFile.txt' in _list_keys(transfer.client)

    transfer.delete('RootFile.txt')
    assert 'RootFile.txt' not in _list_keys(transfer.client)

def test_get(build_client, tmp_path):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    transfer.client = build_client
    transfer.bucket = TEST_BUCKET_NAME
    transfer.path = 'Folder2/'

    filename = str(tmp_path) + os.sep + "DownloadedFile.txt"

    # This isn't a valid message, but it serves our purposes here.
    msg = {'identity': {'method': 'cod', 'value': 'sha512'}, 'mtime': '20240326T182732'}

    size = transfer.get(msg, 'AlsoNestedFile.dat', filename)

    assert size == len(TEST_BUCKET_KEYS['Folder2/AlsoNestedFile.dat']['value']) # This is the size of the "content" string
    assert os.path.isfile(filename)
    assert open(filename, 'r').read() == TEST_BUCKET_KEYS['Folder2/AlsoNestedFile.dat']['value']

def test_getcwd(build_client):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    assert transfer.getcwd() == None

    transfer.client = build_client
    assert transfer.getcwd() == ''

def test_ls(build_client):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    transfer.client = build_client
    transfer.bucket = TEST_BUCKET_NAME
    entries = transfer.ls()
    
    assert len(entries) == 5
    assert 'FolderToDelete' in entries
    assert entries['Folder1'].st_mode == 0o755 | stat.S_IFDIR
    assert entries['FileToRename.txt'].st_mode == 0o644
    assert entries['RootFile.txt'].st_size == 11

def test_mkdir():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    transfer.mkdir('ThisMeansNothing')
    assert True

def test_put(build_client, tmp_path):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    transfer.client = build_client
    transfer.bucket = TEST_BUCKET_NAME
    transfer.path = 'NewFolder/'

    filename = str(tmp_path) + os.sep + "FileToUpload.txt"
    fp = open(filename, 'a')
    fp.write('ThisIsMyBody\n')
    fp.flush()
    fp.close()

    # This isn't a valid message, but it serves our purposes here.
    msg = {'identity': {'method': 'cod', 'value': 'sha512'}, 'mtime': '20240326T182732'}

    size = transfer.put(msg, filename, "FileToUpload.txt", 0,0)
    
    assert size == 13
    assert "NewFolder/FileToUpload.txt" in _list_keys(transfer.client)

def test_registered_as():    
    assert sarracenia.transfer.s3.S3.registered_as() == ['s3']

def test_rename(build_client):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    transfer.client = build_client
    transfer.bucket = TEST_BUCKET_NAME

    assert 'FileToRename.txt' in _list_keys(transfer.client)

    transfer.rename('FileToRename.txt', 'FileNewName.txt')

    assert 'FileToRename.txt' not in _list_keys(transfer.client)
    assert 'FileNewName.txt' in _list_keys(transfer.client)

def test_rmdir(build_client):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)

    transfer.client = build_client
    transfer.bucket = TEST_BUCKET_NAME

    assert 'FolderToDelete/ThisFileWillBeGone.txt' in _list_keys(transfer.client)
    
    transfer.rmdir('FolderToDelete')

    assert 'FolderToDelete/ThisFileWillBeGone.txt' not in _list_keys(transfer.client)

def test_umask():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.s3.S3('s3', options)
    
    transfer.umask()
    assert True