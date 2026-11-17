import pytest
from tests.conftest import *
#from unittest.mock import Mock

import sarracenia.config
import sarracenia.flowcb.poll.odata


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def make_options(timeout=17):
    options = sarracenia.config.default_config()
    options.pollUrl = 'https://example.com/odata/v1/Products?$filter='
    options.post_baseUrl = 'https://example.com/dl/'
    options.publishers.append({'baseUrl': options.post_baseUrl, 'baseDir': None})
    options.dataCollection = None
    options.timeNowMinus = 3600.0
    options.queryString = None
    options.post_urlTemplate = 'Products(--PRODUCT_ID--)/$value'
    options.timeout = timeout
    return options


def test_poll_passes_configured_timeout_including_pagination(mocker):
    """Initial and @odata.nextLink requests must use the configured timeout."""
    options = make_options(timeout=17)
    poll = sarracenia.flowcb.poll.odata.Odata(options)

    page1 = {
        'value': [
            {
                'Id': 'id1',
                'Name': 'file1',
                'ContentLength': 10,
                'Checksum': [{'Algorithm': 'MD5', 'Value': 'abc'}],
                'ContentType': 'application/octet-stream',
                'ModificationDate': '2023-01-01T00:00:00.000Z',
                'GeoFootprint': {'type': 'Polygon', 'coordinates': []},
            }
        ],
        '@odata.nextLink': 'https://example.com/next',
    }
    page2 = {
        'value': [
            {
                'Id': 'id2',
                'Name': 'file2',
                'ContentLength': 20,
                'Checksum': [],
                'ContentType': 'text/plain',
                'ModificationDate': '2023-01-02T00:00:00.000Z',
            }
        ]
    }

    mock_get = mocker.patch(
        'sarracenia.flowcb.poll.odata.requests.get',
        side_effect=[FakeResponse(page1), FakeResponse(page2)])

    gathered = poll.poll()

    assert mock_get.call_count == 2
    assert mock_get.call_args_list[0][0][0].startswith(options.pollUrl)
    assert mock_get.call_args_list[1][0][0] == 'https://example.com/next'
    for call in mock_get.call_args_list:
        assert call[1].get('timeout') == 17
    assert len(gathered) == 2
