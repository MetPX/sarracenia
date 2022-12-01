"""
Plugin save.py:
    Converts a consuming component into one that writes the queue into a file. 
    If there is some sort of problem with a component, then add callback save and restart.

    The messages will accumulate in a save file in ~/.cache/<component>/<config>/ ??<instance>.save
    When the situation is returned to normal (you want the component to process the data as normal):
    * remove the callback save
    * note the queue this configuration is using to read (should be in the log on startup.)
    * run an sr_shovel with -restore_to_queue and the queue name.

Options:
    save.py takes 'msgSaveFile' as an argument.
    "_9999.sav" will be added to msgSaveFile, where the 9999 represents the instance number.
    As instances run in parallel, rather than sychronizing access, just writes to one file per instance.

Usage:
    callback accept.save
    msgSaveFile x
"""

import json
import logging
from sarracenia.flowcb import FlowCB

logger = logging.getLogger('__name__')


class Save(FlowCB):
    def __init__(self, options):
        self.o = options

        if not hasattr(self.o, "msgSaveFile"):
            logger.error(
                "msg_save: setting msg_save_path setting is mandatory")

        self.o.msgSaveFile = open(self.o.msgSaveFile + self.o.save_path[-10:],
                                  "a")
        logger.debug("msg_save initialized")

    def after_accept(self, worklist):
        for message in worklist.incoming:
            self.o.msgSaveFile.write(
                json.dumps([
                    message['topic'], message['headers'], message['notice']
                ]) + '\n')
            self.o.msgSaveFile.flush()
            logger.info(
                "msg_save saving msg with topic:%s (aborting further processing)"
                % message['topic'])
