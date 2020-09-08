#!/usr/bin/python3
"""
  msg_save converts a consuming component into one that writes the queue into a file.

  If there is some sort of problem with a component, then add 

  on_message msg_save

  and restart.

  the messages will accumulate in a save file in ~/.cache/<component>/<config>/ ??<instance>.save

  msg_save takes 'msg_save_file' as an argument.

  to msg_save_file, will be added _9999.sav where the 9999 represents the instance number.
  As instances run in parallel, rather than sychronizing access, just writes to one file per instance.
  
  
  when the situation is returned to normal (you want the component to process the data as normal):
 
  - remove the on_message msg_save
  - note the queue this configuration is using to read (should be in the log on startup.)
  - run an sr_shovel with -restore_to_queue and the queue name.

"""


class Msg_Save(object):
    def __init__(self, parent):

        if not hasattr(parent, "msg_save_file"):
            parent.logger.error(
                "msg_save: setting msg_save_path setting is mandatory")

        parent.msg_save_file = open(
            parent.msg_save_file + parent.save_path[-10:], "a")

        parent.logger.debug("msg_save initialized")

    def on_message(self, parent):

        import json

        msg = parent.msg

        parent.msg_save_file.write(
            json.dumps([msg.topic, msg.headers, msg.notice]) + '\n')

        parent.msg_save_file.flush()

        parent.logger.info(
            "msg_save saving msg with topic:%s (aborting further processing)" %
            msg.topic)

        return False


msg_save = Msg_Save(self)

self.on_message = msg_save.on_message
