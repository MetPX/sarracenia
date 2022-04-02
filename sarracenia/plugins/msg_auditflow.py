#!/usr/bin/python3
"""
  This plugin is used internally for the flow test.
  It compare files to look for copy errors in a specific directory tree.

  also:
  delete files in the flow test once in all the components' directories.

"""


class Msg_AuditFlow(object):
    def __init__(self, parent):

        parent.declare_option('msg_auditflow_topdir')

        if hasattr(parent, 'msg_auditflow_topdir'):
            if type(parent.msg_auditflow_topdir) is list:
                parent.msg_auditflow_topdir = parent.msg_auditflow_topdir[0]

        parent.auditflow_Atotal = 0
        parent.auditflow_Bgood = 0
        parent.auditflow_BtoAratio = 4

    def on_message(self, parent):
        import os, filecmp
        import os.path
        msg = parent.msg

        middir = msg.new_dir.replace(parent.currentDir + os.sep, '')

        a = "%s/%s/%s/%s" % (parent.msg_auditflow_topdir,
                             "downloaded_by_sub_amqp", middir, msg.new_file)
        parent.auditflow_Atotal += 1
        i = 0

        for d in [
                "downloaded_by_sub_u", "sent_by_tsource2send",
                "posted_by_srpost_test2", "recd_by_srpoll_test1"
        ]:
            i += 1
            b = "%s/%s/%s/%s" % (parent.msg_auditflow_topdir, d, middir,
                                 msg.new_file)
            if os.path.exists(b):
                if filecmp.cmp(a, b):
                    parent.auditflow_Bgood += 1
                else:
                    parent.logger.error(
                        "msg_auditflow: files-%d differ: %s vs. %s " %
                        (i, a, b))
                a = b
            else:
                parent.logger.error(
                    "msg_auditflow: compare-%d failed: %s vs. %s " % (i, a, b))

        for d in [
                "downloaded_by_sub_amqp", "posted_by_srpost_test2",
                "recd_by_srpoll_test1", "posted_by_shim",
                "downloaded_by_sub_cp"
        ]:
            f = "%s/%s/%s/%s" % (parent.msg_auditflow_topdir, d, middir,
                                 msg.new_file)
            parent.logger.info("msg_auditflow delete: %s" % f)
            if os.path.exists(f):
                os.unlink(f)
            else:
                parent.logger.error(
                    "msg_auditflow: file could not be deleted because already gone: %s"
                    % (f))
            # sr_watch running here should propagate the deletion to the other directories.

        tally = (parent.auditflow_Atotal * parent.auditflow_BtoAratio /
                 parent.auditflow_Bgood)
        if (tally > 0.90) and (tally < 1.1):
            so_far = "GOOD"
        else:
            so_far = "BAD"

        parent.logger.info( "msg_auditflow: %s so far ( a: %d b: %d ) \n" % \
           ( so_far, parent.auditflow_Atotal, parent.auditflow_Bgood ) )
        return True


msg_auditflow = Msg_AuditFlow(self)

self.on_message = msg_auditflow.on_message
