#!/usr/bin/python3
"""
default on_heartbeat handler that restarts components to deal with memory leaks.

One can specify a specific memory limit with the *hb_memory_max* setting.
By default, there is no specific memory limit. The program first processes *hb_memory_baseline_file*
(default 100) numer of items (messages in for subscribers, messages posted for posting programs). Once that 
number of files has been processed, the amount of memory in use is determined, and the memory max threshold is set 
to *memory_multiplier* times (default 3) that. If memory use ever exceeds the max, then the plugin triggers a restart,
which should reduce the memory consumption.

options:

hb_memory_max - hard code a maximum memory consumption to tolerate.

If there is no max given, then

hb_memory_max will be set to:  <baseline_memory> * <multiplier>

 the following options will have an effect:

hb_memory_baseline_files (default: 100)

  how many files to process before measuring to establish the baseline memory usage.

hb_memory_multiplier (default: 3)

  how much you want to allow the component to grow before you call it a memory leak.
  It could be normal for memory usage to grow, especially if plugins store data in memory.
  
"""


class Hb_Memory(object):
    def __init__(self, parent):

        self.threshold = None
        self.file_count = None

        # make parent know about these possible options

        parent.declare_option('hb_memory_max')
        parent.declare_option('hb_memory_baseline_file')
        parent.declare_option('hb_memory_multiplier')

    def perform(self, parent):
        import os, psutil, humanize
        self.logger = parent.logger

        p = psutil.Process()
        if hasattr(p, 'memory_info'):
            mem = p.memory_info()
        else:
            mem = p.get_memory_info()

        ost = os.times()
        self.logger.info("hb_memory cpu_times user=%s system=%s elapse=%s" %
                         (ost.user, ost.system, ost.elapsed))

        if self.file_count == None:
            if hasattr(parent, 'hb_memory_baseline_file'):
                if type(parent.hb_memory_baseline_file) is list:
                    self.file_count = int(parent.hb_memory_baseline_file[0])
                else:
                    self.file_count = int(parent.hb_memory_baseline_file)
            else:
                self.file_count = 100

        if self.threshold == None:
            if hasattr(parent, 'hb_memory_multiplier'):
                if type(parent.hb_memory_multiplier) is list:
                    parent.hb_memory_multiplier = parent.hb_memory_multiplier[
                        0]
                parent.hb_memory_multiplier = float(
                    parent.hb_memory_multiplier)
            else:
                parent.hb_memory_multiplier = 3

            if hasattr(parent, 'hb_memory_max'):
                if type(parent.hb_memory_max) is list:
                    parent.hb_memory_max = parent.hb_memory_max[0]

                self.threshold = parent.chunksize_from_str(
                    parent.hb_memory_max)

            if (parent.publish_count < self.file_count) and (
                    parent.message_count < self.file_count):
                self.logger.info("hb_memory current usage: %s, accumulating count (%d or %d of %d so far) before setting threshold" \
                      % ( humanize.naturalsize(mem.vms,binary=True), parent.publish_count, parent.message_count, self.file_count) )
                return True

        # from doc memory_full_info()  # "real" USS memory usage (Linux, OSX, Win only)
        # mem(rss=10199040, vms=52133888, shared=3887104, text=2867200, lib=0,\
        #          data=5967872, dirty=0, uss=6545408, pss=6872064, swap=0)

        if self.threshold == None:
            self.threshold = int(parent.hb_memory_multiplier * mem.vms)
            self.logger.info("hb_memory threshold defaulted to %s" %
                             humanize.naturalsize(self.threshold, binary=True))

        parent.logger.info( "hb_memory, current usage: %s trigger restart if increases past: %s " % \
            ( humanize.naturalsize(mem.vms,binary=True), humanize.naturalsize(self.threshold,binary=True) ) )

        if mem.vms > self.threshold: self.restart(parent)

        return True

    def restart(self, parent):
        import subprocess
        cmd = []
        cmd.append(parent.program_name)
        if parent.user_args and len(parent.user_args) > 0:
            cmd.extend(parent.user_args)
        if parent.user_config: cmd.append(parent.user_config)

        cmd.append('restart')

        parent.logger.info("hb_memory triggering %s" % cmd)
        parent.run_command(cmd)

        return


hb_memory = Hb_Memory(self)
self.on_heartbeat = hb_memory.perform
