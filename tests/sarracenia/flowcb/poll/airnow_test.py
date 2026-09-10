import pytest
from tests.conftest import *
#from unittest.mock import Mock

import sarracenia.config
import sarracenia.flowcb.poll.airnow


class FakeResponse:
    ok = True
    headers = {
        'last-modified': 'Wed, 10 Sep 2026 16:00:00 GMT',
        'content-length': '123',
    }


def make_options(timeout=17):
    options = sarracenia.config.default_config()
    options.pollUrl = 'https://example.com/airnow'
    options.post_baseUrl = 'https://example.com/airnow'
    options.publishers.append({'baseUrl': options.post_baseUrl, 'baseDir': None})
    options.scheduled_interval = 60
    options.timeout = timeout
    return options


def test_poll_passes_configured_timeout(mocker):
    """Hourly file requests must use the configured timeout."""
    options = make_options(timeout=17)
    poll = sarracenia.flowcb.poll.airnow.Airnow(options)

    mock_get = mocker.patch(
        'sarracenia.flowcb.poll.airnow.requests.get', return_value=FakeResponse())

    gathered = poll.poll()

    # the poll checks the last two hourly files.
    assert mock_get.call_count == 2
    for call in mock_get.call_args_list:
        assert call[1].get('timeout') == 17
    assert len(gathered) == 2
