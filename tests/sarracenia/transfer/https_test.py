import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

import sarracenia.config
import sarracenia.transfer

FULL_SIZE = 300000
PAYLOAD = (bytes(range(256)) * (FULL_SIZE // 256 + 1))[:FULL_SIZE]

# share of the body each path sends before the connection closes.
SENT_SHARE = {'/truncated': 1 / 3, '/empty': 0}


class ShortBodyHandler(BaseHTTPRequestHandler):
    """
    Announce Content-Length, then close the connection after sending only part
    of the body, like a server or CDN edge dropping a transfer part way through.
    /no-length sends no Content-Length, so the body just ends at the close.
    """

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        # older http.server keeps the leading // that Https.get() sends.
        path = '/' + self.path.lstrip('/')
        body = PAYLOAD
        if 'Range' in self.headers:
            first, last = self.headers['Range'].split('=')[1].split('-')
            body = PAYLOAD[int(first):int(last) + 1]
            self.send_response(206)
        else:
            self.send_response(200)
        if path != '/no-length':
            self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body[:int(len(body) * SENT_SHARE.get(path, 1))])


@pytest.fixture
def transfer():
    server = HTTPServer(('127.0.0.1', 0), ShortBodyHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        options = sarracenia.config.default_config()
        options.sendTo = 'http://127.0.0.1:%d' % server.server_address[1]
        transfer = sarracenia.transfer.Transfer.factory('https', options)
        transfer.connect()
        transfer.cd('/')
        yield transfer
        transfer.close()
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.parametrize('remote_file, remote_offset, length, exactLength, expected', [
    # message with no size: read until the server closes.
    pytest.param('complete', 0, 0, False, FULL_SIZE, id='complete'),
    pytest.param('truncated', 0, 0, False, -1, id='truncated'),
    pytest.param('empty', 0, 0, False, -1, id='empty body'),
    pytest.param('no-length', 0, 0, False, FULL_SIZE, id='no Content-Length'),
    # a wrong size in the message is for acceptSizeWrong in Flow.download() to judge.
    pytest.param('complete', 0, FULL_SIZE + 10, False, FULL_SIZE, id='wrong size'),
    # inplace block after the first: Range request, 206 reply.
    pytest.param('complete', 1000, 5000, True, 5000, id='206 complete'),
    pytest.param('truncated', 1000, 5000, True, -1, id='206 truncated'),
    # first inplace block: no Range header, so the reply is the whole file and
    # read_write() stops at the block length on purpose.
    pytest.param('complete', 0, 5000, True, 5000, id='first block complete'),
    pytest.param('truncated', 0, 200000, True, -1, id='first block truncated'),
])
def test_get_checks_content_length(transfer, tmp_path, remote_file, remote_offset,
                                   length, exactLength, expected):
    local_file = str(tmp_path / remote_file)

    assert transfer.get({}, remote_file, local_file, remote_offset, 0, length,
                        exactLength) == expected

    if expected > 0:
        with open(local_file, 'rb') as f:
            assert f.read() == PAYLOAD[remote_offset:remote_offset + expected]
