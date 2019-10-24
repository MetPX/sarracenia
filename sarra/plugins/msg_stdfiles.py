#!/usr/bin/python3
"""
  a on_msg callback to print the content of the AMQP message.
  one can see clearly the difference between v02 and v03 messages.

"""


class Test_StdFiles(object):
    def __init__(self, parent):
        parent.logger.debug("msg_rawlog initialized")

    def on_message(self, parent):
        import sys
        import subprocess

        msg = parent.msg
        parent.logger.info(
            "stdfiles closed? stdin={}, stdout={}, stderr={}".format(
                sys.stdin.closed, sys.stdout.closed, sys.stderr.closed))
        parent.logger.info(
            "stdfiles fds? stdin={}, stdout={}, stderr={}".format(
                sys.stdin.fileno(), sys.stdout.fileno(), sys.stderr.fileno()))
        parent.logger.info("this is logging")
        print("this is stdout")
        print("this is stderr", file=sys.stderr)
        subprocess.Popen(['/bin/echo', 'this is subprocess stdout'])
        return True


test_stdfiles = Test_StdFiles(self)

self.on_message = test_stdfiles.on_message
