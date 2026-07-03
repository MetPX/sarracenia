import pytest
from tests.conftest import *
from unittest.mock import MagicMock, patch

import sarracenia.config
import sarracenia.flowcb.download.mail_ingest
from sarracenia.flowcb.download.mail_ingest import Mail_ingest
from sarracenia.config.credentials import _urlparse, Credential


def _make_ingest():
    options = sarracenia.config.default_config()
    return Mail_ingest(options)


def _make_msg(base_url):
    msg = MagicMock()
    msg.baseUrl = base_url
    msg.__getitem__ = lambda self, k: {
        'new_dir': '/tmp', 'new_file': 'test.eml', 'baseUrl': base_url
    }[k]
    return msg


def _make_credential(url_str):
    cred = Credential(url_str)
    return cred


class Test_MailIngestCredentials:
    """Regression tests for PR #989 / #1677 credential handling in mail_ingest."""

    def test_password_attribute_does_not_raise(self):
        """Regression: 'urllib.parse.password' AttributeError must not occur.

        Before the fix, line 50 was 'password = urllib.parse.password' which
        raises AttributeError unconditionally on every download attempt.
        """
        ingest = _make_ingest()
        cred = _make_credential('imaps://user:secret@mail.example.com/')
        msg = _make_msg('imaps://user:secret@mail.example.com/')

        ingest.o.credentials = MagicMock()
        ingest.o.credentials.get.return_value = (True, cred)

        # Patch imaplib to avoid real network connection; we only care that
        # credential extraction does not raise before we reach the connect call.
        with patch('imaplib.IMAP4_SSL') as mock_imap:
            mock_conn = MagicMock()
            mock_conn.login.return_value = ('OK', [])
            mock_conn.select.return_value = ('OK', [b'0'])
            mock_conn.search.return_value = ('OK', [b''])
            mock_conn.expunge.return_value = ('OK', [])
            mock_conn.close.return_value = ('OK', [])
            mock_conn.logout.return_value = ('BYE', [])
            mock_imap.return_value = mock_conn

            # Must not raise AttributeError
            result = ingest.download(msg)

        # login must have been called with the decoded username and password
        mock_conn.login.assert_called_once_with('user', 'secret')

    def test_percent_encoded_hash_password_decoded_correctly(self):
        """Password with '%23' in credentials.conf must be decoded to '#' for auth."""
        ingest = _make_ingest()
        cred = _make_credential('imaps://user:pass%23word@mail.example.com/')
        msg = _make_msg('imaps://user:pass%23word@mail.example.com/')

        ingest.o.credentials = MagicMock()
        ingest.o.credentials.get.return_value = (True, cred)

        with patch('imaplib.IMAP4_SSL') as mock_imap:
            mock_conn = MagicMock()
            mock_conn.login.return_value = ('OK', [])
            mock_conn.select.return_value = ('OK', [b'0'])
            mock_conn.search.return_value = ('OK', [b''])
            mock_conn.expunge.return_value = ('OK', [])
            mock_conn.close.return_value = ('OK', [])
            mock_conn.logout.return_value = ('BYE', [])
            mock_imap.return_value = mock_conn

            ingest.download(msg)

        # The decoded password 'pass#word' (not 'pass%23word') must reach imaplib
        mock_conn.login.assert_called_once_with('user', 'pass#word')

    def test_plain_password_unchanged(self):
        """Plain passwords (no encoding) pass through without modification."""
        ingest = _make_ingest()
        cred = _make_credential('imaps://alice:hunter2@mail.example.com/')
        msg = _make_msg('imaps://alice:hunter2@mail.example.com/')

        ingest.o.credentials = MagicMock()
        ingest.o.credentials.get.return_value = (True, cred)

        with patch('imaplib.IMAP4_SSL') as mock_imap:
            mock_conn = MagicMock()
            mock_conn.login.return_value = ('OK', [])
            mock_conn.select.return_value = ('OK', [b'0'])
            mock_conn.search.return_value = ('OK', [b''])
            mock_conn.expunge.return_value = ('OK', [])
            mock_conn.close.return_value = ('OK', [])
            mock_conn.logout.return_value = ('BYE', [])
            mock_imap.return_value = mock_conn

            ingest.download(msg)

        mock_conn.login.assert_called_once_with('alice', 'hunter2')

    def test_invalid_credentials_returns_false(self):
        """download() returns False when credentials.get() returns ok=False."""
        ingest = _make_ingest()
        msg = _make_msg('imaps://user:bad@mail.example.com/')
        ingest.o.credentials = MagicMock()
        ingest.o.credentials.get.return_value = (False, None)

        result = ingest.download(msg)
        assert result is False
