from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import sys
import copy

from pathlib import Path
from tests.conftest import *

import sarracenia
import sarracenia.config
import sarracenia.sr

# =========================================================================== #
# ============= Unit tests for Issue1196 - default.inc feature ============== #
# =========================================================================== #

def _make_config_tree(tmp_path, component, default_content=None, config_content=None):
    """
    Create:

        <tmp_path>/<component>/default.inc
        <tmp_path>/<component>/test.conf

    Returns the component directory.
    """
    component_dir = tmp_path + '/' + component

    Path(component_dir).mkdir(parents=True, exist_ok=True)

    if default_content is not None:
        Path(component_dir + "/default.inc").write_text(default_content)

    if config_content is not None:
        Path(component_dir + "/test.conf").write_text(config_content)

    return component_dir


def _remove_config_tree(tmp_path, component):
    """
    Remove the entire temporary Sarracenia configuration tree.
    """
    component_dir = tmp_path + "/" + component

    for filename in ["default.inc", "test.conf"]:
        filepath = component_dir + "/" + filename

        if Path(filepath).exists():
            Path(filepath).unlink()

    if Path(component_dir).exists():
        Path(component_dir).rmdir()


def _make_global_state(tmp_path, components):
    """
    Create a minimal sr_GlobalState suitable for exercising _read_configs()
    without invoking the normal sr3 command-line startup machinery.
    """
    state = sarracenia.sr.sr_GlobalState.__new__(
        sarracenia.sr.sr_GlobalState
    )

    state.user_config_dir = str(tmp_path)

    state.components = components

    # _read_configs() uses options.action when building each cfgbody.
    state.options = copy.deepcopy(sarracenia.config.default_config())
    state.options.action = "start"

    return state

@pytest.mark.parametrize(
    "component",
    [
        "cpost",
        "cpump",
        "flow",
        "poll",
        "post",
        "report",
        "sarra",
        "sender",
        "subscribe",
        "shovel",
        "watch",
        "winnow"
    ],
)
def test_component_default_inc(component, monkeypatch):
    """
    default.inc should be loaded for every supported flow component.
    """

    tmp_path = '/tmp/'
    monkeypatch.setattr(
        sarracenia.config,
        "get_user_config_dir",
        lambda: str(tmp_path)
    )

    _make_config_tree(
        tmp_path,
        component,
        default_content="fileEvents create,modify\n",
        config_content="exchange xs_Something\n",
    )

    try:
        state = _make_global_state(tmp_path, [component])

        state._read_configs()

        assert component in state.configs
        assert "test" in state.configs[component]

        options = state.configs[component]["test"]["options"]

        assert options.exchange == "xs_Something"
        assert options.fileEvents == {'modify', 'create'}
    finally:
        _remove_config_tree(tmp_path, component)


def test_component_default_inc_can_be_overridden_by_config(monkeypatch):
    """
    Values from <component>/default.inc are defaults and must be overridden
    by values explicitly specified in the component configuration.
    """
    tmp_path = '/tmp/'
    monkeypatch.setattr(
        sarracenia.config,
        "get_user_config_dir",
        lambda: str(tmp_path)
    )

    _make_config_tree(
        tmp_path,
        "poll",
        default_content="retry_ttl 1d\n",
        config_content="retry_ttl 1h\n",
    )

    try:
        state = _make_global_state(tmp_path, ["poll"])

        state._read_configs()

        options = state.configs["poll"]["test"]["options"]

        assert options.retry_ttl == 3600
    finally:
        _remove_config_tree(tmp_path, "poll")


def test_component_default_inc_only_applies_to_its_component(monkeypatch):
    """
    A component's default.inc must not leak into another component.
    """
    tmp_path = '/tmp/'
    monkeypatch.setattr(
        sarracenia.config,
        "get_user_config_dir",
        lambda: str(tmp_path)
    )

    _make_config_tree(
        tmp_path,
        "poll",
        default_content="retry_ttl 1h\n",
        config_content="exchange poll_exchange\n",
    )

    _make_config_tree(
        tmp_path,
        "sarra",
        default_content="retry_ttl 2h\n",
        config_content="exchange sarra_exchange\n",
    )

    try:
        state = _make_global_state(tmp_path, ["poll", "sarra"])

        state._read_configs()

        assert state.configs["poll"]["test"]["options"].retry_ttl == 3600
        assert state.configs["sarra"]["test"]["options"].retry_ttl == 7200
    finally:
        _remove_config_tree(tmp_path, "poll")
        _remove_config_tree(tmp_path, "sarra")

def test_component_default_inc_with_two_of_same_component(monkeypatch):
    """
    A component's default.inc must not leak into another component.
    """
    tmp_path = '/tmp/'
    monkeypatch.setattr(
        sarracenia.config,
        "get_user_config_dir",
        lambda: str(tmp_path)
    )

    _make_config_tree(
        tmp_path,
        "sarra",
        default_content="retry_ttl 1h\n",
        config_content="exchange sarra_exchange1\n",
    )

    Path(tmp_path + "sarra/test1.conf").write_text("exchange sarra_exchange2\n")

    try:
        state = _make_global_state(tmp_path, ["sarra"])

        state._read_configs()

        assert state.configs["sarra"]["test"]["options"].retry_ttl == 3600
        assert state.configs["sarra"]["test"]["options"].exchange == 'sarra_exchange1'
        assert state.configs["sarra"]["test1"]["options"].retry_ttl == 3600
        assert state.configs["sarra"]["test1"]["options"].exchange == 'sarra_exchange2'
    finally:
        Path(tmp_path + "sarra/test1.conf").unlink()
        _remove_config_tree(tmp_path, "sarra")


def test_default_inc_is_not_a_configuration(monkeypatch):
    """
    default.inc is an include/default file and must not itself appear as a
    configuration.
    """
    tmp_path = '/tmp/'
    monkeypatch.setattr(
        sarracenia.config,
        "get_user_config_dir",
        lambda: str(tmp_path)
    )

    _make_config_tree(
        tmp_path,
        "poll",
        default_content="exchange xs_Something\n",
        config_content="accept .*\n",
    )

    try:
        state = _make_global_state(tmp_path, ["poll"])

        state._read_configs()

        assert "test" in state.configs["poll"]
        assert "default" not in state.configs["poll"]
    finally:
        _remove_config_tree(tmp_path, "poll")


def test_default_inc_is_optional(monkeypatch):
    """
    A component without a default.inc must continue to load normally.
    """
    tmp_path = '/tmp/'
    monkeypatch.setattr(
        sarracenia.config,
        "get_user_config_dir",
        lambda: str(tmp_path)
    )

    _make_config_tree(
        tmp_path,
        "poll",
        default_content=None,
        config_content="exchange configured_exchange\n",
    )

    try:
        state = _make_global_state(tmp_path, ["poll"])

        state._read_configs()

        assert "test" in state.configs["poll"]
        assert (
            state.configs["poll"]["test"]["options"].exchange
            == "configured_exchange"
        )
    finally:
        _remove_config_tree(tmp_path, "poll")


def test_default_inc_nested_include(monkeypatch):
    """
    A nested include file inside default.inc should parse properly
    """
    tmp_path = '/tmp/'
    monkeypatch.setattr(
        sarracenia.config,
        "get_user_config_dir",
        lambda: str(tmp_path)
    )

    component_dir = tmp_path + "/poll"
    Path(component_dir).mkdir()

    Path(component_dir + "/default.inc").write_text(
        "include nested.inc\n"
    )

    Path(component_dir + "/nested.inc").write_text(
        "retry_ttl 3h\n"
    )

    Path(component_dir + "/test.conf").write_text(
        "exchange my_exchange\n"
    )

    try:
        state = _make_global_state(tmp_path, ["poll"])
        state._read_configs()

        options = state.configs["poll"]["test"]["options"]

        assert options.retry_ttl == 10800
        assert options.exchange == "my_exchange"
    finally:
        Path(component_dir + "/nested.inc").unlink()
        _remove_config_tree(tmp_path, "poll")


def test_default_inc_nested_include_can_be_overridden():
    """
    A nested include file inside default.inc should have its values ignored if the configuration overrides that value
    """
    tmp_path = '/tmp'
    component_dir = tmp_path + "/poll"
    Path(component_dir).mkdir()

    Path(component_dir + "/default.inc").write_text(
        "include nested.inc\n"
    )

    Path(component_dir + "/nested.inc").write_text(
        "retry_ttl 3h\n"
    )

    Path(component_dir + "/test.conf").write_text(
        "retry_ttl 30m\n"
    )

    try:
        state = _make_global_state(tmp_path, ["poll"])
        state._read_configs()

        options = state.configs["poll"]["test"]["options"]

        assert options.retry_ttl == 1800
    finally:
        Path(component_dir + "/nested.inc").unlink()
        _remove_config_tree(tmp_path, "poll")

def test_one_config_applies_component_default_inc(monkeypatch):
    """
    one_config() should apply the component's default.inc when a
    configuration is loaded directly at runtime.
    """
    monkeypatch.setattr(sys, "argv", ["sr3 start poll/test"])
    tmp_path = "/tmp/"

    monkeypatch.setattr(
        sarracenia.config,
        "get_user_config_dir",
        lambda: str(tmp_path)
    )

    _make_config_tree(
        tmp_path,
        "poll",
        default_content="retry_ttl 3h\n",
        config_content="exchange my_exchange\n",
    )

    try:
        config = sarracenia.config.one_config(
            "poll",
            "test",
            "start"
        )

        assert config.retry_ttl == 10800
        assert config.exchange == "my_exchange"

    finally:
        _remove_config_tree(tmp_path, "poll")
# =========================================================================== #
# ============================== End of Tests =============================== #
# =========================================================================== #
        
        
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

    assert sr._set_state_dir("subscribe", "amis") == str(tmp_path / "my-host" / "subscribe" / "amis")


def test_statehost_dir_uses_standard_cache_dir_when_disabled(tmp_path):
    sr = make_sr(tmp_path)
    sr.configs = {
        "subscribe": {
            "amis": {
                "options": SimpleNamespace(statehost=False)
            }
        }
    }

    assert sr._set_state_dir("subscribe", "amis") == str(tmp_path / "subscribe" / "amis")


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
