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


def test_poll_logs_and_skips_a_request_that_times_out(mocker, caplog):
    """A timed out browse or detail request is logged and skipped, the rest of the poll goes on."""
    options = make_options(timeout=17)
    poll = sarracenia.flowcb.poll.eumetsat.Eumetsat(options)

    browse_payload = {
        'products': [
            {'links': [{'title': 'Product details', 'href': 'https://example.com/detail/1'}]},
            {'links': [{'title': 'Product details', 'href': 'https://example.com/detail/2'}]},
        ]
    }
    detail_payload = {
        'properties': {
            'updated': '2023-12-29T02:06:33.451Z',
            'links': {'data': [{'href': options.post_baseUrl + 'EO/file.nc/entry?name=file.nc',
                                'mediaType': 'application/x-netcdf'}]},
        }
    }
    browse_calls = []

    def fake_get(url, **kwargs):
        if url.endswith('/detail/1'):
            raise sarracenia.flowcb.poll.eumetsat.requests.exceptions.ReadTimeout('Read timed out.')
        if 'detail' in url:
            return FakeResponse(detail_payload)
        browse_calls.append(url)
        if len(browse_calls) == 1:
            raise sarracenia.flowcb.poll.eumetsat.requests.exceptions.ConnectTimeout('Connect timed out.')
        return FakeResponse(browse_payload)

    mocker.patch('sarracenia.flowcb.poll.eumetsat.requests.get', side_effect=fake_get)

    gathered = poll.poll()

    # the first browse hour timed out, the second one listed two products, of which detail/1 timed out.
    assert len(gathered) == 1
    errors = [r.getMessage() for r in caplog.records if r.levelname == 'ERROR']
    assert any('Connect timed out' in e and 'skipping this hour' in e for e in errors)
    assert any('/detail/1' in e and 'Read timed out' in e for e in errors)


def test_poll_logs_and_skips_a_details_page_that_is_not_json(mocker, caplog):
    """An html error page instead of json is logged and skipped, not a crash."""
    import json
    options = make_options(timeout=17)
    poll = sarracenia.flowcb.poll.eumetsat.Eumetsat(options)

    browse_payload = {'products': [{'links': [{'title': 'Product details', 'href': 'https://example.com/detail/1'}]}]}

    class HtmlResponse:
        def json(self):
            raise json.JSONDecodeError('Expecting value', '<html>', 0)

    def fake_get(url, **kwargs):
        if 'detail' in url:
            return HtmlResponse()
        return FakeResponse(browse_payload)

    mocker.patch('sarracenia.flowcb.poll.eumetsat.requests.get', side_effect=fake_get)

    assert poll.poll() == []
    errors = [r.getMessage() for r in caplog.records if r.levelname == 'ERROR']
    assert any('/detail/1' in e and 'skipping this product' in e for e in errors)


def test_poll_logs_and_skips_a_browse_page_that_is_not_json(mocker, caplog):
    """A 200 whose body is html (maintenance page) is logged and skipped, not a crash."""
    import json
    options = make_options(timeout=17)
    poll = sarracenia.flowcb.poll.eumetsat.Eumetsat(options)

    class HtmlResponse:
        def __bool__(self):
            return True

        def json(self):
            raise json.JSONDecodeError('Expecting value', '<html>', 0)

    mocker.patch('sarracenia.flowcb.poll.eumetsat.requests.get', return_value=HtmlResponse())

    assert poll.poll() == []
    errors = [r.getMessage() for r in caplog.records if r.levelname == 'ERROR']
    assert len(errors) == 2
    assert all('Expecting value' in e and 'skipping this hour' in e for e in errors)
