"""
Default on_housekeeping handler that:
- Logs Memory and CPU usage.
- Restarts components to deal with memory leaks.

If `MemoryMax` is not in the config, it is automatically calculated with the following procedure:

1. The plugin processes the first `MemoryBaseLineFile` items to reach a steady state.
   - Subscribers process messages-in
   - Posting programs process messages-posted
2. Set `MemoryMax` threshold to `MemoryMultiplier` * (memory usage at time steady state)

If memory use ever exceeds the `MemoryMax` threshold, then the plugin triggers a restart, reducing memory consumption.

Parameters:

MemoryMax : size (default: none)
    Hard coded maximum for tolerable memory consumption.
    Must be suffixed with k/m/g for Kilo/Mega/Giga byte values.
    If not set then the following options will have an effect:

MemoryBaseLineFile : int, optional (default: 100)
    How many files to process before measuring to establish the baseline memory usage.
    (how many files are expected to process before a steady state is reached)

MemoryMultiplier : int, optional (default: 3)
    How many times past the steady state memory footprint you want to allow the component to grow before restarting.
    It could be normal for memory usage to grow, especially if plugins store data in memory.


Returns:
    Nothing, restarts components if memory usage is outside of configured thresholds.
"""

import logging

import os
import time
import signal

from sarracenia.flowcb import FlowCB
from sarracenia import naturalSize, naturalTime, user_cache_dir, nowstr, nowflt
from sarracenia.featuredetection import features

if features['process']['present']:
    import psutil

import sys

logger = logging.getLogger(__name__)

class Resources(FlowCB):
    def __init__(self, options):
        super().__init__(options,logger)
        # Set option to neg value to determine if user set in config
        self.o.add_option('CpuTimeMax', 'float', '0')
        self.o.add_option('MemoryMax', 'size', '0')
        self.o.add_option('MemoryBaseLineFile', 'count', 100)
        self.o.add_option('MemoryMultiplier', 'float', 3)

        if type(self.o.MemoryMax) is not str and self.o.MemoryMax > 0:
            self.threshold_memory = self.o.MemoryMax
        else:
            self.threshold_memory = None

        ''' Per-process maximum memory footprint that is considered too large, forcing a process restart.'''
        self.transferCount = 0
        self.msgCount = 0

        if self.o.CpuTimeMax > 0:
            self.cpu_threshold_msg = f" (CpuTimeMax threshold={self.o.CpuTimeMax:.2f})"
        else:
            self.cpu_threshold_msg = ""

        # self.stop_requested is changed by the rest of the sr3 code and can change at almost
        # any time when SIGTERM is sent to this process.
        # this variable specifically tracks if/when *this plugin* initiated the restart
        self.restart_initiated_time = None

    def on_housekeeping(self):
        if features['process']['present']:
            mem = psutil.Process().memory_info().vms
        else:
            mem = 0

        ost = os.times()
        cpu_time_total = ost.system + ost.user
        logger.info(f"Current cpu_times: user={ost.user} system={ost.system} total={cpu_time_total:.2f}{self.cpu_threshold_msg}")

        # check current CPU and memory usage, restart if needed
        if self.threshold_memory is not None and mem > self.threshold_memory and not self.stop_requested:
            logger.info(f"Memory threshold surpassed! Triggering a restart for '{sys.argv}' via '{sys.executable}'")
            self.restart()
        elif self.o.CpuTimeMax > 0 and cpu_time_total > self.o.CpuTimeMax:
            if not self.stop_requested:
                logger.info(f"CPU threshold surpassed! Triggering a restart for '{sys.argv}' via '{sys.executable}'")
            # this is not inside the if, because we want it to run and trigger SIGKILL if needed
            self.restart_reset()

        # User did not set MemoryMax, now to figure out what our baseline memory usage is at a steady state
        if self.threshold_memory is None:
            #   Process MemoryBaseLineFile(s)+ then get a memory reading before setting memory restart threshold.
            if (self.transferCount < self.o.MemoryBaseLineFile) and (self.msgCount < self.o.MemoryBaseLineFile):
                # Not enough files processed for steady state, continue to wait..
                logger.info(
                    f"Current mem usage: {naturalSize(mem)}, accumulating count "
                    f"({self.transferCount} or {self.msgCount}/{self.o.MemoryBaseLineFile} so far) "
                    f"before self-setting threshold")
            else:
                self.threshold_memory = int(self.o.MemoryMultiplier * mem)
                logger.info(f"Memory threshold set to: {naturalSize(self.threshold_memory)}")
        else:
            logger.info(
                f"Current Memory usage: {naturalSize(mem)} / "
                f"{naturalSize(self.threshold_memory)} = {(mem/self.threshold_memory):.2%}"
            )

    def restart(self):
        """
        Do an in-place restart of the current process (keeps pid).
        Gets a new memory stack/heap, keeps all file descriptors but replaces the buffers.
        """
        self.write_restart_statefile()

        # First arg must be the program to be run (absolute path to program)
        # Second arg has to be python for windows, see how this affects the linux side of things..
        # Third arg is the name of the program you wish to run (should be full path to script) plus all the args.
        #   The star unpacks the sys.argv list into the remaining function args

        if sys.platform.startswith(('linux', 'cygwin', 'darwin', 'aix')):
            # Unix* (Linux / Windows/Cygwin / MacOS / AIX) Specific restart
            os.execl(sys.executable, sys.executable, *sys.argv)
        elif sys.platform.startswith('win32'):
            # Windows Specific restart
            os.execl(sys.executable, 'python', *sys.argv)
        else:
            logger.error(
                f'Unknown platform type: "{sys.platform}", attempting default unix process restart..'
            )
            os.execl(sys.executable, sys.executable, *sys.argv)

        # Scream out in agony and die
        logger.critical(
            f'Plugin resources.py:restart() "execl" failed, this should never be logged.'
        )
        exit(1)

    def restart_reset(self):
        """
        Restart the config (new PID, CPU time is reset). By:
        1. Forking to get a new PID
        2. Shutting down the process in the old PID (clean shutdown with SIGTERM)
        3. (Re-)Starting up the process in the new PID
        """

        parent_pid = os.getpid()

        # only fork if we're not already in the middle of a restart
        if not self.stop_requested:
            self.write_restart_statefile() # need to do this before it's done in restart()
            child_pid = os.fork()
        else:
            child_pid = parent_pid

        if child_pid == 0:
            # this is the child
            # not safe to use the logger here until the parent shuts down
            # wait for the parent to shut down
            while self.is_pid_running(parent_pid):
                time.sleep(2)
            logger.info(f"parent PID {parent_pid} has stopped, PID {os.getpid()} taking over")
            logger.debug(f"CPU times in new process: {os.times()}")
            self.restart()
        else:
            # this is the parent, we want to shut down
            if not self.stop_requested:
                self.write_restart_statefile()
                logger.info(f"shutting down PID {parent_pid}, will auto-restart as PID {child_pid}")
                self.stop_requested = True
                self.restart_initiated_time = nowflt()
                os.kill(parent_pid, signal.SIGTERM)
            # if this plugin initiated a restart...
            elif self.restart_initiated_time is not None:
                # ... and a whole housekeeping interval has elapsed since then, something has gone wrong; the SIGTERM
                # failed to shutdown the parent process. We need to kill it.
                if (nowflt() - self.restart_initiated_time) >= self.o.housekeeping:
                    logger.info(f"shutting down PID {parent_pid} by SIGKILL")
                    os.kill(parent_pid, signal.SIGKILL)

    def after_work(self, worklist):
        self.transferCount += len(worklist.ok)
        # if self.threshold_memory is not None:
        #    TODO: Remove this callback when issue #444 is implemented

    def after_accept(self, worklist):
        self.msgCount += len(worklist.incoming)
        # if self.threshold_memory is not None:
        #    TODO: Remove this callback when issue #444 is implemented

    def is_pid_running(self, pid):
        """ return True if ``pid`` is running, False if not
        """
        if features['process']['present']:
            try:
                proc = psutil.Process(pid)
                return proc.is_running()
            except psutil.NoSuchProcess:
                return False
        elif sys.platform.startswith('win32'):
            logger.warning("On Windows, can't check if a PID is running without psutil")
            # hopefully the process shuts down in < 30 seconds
            time.sleep(30)
            return False
        else:
            # Linux only method of checking if process is running
            # stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid-in-python
            try:
                os.kill(pid, 0)
            except OSError:
                return False
            else:
                return True

    def write_restart_statefile(self):
        """ Before triggering a restart, write a state file to prevent other processes (sr3 stop/start/sanity)
            to stop/start it at the same time.
        """
        self.state_file = self.o.cfg_run_dir + os.sep + 'resources_restart'

        with open(self.state_file, "w") as f:
            f.write(nowstr())
