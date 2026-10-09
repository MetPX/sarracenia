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


def test_poll_logs_and_skips_a_site_that_times_out(mocker, caplog):
    """A timed out station request is logged and the next station is still polled."""
    import socket
    options = make_options(
        stations=['7|70026|9014087|Site A|US|MI|-5.0', '7|70027|9014088|Site B|US|MI|-5.0'],
        batch=1, timeout=17)
    poll = sarracenia.flowcb.poll.usgs.Usgs(options)

    def fake_urlopen(url, timeout=None):
        if url.endswith('9014087'):
            raise socket.timeout('timed out')
        response = mocker.MagicMock()
        response.getcode.return_value = 200
        return response

    mocker.patch('sarracenia.flowcb.poll.usgs.urllib.request.urlopen', side_effect=fake_urlopen)

    gathered = poll.poll()

    assert len(gathered) == 1
    errors = [r.getMessage() for r in caplog.records if r.levelname == 'ERROR']
    assert any('9014087' in e and 'timed out' in e for e in errors)


def test_poll_logs_and_skips_a_batch_that_times_out(mocker, caplog):
    import socket
    options = make_options(
        stations=['7|70026|9014087|Site A|US|MI|-5.0', '7|70027|9014088|Site B|US|MI|-5.0',
                  '7|70028|9014089|Site C|US|MI|-5.0'],
        batch=2, timeout=17)
    poll = sarracenia.flowcb.poll.usgs.Usgs(options)

    def fake_urlopen(url, timeout=None):
        if '9014087' in url:
            raise socket.timeout('timed out')
        response = mocker.MagicMock()
        response.getcode.return_value = 200
        return response

    mocker.patch('sarracenia.flowcb.poll.usgs.urllib.request.urlopen', side_effect=fake_urlopen)

    gathered = poll.poll()

    assert len(gathered) == 1
    errors = [r.getMessage() for r in caplog.records if r.levelname == 'ERROR']
    assert any('9014087,9014088' in e and 'timed out' in e for e in errors)


def test_poll_stops_when_usgs_blocks_the_ip(mocker, caplog):
    """urlopen raises HTTPError for a 403: log the blocked-IP message and stop polling this cycle."""
    import urllib.error
    options = make_options(
        stations=['7|70026|9014087|Site A|US|MI|-5.0', '7|70027|9014088|Site B|US|MI|-5.0'],
        batch=1, timeout=17)
    poll = sarracenia.flowcb.poll.usgs.Usgs(options)

    mock_urlopen = mocker.patch(
        'sarracenia.flowcb.poll.usgs.urllib.request.urlopen',
        side_effect=urllib.error.HTTPError('https://example.com/?site=9014087', 403, 'Forbidden', {}, None))

    assert poll.poll() == []
    assert mock_urlopen.call_count == 1
    errors = [r.getMessage() for r in caplog.records if r.levelname == 'ERROR']
    assert any('blocked your IP' in e for e in errors)


def test_poll_stops_when_usgs_blocks_the_ip_in_batch_mode(mocker, caplog):
    import urllib.error
    options = make_options(
        stations=['7|70026|9014087|Site A|US|MI|-5.0', '7|70027|9014088|Site B|US|MI|-5.0',
                  '7|70028|9014089|Site C|US|MI|-5.0', '7|70029|9014090|Site D|US|MI|-5.0',
                  '7|70030|9014091|Site E|US|MI|-5.0'],
        batch=2, timeout=17)
    poll = sarracenia.flowcb.poll.usgs.Usgs(options)

    def fake_urlopen(url, timeout=None):
        if '9014089' in url:
            raise urllib.error.HTTPError(url, 403, 'Forbidden', {}, None)
        response = mocker.MagicMock()
        response.getcode.return_value = 200
        return response

    mock_urlopen = mocker.patch('sarracenia.flowcb.poll.usgs.urllib.request.urlopen', side_effect=fake_urlopen)

    gathered = poll.poll()

    # the first batch is kept, the second gets the 403, the third is never asked for.
    assert len(gathered) == 1
    assert mock_urlopen.call_count == 2
    errors = [r.getMessage() for r in caplog.records if r.levelname == 'ERROR']
    assert any('blocked your IP' in e for e in errors)


def test_poll_logs_and_skips_a_site_with_another_http_error(mocker, caplog):
    import urllib.error
    options = make_options(
        stations=['7|70026|9014087|Site A|US|MI|-5.0', '7|70027|9014088|Site B|US|MI|-5.0'],
        batch=1, timeout=17)
    poll = sarracenia.flowcb.poll.usgs.Usgs(options)

    def fake_urlopen(url, timeout=None):
        if url.endswith('9014087'):
            raise urllib.error.HTTPError(url, 503, 'Service Unavailable', {}, None)
        response = mocker.MagicMock()
        response.getcode.return_value = 200
        return response

    mocker.patch('sarracenia.flowcb.poll.usgs.urllib.request.urlopen', side_effect=fake_urlopen)

    gathered = poll.poll()

    assert len(gathered) == 1
    errors = [r.getMessage() for r in caplog.records if r.levelname == 'ERROR']
    assert any('9014087' in e and '503' in e for e in errors)
