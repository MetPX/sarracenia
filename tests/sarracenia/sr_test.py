import pytest
from tests.conftest import *
#from unittest.mock import Mock

import sarracenia.config
import sarracenia.sr

import copy
import os
import shutil
import pytest
from pathlib import Path

import sarracenia
import sarracenia.config
import sarracenia.sr


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
