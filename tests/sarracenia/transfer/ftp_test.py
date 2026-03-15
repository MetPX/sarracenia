import pytest
from unittest.mock import patch, MagicMock

import logging

import sarracenia
import sarracenia.config
from sarracenia.transfer.ftp import Ftp

logger = logging.getLogger(__name__)


@pytest.fixture
def ftp_options():
    options = sarracenia.config.default_config()
    options.sendTo = 'ftp://testuser@testhost/path'
    options.timeout = 5
    options.credentials = MagicMock()
    url = MagicMock()
    url.hostname = 'testhost'
    url.port = 21
    url.username = 'testuser'
    url.password = 'testpass'
    details = MagicMock()
    details.url = url
    details.ssh_keyfile = None
    details.passive = True
    details.binary = True
    details.tls = False
    details.prot_p = False
    details.implicit_ftps = False
    options.credentials.get.return_value = (True, details)
    return options


class Test_FtpConnectCleanup:
    """Test that failed FTP connections close sockets to prevent fd leaks."""

    @patch('sarracenia.transfer.ftp.ftplib.FTP')
    def test_connect_failure_closes_ftp(self, mock_ftp_class, ftp_options):
        """When ftp.login() raises, the FTP connection should be closed."""
        mock_ftp = MagicMock()
        mock_ftp.login.side_effect = Exception("Login failed")
        mock_ftp_class.return_value = mock_ftp

        ftp = Ftp('ftp', ftp_options)
        result = ftp.connect()

        assert result is False
        mock_ftp.close.assert_called_once()

    @patch('sarracenia.transfer.ftp.ftplib.FTP')
    def test_connect_network_failure_closes_ftp(self, mock_ftp_class, ftp_options):
        """When ftp.connect() raises, the FTP object should be closed."""
        mock_ftp = MagicMock()
        mock_ftp.connect.side_effect = Exception("Connection refused")
        mock_ftp_class.return_value = mock_ftp

        ftp = Ftp('ftp', ftp_options)
        result = ftp.connect()

        assert result is False
        mock_ftp.close.assert_called_once()
