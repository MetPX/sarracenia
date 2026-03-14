import pytest
from tests.conftest import *
from unittest.mock import Mock, patch

import os
import pathlib
import sarracenia.config
import sarracenia.sr

logger = sarracenia.sr.logging.getLogger(__name__)


class Test_PidFileRaceCondition:
    """
    Regression tests for https://github.com/MetPX/sarracenia/issues/1571

    sr3 restart crashes with FileNotFoundError when a PID file disappears
    between os.listdir() and p.read_text() due to a race condition.

    The fix adds FileNotFoundError handling so the code gracefully continues
    instead of crashing.
    """

    def _make_mock_sr(self, tmp_path):
        """Create a minimal mock sr object with the methods under test."""
        mock_sr = Mock()
        mock_sr.options = Mock()
        mock_sr.options.dry_run = False
        mock_sr.procs = {}
        mock_sr.missing = []
        mock_sr.hostdir = 'testhost'
        mock_sr.user_cache_dir = str(tmp_path)
        mock_sr.components = ['sarra']
        mock_sr.configs = {}

        # Bind the real methods to our mock
        mock_sr._find_missing_instances_dir = (
            sarracenia.sr.sr_GlobalState._find_missing_instances_dir.__get__(mock_sr)
        )
        mock_sr._clean_missing_proc_state_dir = (
            sarracenia.sr.sr_GlobalState._clean_missing_proc_state_dir.__get__(mock_sr)
        )
        mock_sr._instance_num_from_pidfile = (
            sarracenia.sr.sr_GlobalState._instance_num_from_pidfile.__get__(mock_sr)
        )
        return mock_sr

    def test_find_missing_pid_file_disappears(self, tmp_path):
        """_find_missing_instances_dir should not crash when a PID file
        disappears between os.listdir() and read_text()."""

        mock_sr = self._make_mock_sr(tmp_path)

        # Set up a sarra/test_config directory with a pid file
        comp_dir = tmp_path / "sarra"
        cfg_dir = comp_dir / "test_config"
        cfg_dir.mkdir(parents=True)

        pid_file = cfg_dir / "sarra_test_config_01.pid"
        pid_file.write_text("12345")

        mock_sr.configs = {
            'sarra': {
                'test_config': {
                    'status': 'running',
                    'instances': 1,
                    'options': Mock(statehost=False),
                }
            }
        }

        # Patch read_text to raise FileNotFoundError (simulating race condition)
        original_read_text = pathlib.Path.read_text

        def flaky_read_text(self, *args, **kwargs):
            if str(self).endswith('.pid'):
                raise FileNotFoundError(
                    f"No such file or directory: '{self.name}'"
                )
            return original_read_text(self, *args, **kwargs)

        with patch.object(pathlib.Path, 'read_text', flaky_read_text):
            # This should NOT raise FileNotFoundError
            mock_sr._find_missing_instances_dir(str(tmp_path), False)

        # The instance should be treated as missing
        assert len(mock_sr.missing) >= 1

    def test_clean_missing_pid_file_disappears(self, tmp_path):
        """_clean_missing_proc_state_dir should not crash when a PID file
        disappears between os.listdir() and read_text()."""

        mock_sr = self._make_mock_sr(tmp_path)

        # Set up a sarra/test_config directory with a pid file
        comp_dir = tmp_path / "sarra"
        cfg_dir = comp_dir / "test_config"
        cfg_dir.mkdir(parents=True)

        pid_file = cfg_dir / "sarra_test_config_01.pid"
        pid_file.write_text("12345")

        mock_sr.missing = [['sarra', 'test_config', 1]]

        # Patch read_text to raise FileNotFoundError (simulating race condition)
        original_read_text = pathlib.Path.read_text

        def flaky_read_text(self, *args, **kwargs):
            if str(self).endswith('.pid'):
                raise FileNotFoundError(
                    f"No such file or directory: '{self.name}'"
                )
            return original_read_text(self, *args, **kwargs)

        with patch.object(pathlib.Path, 'read_text', flaky_read_text):
            # This should NOT raise FileNotFoundError
            mock_sr._clean_missing_proc_state_dir(str(tmp_path))

        # The pid file should still exist (couldn't read it, so skipped it)
        assert pid_file.exists()
