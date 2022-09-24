"""
   Adjust fileOp paths, modifies the paths in file operation fileds, for file renaming,
   removal or links.

   where files from a 'before' directory, are sent by an sr_sender to a 'after' directory.
   This also applies to the HPC mirroring case, where one would likely have a setting like

   adjustFileOpPaths site5,site6

   sample usage:

   adjustFileOpPaths before,after

   flowcb accept.adjustfileoppaths
 
"""

import logging

import os

from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Adjustfileoppaths():
    def __init__(self, options):

        self.o = options

        self.o.add_option('adjustFileOpPaths', 'list' )


    def on_start(self):

        if not hasattr(self.o, 'adjustFileOpPaths'):
            logger.error("adjustFileOpPaths setting mandatory")
            return

        logger.debug("adjustFileOpPaths is %s " % self.o.adjustFileOpPaths )

    def after_accept(self, worklist):

        if not hasattr(self.o, 'adjustFileOpPaths'):
            return

        for msg in worklist.incoming:
            for p in self.o.adjustFileOpPaths:
                (b, a) = p.split(",")

                # not sure if replacing in the main path is needed... maybe just in fileOp fields?
                logger.info("replace: %s by %s " % (b, a) )
                msg['new_dir'] = msg['new_dir'].replace(b, a, 1)
                msg['new_relPath'] = msg['new_dir'] + os.sep + msg['new_file']
    
                # adjust oldname/newname/link  if related to strings to replace
    
                if 'fileOp' in msg:
                    if 'rename' in msg['fileOp']:
                        msg['fileOp']['rename'] = msg['fileOp']['rename'].replace(b, a, 1)
                    if 'hlink' in msg['fileOp']:
                        msg['fileOp']['hlink'] = msg['fileOp']['hlink'].replace(b, a, 1)
                    if 'link' in msg['fileOp']:
                        msg['fileOp']['link'] = msg['fileOp']['link'].replace(b, a, 1)
    
                # adjust new_relpath if posting
                if not self.o.post_broker: return True
    
                if self.o.post_baseDir:
                    msg['new_relPath'] = msg['new_relPath'].replace(self.o.post_baseDir, '',1)

