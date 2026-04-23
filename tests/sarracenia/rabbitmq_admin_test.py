import pytest
from tests.conftest import *
from unittest.mock import patch, MagicMock

import sarracenia.config
import sarracenia.rabbitmq_admin
from sarracenia.rabbitmq_admin import exec_rabbitmqadmin
from sarracenia.config.credentials import _urlparse


class Test_ExecRabbitmqadmin:
    """Regression tests for PR #989 / #1677 credential handling in rabbitmq_admin."""

    def test_plain_password_reaches_command(self):
        """Plain password is passed to exec_rabbitmqadmin without modification."""
        url = _urlparse('amqp://admin:secret@localhost/')
        with patch('sarracenia.rabbitmq_admin.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=b'[]')
            exec_rabbitmqadmin(url, 'list exchanges name')
        call_args = mock_run.call_args[0][0]
        assert 'secret' in call_args

    def test_encoded_hash_password_decoded_for_command(self):
        """Password with '%23' must be decoded to '#' before being passed to rabbitmqadmin.

        Regression: exec_rabbitmqadmin used urllib.parse.urlparse() in __main__
        (plain ParseResult) and then dropped the unquote() call, so percent-encoded
        passwords were passed verbatim ('pass%23word') instead of decoded ('pass#word').
        """
        url = _urlparse('amqp://admin:pass%23word@localhost/')
        assert url.password == 'pass#word', "UrlParseResult must decode %23 to #"

        with patch('sarracenia.rabbitmq_admin.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=b'[]')
            exec_rabbitmqadmin(url, 'list exchanges name')
        call_args = mock_run.call_args[0][0]
        # Decoded password must appear; encoded form must not
        assert 'pass#word' in ' '.join(call_args) or 'pass#word' in call_args
        assert 'pass%23word' not in ' '.join(call_args)

    def test_plain_urlparse_would_pass_encoded_password(self):
        """Demonstrates the bug: stdlib urlparse returns encoded password from url.password.

        This test documents why the __main__ block must use _urlparse, not urlparse.
        Plain ParseResult.password does NOT decode percent-encoding.
        """
        import urllib.parse
        url_broken = urllib.parse.urlparse('amqp://admin:pass%23word@localhost/')
        assert url_broken.password == 'pass%23word', \
            "stdlib urlparse must NOT decode — confirms why _urlparse is needed in __main__"
