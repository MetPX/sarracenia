#!/usr/bin/python3
""" msg_pclean_f90 module: second file propagation test for Sarracenia components (in flow test)
"""

from difflib import Differ
import filecmp
import logging
import os
import random

from sarracenia.flowcb.pclean import PClean
from sarracenia import timestr2flt, nowflt

logger = logging.getLogger(__name__)


class PClean_F92(PClean):
    """ This plugin that manage the removal of every file

     - it fails if one removal failed
    """
    def after_accept(self, worklist):
        import os

        logger.info("start len(worklist.incoming) = %d" %
                    len(worklist.incoming))

        outgoing = []

        for msg in worklist.incoming:
            result = True
            ext = self.get_extension('/' + msg['relPath'])
            logger.info("relPath=%s ext: %s in %s ?" % (msg['relPath'], ext, self.test_extension_list) )

            if ext in self.test_extension_list:
                f20_path = '/' + msg['relPath'].replace(
                    "{}/".format(self.all_fxx_dirs[1]), self.all_fxx_dirs[0])
                f20_path = f20_path.replace(ext, '')
                try:
                    os.unlink(f20_path)
                    logger.info("unlinked 1: %s" % f20_path )
                except FileNotFoundError as err:
                    logger.error("could not unlink in {}: {}".format(
                        f20_path, err))
                    logger.debug("Exception details:", exc_info=True)
                    result = False
                fxx_dirs = self.all_fxx_dirs[1:2] + self.all_fxx_dirs[6:]
                path_dict = self.build_path_dict(fxx_dirs,
                                                 '/' + msg['relPath'])
                for fxx_dir, path in path_dict.items():
                    try:
                        os.unlink(path)
                        logger.info("unlinked 2: %s" % path )
                        if ext != '.moved':
                            os.unlink(path.replace(ext, ''))
                            logger.info("unlinked 3: %s" % path.replace(ext,'') )
                    except OSError as err:
                        logger.error("could not unlink in {}: {}".format(
                            fxx_dir, err))
                        logger.debug("Exception details:", exc_info=True)
                        result = False
            if result:
                logger.debug('passing to pclean_f92')
                outgoing.append(msg)
            else:
                worklist.rejected.append(msg)

        worklist.incoming = outgoing
        logger.info("len(worklist.incoming) = %d" % len(worklist.incoming))
        logger.info("len(worklist.rejected) = %d" % len(worklist.rejected))
