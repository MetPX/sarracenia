import errno
import logging
from types import SimpleNamespace
from unittest.mock import call, patch, MagicMock

import pytest

import sarracenia
import sarracenia.config
from sarracenia.transfer.sftp import Sftp

logger = logging.getLogger(__name__)


@pytest.fixture
def sftp_options():
    options = sarracenia.config.default_config()
    options.sendTo = 'sftp://testuser@testhost/path'
    options.timeout = 5
    options.credentials = MagicMock()
    url = MagicMock()
    url.hostname = 'testhost'
    url.port = 22
    url.username = 'testuser'
    url.password = 'testpass'
    details = MagicMock()
    details.url = url
    details.ssh_keyfile = None
    options.credentials.get.return_value = (True, details)
    return options


class Test_SftpConnectCleanup:
    """Test that failed SFTP connections close sockets to prevent fd leaks."""

    @patch('sarracenia.transfer.sftp.paramiko.SSHClient')
    def test_connect_failure_closes_ssh(self, mock_ssh_class, sftp_options):
        """When ssh.connect() raises, the SSHClient should be closed."""
        mock_ssh = MagicMock()
        mock_ssh.connect.side_effect = Exception("Connection refused")
        mock_ssh_class.return_value = mock_ssh

        sftp = Sftp('sftp', sftp_options)
        result = sftp.connect()

        assert result is False
        mock_ssh.close.assert_called_once()
        assert sftp.ssh is None

    @patch('sarracenia.transfer.sftp.paramiko.SSHClient')
    def test_connect_auth_failure_closes_ssh(self, mock_ssh_class, sftp_options):
        """When ssh.connect() raises auth error, the SSHClient should be closed."""
        mock_ssh = MagicMock()
        mock_ssh.connect.side_effect = Exception("Authentication failed")
        mock_ssh_class.return_value = mock_ssh

        sftp = Sftp('sftp', sftp_options)
        result = sftp.connect()

        assert result is False
        mock_ssh.close.assert_called_once()

    @patch('sarracenia.transfer.sftp.paramiko.SSHClient')
    def test_connect_success_does_not_close(self, mock_ssh_class, sftp_options):
        """Successful connect should not close the connection."""
        mock_ssh = MagicMock()
        mock_sftp_channel = MagicMock()
        mock_sftp_channel.getcwd.return_value = '/home/testuser'
        mock_ssh.open_sftp.return_value = mock_sftp_channel
        mock_ssh_class.return_value = mock_ssh

        sftp = Sftp('sftp', sftp_options)
        result = sftp.connect()

        assert result is True
        mock_ssh.close.assert_not_called()
        assert sftp.connected is True

    @patch('sarracenia.transfer.sftp.paramiko.SSHClient')
    def test_repeated_connect_failures_no_fd_leak(self, mock_ssh_class, sftp_options):
        """Multiple failed connect attempts should each close their ssh client."""
        mock_ssh_instances = [MagicMock() for _ in range(5)]
        for m in mock_ssh_instances:
            m.connect.side_effect = Exception("Connection refused")

        sftp = Sftp('sftp', sftp_options)

        for i in range(5):
            mock_ssh_class.side_effect = [mock_ssh_instances[i]]
            result = sftp.connect()
            assert result is False

        for m in mock_ssh_instances:
            m.close.assert_called_once()


class TestSftpMultipartPut:

    @staticmethod
    def make_transfer():
        transfer = Sftp.__new__(Sftp)
        transfer.o = SimpleNamespace(timeout=5, bufSize=8192, nofsetstat=False)
        transfer.sftp = MagicMock()
        transfer.compat_mode = False
        transfer.readlocal_write = MagicMock(return_value=4)
        return transfer

    @patch('sarracenia.transfer.sftp.alarm_cancel')
    @patch('sarracenia.transfer.sftp.alarm_set')
    def test_transient_stat_failure_does_not_open_target(self, _alarm_set, _alarm_cancel):
        transfer = self.make_transfer()
        transient_error = OSError(errno.EIO, 'temporary server failure')
        transfer.sftp.stat.side_effect = transient_error

        with pytest.raises(OSError) as raised:
            transfer.put({}, 'part.bin', 'target.bin', remote_offset=4, length=4)

        assert raised.value is transient_error
        transfer.sftp.file.assert_not_called()
        transfer.readlocal_write.assert_not_called()

    @patch('sarracenia.transfer.sftp.alarm_cancel')
    @patch('sarracenia.transfer.sftp.alarm_set')
    def test_missing_target_is_created_before_multipart_update(self, _alarm_set, _alarm_cancel):
        transfer = self.make_transfer()
        transfer.sftp.stat.side_effect = FileNotFoundError(errno.ENOENT, 'missing')
        create_handle = MagicMock()
        update_handle = MagicMock()
        transfer.sftp.file.side_effect = [create_handle, update_handle]

        written = transfer.put({}, 'part.bin', 'target.bin', remote_offset=4, length=4)

        assert written == 4
        assert transfer.sftp.file.call_args_list == [
            call('target.bin', 'wb', 8192),
            call('target.bin', 'r+b', 8192),
        ]
        create_handle.close.assert_called_once_with()
        update_handle.seek.assert_called_once_with(4, 0)
        transfer.readlocal_write.assert_called_once_with('part.bin', 0, 4, update_handle)
