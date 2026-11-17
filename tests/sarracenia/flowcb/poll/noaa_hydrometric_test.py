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


def test_poll_logs_and_skips_requests_that_time_out(mocker, caplog):
    """A timed out water temperature or water level request is logged and skipped."""
    import socket
    import urllib.error
    options = make_options(timeout=17)
    poll = sarracenia.flowcb.poll.noaa_hydrometric.Noaa_hydrometric(options)
    del poll.o.poll_noaa_stn_file

    def fake_urlopen(url, timeout=None):
        if 'stationsXML' in url:
            return io.BytesIO(STATIONS_XML)
        if 'station=111' in url and 'water_temperature' in url:
            raise urllib.error.URLError(socket.timeout('timed out'))
        if 'station=222' in url and 'water_level' in url:
            raise socket.timeout('timed out')
        response = mocker.MagicMock()
        response.getcode.return_value = 200
        return response

    mocker.patch('sarracenia.flowcb.poll.noaa_hydrometric.urllib.request.urlopen', side_effect=fake_urlopen)

    gathered = poll.poll()

    # each site loses only the request that timed out: 111 keeps its water level, 222 its water temperature.
    assert [m['new_file'].split('_', 3)[-1] for m in gathered] == ['111_WL.csv', '222_WT.csv']
    errors = [r.getMessage() for r in caplog.records if r.levelname == 'ERROR']
    assert len(errors) == 2
    assert all('timed out' in e for e in errors)


def test_poll_logs_and_returns_nothing_when_station_list_times_out(mocker, caplog):
    import socket
    options = make_options(timeout=17)
    poll = sarracenia.flowcb.poll.noaa_hydrometric.Noaa_hydrometric(options)
    del poll.o.poll_noaa_stn_file

    mocker.patch('sarracenia.flowcb.poll.noaa_hydrometric.urllib.request.urlopen',
                 side_effect=socket.timeout('timed out'))

    assert poll.poll() == []
    errors = [r.getMessage() for r in caplog.records if r.levelname == 'ERROR']
    assert any('stationsXML' in e and 'timed out' in e for e in errors)


def test_poll_logs_and_skips_an_http_error(mocker, caplog):
    import urllib.error
    options = make_options(timeout=17)
    poll = sarracenia.flowcb.poll.noaa_hydrometric.Noaa_hydrometric(options)
    del poll.o.poll_noaa_stn_file

    def fake_urlopen(url, timeout=None):
        if 'stationsXML' in url:
            return io.BytesIO(STATIONS_XML)
        if 'station=111' in url:
            raise urllib.error.HTTPError(url, 503, 'Service Unavailable', {}, None)
        response = mocker.MagicMock()
        response.getcode.return_value = 200
        return response

    mocker.patch('sarracenia.flowcb.poll.noaa_hydrometric.urllib.request.urlopen', side_effect=fake_urlopen)

    gathered = poll.poll()

    assert [m['new_file'].split('_', 3)[-1] for m in gathered] == ['222_WT.csv', '222_WL.csv']
    errors = [r.getMessage() for r in caplog.records if r.levelname == 'ERROR']
    assert len(errors) == 2
    assert all('503' in e for e in errors)
