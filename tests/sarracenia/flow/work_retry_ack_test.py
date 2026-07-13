"""Regression tests for retry persistence and source acknowledgement ordering."""

import types
from unittest.mock import MagicMock

import pytest

from sarracenia import Message
from sarracenia.flow import Flow
from sarracenia.flowcb.retry import Retry


class _EmptyQueue:

    def __len__(self):
        return 0


def _make_message(delivery_tag=1):
    message = Message()
    message["ack_id"] = {"delivery_tag": delivery_tag}
    message["_deleteOnPost"].add("ack_id")
    return message


def _make_retry(put, retry_count_max=0):
    retry = object.__new__(Retry)
    retry.o = types.SimpleNamespace(batch=0, retryCountMax=retry_count_max)
    retry.download_retry = types.SimpleNamespace(put=put)
    retry.download_retry_name = "work_retry"
    retry.post_retry = _EmptyQueue()
    return retry


def _make_flow(messages, retry, events):
    flow = object.__new__(Flow)
    flow.o = types.SimpleNamespace(publishers=[])
    flow.worklist = types.SimpleNamespace(
        ok=[], incoming=[], rejected=[], failed=messages, failed_ackable=[], failed_pending=[], directories_ok=[])
    flow.plugins = {"after_work": [retry.after_work]}
    flow._logLevel_debug = False
    flow.do = MagicMock()
    flow.stop_request = MagicMock()
    failed_message_ids = {id(message) for message in messages}

    def ack(acknowledged):
        failed_acknowledged = [
            message for message in acknowledged if id(message) in failed_message_ids and "ack_id" in message]
        if failed_acknowledged:
            events.append("ack")
            for message in failed_acknowledged:
                del message["ack_id"]

    flow.ack = ack
    return flow


def test_work_persists_failed_message_before_acknowledging_it():
    message = _make_message()
    events = []

    def put(messages):
        assert messages == [message]
        assert "ack_id" in message
        events.append("retry_put")

    retry = _make_retry(put)
    flow = _make_flow([message], retry, events)

    Flow.work(flow)

    assert events == ["retry_put", "ack"]
    assert "ack_id" not in message
    assert flow.worklist.failed == []
    flow.stop_request.assert_not_called()


def test_work_defers_ack_until_retry_persistence_recovers():
    message = _make_message()
    events = []

    def put(messages):
        assert messages == [message]
        events.append("retry_put")
        raise OSError("retry queue unavailable")

    retry = _make_retry(put)
    flow = _make_flow([message], retry, events)

    Flow.work(flow)

    assert events == ["retry_put"]
    assert "ack_id" in message
    assert flow.worklist.failed == []
    assert flow.worklist.failed_pending == [message]
    flow.stop_request.assert_not_called()

    def succeeding_put(messages):
        assert messages == [message]
        assert "ack_id" in message
        events.append("retry_put")

    retry.download_retry.put = succeeding_put
    Flow.work(flow)

    assert events == ["retry_put", "retry_put", "ack"]
    assert "ack_id" not in message
    assert flow.worklist.failed_pending == []


def test_filter_does_not_ack_failed_messages_before_work_retry():
    message = _make_message()
    acknowledged = []
    flow = object.__new__(Flow)
    flow.o = types.SimpleNamespace(directory="/tmp")
    flow.worklist = types.SimpleNamespace(
        ok=[], incoming=[], rejected=[], failed=[message], failed_ackable=[], failed_pending=[], directories_ok=[])
    flow.plugins = {"after_accept": []}
    flow._logLevel_debug = False
    flow._stop_requested = False
    flow.have_vip = True
    flow.ack = lambda messages: acknowledged.extend(messages)

    Flow.filter(flow)

    assert message not in acknowledged
    assert "ack_id" in message
    assert flow.worklist.failed == [message]


def test_work_does_not_ack_any_message_after_partial_retry_put():
    messages = [_make_message(1), _make_message(2)]
    events = []
    persisted = []

    def put(to_retry):
        persisted.append(to_retry[0])
        events.append("partial_retry_put")
        raise OSError("retry queue failed after a partial write")

    retry = _make_retry(put)
    flow = _make_flow(messages, retry, events)

    Flow.work(flow)

    assert persisted == [messages[0]]
    assert events == ["partial_retry_put"]
    assert all("ack_id" in message for message in messages)
    assert flow.worklist.failed_ackable == []
    assert flow.worklist.failed_pending == messages
    flow.stop_request.assert_not_called()


def test_retry_limit_acks_entire_handled_batch_after_put():
    eligible = _make_message(1)
    eligible["_isRetry"] = 0
    exhausted = _make_message(2)
    exhausted["_isRetry"] = 1
    messages = [eligible, exhausted]
    events = []
    persisted = []

    def put(to_retry):
        persisted.extend(to_retry)
        events.append("retry_put")

    retry = _make_retry(put, retry_count_max=1)
    flow = _make_flow(messages, retry, events)

    Flow.work(flow)

    assert persisted == [eligible]
    assert events == ["retry_put", "ack"]
    assert all("ack_id" not in message for message in messages)
    assert flow.worklist.failed == []
    assert flow.worklist.failed_ackable == []
    flow.stop_request.assert_not_called()


def test_retry_limit_does_not_require_store_for_exhausted_batch():
    exhausted = _make_message()
    exhausted["_isRetry"] = 1
    put = MagicMock(side_effect=OSError("retry queue unavailable"))
    retry = _make_retry(put, retry_count_max=1)
    events = []
    flow = _make_flow([exhausted], retry, events)

    Flow.work(flow)

    put.assert_not_called()
    assert events == ["ack"]
    assert "ack_id" not in exhausted
    assert flow.worklist.failed == []
    assert flow.worklist.failed_pending == []


@pytest.mark.parametrize("debug", [False, True])
def test_retry_message_without_ack_id_survives_put_failure_and_post_cycle(debug):
    message = Message()
    events = []
    persisted = []
    fail_put = True

    def put(to_retry):
        nonlocal fail_put
        events.append("retry_put")
        if fail_put:
            fail_put = False
            raise OSError("retry queue unavailable")
        persisted.extend(to_retry)

    retry = _make_retry(put)
    flow = _make_flow([message], retry, events)
    flow._logLevel_debug = debug

    Flow.work(flow)

    assert flow.worklist.failed == []
    assert flow.worklist.failed_pending == [message]

    flow.o.post_broker = False
    flow._runCallbackMetrics = MagicMock()
    Flow.post(flow, 0)

    assert flow.worklist.failed_pending == [message]

    Flow.work(flow)

    assert events == ["retry_put", "retry_put"]
    assert persisted == [message]
    assert flow.worklist.failed == []
    assert flow.worklist.failed_pending == []
    assert flow.worklist.failed_ackable == []
    flow.stop_request.assert_not_called()


def test_after_accept_does_not_dequeue_more_retries_while_persistence_is_pending():
    retry = object.__new__(Retry)
    retry.o = types.SimpleNamespace(retry_refilter=False)
    retry.download_retry = MagicMock()
    retry.download_retry.__len__.return_value = 1
    worklist = types.SimpleNamespace(incoming=[], failed_pending=[Message()])

    retry.after_accept(worklist)

    retry.download_retry.get.assert_not_called()


def test_one_shot_flow_sleeps_between_pending_persistence_attempts(monkeypatch):
    flow = object.__new__(Flow)
    flow.o = types.SimpleNamespace(
        component="post",
        config="retry_test",
        housekeeping=300,
        hostdir="/tmp",
        logLevel="info",
        messageCountMax=0,
        messageRateMax=0,
        messageRateMin=0,
        no=0,
        retryEmptyBeforeExit=False,
        sleep=-1,
        statehost=False,
    )
    flow.plugins = {"load": []}
    flow.metrics = {"flow": {"cpuTime": 1}}
    flow.worklist = types.SimpleNamespace(
        incoming=[], ok=[], rejected=[], failed=[], failed_ackable=[], failed_pending=[Message()])
    flow._stop_requested = False
    flow.loadCallbacks = MagicMock(return_value=True)
    flow._run_vip_update = MagicMock(side_effect=lambda: setattr(flow, "have_vip", False))
    flow._runHousekeeping = MagicMock(return_value=float("inf"))
    flow.filter = MagicMock()
    flow.post = MagicMock()
    flow.close = MagicMock()
    sleeps = []
    work_calls = 0
    current_time = 0

    def work():
        nonlocal work_calls
        work_calls += 1
        if work_calls == 2:
            flow.worklist.failed_pending = []

    def run_callbacks(entry_point):
        if entry_point == "please_stop":
            flow._stop_requested = True

    def now():
        nonlocal current_time
        current_time += 0.001
        return current_time

    flow.work = work
    flow.runCallbacksTime = MagicMock(side_effect=run_callbacks)
    monkeypatch.setattr("sarracenia.config.get_pid_filename", lambda *args: "/tmp/sarracenia-test.pid")
    monkeypatch.setattr("sarracenia.flow.nowflt", now)
    monkeypatch.setattr("sarracenia.flow.time.sleep", lambda seconds: sleeps.append(seconds))

    Flow.run(flow)

    assert work_calls == 2
    assert sleeps
    assert all(seconds > 0 for seconds in sleeps)
    flow.close.assert_called_once_with()
