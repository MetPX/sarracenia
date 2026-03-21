"""
Regression test: _runCallbackMetrics must not mutate self.plugins["metricsReport"].

Before the fix, it assigned the live list to a local variable and appended
transfer protocol metricsReport functions onto it every housekeeping cycle,
causing unbounded list growth and redundant metricsReport() calls.
"""

import unittest
from unittest.mock import MagicMock


class FakeProto:
    """Fake transfer protocol with a metricsReport method."""
    def metricsReport(self):
        return {'bytes': 42}


class TestMetricsReportListGrowth(unittest.TestCase):

    def _make_flow(self):
        """Build a minimal Flow-like object with just enough state."""
        flow = MagicMock()
        flow.plugins = {"metricsReport": []}
        flow.proto = {"sftp": FakeProto()}
        flow.o = MagicMock()
        flow.o.logLevel.lower.return_value = 'info'
        flow.metrics = {
            'flow': {
                'transferConnected': False,
                'last_housekeeping_cpuTime': 0,
            }
        }
        return flow

    def test_plugin_list_stable_across_calls(self):
        """plugins['metricsReport'] must not grow across housekeeping cycles."""
        from sarracenia.flow import Flow

        flow = self._make_flow()

        for i in range(5):
            Flow._runCallbackMetrics(flow)

        self.assertEqual(len(flow.plugins["metricsReport"]), 0,
                         "plugins['metricsReport'] should stay empty — "
                         "transfer protocol functions must not leak into it")


if __name__ == '__main__':
    unittest.main()
