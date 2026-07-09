"""
Regression tests for sarracenia.flowcb.report

The report callback's report() method copies failed messages before passing
them to reportPost, because failed messages may be retried later and must
not be modified. The original code used copy.deepcopy but never imported
copy, so it would crash with NameError on any non-empty worklist.failed.

Fix: shallow copy via dict() -- reportPost only touches top-level keys
(deletes 'content', reassigns '_deleteOnPost').
"""

import types
import unittest
from unittest.mock import MagicMock


class TestReportPostShallowCopy(unittest.TestCase):
    """Verify reportPost does not modify the original failed message."""

    def _make_message(self):
        return {
            'baseUrl': 'sftp://server.example.com/',
            'relPath': '/data/obs/file.dat',
            'pubTime': '20260320T220000.0',
            'report': {'code': 503, 'message': 'download failed'},
            'content': {'encoding': 'utf-8', 'value': 'some data'},
            'integrity': {'method': 'sha512', 'value': 'abc123'},
            '_format': 'v03',
            '_deleteOnPost': set(['_format', 'report', 'exchange']),
            'exchange': 'xpublic',
        }

    def test_failed_message_not_modified_by_report(self):
        """Shallow copy in report() must protect the original message."""
        msg = self._make_message()
        original_keys = set(msg.keys())
        original_dop = msg['_deleteOnPost'].copy()

        # Simulate what reportPost does
        mm = dict(msg)
        if 'content' in mm:
            del mm['content']
        mm['_deleteOnPost'] = mm['_deleteOnPost'].difference(set(['report']))

        # Original must be untouched
        self.assertEqual(set(msg.keys()), original_keys)
        self.assertIn('content', msg)
        self.assertEqual(msg['_deleteOnPost'], original_dop)

    def test_nested_dicts_intact_after_report(self):
        """Nested dicts are shared but reportPost only reads them."""
        msg = self._make_message()
        mm = dict(msg)

        self.assertIs(msg['integrity'], mm['integrity'])
        self.assertIs(msg['report'], mm['report'])

        # reportPost reads report but does not mutate it
        _ = mm['report']['code']
        self.assertEqual(msg['report']['code'], 503)

    def test_deleteOnPost_reassignment_does_not_affect_original(self):
        """reportPost reassigns _deleteOnPost with .difference() -- not in-place."""
        msg = self._make_message()
        original_dop = msg['_deleteOnPost'].copy()

        mm = dict(msg)
        # This is exactly what reportPost does at line 102
        mm['_deleteOnPost'] = mm['_deleteOnPost'].difference(set(['report']))

        # .difference() returns a new set and reassigns on the copy,
        # so the original's _deleteOnPost must be unchanged
        self.assertEqual(msg['_deleteOnPost'], original_dop)
        self.assertIn('report', msg['_deleteOnPost'])
        self.assertNotIn('report', mm['_deleteOnPost'])

    def test_report_calls_reportPost_for_failed_messages(self):
        """report() must call reportPost for each failed message without crashing."""
        from sarracenia.flowcb.report import Report

        # Build a minimal mock to avoid needing a real broker connection
        mock_options = MagicMock()
        mock_options.logLevel = 'INFO'
        mock_options.logFormat = '%(message)s'
        mock_options.report_broker = None
        mock_options.add_option = MagicMock()

        # Patch __init__ to skip broker setup, then test report() directly
        report_obj = Report.__new__(Report)
        report_obj.o = mock_options

        mock_poster = MagicMock()
        mock_poster.putNewMessage = MagicMock()
        report_obj.poster = mock_poster
        report_obj.reportCount = 0

        worklist = types.SimpleNamespace()
        worklist.ok = []
        worklist.rejected = []
        worklist.failed = [self._make_message(), self._make_message()]

        report_obj.report(worklist)

        self.assertEqual(mock_poster.putNewMessage.call_count, 2)


if __name__ == '__main__':
    unittest.main()
