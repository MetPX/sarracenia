import datetime
import logging
import pytest
import types
from tests.conftest import *

import sarracenia.config
import sarracenia.flowcb.scheduled

logger = logging.getLogger(__name__)

UTC = datetime.timezone.utc
DAY = datetime.date(2026, 1, 15)


def at(hour, minute, second=0, days=0):
    """ a time on DAY (or days after it), UTC """
    return datetime.datetime.combine(DAY + datetime.timedelta(days=days),
                                     datetime.time(hour, minute, second, tzinfo=UTC))


def build_options():
    o = sarracenia.config.default_config()
    o.component = 'flow'
    o.config = 'ex1'
    o.action = 'start'

    o.parse_line(o.component, o.config, "flow/ex1", 1, "no 1")
    o.parse_line(o.component, o.config, "", 1, "no 1")
    o.finalize()
    return o


class Clock:
    """
       replaces the clock the scheduled module reads (datetime.datetime.now and time.time),
       so the tests give the same result whatever time of day they run. Set clock.now to move it.
    """

    def __init__(self, monkeypatch, now):
        self.now = now
        clock = self

        class FakeDatetime(datetime.datetime):
            @classmethod
            def now(cls, tz=None):
                return clock.now

        monkeypatch.setattr(sarracenia.flowcb.scheduled, 'datetime',
                            types.SimpleNamespace(datetime=FakeDatetime, time=datetime.time,
                                                  timedelta=datetime.timedelta, timezone=datetime.timezone))
        monkeypatch.setattr(sarracenia.flowcb.scheduled, 'time',
                            types.SimpleNamespace(time=lambda: clock.now.timestamp()))


@pytest.fixture
def clock(monkeypatch):
    return Clock(monkeypatch, at(0, 5))


def scheduled(hour=[], minute=[], time=[], interval=0):
    o = build_options()
    o.scheduled_hour = hour
    o.scheduled_minute = minute
    o.scheduled_time = time
    o.scheduled_interval = interval
    return sarracenia.flowcb.scheduled.Scheduled(o)


def gathers_at(me, clock, when):
    clock.now = when
    gathered, messages = me.gather(1)
    return gathered


def test_update_appointments(clock):
    midnight = at(0, 0)

    me = scheduled(time=["12:40", "7:37"])
    me.update_appointments(midnight)
    assert me.appointments == [at(7, 37), at(12, 40)]

    me = scheduled(hour=['1', '3', '5', ' 7', ' 9', ' 13', '21', '23'],
                   minute=['1,3,5', ' 7', ' 9', ' 13', ' 15', ' 51', '53'])
    me.update_appointments(midnight)
    assert len(me.appointments) == 72

    me = scheduled(hour=["2", "4"], minute=["2"], time=["12:40", "7:37"])
    me.update_appointments(midnight)
    assert me.appointments == [at(2, 2), at(4, 2), at(7, 37), at(12, 40)]

    me = scheduled(hour=["2", "4"])
    me.update_appointments(midnight)
    assert me.appointments == [at(2, 0), at(4, 0)]

    me = scheduled(minute=["2", "4"])
    me.update_appointments(midnight)
    assert len(me.appointments) == 48

    # appointments already passed today are left out
    me.update_appointments(at(0, 5))
    assert me.appointments[0] == at(1, 2)
    assert len(me.appointments) == 46

    me = scheduled()
    me.update_appointments(midnight)
    assert me.appointments == []


@pytest.mark.parametrize("schedule,expected", [
    (dict(hour=['1'], minute=['1']), [at(1, 1), at(1, 1, days=1)]),
    (dict(hour=["2", "4"], minute=["2"], time=["12:40", "7:37"]),
     [at(2, 2), at(4, 2), at(7, 37), at(12, 40), at(2, 2, days=1)]),
    (dict(hour=["2", "4"]), [at(2, 0), at(4, 0), at(2, 0, days=1)]),
    (dict(minute=["2", "4"]), [at(1, 2), at(1, 4), at(2, 2)]),
    (dict(), [at(0, 10), at(0, 15), at(0, 20)]),
])
def test_gather_follows_schedule(clock, schedule, expected):
    """ starting at 00:05, gather only when each appointment comes up, not a second before """
    me = scheduled(**schedule)
    assert not gathers_at(me, clock, at(0, 5))

    for when in expected:
        assert not gathers_at(me, clock, when - datetime.timedelta(seconds=1))
        assert gathers_at(me, clock, when)
        assert not gathers_at(me, clock, when)


def test_gather_scheduled_interval(clock):
    """ with scheduled_interval, gather right away when started, then once per interval """
    me = scheduled(interval=3600)
    assert gathers_at(me, clock, at(0, 5))
    assert not gathers_at(me, clock, at(1, 4, 59))
    assert gathers_at(me, clock, at(1, 5))
    assert not gathers_at(me, clock, at(1, 5))


def test_gather_scheduled_interval_overrides_appointments(clock):
    me = scheduled(time=["12:40", "7:37"], interval=3600)
    assert gathers_at(me, clock, at(0, 5))
    assert gathers_at(me, clock, at(1, 5))
    assert gathers_at(me, clock, at(2, 5))


def test_gather_late_runs_once(clock):
    """ a flow that wakes up after several appointments went by gathers once, then waits for the next one """
    me = scheduled(hour=["2", "4"], minute=["2"], time=["12:40", "7:37"])
    assert gathers_at(me, clock, at(5, 0))
    assert not gathers_at(me, clock, at(5, 0))
    assert not gathers_at(me, clock, at(7, 36, 59))
    assert gathers_at(me, clock, at(7, 37))


def test_gather_late_on_another_appointment_runs_once(clock):
    """ waking up late exactly on a later appointment counts as that appointment, not a second gather """
    me = scheduled(hour=["2", "4"], minute=["2"], time=["12:40", "7:37"])
    assert gathers_at(me, clock, at(4, 2))
    assert not gathers_at(me, clock, at(4, 2))
    assert gathers_at(me, clock, at(7, 37))


def test_calc_next_gather_time(clock):
    """ calc_next_gather_time is called right after a gather, the appointment just used is dropped """
    me = scheduled(hour=["2", "4"], minute=["2"], time=["12:40", "7:37"])
    assert me.next_gather_time == at(2, 2)
    assert me.appointments == [at(2, 2), at(4, 2), at(7, 37), at(12, 40)]

    me.calc_next_gather_time(at(2, 2))
    assert me.next_gather_time == at(4, 2)
    assert me.appointments == [at(4, 2), at(7, 37), at(12, 40)]

    # late by more than one appointment: the ones that went by are dropped too
    me.calc_next_gather_time(at(8, 0))
    assert me.next_gather_time == at(12, 40)
    assert me.appointments == [at(12, 40)]

    # none left today: the schedule starts over tomorrow
    me.calc_next_gather_time(at(12, 40))
    assert me.next_gather_time == at(2, 2, days=1)
    assert me.appointments == [at(2, 2, days=1), at(4, 2, days=1), at(7, 37, days=1), at(12, 40, days=1)]


def test_calc_next_gather_time_after_missed_appointments(clock):
    me = scheduled(hour=["2", "4"], minute=["2"], time=["12:40", "7:37"])
    me.calc_next_gather_time(at(13, 0))
    assert me.next_gather_time == at(2, 2, days=1)


def test_calc_next_gather_time_defaults_to_now(clock):
    me = scheduled(hour=["2", "4"], minute=["2"])
    clock.now = at(3, 0)
    me.calc_next_gather_time()
    assert me.next_gather_time == at(4, 2)


def test_calc_next_gather_time_interval(clock):
    me = scheduled(interval=3600)
    me.calc_next_gather_time(at(1, 0))
    assert me.next_gather_time == at(2, 0)


def test_calc_next_gather_time_default_wait(clock):
    me = scheduled()
    assert me.next_gather_time == at(0, 10)
    me.calc_next_gather_time(at(1, 0))
    assert me.next_gather_time == at(1, 5)
