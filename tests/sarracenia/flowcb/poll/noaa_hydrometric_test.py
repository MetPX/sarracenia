import io

import pytest
from tests.conftest import *
#from unittest.mock import Mock

import sarracenia.config
import sarracenia.flowcb.poll.noaa_hydrometric

STATIONS_XML = (
    b'<?xml version="1.0"?>'
    b'<stations><station ID="111"/><station ID="222"/></stations>'
)


def make_options(timeout=17):
    options = sarracenia.config.default_config()
    options.pollUrl = 'https://example.com/api/'
    options.post_baseUrl = 'https://example.com/api/'
    options.publishers.append({'baseUrl': options.post_baseUrl, 'baseDir': None})
    options.identity_method = 'cod,testval'
    options.retrievePathPattern = (
        'datagetter?range=1&station={0:}&product={1:}'
        '&units=metric&time_zone=gmt&application=web_services&format=csv'
    )
    options.timeout = timeout
    return options


def test_poll_passes_configured_timeout_to_all_requests(mocker):
    """Station list, water temperature, and water level requests must use
    the configured timeout."""
    options = make_options(timeout=17)
    poll = sarracenia.flowcb.poll.noaa_hydrometric.Noaa_hydrometric(options)
    # add_option declares poll_noaa_stn_file with a None default, which makes
    # hasattr() true and hides the station-list branch. Remove it so the poll
    # takes the stationsXML branch like a config without that option.
    del poll.o.poll_noaa_stn_file

    def fake_urlopen(url, timeout=None):
        if 'stationsXML' in url:
            return io.BytesIO(STATIONS_XML)
        response = mocker.MagicMock()
        response.getcode.return_value = 200
        return response

    mock_urlopen = mocker.patch(
        'sarracenia.flowcb.poll.noaa_hydrometric.urllib.request.urlopen',
        side_effect=fake_urlopen)

    gathered = poll.poll()

    urls = [call[0][0] for call in mock_urlopen.call_args_list]
    assert 'https://opendap.co-ops.nos.noaa.gov/stations/stationsXML.jsp' in urls
    assert any('product=water_temperature' in url for url in urls)
    assert any('product=water_level' in url for url in urls)
    for call in mock_urlopen.call_args_list:
        assert call[1].get('timeout') == 17
    # two stations, each posting a water temperature and a water level file.
    assert len(gathered) == 4
