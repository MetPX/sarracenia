#!/usr/bin/python3
""" msg_pclean_f90 module: file propagation test for Sarracenia components (in flow test)
"""

from difflib import Differ
import filecmp
import logging
import os
import random

from sarracenia.flowcb.pclean import PClean
from sarracenia import timestr2flt, nowflt

logger = logging.getLogger(__name__)


class PClean_F90(PClean):
    """ This plugin class receive a msg from xflow_public and check propagation of the underlying file

     - it checks if the propagation was ok
     - it randomly set a new test file with a different type in the watch dir (f31 amqp)
     - it posts the product to be treated by f92
     - when the msg for the extension file comes back, recheck the propagation

    When a product is not fully propagated, the error is reported and the test is considered as a
    failure. It also checks if the file differs from original
    """
    def after_accept(self, worklist):

        logger.info("start len(worklist.incoming) = %d" % len(worklist.incoming))

        outgoing = []

        for msg in worklist.incoming:

            result = True
            f20_path = '/' + msg['relPath'].replace(
                "{}/".format(self.all_fxx_dirs[1]), self.all_fxx_dirs[0])
            path_dict = self.build_path_dict(self.all_fxx_dirs[2:],
                                             '/' + msg['relPath'])
            ext = self.get_extension('/' + msg['relPath'])
            logger.info( 'looking at: %s' % msg['relPath'] )
            logger.info( 'path_dict: %s' % path_dict )

            for fxx_dir, path in path_dict.items():
                # f90 test
                logger.info( 'for looping: %s' % path )
                if not os.path.exists(path):
                    # propagation check to all path except f20 which is the origin
                    err_msg = "file not in folder {} with {:.3f}s elapsed"
                    lag = nowflt() - timestr2flt(msg['pubTime'])
                    logger.error(err_msg.format(fxx_dir, lag))
                    logger.debug("file missing={}".format(path))
                    result = False
                    break
                elif ext not in self.test_extension_list and not filecmp.cmp(
                        f20_path, path):
                    # file differ check: f20 against others
                    logger.error(
                        "skipping, file differs from f20 file: {}".format(
                            path))
                    with open(f20_path, 'r', encoding='iso-8859-1') as f:
                        f20_lines = f.readlines()
                    with open(path, 'r', encoding='iso-8859-1') as f:
                        f_lines = f.readlines()
                    diff = Differ().compare(f20_lines, f_lines)
                    diff = [d for d in diff
                            if d[0] != ' ']  # Diffs without context
                    logger.info("a: len(%s) = %d" %
                                 (f20_path, len(f20_lines)))
                    logger.info("b: len(%s) = %d" % (path, len(f_lines)))
                    logger.info("diffs found:\n{}".format("".join(diff)))

            if ext not in self.test_extension_list:
                # prepare next f90 test
                test_extension = self.test_extension_list[ self.ext_count % len(self.test_extension_list) ]
                self.ext_count += 1
                # pick one test identified by file extension
                src = '/' + msg['relPath']  # src file is in f30 dir
                dest = "{}{}".format(
                    src, test_extension
                )  # format input file for extension test (next f90)

                try:
                    if test_extension == '.slink':
                        os.symlink(src, dest)
                        logger.info('symlinked %s %s' % (src, dest) )
                    elif test_extension == '.hlink':
                        os.link(src, dest)
                        logger.info('hlinked %s %s' % (src, dest) )
                    elif test_extension == '.moved':
                        os.rename(src, dest)
                        logger.info('moved %s %s' % (src, dest) )
                    else:
                        logger.error("test '{}' is not supported".format(
                            test_extension))
                except FileNotFoundError as err:
                    # src is not there
                    logger.error("test failed: {}".format(err))
                    logger.debug("Exception details:", exc_info=True)
                    result = False
                except FileExistsError as err:
                    # dest is already there
                    logger.error(
                        'skipping, found a moving target {}'.format(err))
                    logger.debug("Exception details:", exc_info=True)
                    result = False
            else:
                logger.info('ext not in test_extenion_list')

            if 'toolong' in msg:
                # cleanup
                del msg['toolong']

            if result:
                outgoing.append(msg)
            else:
                worklist.rejected.append(msg)

        worklist.incoming = outgoing
        logger.info("end len(worklist.incoming) = %d" % len(worklist.incoming))
        logger.info("end len(worklist.rejected) = %d" % len(worklist.rejected))
