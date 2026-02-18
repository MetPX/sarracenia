'''
Description
--------------------------------

    Add file contents `inline` (or inside) the sarracenia message after work has been completed.
    As of July 2025, sarracenia will only add the file contents in the sarracenia message 
    from the built-in gather entry point (flowcb.gather.file.py). 

    This plugin allows us to place the recently downloaded data into the sarracenia message. 
    We'd want to do this in the case a client would prefer to have the data included in the message, 
    instead of providing a link for downloading.

Usage
--------------------------------

    This plugin is already being invoked from the list of flow callbacks when the ``inline`` option 
    is set to True.
    

'''

from sarracenia.flowcb import FlowCB
import logging

logger = logging.getLogger(__name__)


class Add_inline(FlowCB):
    def __init__(self, options):
        super().__init__(options,logger)
        self.o = options

    def after_work(self, worklist):

        for msg in worklist.ok:
            if 'content' not in msg:
                msg.putContentInline(self.o)
