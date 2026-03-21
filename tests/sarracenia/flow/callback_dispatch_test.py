"""
Test that flow callback dispatch uses getattr instead of eval.
"""

import unittest
from unittest.mock import MagicMock


class TestCallbackDispatch(unittest.TestCase):

    def _make_flow(self):
        flow = MagicMock()
        flow.o = MagicMock()
        flow.o.logLevel.lower.return_value = 'info'
        flow.worklist = MagicMock()
        flow.plugins = {
            'after_accept': [MagicMock()],
            'on_housekeeping': [MagicMock()],
        }
        return flow

    def test_worklist_callback_calls_flow_method(self):
        from sarracenia.flow import Flow

        flow = self._make_flow()
        flow.after_accept = MagicMock()

        Flow._runCallbacksWorklist(flow, 'after_accept')

        flow.after_accept.assert_called_once_with(flow.worklist)

    def test_worklist_callback_calls_plugins(self):
        from sarracenia.flow import Flow

        flow = self._make_flow()
        plugin = flow.plugins['after_accept'][0]

        Flow._runCallbacksWorklist(flow, 'after_accept')

        plugin.assert_called_once_with(flow.worklist)

    def test_time_callback_calls_flow_method(self):
        from sarracenia.flow import Flow

        flow = self._make_flow()
        flow.on_housekeeping = MagicMock()

        Flow.runCallbacksTime(flow, 'on_housekeeping')

        flow.on_housekeeping.assert_called_once_with()

    def test_time_callback_calls_plugins(self):
        from sarracenia.flow import Flow

        flow = self._make_flow()
        plugin = flow.plugins['on_housekeeping'][0]

        Flow.runCallbacksTime(flow, 'on_housekeeping')

        plugin.assert_called_once_with()

    def test_worklist_callback_exception_handled(self):
        from sarracenia.flow import Flow

        flow = self._make_flow()
        flow.after_accept = MagicMock(side_effect=RuntimeError("boom"))

        # Should not raise
        Flow._runCallbacksWorklist(flow, 'after_accept')

    def test_missing_entry_point_no_plugins(self):
        """If no flow method and no plugins for entry_point, nothing happens."""
        from sarracenia.flow import Flow

        flow = self._make_flow()
        flow.plugins['nonexistent'] = []

        # MagicMock has every attr by default, so remove it
        delattr(flow, 'nonexistent')

        # Should not raise
        Flow._runCallbacksWorklist(flow, 'nonexistent')

    def test_time_callback_missing_entry_point(self):
        """runCallbacksTime should not KeyError on missing entry_point."""
        from sarracenia.flow import Flow

        flow = self._make_flow()
        delattr(flow, 'nonexistent')

        # Should not raise — entry_point not in self.plugins
        Flow.runCallbacksTime(flow, 'nonexistent')


if __name__ == '__main__':
    unittest.main()
