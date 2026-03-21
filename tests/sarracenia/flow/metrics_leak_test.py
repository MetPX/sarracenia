"""
Regression test: _runCallbackMetrics must not mutate self.plugins["metricsReport"].
"""

import unittest
from unittest.mock import MagicMock


class FakeProto:
    def metricsReport(self):
        return {'byteRateInstant': 0}


class FakePlugin:
    __module__ = 'sarracenia.flowcb.fakeplugin'

    def __call__(self):
        return {'plugin_metric': 1}


class TestMetricsReportListGrowth(unittest.TestCase):

    def _make_flow(self):
        flow = MagicMock()
        flow.plugins = {"metricsReport": [FakePlugin()]}
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

        for _ in range(10):
            Flow._runCallbackMetrics(flow)

        self.assertEqual(len(flow.plugins["metricsReport"]), 1,
                         "plugins['metricsReport'] should keep its original "
                         "entry count — proto functions must not leak into it")


if __name__ == '__main__':
    unittest.main()
