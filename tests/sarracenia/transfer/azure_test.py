import pytest
#from unittest.mock import Mock

import os
import logging

import sarracenia
import sarracenia.config
import sarracenia.transfer
import sarracenia.transfer.azure

from azure.storage.blob import ContainerClient
import azure.core.exceptions

import base64
import json
import stat

#useful for debugging tests
import pprint
pretty = pprint.PrettyPrinter(indent=2, width=200).pprint


logger = logging.getLogger('sarracenia.config')
logger.setLevel('DEBUG')


TEST_ACCOUNT_NAME = 'notarealaccount'
TEST_CONTAINER_NAME = 'notarealcontainer'
TEST_CONTAINER_FILES = {
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
    client = ContainerClient.from_container_url(f'https://{TEST_ACCOUNT_NAME}.blob.core.windows.net/{TEST_CONTAINER_NAME}', credential="SomethingGoesHere")
    
    yield client

def _list_blobs(client):
    return [b for b in client.list_blob_names()]

def test___init__():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.azure.Azure('azure', options)

    assert type(transfer) is sarracenia.transfer.azure.Azure
    assert transfer.entries == {}

def test___credentials():
    transfer = sarracenia.transfer.azure.Azure('azure', sarracenia.config.default_config())

    #simple path
    transfer.o.credentials._parse('azure://testing_simple_account/container')
    transfer.sendTo = 'azure://testing_simple_account/container'
    transfer._Azure__credentials()
    assert transfer.account == 'testing_simple_account'
    assert transfer.container == 'container'
    assert transfer.credentials == None

    #Complex, with all options/details
    transfer = sarracenia.transfer.azure.Azure('azure', sarracenia.config.default_config())
    transfer.o.credentials._parse('azure://testing_complex_account/container azure_storage_credentials=testing_credentials')
    transfer.sendTo = 'azure://testing_complex_account/container'
    transfer._Azure__credentials()
    assert transfer.account == 'testing_complex_account'
    assert transfer.container == 'container'
    assert transfer.credentials == 'testing_credentials'

    #Complex, with all options/details, using 'azblob' scheme
    transfer = sarracenia.transfer.azure.Azure('azure', sarracenia.config.default_config())
    transfer.o.credentials._parse('azblob://testing_complex_account/container azure_storage_credentials=testing_credentials')
    transfer.sendTo = 'azblob://testing_complex_account/container'
    transfer._Azure__credentials()
    assert transfer.account == 'testing_complex_account'
    assert transfer.container == 'container'
    assert transfer.credentials == 'testing_credentials'

def test_cd():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.azure.Azure('azure', options)

    assert transfer.path == ""
    assert transfer.cwd == ""

    transfer.cd("/this/Is/A/Path/")

    assert transfer.path == "this/Is/A/Path/"
    assert transfer.cwd == "/this/Is/A/Path"

def test_cd_forced():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.azure.Azure('azure', options)

    assert transfer.path == ""
    assert transfer.cwd == ""

    transfer.cd_forced('777', "/this/Is/A/Path/")

    assert transfer.path == "this/Is/A/Path/"
    assert transfer.cwd == "/this/Is/A/Path"

@pytest.mark.depends(on=['test_close'])
def test_check_is_connected():
    options = sarracenia.config.default_config()
    options.sendTo = 'azure://testing_simple_account/container'
    transfer = sarracenia.transfer.azure.Azure('azure', options)

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
    transfer = sarracenia.transfer.azure.Azure('azure', options)
    
    transfer.chmod('777')
    assert True

def test_close():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.azure.Azure('azure', options)
    
    transfer.connected = True
    transfer.client = ContainerClient.from_container_url(f'https://{TEST_ACCOUNT_NAME}.blob.core.windows.net/{TEST_CONTAINER_NAME}')

    transfer.close()

    assert transfer.connected == False
    assert transfer.client == None

@pytest.mark.skip(reason="no good way to mock Azure SDK")
@pytest.mark.depends(on=['test___credentials'])
def test_connect(build_client):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.azure.Azure('azure', options)

    transfer.o.credentials._parse('azure://testing_simple_account/container')
    transfer.o.sendTo = 'azure://testing_simple_account/container'

    assert transfer.connect() == False

    transfer.o.sendTo = f'azure://{TEST_ACCOUNT_NAME}.blob.core.windows.net/{TEST_CONTAINER_NAME}'
    assert transfer.connect() == True

    # Probably need to test exception handling here, but... that sounds like a lot of work.

@pytest.mark.skip(reason="no good way to mock Azure SDK")
def test_delete(build_client):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.azure.Azure('azure', options)

    transfer.client = build_client
    transfer.account = TEST_ACCOUNT_NAME
    transfer.container = TEST_CONTAINER_NAME
    transfer.container_url = f'https://{TEST_ACCOUNT_NAME}.blob.core.windows.net/{TEST_CONTAINER_NAME}'

    assert 'RootFile.txt' in _list_blobs(transfer.client)

    transfer.delete('RootFile.txt')
    assert 'RootFile.txt' not in _list_blobs(transfer.client)

@pytest.mark.skip(reason="no good way to mock Azure SDK")
def test_get(build_client, tmp_path):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.azure.Azure('azure', options)
    transfer.client = build_client
    transfer.account = TEST_ACCOUNT_NAME
    transfer.container = TEST_CONTAINER_NAME
    transfer.container_url = f'https://{TEST_ACCOUNT_NAME}.blob.core.windows.net/{TEST_CONTAINER_NAME}'
    transfer.path = 'Folder2/'

    filename = str(tmp_path) + os.sep + "DownloadedFile.txt"

    # This isn't a valid message, but it serves our purposes here.
    msg = {'identity': {'method': 'cod', 'value': 'sha512'}, 'mtime': '20240326T182732'}

    size = transfer.get(msg, 'AlsoNestedFile.dat', filename)

    assert size == len(TEST_CONTAINER_FILES['Folder2/AlsoNestedFile.dat']['value']) # This is the size of the "content" string
    assert os.path.isfile(filename)
    assert open(filename, 'r').read() == TEST_CONTAINER_FILES['Folder2/AlsoNestedFile.dat']['value']

def test_getcwd(build_client):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.azure.Azure('azure', options)
    
    assert transfer.getcwd() == None

    transfer.client = build_client
    assert transfer.getcwd() == ''

@pytest.mark.skip(reason="no good way to mock Azure SDK")
def test_ls(build_client):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.azure.Azure('azure', options)
    
    transfer.client = build_client
    transfer.account = TEST_ACCOUNT_NAME
    transfer.container = TEST_CONTAINER_NAME
    transfer.container_url = f'https://{TEST_ACCOUNT_NAME}.blob.core.windows.net/{TEST_CONTAINER_NAME}'
    entries = transfer.ls()
    
    assert len(entries) == 5
    assert 'FolderToDelete' in entries
    assert entries['Folder1'].st_mode == 0o755 | stat.S_IFDIR
    assert entries['FileToRename.txt'].st_mode == 0o644
    assert entries['RootFile.txt'].st_size == 11

def test_mkdir():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.azure.Azure('azure', options)
    
    transfer.mkdir('ThisMeansNothing')
    assert True

@pytest.mark.skip(reason="no good way to mock Azure SDK")
def test_put(build_client, tmp_path):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.azure.Azure('azure', options)
    transfer.client = build_client
    transfer.account = TEST_ACCOUNT_NAME
    transfer.container = TEST_CONTAINER_NAME
    transfer.container_url = f'https://{TEST_ACCOUNT_NAME}.blob.core.windows.net/{TEST_CONTAINER_NAME}'

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
    assert "NewFolder/FileToUpload.txt" in _list_blobs(transfer.client)

def test_registered_as():    
    assert sarracenia.transfer.azure.Azure.registered_as() == ['azure', 'azblob']

@pytest.mark.skip(reason="no good way to mock Azure SDK")
def test_rename(build_client):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.azure.Azure('azure', options)
    
    transfer.client = build_client
    transfer.account = TEST_ACCOUNT_NAME
    transfer.container = TEST_CONTAINER_NAME
    transfer.container_url = f'https://{TEST_ACCOUNT_NAME}.blob.core.windows.net/{TEST_CONTAINER_NAME}'

    assert 'FileToRename.txt' in _list_blobs(transfer.client)

    transfer.rename('FileToRename.txt', 'FileNewName.txt')

    assert 'FileToRename.txt' not in _list_blobs(transfer.client)
    assert 'FileNewName.txt' in _list_blobs(transfer.client)

@pytest.mark.skip(reason="no good way to mock Azure SDK")
def test_rmdir(build_client):
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.azure.Azure('azure', options)

    transfer.client = build_client
    transfer.account = TEST_ACCOUNT_NAME
    transfer.container = TEST_CONTAINER_NAME
    transfer.container_url = f'https://{TEST_ACCOUNT_NAME}.blob.core.windows.net/{TEST_CONTAINER_NAME}'

    assert 'FolderToDelete/ThisFileWillBeGone.txt' in _list_blobs(transfer.client)
    
    transfer.rmdir('FolderToDelete')

    assert 'FolderToDelete/ThisFileWillBeGone.txt' not in _list_blobs(transfer.client)

def test_umask():
    options = sarracenia.config.default_config()
    transfer = sarracenia.transfer.azure.Azure('azure', options)
    
    transfer.umask()
    assert True