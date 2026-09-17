import pytest
from tests.conftest import *
#from unittest.mock import Mock

import sarracenia.config
import sarracenia.flowcb.poll.nasa_cmr


class FakeCatalogueResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class FakeMd5Response:
    text = 'd41d8cd98f00b204e9800998ecf8427e  file.nc'

    def json(self):
        return {}


def make_options(timeout=17):
    options = sarracenia.config.default_config()
    options.pollUrl = 'https://cmr.earthdata.nasa.gov/search/granules.umm_json'
    options.publishers.append({'baseUrl': 'https://example.com/', 'baseDir': None})
    options.collectionConceptId = ['C123']
    options.dataSource = 'podaac'
    options.timeNowMinus = 3600.0
    options.pageSize = 10
    options.identity_method = 'cod,sha512'
    options.timeout = timeout
    return options


def test_poll_passes_configured_timeout_to_catalogue_and_md5(mocker):
    """Catalogue and MD5 checksum requests must use the configured timeout."""
    options = make_options(timeout=17)
    poll = sarracenia.flowcb.poll.nasa_cmr.Nasa_cmr(options)

    catalogue = {
        'items': [
            {
                'umm': {
                    'RelatedUrls': [
                        {
                            'Type': 'GET DATA',
                            'Description': 'Download data',
                            'URL': 'https://podaac.example.com/data/file.nc',
                        },
                        {
                            'Type': 'EXTENDED METADATA',
                            'Description': 'Download md5 checksum',
                            'URL': 'https://podaac.example.com/data/file.nc.md5',
                        },
                    ]
                }
            }
        ]
    }

    mock_get = mocker.patch(
        'sarracenia.flowcb.poll.nasa_cmr.requests.get',
        side_effect=[FakeCatalogueResponse(catalogue), FakeMd5Response()])

    gathered = poll.poll()

    assert mock_get.call_count == 2
    assert mock_get.call_args_list[0][0][0].startswith(
        'https://cmr.earthdata.nasa.gov/search/granules.umm_json')
    assert mock_get.call_args_list[1][0][0] == \
        'https://podaac.example.com/data/file.nc.md5'
    for call in mock_get.call_args_list:
        assert call[1].get('timeout') == 17
    assert len(gathered) == 1
    assert gathered[0]['identity'] == {
        'method': 'md5',
        'value': 'd41d8cd98f00b204e9800998ecf8427e',
    }
