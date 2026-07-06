import ftplib
from unittest.mock import MagicMock, patch

import pytest

from sarracenia.transfer.ftp import Ftp


class MockOptions:

    def __init__(self):
        self.sendTo = "ftp://user:pass@localhost/"
        self.timeout = 30
        self.logLevel = "DEBUG"
        self.logFormat = ""
        self.batch = 100
        self.byteRateMax = 0
        self.bufSize = 8192
        self.ftpFilenameEncoding = "utf-8"
        self.tlsRigour = "normal"
        self.credentials = MagicMock()

    def add_option(self, option, kind, default=None):
        if not hasattr(self, option):
            setattr(self, option, default)


def make_ftp_transfer():
    options = MockOptions()
    options.credentials.get.return_value = (
        True,
        MagicMock(
            url=MagicMock(
                hostname="localhost",
                port=21,
                username="user",
                password="pass",
            ),
            tls=False,
            prot_p=False,
            passive=True,
            binary=True,
            implicit_ftps=False,
        ),
    )
    transfer = Ftp.__new__(Ftp)
    transfer.o = options
    transfer.connected = False
    transfer.ftp = None
    transfer.sendTo = options.sendTo
    transfer.host = "localhost"
    transfer.port = 21
    transfer.user = "user"
    transfer.password = "pass"
    transfer.tls = False
    transfer.implicit_ftps = False
    transfer.prot_p = False
    transfer.passive = True
    transfer.binary = True
    transfer.originalDir = "."
    transfer.pwd = "."
    return transfer


def test_connect_closes_ftp_on_login_failure():
    transfer = make_ftp_transfer()

    mock_ftp = MagicMock(spec=ftplib.FTP)
    mock_ftp.connect.return_value = None
    mock_ftp.login.side_effect = ftplib.error_perm("530 Login incorrect")

    with patch("ftplib.FTP", return_value=mock_ftp):
        with patch("sarracenia.transfer.ftp.alarm_set"):
            with patch("sarracenia.transfer.ftp.alarm_cancel"):
                result = transfer.connect()

    assert result is False
    assert transfer.connected is False
    mock_ftp.close.assert_called_once()


def test_connect_closes_ftp_on_connect_failure():
    transfer = make_ftp_transfer()

    mock_ftp = MagicMock(spec=ftplib.FTP)
    mock_ftp.connect.side_effect = OSError("Connection refused")

    with patch("ftplib.FTP", return_value=mock_ftp):
        with patch("sarracenia.transfer.ftp.alarm_set"):
            with patch("sarracenia.transfer.ftp.alarm_cancel"):
                result = transfer.connect()

    assert result is False
    assert transfer.connected is False
    mock_ftp.close.assert_called_once()


def test_connect_closes_ftp_on_set_pasv_failure():
    transfer = make_ftp_transfer()

    mock_ftp = MagicMock(spec=ftplib.FTP)
    mock_ftp.connect.return_value = None
    mock_ftp.login.return_value = None
    mock_ftp.set_pasv.side_effect = OSError("set_pasv failed")

    with patch("ftplib.FTP", return_value=mock_ftp):
        with patch("sarracenia.transfer.ftp.alarm_set"):
            with patch("sarracenia.transfer.ftp.alarm_cancel"):
                result = transfer.connect()

    assert result is False
    assert transfer.connected is False
    mock_ftp.close.assert_called_once()


def test_connect_keyboard_interrupt_propagates():
    transfer = make_ftp_transfer()

    mock_ftp = MagicMock(spec=ftplib.FTP)
    mock_ftp.connect.side_effect = KeyboardInterrupt

    with patch("ftplib.FTP", return_value=mock_ftp):
        with patch("sarracenia.transfer.ftp.alarm_set"):
            with patch("sarracenia.transfer.ftp.alarm_cancel"):
                with pytest.raises(KeyboardInterrupt):
                    transfer.connect()


def test_connect_success_does_not_close():
    transfer = make_ftp_transfer()

    mock_ftp = MagicMock(spec=ftplib.FTP)
    mock_ftp.connect.return_value = None
    mock_ftp.login.return_value = None
    mock_ftp.set_pasv.return_value = None
    mock_ftp.pwd.return_value = "/home/user"

    with patch("ftplib.FTP", return_value=mock_ftp):
        with patch("sarracenia.transfer.ftp.alarm_set"):
            with patch("sarracenia.transfer.ftp.alarm_cancel"):
                result = transfer.connect()

    assert result is True
    assert transfer.connected is True
    assert transfer.ftp is mock_ftp
    mock_ftp.close.assert_not_called()
