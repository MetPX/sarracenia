import types

import pytest
from tests.conftest import *
#from unittest.mock import Mock

import sarracenia.config
import sarracenia.flowcb.poll.usgs


def make_options(stations, batch, timeout=17):
    options = sarracenia.config.default_config()
    options.pollUrl = 'https://example.com/?site={0:}'
    options.post_baseUrl = 'https://example.com/files/'
    options.publishers.append({'baseUrl': options.post_baseUrl, 'baseDir': None})
    options.poll_usgs_station = stations
    options.batch = batch
    options.timeout = timeout
    options.msg = types.SimpleNamespace(new_baseurl=None)
    return options


def check_urlopen_calls(mock_urlopen, timeout):
    assert mock_urlopen.call_count == 1
    for call in mock_urlopen.call_args_list:
        assert call[1].get('timeout') == timeout


def test_poll_single_station_passes_configured_timeout(mocker):
    """One-at-a-time station requests must use the configured timeout."""
    options = make_options(
        stations=['7|70026|9014087|Dry Dock, MI|US|MI|-5.0'], batch=1, timeout=17)
    poll = sarracenia.flowcb.poll.usgs.Usgs(options)

    fake_response = mocker.MagicMock()
    fake_response.getcode.return_value = 200
    mock_urlopen = mocker.patch(
        'sarracenia.flowcb.poll.usgs.urllib.request.urlopen',
        return_value=fake_response)

    gathered = poll.poll()

    check_urlopen_calls(mock_urlopen, 17)
    assert mock_urlopen.call_args_list[0][0][0] == 'https://example.com/?site=9014087'
    assert len(gathered) == 1


def test_poll_batched_stations_passes_configured_timeout(mocker):
    """Batched station requests must use the configured timeout."""
    options = make_options(
        stations=[
            '7|70026|9014087|Site A|US|MI|-5.0',
            '7|70027|9014088|Site B|US|MI|-5.0',
        ],
        batch=2,
        timeout=17)
    poll = sarracenia.flowcb.poll.usgs.Usgs(options)

    fake_response = mocker.MagicMock()
    fake_response.getcode.return_value = 200
    mock_urlopen = mocker.patch(
        'sarracenia.flowcb.poll.usgs.urllib.request.urlopen',
        return_value=fake_response)

    gathered = poll.poll()

    check_urlopen_calls(mock_urlopen, 17)
    assert mock_urlopen.call_args_list[0][0][0] == \
        'https://example.com/?site=9014087,9014088'
    assert len(gathered) == 1
