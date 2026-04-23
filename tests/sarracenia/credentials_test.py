import pytest
from tests.conftest import *
#from unittest.mock import Mock

import sarracenia.config
import sarracenia.config.credentials
from sarracenia.config.credentials import Credential, CredentialDB, _urlparse


class Test_UrlParseResult:

    def test_normal_password_unquoted(self):
        """Plain password is returned unchanged."""
        url = _urlparse('amqps://user:plainpass@broker.example.com/')
        assert url.password == 'plainpass'
        assert url.username == 'user'

    def test_percent_encoded_hash_in_password(self):
        """'%23' in password is decoded to '#'."""
        url = _urlparse('amqps://user:pass%23word@broker.example.com/')
        assert url.password == 'pass#word'
        assert url.raw_password == 'pass%23word'

    def test_percent_encoded_at_in_password(self):
        """'%40' in password is decoded to '@'."""
        url = _urlparse('amqps://user:pass%40word@broker.example.com/')
        assert url.password == 'pass@word'
        assert url.raw_password == 'pass%40word'

    def test_percent_encoded_colon_in_password(self):
        """'%3a' in password is decoded to ':'."""
        url = _urlparse('amqps://user:pass%3aword@broker.example.com/')
        assert url.password == 'pass:word'
        assert url.raw_password == 'pass%3aword'

    def test_none_password_stays_none(self):
        """URL with no password returns None for both password and raw_password."""
        url = _urlparse('amqps://broker.example.com/')
        assert url.password is None
        assert url.raw_password is None

    def test_raw_password_used_for_key_stripping(self):
        """raw_password returns the percent-encoded form for URL key reconstruction."""
        url = _urlparse('amqps://user:pass%23word@broker.example.com/')
        assert url.raw_password == 'pass%23word'
        assert url.password == 'pass#word'


class Test_HashDetection:
    """Verify that unencoded '#' in a credential URL is detected and reported."""

    def test_hash_in_password_detected(self, caplog):
        """CredentialDB._parse() reports an error when '#' breaks the URL."""
        import logging
        db = CredentialDB()
        with caplog.at_level(logging.ERROR, logger='sarracenia.config.credentials'):
            db._parse('amqps://user:pass#word@broker.example.com/')
        assert any('<secret>' in r.message for r in caplog.records), \
            f"expected <secret> in error log, got: {[r.message for r in caplog.records]}"

    def test_hash_detection_does_not_add_credential(self):
        """Broken credential with '#' is not added to the DB."""
        db = CredentialDB()
        db._parse('amqps://user:pass#word@broker.example.com/')
        assert len(db.credentials) == 0

    def test_valid_credential_not_falsely_flagged(self, caplog):
        """Valid credential with no '#' produces no fragment-detection error."""
        import logging
        db = CredentialDB()
        with caplog.at_level(logging.ERROR, logger='sarracenia.config.credentials'):
            db._parse('amqps://user:plainpass@broker.example.com/')
        assert not any('password likely contains' in r.message for r in caplog.records)

    def test_encoded_hash_not_flagged(self, caplog):
        """Percent-encoded '#' (%23) is valid and must not trigger the detection."""
        import logging
        db = CredentialDB()
        with caplog.at_level(logging.ERROR, logger='sarracenia.config.credentials'):
            db._parse('amqps://user:pass%23word@broker.example.com/')
        assert not any('password likely contains' in r.message for r in caplog.records)

    def test_anonymous_url_not_flagged(self, caplog):
        """Anonymous URL (no credentials) does not trigger fragment detection."""
        import logging
        db = CredentialDB()
        with caplog.at_level(logging.ERROR, logger='sarracenia.config.credentials'):
            db._parse('amqps://broker.example.com/')
        assert not any('password likely contains' in r.message for r in caplog.records)


class Test_CredentialDbAdd:

    def test_add_encoded_password_key_strips_correctly(self):
        """add() key must strip the encoded password so lookup by bare URL works."""
        db = CredentialDB()
        db.add('amqps://user:pass%23word@broker.example.com/')
        # Lookup key is URL without password (encoded form stripped)
        keys = list(db.credentials.keys())
        assert any('pass%23word' not in k and 'broker.example.com' in k for k in keys), \
            f"password not stripped from key, keys: {keys}"


class Test_LogScrubbing:
    """Verify that broker_str construction strips the password from log output.

    Regression for https://github.com/MetPX/sarracenia/issues/989.
    geturl() preserves percent-encoding, so the replace must use raw_password
    (encoded form) rather than password (decoded form) to match.
    """

    def test_scrub_plain_password(self):
        """Plain password is stripped from geturl() output."""
        url = _urlparse('amqps://user:secret@broker.example.com/')
        broker_str = url.geturl().replace(':' + url.raw_password + '@', '@')
        assert 'secret' not in broker_str
        assert 'user@broker.example.com' in broker_str

    def test_scrub_encoded_hash_password(self):
        """Percent-encoded '#' password (%23) is stripped from geturl() output."""
        url = _urlparse('amqps://user:pass%23word@broker.example.com/')
        broker_str = url.geturl().replace(':' + url.raw_password + '@', '@')
        assert '%23' not in broker_str
        assert 'pass' not in broker_str
        assert 'user@broker.example.com' in broker_str

    def test_scrub_with_decoded_password_fails(self):
        """Demonstrates why decoded .password fails to scrub encoded URLs.

        This is the root cause of the PR #989 log-leak bug: geturl() keeps
        the encoded form, but .password returns the decoded form, so replace()
        finds no match.
        """
        url = _urlparse('amqps://user:pass%23word@broker.example.com/')
        broker_str_broken = url.geturl().replace(':' + url.password + '@', '@')
        assert 'pass%23word' in broker_str_broken

    def test_password_decoded_for_auth(self):
        """url.password delivers the decoded value for library auth calls."""
        url = _urlparse('amqps://user:pass%23word@broker.example.com/')
        assert url.password == 'pass#word'
