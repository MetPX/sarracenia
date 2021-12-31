#!/usr/bin/python3
"""
Default `on_heartbeat` handler that restarts components to deal with memory leaks.

The program processes the first `hkMemoryBaseLineFile` items
(messages-in for subscribers, messages-posted for posting programs).
Once processed, the `memory max threshold` is set to `memory_multiplier` times the current memory in use.
If memory use ever exceeds the max, then the plugin triggers a restart, which should reduce the memory consumption.

Parameters
----------

hkMemoryMax : size (default: infinity)
    Hard coded maximum tolerable memory consumption.
    Must be suffixed with k/m/g for Kilo/Mega/Giga byte values.
    If there is no max given, then `hkMemoryMax` will be set to:  `<baseline_memory> * <multiplier>`
    The following options will have an effect:

hkMemoryBaseLineFile : int, optional (default: 100)
    How many files to process before measuring to establish the baseline memory usage.

hkMemoryMultiplier : int, optional (default: 3)
    How much you want to allow the component to grow before you call it a memory leak.
    It could be normal for memory usage to grow, especially if plugins store data in memory.


Returns
-------
    Nothing, restarts components if memory usage is outside of set thresholds.
"""

from _typeshed import Self
import logging
import humanize
import os
import psutil
from sarracenia.config import chunksize_from_str
from sarracenia.flowcb import FlowCB
from sr import sr_GlobalState

logger = logging.getLogger(__name__)


class Memory(FlowCB):

    def __init__(self, options):
        self.o = options
        self.o.add_option('hkMemoryMax', 'size')
        self.o.add_option('hkMemoryBaselineFile', 'count', 100)
        self.o.add_option('hkMemoryMultiplier', 'count', 3)

        self.threshold = None
        self.file_count = None

    def on_housekeeping(self):
        logger.error('*Screams into the void\n\n\t\tAAAAHHHHHHHH\n\n...*')
        logger.info('*Screams into the void\n\n\t\tAAAAHHHHHHHH\n\n...*')
        self.checkMemory(self)

    def checkMemory(self):
        proc = psutil.Process()
        if hasattr(proc, 'memory_info'):
            # “Virtual Memory Size”, this is the total amount of virtual memory used by the process in bytes.
            mem = proc.memory_info().vms
        else:
            # FIXME Is this a legacy smell? psutil Doesn't have this function now..
            mem = proc.get_memory_info().vms

        ost = os.times()
        logger.info("Memory cpu_times user=%s system=%s elapse=%s" %
                    (ost.user, ost.system, ost.elapsed))

        if self.file_count is None:
            if hasattr(self.o, 'hkMemoryBaseLineFile'):
                self.file_count = int(self.o.hkMemoryBaseLineFile)
            else:
                self.file_count = 100

        if self.threshold is None:
            if hasattr(self.o, 'hkMemoryMultiplier'):
                self.o.hkMemoryMultiplier = float(self.o.hkMemoryMultiplier)
            else:
                self.o.hkMemoryMultiplier = 3

            if hasattr(self.o, 'hkMemoryMax'):
                self.threshold = chunksize_from_str(self.o.hkMemoryMax)

            if (self.o.publish_count < self.file_count) and (
                    self.o.message_count < self.file_count):
                logger.info("Current mem usage: %s, accumulating count (%d or %d / %d so far) before setting threshold"
                            % (humanize.naturalsize(mem, binary=True),
                                self.o.publish_count,
                                self.o.message_count,
                                self.file_count))
                return True

        if self.threshold is None:
            self.threshold = int(self.o.hkMemoryMultiplier * mem)
            logger.info("hb_memory threshold defaulted to %s" % humanize.naturalsize(self.threshold, binary=True))

        logger.info("hb_memory, current usage: %s trigger restart if increases past: %s " %
                    (humanize.naturalsize(mem, binary=True), humanize.naturalsize(self.threshold, binary=True)))

        if mem > self.threshold:
            self.restart(self)

        return True

    def restart(self):
        """
        """
        cmd = []
        # TODO: Is this looking for "sarra"/"sr"/"src"/"sr3" ??
        #  May be wanting to use sys.argv[0]
        cmd.append(self.o.program_name)

        # TODO: Need to figure out where to access these vars (user_{args,config})
        #  May be wanting to use  sys.argv[1:-1]:
        if self.o.user_args and len(self.o.user_args) > 0:
            cmd.extend(self.o.user_args)
        if self.o.user_config:
            cmd.append(self.o.user_config)

        cmd.append('restart')

        logger.info("hb_memory triggering %s" % cmd)
        sr_GlobalState.run_command(cmd)

        return

# FIXME: A list of things and stuff..
# - Confirm that the options are actually renamed
# - Add the entry point in sarracenia/config.py ?somewhere?
# - Figure out where restart can get args ($*) from.. (sarracenia.config.Config)
# - Actually run the plugin and see what explodes...
