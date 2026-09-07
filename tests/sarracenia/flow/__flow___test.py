import copy
import os

import pytest

import sarracenia.config
import sarracenia.flow
from tests.conftest import *

__COMPONENT="subscribe"
__CONFIG="flow_class_test"

def __make_fake_config(lines=[]):
    """ build and return a fake config object
    """
    options = copy.deepcopy(sarracenia.config.default_config())
    options.component = __COMPONENT
    options.config = __CONFIG
    options.action = 'start'
    for line in lines:
        options.parse_line(__COMPONENT, __CONFIG, f"{__COMPONENT}/{__CONFIG}", 1, line)
    options.metricsFilename = '/tmp/fake_filename_nothing_here'
    options.novipFilename = options.metricsFilename
    options.acceptUnmatched = False
    options.finalize()
    return options


def test_msg_accepted_with_sundew_extension():
    """
    Regression test for https://github.com/MetPX/sarracenia/issues/1573
    sundew_extension should be included in filtering, even when URL has a port
    """
    options = __make_fake_config(lines=["accept .*rxer:CCCC:TT:3:Direct.*"])

    flow = sarracenia.flow.Flow(options)
    flow.have_vip = True
    msg = sarracenia.Message()
    msg['pubTime'] = '20260101T010203.123'
    msg['baseUrl'] = 'http://dms-dev1.domain:8180/data/msc/'
    msg['relPath'] = 'forecast/atmospheric/aviation/file.txt'
    msg['sundew_extension'] = 'rxer:CCCC:TT:3:Direct'

    flow.worklist.incoming.append(msg)

    # based on the accept statement, the message should only be accepted when the sundew_extension is correctly added
    flow.filter()
    assert(len(flow.worklist.rejected) == 0)
    assert(msg not in flow.worklist.rejected)
    assert(msg in flow.worklist.incoming)

def test_msg_rejected_when_sundew_extension_already_present():
    """
    If the path itself already contains a different sundew extension,
    the sundew_extension header in the msg should not be used for filtering
    """
    options = __make_fake_config(lines=["accept .*rxer:CCCC:TT:3:Direct.*"])

    flow = sarracenia.flow.Flow(options)
    flow.have_vip = True
    msg = sarracenia.Message()
    msg['pubTime'] = '20260101T010203.123'
    msg['baseUrl'] = 'http://dms-dev1.domain:8180/data/msc/'
    msg['relPath'] = 'forecast/atmospheric/aviation/file.txt:something:CWAO:SA:3:Direct'
    msg['sundew_extension'] = 'rxer:CCCC:TT:3:Direct'

    flow.worklist.incoming.append(msg)

    # msg already has a different sundew extension that does not match the accept, it should be rejected
    flow.filter()

    # worklist.rejected gets acked and set to [] at the end of filter
    assert(len(flow.worklist.incoming) == 0)
    assert(len(flow.worklist.rejected) == 0)
    assert(msg not in flow.worklist.incoming)


def test_work_restores_cwd_after_inline_download(tmp_path, monkeypatch):
    options = __make_fake_config(lines=["download True"])
    flow = sarracenia.flow.Flow(options)
    runtime_dir = tmp_path / "runtime"
    payload_dir = tmp_path / "public_data" / "20260904" / "product" / "19"
    runtime_dir.mkdir()

    message = sarracenia.Message()
    message["new_dir"] = str(payload_dir)
    message["new_file"] = "payload.txt"
    message["content"] = {"encoding": "utf-8", "value": "test payload\n"}
    message["identity"] = {"method": "arbitrary", "value": "test"}
    flow.worklist.incoming.append(message)

    monkeypatch.chdir(runtime_dir)
    flow.work()

    assert os.getcwd() == str(runtime_dir)
    assert (payload_dir / "payload.txt").read_text() == "test payload\n"


def test_work_restores_cwd_when_work_raises(tmp_path, monkeypatch):
    options = __make_fake_config()
    flow = sarracenia.flow.Flow(options)
    runtime_dir = tmp_path / "runtime"
    payload_dir = tmp_path / "public_data" / "20260904"
    runtime_dir.mkdir()
    payload_dir.mkdir(parents=True)

    def fail_inside_payload_dir():
        error = "test failure"
        os.chdir(payload_dir)
        raise RuntimeError(error)

    monkeypatch.setattr(flow, "do", fail_inside_payload_dir)
    monkeypatch.chdir(runtime_dir)

    with pytest.raises(RuntimeError, match="test failure"):
        flow.work()

    assert os.getcwd() == str(runtime_dir)


@pytest.mark.skipif(os.name == "nt", reason="Windows does not permit removing the process cwd")
def test_work_recovers_when_cwd_is_unavailable_at_entry(tmp_path, monkeypatch):
    options = __make_fake_config()
    fallback_dir = tmp_path / "cache" / "subscribe" / "flow_class_test"
    unavailable_dir = tmp_path / "unavailable"
    payload_dir = tmp_path / "public_data" / "20260904"
    fallback_dir.mkdir(parents=True)
    unavailable_dir.mkdir()
    payload_dir.mkdir(parents=True)
    options.cfg_run_dir = str(fallback_dir)
    flow = sarracenia.flow.Flow(options)
    worked = []

    def work_in_payload_dir():
        os.chdir(payload_dir)
        worked.append(True)

    monkeypatch.setattr(flow, "do", work_in_payload_dir)

    monkeypatch.chdir(unavailable_dir)
    unavailable_dir.rmdir()
    try:
        flow.work()
        assert worked == [True]
        assert os.getcwd() == str(fallback_dir)
    finally:
        os.chdir(fallback_dir)


def test_work_uses_fallback_when_saved_cwd_is_renamed(tmp_path, monkeypatch):
    options = __make_fake_config()
    fallback_dir = tmp_path / "cache" / "subscribe" / "flow_class_test"
    runtime_dir = tmp_path / "runtime"
    renamed_runtime_dir = tmp_path / "runtime-renamed"
    payload_dir = tmp_path / "public_data" / "20260904"
    fallback_dir.mkdir(parents=True)
    runtime_dir.mkdir()
    payload_dir.mkdir(parents=True)
    options.cfg_run_dir = str(fallback_dir)
    flow = sarracenia.flow.Flow(options)

    def rename_saved_cwd():
        os.chdir(payload_dir)
        runtime_dir.rename(renamed_runtime_dir)

    monkeypatch.setattr(flow, "do", rename_saved_cwd)
    monkeypatch.chdir(runtime_dir)

    flow.work()

    assert os.getcwd() == str(fallback_dir)


def test_work_preserves_exception_when_saved_cwd_is_removed(tmp_path, monkeypatch):
    options = __make_fake_config()
    fallback_dir = tmp_path / "cache" / "subscribe" / "flow_class_test"
    runtime_dir = tmp_path / "runtime"
    payload_dir = tmp_path / "public_data" / "20260904"
    fallback_dir.mkdir(parents=True)
    runtime_dir.mkdir()
    payload_dir.mkdir(parents=True)
    options.cfg_run_dir = str(fallback_dir)
    flow = sarracenia.flow.Flow(options)
    work_error = RuntimeError("test failure")

    def fail_after_removing_saved_cwd():
        os.chdir(payload_dir)
        runtime_dir.rmdir()
        raise work_error

    monkeypatch.setattr(flow, "do", fail_after_removing_saved_cwd)
    monkeypatch.chdir(runtime_dir)

    with pytest.raises(RuntimeError) as exc_info:
        flow.work()

    assert exc_info.value is work_error
    assert os.getcwd() == str(fallback_dir)
