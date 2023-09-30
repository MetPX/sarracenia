"""
    Adjust file paths, modifies the paths in file operation fileds, for file renaming,
    removal or links, or to give files different names on download.

    where files from a 'before' directory, are sent by an sr_sender to a 'after' directory.
    This also applies to the HPC mirroring case, where one would likely have a setting like

    pathReplace site5,site6
    pathReplaceFields dir

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
        super().__init__(options, logger)

        self.o.add_option('pathReplace', 'list' )

        all_fields = set(['dir','file','rename','hlink','link'])
        self.o.add_option( 'pathReplaceFields', 'set', all_fields, all_fields )

    def on_start(self):
        if self.o.pathReplace == None:
            logger.error("pathReplace setting mandatory")
            return

        logger.debug("pathReplace is %s " % self.o.pathReplace )

    def after_accept(self, worklist):
        if self.o.pathReplace == None:
            return

        for msg in worklist.incoming:
            for p in self.o.pathReplace:
                (b, a) = p.split(",")

                # not sure if replacing in the main path is needed... maybe just in fileOp fields?
                logger.info("replace: %s by %s in: %s" % (b, a, self.o.pathReplaceFields) )

                if 'dir' in self.o.pathReplaceFields:
                    new_new_dir = msg['new_dir'].replace(b, a, 1)

                    if new_new_dir != msg['new_dir'] :
                        msg['new_dir'] = new_new_dir

                if 'file' in self.o.pathReplaceFields:
                    msg['new_file'] = msg['new_file'].replace(b, a, 1)

                msg['new_relPath'] = msg['new_dir'] + os.sep + msg['new_file']
    
                # adjust oldname/newname/link  if related to strings to replace
    
                if 'fileOp' in msg:
                    if 'rename' in msg['fileOp'] and 'rename' in self.o.pathReplaceFields:
                        msg['fileOp']['rename'] = msg['fileOp']['rename'].replace(b, a, 1)
                    if 'hlink' in msg['fileOp'] and 'hlink' in self.o.pathReplaceFields:
                        msg['fileOp']['hlink'] = msg['fileOp']['hlink'].replace(b, a, 1)
                    if 'link' in msg['fileOp'] and 'link' in self.o.pathReplaceFields:
                        msg['fileOp']['link'] = msg['fileOp']['link'].replace(b, a, 1)
    
                ## adjust new_relpath if posting    
                if self.o.post_baseDir:
                    msg['new_relPath'] = msg['new_relPath'].replace(self.o.post_baseDir, '',1)

