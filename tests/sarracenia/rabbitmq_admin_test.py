import pytest
from tests.conftest import *
from unittest.mock import patch, MagicMock

import sarracenia.config
import sarracenia.rabbitmq_admin
from sarracenia.rabbitmq_admin import exec_rabbitmqadmin, run_rabbitmqadmin
from sarracenia.config.credentials import _urlparse


class Test_ExecRabbitmqadmin:
    """Regression tests for PR #989 / #1677 credential handling in rabbitmq_admin."""

    def _run_and_get_cmdlst(self, url, options='list exchanges name'):
        with patch('sarracenia.rabbitmq_admin.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=b'[]')
            exec_rabbitmqadmin(url, options)
        return mock_run.call_args[0][0]

    def test_password_passed_as_separate_argument(self):
        """Password must be a standalone element in the argument list, not shell-interpolated.

        The old implementation built a shell command string and used getstatusoutput
        (shell=True) or replace()+split(), both of which allowed injection or corruption.
        The fix uses subprocess.run with a list — password is never shell-parsed.
        """
        url = _urlparse('amqp://admin:secret@localhost/')
        cmdlst = self._run_and_get_cmdlst(url)
        assert isinstance(cmdlst, list), "subprocess.run must receive a list, not a string"
        # '-p' followed immediately by the password as its own element
        assert '-p' in cmdlst
        password_index = cmdlst.index('-p') + 1
        assert cmdlst[password_index] == 'secret'

    def test_encoded_hash_password_decoded_for_command(self):
        """Password '%23' must be decoded to '#' as a separate argument."""
        url = _urlparse('amqp://admin:pass%23word@localhost/')
        cmdlst = self._run_and_get_cmdlst(url)
        password_index = cmdlst.index('-p') + 1
        assert cmdlst[password_index] == 'pass#word'
        assert 'pass%23word' not in cmdlst

    def test_password_with_single_quote_not_corrupted(self):
        """Password containing a single quote must not be stripped or split.

        The old replace("'","").split() approach silently dropped the quote,
        causing authentication to fail for any password containing "'".
        """
        url = _urlparse("amqp://admin:it's@localhost/")
        cmdlst = self._run_and_get_cmdlst(url)
        password_index = cmdlst.index('-p') + 1
        assert cmdlst[password_index] == "it's"

    def test_no_shell_injection_via_password(self):
        """A password containing shell metacharacters is passed as a single safe argument."""
        url = _urlparse('amqp://admin:secret;id@localhost/')
        cmdlst = self._run_and_get_cmdlst(url)
        assert isinstance(cmdlst, list)
        password_index = cmdlst.index('-p') + 1
        assert cmdlst[password_index] == 'secret;id'

    def test_options_tokenised_correctly(self):
        """Options string is split into tokens, not concatenated into a shell string."""
        url = _urlparse('amqp://admin:secret@localhost/')
        cmdlst = self._run_and_get_cmdlst(url, 'list exchanges name')
        assert 'list' in cmdlst
        assert 'exchanges' in cmdlst
        assert 'name' in cmdlst

    def test_amqps_adds_ssl_flag(self):
        """AMQPS scheme adds --ssl and --port=15671 to the argument list."""
        url = _urlparse('amqps://admin:secret@broker.example.com/')
        cmdlst = self._run_and_get_cmdlst(url)
        assert '--ssl' in cmdlst
        assert '--port=15671' in cmdlst

class Test_RunRabbitmqadmin:
    """Tests for run_rabbitmqadmin JSON parsing (eval -> json.loads fix)."""

    def _run_with_response(self, stdout_bytes, returncode=0):
        url = _urlparse('amqp://admin:secret@localhost/')
        with patch('sarracenia.rabbitmq_admin.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=returncode, stdout=stdout_bytes)
            return run_rabbitmqadmin(url, 'list exchanges name')

    def test_valid_json_parsed_to_list(self):
        """Valid JSON array from rabbitmqadmin is returned as a Python list."""
        result = self._run_with_response(b'[{"name": "xpublic"}, {"name": "xs_user"}]')
        assert result == [{'name': 'xpublic'}, {'name': 'xs_user'}]

    def test_malicious_eval_payload_not_executed(self):
        """A response that would execute code under eval() is safe under json.loads().

        eval('[x for x in ().__class__.__bases__[0].__subclasses__()]') would
        return a list of all Python classes — a code-execution gadget.
        json.loads() raises JSONDecodeError instead.
        """
        malicious = b'[x for x in ().__class__.__bases__[0].__subclasses__()]'
        result = self._run_with_response(malicious)
        assert result == []

    def test_non_json_response_returns_empty_list(self):
        """Non-JSON output (e.g. rabbitmqadmin error text) returns [] without raising."""
        result = self._run_with_response(b'Error: blah blah blah')
        assert result == []

    def test_failed_subprocess_returns_empty_list(self):
        """Non-zero exit code from rabbitmqadmin returns [] without raising."""
        result = self._run_with_response(b'', returncode=1)
        assert result == []


class Test_StdlibUrlparseRegression:
    def test_plain_urlparse_would_pass_encoded_password(self):
        """Demonstrates the bug: stdlib urlparse returns encoded password from url.password.

        This test documents why the __main__ block must use _urlparse, not urlparse.
        Plain ParseResult.password does NOT decode percent-encoding.
        """
        import urllib.parse
        url_broken = urllib.parse.urlparse('amqp://admin:pass%23word@localhost/')
        assert url_broken.password == 'pass%23word', \
            "stdlib urlparse must NOT decode -- confirms why _urlparse is needed in __main__"
