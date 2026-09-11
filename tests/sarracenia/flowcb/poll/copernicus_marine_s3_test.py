import pytest
from tests.conftest import *
#from unittest.mock import Mock

import sarracenia.config
import sarracenia.flowcb.poll.copernicus_marine_s3


class FakeStacResponse:
    def __init__(self, payload):
        self._payload = payload

    def __bool__(self):
        return True

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def make_options(timeout=17):
    options = sarracenia.config.default_config()
    options.pollUrl = 'https://stac.example.com/metadata'
    options.post_baseUrl = 'https://example.com/'
    options.publishers.append({'baseUrl': options.post_baseUrl, 'baseDir': None})
    options.productID = ['PROD1']
    options.timeout = timeout
    return options


def test_get_s3_urls_passes_configured_timeout(mocker):
    """Product and dataset STAC requests must use the configured timeout."""
    options = make_options(timeout=17)
    poll = sarracenia.flowcb.poll.copernicus_marine_s3.Copernicus_marine_s3(options)

    product_page = {'links': [{'href': 'DATASET1/dataset.stac.json'}]}
    dataset_page = {
        'assets': {'native': {'href': 'https://s3.example.com/bucket/prefix/file.nc'}}
    }

    mock_get = mocker.patch(
        'sarracenia.flowcb.poll.copernicus_marine_s3.requests.get',
        side_effect=[FakeStacResponse(product_page), FakeStacResponse(dataset_page)])

    s3_urls = poll.get_s3_urls_from_stac(poll.productIDs)

    assert mock_get.call_count == 2
    assert mock_get.call_args_list[0][0][0] == \
        'https://stac.example.com/metadata/PROD1/product.stac.json'
    assert mock_get.call_args_list[1][0][0] == \
        'https://stac.example.com/metadata/PROD1/DATASET1/dataset.stac.json'
    for call in mock_get.call_args_list:
        assert call[1].get('timeout') == 17
    assert s3_urls == {'PROD1': ['https://s3.example.com/bucket/prefix/file.nc']}
