import pytest
from tests.conftest import *
from unittest.mock import Mock, patch, MagicMock

import logging

import sarracenia
import sarracenia.config
import sarracenia.transfer
import sarracenia.transfer.sftp

logger = logging.getLogger(__name__)


class Test_SftpFileHandleLeak:
    """
    Regression tests for https://github.com/MetPX/sarracenia/issues/1559

    SFTP put() and get() leaked remote file handles when readlocal_write()
    or read_writelocal() raised an exception during data transfer.
    Each failed retry leaked a handle, eventually causing
    OSError: [Errno 24] Too many open files.

    The fix wraps the read/write calls in try/finally to ensure rfp.close()
    is always called.
    """

    def _make_sftp_transfer(self):
        options = sarracenia.config.default_config()
        options.timeout = 300
        options.bufSize = 8192
        options.nofsetstat = False
        options.sendTo = 'sftp://user@localhost/'
        transfer = sarracenia.transfer.sftp.Sftp('sftp', options)
        transfer.sftp = Mock()
        transfer.connected = True
        return transfer

    def test_put_closes_handle_on_write_failure(self):
        """put() must close the remote file handle even when
        readlocal_write() raises an exception."""

        transfer = self._make_sftp_transfer()

        mock_rfp = Mock()
        transfer.sftp.file.return_value = mock_rfp

        with patch.object(transfer, 'readlocal_write',
                          side_effect=IOError("connection lost")):
            with pytest.raises(IOError):
                transfer.put(Mock(), '/local/file', '/remote/file')

        mock_rfp.close.assert_called_once()

    def test_get_closes_handle_on_read_failure(self):
        """get() must close the remote file handle even when
        read_writelocal() raises an exception."""

        transfer = self._make_sftp_transfer()

        mock_rfp = Mock()
        transfer.sftp.file.return_value = mock_rfp

        with patch.object(transfer, 'read_writelocal',
                          side_effect=IOError("connection lost")):
            with pytest.raises(IOError):
                transfer.get(Mock(), '/remote/file', '/local/file')

        mock_rfp.close.assert_called_once()
