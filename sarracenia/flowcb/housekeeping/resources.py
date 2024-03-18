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
from sarracenia.flowcb import FlowCB
from sarracenia import naturalSize, naturalTime
from sarracenia.featuredetection import features

if features['process']['present']:
    import psutil

import sys

logger = logging.getLogger(__name__)

class Resources(FlowCB):
    def __init__(self, options):
        super().__init__(options,logger)
        # Set option to neg value to determine if user set in config
        self.o.add_option('MemoryMax', 'size', '0')
        self.o.add_option('MemoryBaseLineFile', 'count', 100)
        self.o.add_option('MemoryMultiplier', 'float', 3)

        self.threshold = None
        ''' Per-process maximum memory footprint that is considered too large, forcing a process restart.'''
        self.transferCount = 0
        self.msgCount = 0

    def on_housekeeping(self):
        if features['process']['present']:
            mem = psutil.Process().memory_info().vms
        else:
            mem = 0

        ost = os.times()
        logger.info(f"Current cpu_times: user={ost.user} system={ost.system}")

        # We must set a threshold **after** the config file has been parsed.
        if self.threshold is None:
            # If the config set something, use it.
            if self.o.MemoryMax != 0:
                self.threshold = self.o.MemoryMax

            if self.threshold is None:
                # No user input set, now to figure out what our baseline memory usage is at a steady state
                #   Process MemoryBaseLineFile(s)+ then get a memory reading before setting memory restart threshold.
                if (self.transferCount < self.o.MemoryBaseLineFile) and (
                        self.msgCount < self.o.MemoryBaseLineFile):
                    # Not enough files processed for steady state, continue to wait..
                    logger.info(
                        f"Current mem usage: {naturalSize(mem)}, accumulating count "
                        f"({self.transferCount} or {self.msgCount}/{self.o.MemoryBaseLineFile} so far) "
                        f"before self-setting threshold")
                    return True

                self.threshold = int(self.o.MemoryMultiplier * mem)

            logger.info(f"Memory threshold set to: {naturalSize(self.threshold)}")

        logger.info(
            f"Current Memory usage: {naturalSize(mem)} / "
            f"{naturalSize(self.threshold)} = {(mem/self.threshold):.2%}"
        )

        if mem > self.threshold:
            self.restart()
        # self.restart()

        return True

    def restart(self):
        """
        Do an in-place restart of the current process (keeps pid).
        Gets a new memory stack/heap, keeps all file descriptors but replaces the buffers.
        """
        logger.info(
            f"Memory threshold surpassed! Triggering a restart for '{sys.argv}' via '{sys.executable}'"
        )
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

    def after_work(self, worklist):
        self.transferCount += len(worklist.ok)
        # if self.threshold is not None:
        #    TODO: Remove this callback when issue #444 is implemented

    def after_accept(self, worklist):
        self.msgCount += len(worklist.incoming)
        # if self.threshold is not None:
        #    TODO: Remove this callback when issue #444 is implemented
