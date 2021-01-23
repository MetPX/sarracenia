#!/usr/bin/python3
"""
this plugin use ENV  MAX_MESSAGES to stop the process when this limit of messages is reatch

CAUTION: puts the process in strange state once limit is reached
         trying to  start/restart  the process will simply stop.

"""


class Msg_Stopper(object):
    def __init__(self, parent):
        self.msg_count = 0

    def on_message(self, parent):
        import os
        logger = parent.logger

        # if not defined... max is huge
        msg_max = 9999999
        maxstr = os.environ.get('MAX_MESSAGES')
        if maxstr: msg_max = int(maxstr)

        if self.msg_count >= msg_max: self.stop(parent)

        self.msg_count += 1

        return True

    # restoring msg_count
    def on_start(self, parent):

        msg_total_file = parent.user_cache_dir + os.sep
        msg_total_file += 'msg_stopper_plugin_%.4d.vars' % parent.instance

        if not os.path.isfile(msg_total_file): return True

        fp = open(msg_total_file, 'r')
        line = fp.read(8192)
        fp.close()

        line = line.strip('\n')
        words = line.split()

        self.msg_count = int(words[0])

        return True

    # saving msg_count
    def on_stop(self, parent):

        msg_total_file = parent.user_cache_dir + os.sep
        msg_total_file += 'msg_stopper_plugin_%.4d.vars' % parent.instance

        fp = open(msg_total_file, 'w')
        line = "%d\n" % self.msg_count
        fp.write('%d')
        fp.close()

        return True

    # stop process
    def stop(self, parent):
        import subprocess
        cmd = []
        cmd.append(parent.program_name)
        if parent.user_args and len(parent.user_args) > 0:
            cmd.extend(parent.user_args)
        if parent.user_config: cmd.append(parent.user_config)

        cmd.append('stop')

        parent.logger.info("msg_stopper triggering %s" % cmd)
        parent.run_command(cmd)

        return


self.plugin = 'Msg_Stopper'
