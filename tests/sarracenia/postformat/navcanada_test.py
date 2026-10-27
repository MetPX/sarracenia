"""
Basic tests for the NAV CANADA message format.
"""
import pytest
from tests.conftest import *
#from unittest.mock import Mock
from datetime import datetime

from sarracenia.postformat.navcanada import NavCanada


@pytest.mark.parametrize(
    'msg_type',
    ['NCFILESHARE', NavCanada.MSG_TYPE, 'TAC-SA', 'TAC-FT'],
)
def test_mine_supported_types(msg_type):
    assert NavCanada.mine(None, {'MSG_TYPE': msg_type}, None, None)


def test_mine_unsupported_type():
    assert not NavCanada.mine(None, {'MSG_TYPE': 'OTHER'}, None, None)


@pytest.mark.parametrize(
    'value, expected',
    [
        ('2026-08-18T08:13:08.399Z', '20260818T081308.399'),
        ('2026-08-18T08:13:08Z',     '20260818T081308.000'),
        (0,                          '19700101T000000.000'),
        ('1772657588',               '20260304T205308.000'),
        ('2026-10-15T12:50:11.989626+0000', '20261015T125011.989'),
        ('2026-10-15T12:50:11.989626+0500', '20261015T075011.989'),
        ('2026-10-15T12:50:11.989626+00:00', '20261015T125011.989'),
        ('2026-10-15T12:50:11.989626+05:00', '20261015T075011.989'),
        ('2026-10-27 20:15:25',      '20261027T201525.000'),
    ],
)
def test_parse_navcan_time(value, expected):
    assert NavCanada.parseNavCanTime(value) == expected


@pytest.mark.parametrize('value', ['not-a-time', None])
def test_parse_navcan_time_invalid(value):
    # Invalid values should not cause an exception.
    assert NavCanada.parseNavCanTime(value)


def test_sarra_timestr_to_dt():
    assert NavCanada._NavCanada__sarra_timestr_to_dt(
        '20260309T191032.404855'
    ) == datetime(2026, 3, 9, 19, 10, 32, 404855)


def test_sarra_timestr_to_dt_invalid():
    with pytest.raises(ValueError):
        NavCanada._NavCanada__sarra_timestr_to_dt('not-a-time')


def test_dt_to_nc_timestr():
    dt = datetime(2026, 10, 8, 17, 42, 38, 456789)

    assert NavCanada._NavCanada__dt_to_nc_timestr(dt) == (
        '2026-10-08T17:42:38.456Z'
    )


def test_import_mine_valid_message():
    headers = {
        'MSG_TYPE': 'NCFILESHARE',
        'MSG_PUBLISH_TIME': '2026-08-18T08:13:08.399Z',
        'NCFILESHARE_FILE_MTIME': '1772657588',
        'DESTINATION': 'NCFILESHARE/ALL/CERT/WEATHER/',
        'NCFILESHARE_FILE_NAME': 'sample.txt',
        'amqp1_address': 'topic://NCFILESHARE/ALL/CERT/WEATHER/',
        'amqp1_content_type': 'text/plain',
    }

    msg = NavCanada.importMine(b'hello world', headers, None)

    assert msg is not None
    assert msg['_format'] == 'navcanada'
    assert msg['relPath'].endswith('sample.txt')
    assert msg['content']['value'] == 'hello world'
    assert msg['size'] == 11


def test_import_mine_missing_filename():
    assert NavCanada.importMine(
        b'data', {'MSG_PUBLISH_TIME': '2026-08-18T08:13:08Z'}, None
    ) is None


def test_import_mine_invalid_utf8():
    headers = {
        'MSG_PUBLISH_TIME': '2026-08-18T08:13:08Z',
        'NCFILESHARE_FILE_NAME': 'sample.txt',
    }

    assert NavCanada.importMine(b'\xff\xfe', headers, None) is None

def test_export_mine_valid_message():
    msg = {
        'relPath': 'weather/sample.txt',
        'topic': 'weather',
        'mtime': '20260304T205308.000',
        'pubTime': '20260818T081308.399',
        'content': {
            'encoding': 'utf-8',
            'value': 'hello world',
        },
        'size': 11,
    }

    from sarracenia.config.credentials import _urlparse

    options = {
        'publisher_index': 0,
        'publishers': [{
            'broker': type(
                'PublisherConfig', (), {'url': _urlparse('amq1://localhost')}
            )(),
            'topicPrefix': ['topic://ECCC'],
        }],
        'post_topicPrefix': ['topic://ECCC'],

    }

    body, headers, content_type = NavCanada.exportMine(msg, options)

    assert body == 'hello world'
    assert content_type == 'text/plain'
    assert headers['MSG_TYPE'] == NavCanada.MSG_TYPE
    assert headers['MSG_ORIGINATOR'] == 'ECCC'
    assert headers['FILE_NAME'] == 'sample.txt'
    assert headers['MSG_PUBLISH_TIME'] == '2026-08-18T08:13:08.399Z'
    assert headers['FILE_MTIME'] == '2026-03-04T20:53:08.000Z'
    assert headers['DESTINATION'].endswith('/WEATHER/')
