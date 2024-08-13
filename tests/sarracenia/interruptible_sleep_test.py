import pytest
from tests.conftest import *
#from unittest.mock import Mock

import datetime
import os
import signal
import subprocess
from sarracenia.interruptible_sleep import interruptible_sleep

class SleepThing():
    def __init__(self):
        self._stop_requested = False
        self.other_name = False
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, stack):
        self._stop_requested = True
        self.other_name = True

def test_interruptible_sleep():
    st = SleepThing()
    stime = 10

    # Test that sleep sleeps for the right amount of time when not interrupted
    before_time = datetime.datetime.now()
    result = interruptible_sleep(stime, st)
    after_time = datetime.datetime.now()
    assert (result == False)
    assert ( (after_time - before_time).seconds == stime)

    # Test that the sleep behaves correctly when interrupted
    # send a SIGINT to this process after 5 seconds:
    cmdline = f"""bash -c '/usr/bin/sleep 5; kill -SIGTERM {os.getpid()};' &"""
    subprocess.run(cmdline, shell=True)
    before_time = datetime.datetime.now()
    result = interruptible_sleep(stime, st)
    after_time = datetime.datetime.now()
    assert result
    assert ( (after_time - before_time).seconds == 5)

    # Test using a different nap_time
    st = SleepThing()
    # send a SIGINT to this process after 5 seconds:
    cmdline = f"""bash -c '/usr/bin/sleep 5; kill -SIGTERM {os.getpid()};' &"""
    subprocess.run(cmdline, shell=True)
    before_time = datetime.datetime.now()
    result = interruptible_sleep(stime, st, nap_time=1)
    after_time = datetime.datetime.now()
    assert result
    assert ( (after_time - before_time).seconds == 5)


    # Test using a different attribute name
    st = SleepThing()
    # send a SIGINT to this process after 5 seconds:
    cmdline = f"""bash -c '/usr/bin/sleep 5; kill -SIGTERM {os.getpid()};' &"""
    subprocess.run(cmdline, shell=True)
    before_time = datetime.datetime.now()
    result = interruptible_sleep(stime, st, stop_flag_name = 'other_name')
    after_time = datetime.datetime.now()
    assert result
    assert ( (after_time - before_time).seconds == 5)



