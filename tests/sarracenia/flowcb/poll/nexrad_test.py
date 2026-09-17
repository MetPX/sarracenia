import io

import pytest
from tests.conftest import *
#from unittest.mock import Mock

import sarracenia.config
import sarracenia.flowcb.poll.nexrad


def make_station_line(icao):
    # the poll keeps lines longer than 80 chars that end with US,
    # with an X at index 65 and the ICAO at index 20:24.
    line = 'X' * 20 + icao + 'Y' * 41 + 'X' + 'Z' * 14 + 'US\n'
    assert len(line) > 80
    assert line[65] == 'X'
    assert line.endswith('US\n')
    return line


class FakeStationsResponse:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return io.BytesIO(self._payload)

    def __exit__(self, *args):
        return False


def make_options(timeout=17):
    options = sarracenia.config.default_config()
    options.pollUrl = 'https://example.com/'
    options.post_baseUrl = 'https://example.com/'
    options.publishers.append({'baseUrl': options.post_baseUrl, 'baseDir': None})
    options.poll_nexrad_day = ''
    options.timeout = timeout
    return options


def test_poll_passes_configured_timeout_to_station_list(mocker):
    """The aviationweather station list request must use the configured timeout."""
    options = make_options(timeout=17)
    poll = sarracenia.flowcb.poll.nexrad.Nexrad(options)
    poll.metrics = {'transferRxBytes': 0}

    payload = (make_station_line('KARX') + 'short line\n').encode()
    mock_urlopen = mocker.patch(
        'sarracenia.flowcb.poll.nexrad.urllib.request.urlopen',
        return_value=FakeStationsResponse(payload))
    fake_s3 = mocker.MagicMock()

    def fake_list_objects(**kwargs):
        if '/KARX/' in kwargs['Prefix']:
            return {'Contents': [{'Key': '2026/01/01/KARX/KARXfile', 'Size': 123}]}
        return {}

    fake_s3.list_objects.side_effect = fake_list_objects
    mocker.patch(
        'sarracenia.flowcb.poll.nexrad.boto3.client', return_value=fake_s3)

    gathered = poll.poll()

    assert mock_urlopen.call_count == 1
    assert mock_urlopen.call_args[0][0] == \
        'https://www.aviationweather.gov/docs/metar/stations.txt'
    assert mock_urlopen.call_args[1].get('timeout') == 17
    assert len(gathered) == 1
