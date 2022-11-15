"""
   Adjust file paths, modifies the paths in file operation fileds, for file renaming,
   removal or links, or to give files different names on download.

   where files from a 'before' directory, are sent by an sr_sender to a 'after' directory.
   This also applies to the HPC mirroring case, where one would likely have a setting like

   pathReplace site5,site6

   sample usage:

   pathReplace before,after

   flowcb accept.pathreplace
 
"""

import logging

import os

from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Pathreplace(FlowCB):
    def __init__(self, options):

        self.o = options

        self.o.add_option('pathReplace', 'list' )


    def on_start(self):

        if not hasattr(self.o, 'pathReplace'):
            logger.error("pathReplace setting mandatory")
            return

        logger.debug("pathReplace is %s " % self.o.pathReplace )

    def after_accept(self, worklist):

        if not hasattr(self.o, 'pathReplace'):
            return

        for msg in worklist.incoming:
            for p in self.o.pathReplace:
                (b, a) = p.split(",")

                # not sure if replacing in the main path is needed... maybe just in fileOp fields?
                logger.info("replace: %s by %s " % (b, a) )
                new_new_dir = msg['new_dir'].replace(b, a, 1)

                if new_new_dir != msg['new_dir'] :
                    msg['new_dir'] = new_new_dir
                else:
                    msg['new_file'] = msg['new_file'].replace(b, a, 1)

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

