from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from tests.conftest import *

import sarracenia.config
import sarracenia.sr

# =========================================================================== #
# ============= Unit tests for sarracenia.sr.SR._tag_progress() ============= #
# =========================================================================== #

def make_sr(tmp_path):
    sr = object.__new__(sarracenia.sr.sr_GlobalState)
    sr.user_cache_dir = str(tmp_path)
    sr.hostdir = "test-host"
    sr.configs = {}
    return sr

def test_tag_progress_creates_marker(tmp_path):
    sr = make_sr(tmp_path)
    sr.configs = {
        "subscribe": {
            "amis": {
                "options": SimpleNamespace(statehost=False)
            }
        }
    }

    result = sr._tag_progress(
        "subscribe",
        "amis",
        "starting",
        ending=False
    )

    marker = tmp_path / "subscribe" / "amis" / "starting"

    assert result is True
    assert marker.exists()
    assert marker.read_text()

def test_tag_progress_returns_false_when_marker_already_exists(tmp_path):
    sr = make_sr(tmp_path)
    sr.configs = {
        "subscribe": {
            "amis": {
                "options": SimpleNamespace(statehost=False)
            }
        }
    }

    marker = tmp_path / "subscribe" / "amis" / "starting"
    marker.parent.mkdir(parents=True)
    marker.write_text("timestamp")

    assert sr._tag_progress("subscribe", "amis", "starting", False) is False

def test_tag_progress_returns_false_when_removing_missing_marker(tmp_path):
    sr = make_sr(tmp_path)
    sr.configs = {
        "subscribe": {
            "amis": {
                "options": SimpleNamespace(statehost=False)
            }
        }
    }

    assert sr._tag_progress("subscribe", "amis", "starting", True) is False

def test_tag_progress_uses_host_directory(tmp_path):
    sr = make_sr(tmp_path)
    sr.hostdir = "my-host"
    sr.configs = {
        "subscribe": {
            "amis": {
                "options": SimpleNamespace(statehost=True)
            }
        }
    }

    sr._tag_progress("subscribe", "amis", "starting", False)

    marker = tmp_path / "my-host" / "subscribe" / "amis" / "starting"
    assert marker.exists()

# =========================================================================== #
# ============================== End of Tests =============================== #
# =========================================================================== #



# =========================================================================== #
# ================ Unit tests for sarracenia.sr.SR.disabled() =============== #
# =========================================================================== #

def make_disable_sr():
    sr = object.__new__(sarracenia.sr.sr_GlobalState)
    sr.leftovers = []
    sr._action_all_configs = False
    sr.filtered_configurations = []
    sr.please_stop = False
    sr.configs = {}
    sr.states = {}
    sr._tag_progress = Mock(return_value=True)
    return sr

def test_disable_tags_stopped_configuration():
    sr = make_disable_sr()
    sr.filtered_configurations = ["subscribe/amis"]
    sr.configs = {
        "subscribe": {
            "amis": {
                "options": object()
            }
        }
    }
    sr.states = {
        "subscribe": {
            "amis": {
                "instance_pids": {}
            }
        }
    }

    sr.disable()

    sr._tag_progress.assert_called_once_with(
        "subscribe",
        "amis",
        "disabled",
        ending=False
    )

def test_disable_skips_running_configuration():
    sr = make_disable_sr()
    sr.filtered_configurations = ["subscribe/amis"]
    sr.configs = {
        "subscribe": {
            "amis": {
                "options": object()
            }
        }
    }
    sr.states = {
        "subscribe": {
            "amis": {
                "instance_pids": {1: 12345}
            }
        }
    }

    sr.disable()

    sr._tag_progress.assert_not_called()

def test_disable_returns_when_leftovers_exist():
    sr = make_disable_sr()
    sr.leftovers = ["missing"]
    sr._action_all_configs = False

    sr.disable()

    sr._tag_progress.assert_not_called()

# =========================================================================== #
# ============================== End of Tests =============================== #
# =========================================================================== #



# =========================================================================== #
# ================ Unit tests for sarracenia.sr.SR._statehost_dir() ========= #
# =========================================================================== #

def test_statehost_dir_uses_host_directory_when_enabled(tmp_path):
    sr = make_sr(tmp_path)
    sr.hostdir = "my-host"
    sr.configs = {
        "subscribe": {
            "amis": {
                "options": SimpleNamespace(statehost=True)
            }
        }
    }

    assert sr._statehost_dir("subscribe", "amis") == str(tmp_path / "my-host" / "subscribe" / "amis")


def test_statehost_dir_uses_standard_cache_dir_when_disabled(tmp_path):
    sr = make_sr(tmp_path)
    sr.configs = {
        "subscribe": {
            "amis": {
                "options": SimpleNamespace(statehost=False)
            }
        }
    }

    assert sr._statehost_dir("subscribe", "amis") == str(tmp_path / "subscribe" / "amis")


def test_enable_and_disable_use_statehost_directory(tmp_path):
    sr = make_sr(tmp_path)
    sr.hostdir = "my-host"
    sr.leftovers = []
    sr._action_all_configs = False
    sr.filtered_configurations = ["subscribe/amis"]
    sr.please_stop = False
    sr.states = {
        "subscribe": {
            "amis": {
                "instance_pids": {}
            }
        }
    }
    sr.configs = {
        "subscribe": {
            "amis": {
                "options": SimpleNamespace(statehost=True)
            }
        }
    }

    state_dir = tmp_path / "my-host" / "subscribe" / "amis"
    state_dir.mkdir(parents=True)
    disabled_marker = state_dir / "disabled"
    disabled_marker.write_text("disabled")

    sr.enable()
    assert not disabled_marker.exists()

    sr.disable()
    marker = state_dir / "disabled"
    assert marker.exists()
    assert marker.read_text()

# =========================================================================== #
# ============================== End of Tests =============================== #
# =========================================================================== #