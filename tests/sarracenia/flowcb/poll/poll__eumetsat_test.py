import pytest
from tests.conftest import *
#from unittest.mock import Mock

import sarracenia.config
import sarracenia.flowcb.poll.eumetsat


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def __bool__(self):
        return True

    def json(self):
        return self._payload


def make_options(timeout=17):
    options = sarracenia.config.default_config()
    options.pollUrl = 'https://example.com/browse/collections/'
    options.post_baseUrl = 'https://example.com/download/1.0.0/collections/'
    options.publishers.append({'baseUrl': options.post_baseUrl, 'baseDir': None})
    options.collectionId = ['EO:EUM:DAT:0412']
    options.acceptMediaType = ['application/x-netcdf']
    options.timeNowMinus = 3600.0
    options.timeout = timeout
    return options


def test_poll_passes_configured_timeout(mocker):
    """Browse and detail requests must use the configured timeout."""
    options = make_options(timeout=17)
    poll = sarracenia.flowcb.poll.eumetsat.Eumetsat(options)

    browse_payload = {
        'products': [
            {'links': [{'title': 'Product details', 'href': 'https://example.com/detail/1'}]}
        ]
    }
    detail_payload = {
        'properties': {
            'updated': '2023-12-29T02:06:33.451Z',
            'links': {
                'data': [
                    {
                        'href': options.post_baseUrl + 'EO/file.nc/entry?name=file.nc',
                        'mediaType': 'application/x-netcdf',
                    }
                ]
            },
        }
    }

    def fake_get(url, **kwargs):
        if 'detail' in url:
            return FakeResponse(detail_payload)
        return FakeResponse(browse_payload)

    mock_get = mocker.patch(
        'sarracenia.flowcb.poll.eumetsat.requests.get', side_effect=fake_get)

    gathered = poll.poll()

    # n_hours is 2 here, so two browse calls plus one detail call per product.
    assert mock_get.call_count == 4
    for call in mock_get.call_args_list:
        assert call[1].get('timeout') == 17
    assert len(gathered) == 2
