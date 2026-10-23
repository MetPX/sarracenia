import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

import sarracenia.config
import sarracenia.transfer

FULL_SIZE = 300000
PAYLOAD = (bytes(range(256)) * (FULL_SIZE // 256 + 1))[:FULL_SIZE]

# share of the announced Content-Length each path actually sends before closing.
SENT_SHARE = {'/complete': 1, '/truncated': 1 / 3, '/empty': 0}


class ShortBodyHandler(BaseHTTPRequestHandler):
    """
    Announce Content-Length, then close the connection after sending only part
    of it, like a server or CDN edge dropping a transfer part way through.
    A Range request gets a 206 with the Content-Length of the range.
    """

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/chunked':
            # Content-Length is ignored when Transfer-Encoding is set.
            self.send_response(200)
            self.send_header('Transfer-Encoding', 'chunked')
            self.send_header('Content-Length', str(FULL_SIZE * 2))
            self.end_headers()
            self.wfile.write(b'%x\r\n%s\r\n0\r\n\r\n' % (FULL_SIZE, PAYLOAD))
            return

        if self.path == '/no-length':
            # body ends when the connection closes, nothing to check against.
            self.send_response(200)
            self.end_headers()
            self.wfile.write(PAYLOAD)
            return

        if self.path not in SENT_SHARE:
            self.send_error(404)
            return

        body = PAYLOAD
        if 'Range' in self.headers:
            first, last = self.headers['Range'].split('=')[1].split('-')
            body = PAYLOAD[int(first):int(last) + 1]
            self.send_response(206)
            self.send_header('Content-Range',
                             'bytes %s-%s/%d' % (first, last, FULL_SIZE))
        else:
            self.send_response(200)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body[:int(len(body) * SENT_SHARE[self.path])])


@pytest.fixture
def transfer():
    server = HTTPServer(('127.0.0.1', 0), ShortBodyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
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
    pytest.param('complete', 0, 0, False, FULL_SIZE, id='no size, complete'),
    pytest.param('truncated', 0, 0, False, -1, id='no size, truncated'),
    pytest.param('empty', 0, 0, False, -1, id='no size, empty body'),
    pytest.param('chunked', 0, 0, False, FULL_SIZE, id='chunked'),
    pytest.param('no-length', 0, 0, False, FULL_SIZE, id='no Content-Length'),
    # a wrong size in the message is for acceptSizeWrong in Flow.download() to judge.
    pytest.param('complete', 0, FULL_SIZE + 10, False, FULL_SIZE,
                 id='wrong message size'),
    # inplace block after the first: Range request, 206 reply.
    pytest.param('complete', 1000, 5000, True, 5000, id='206, complete'),
    pytest.param('truncated', 1000, 5000, True, -1, id='206, truncated'),
    # first inplace block: no Range header, so the server sends the whole file
    # and read_write() stops at the block length on purpose.
    pytest.param('complete', 0, 5000, True, 5000, id='first block, complete'),
    pytest.param('truncated', 0, 200000, True, -1, id='first block, truncated'),
])
def test_get_checks_content_length(transfer, tmp_path, remote_file, remote_offset,
                                   length, exactLength, expected):
    local_file = str(tmp_path / remote_file)

    assert transfer.get({}, remote_file, local_file, remote_offset, 0, length,
                        exactLength) == expected

    if expected > 0:
        with open(local_file, 'rb') as f:
            assert f.read() == PAYLOAD[remote_offset:remote_offset + expected]
