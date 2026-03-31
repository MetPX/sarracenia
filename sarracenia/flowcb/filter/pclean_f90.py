""" 
   msg_pclean_f90 module: file propagation test for Sarracenia components (in flow test)
   https://github.com/MetPX/sr_insects/

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
    """ 
     functionality within the flow_tests of the sr_insects project.
     This plugin class receive a msg from xflow_public and check propagation of the underlying file

     - it checks if the propagation was ok
     - it randomly set a new test file with a different type in the watch dir (f31 amqp)
     - it posts the product to be treated by f92
     - when the msg for the extension file comes back, recheck the propagation

    When a product is not fully propagated, the error is reported and the test is considered as a
    failure. It also checks if the file differs from original
    """
    def after_accept(self, worklist):

        logger.info(f"start len(worklist.incoming) = {len(worklist.incoming)}")

        outgoing = []

        for msg in worklist.incoming:

            result = True
            f20_path = '/' + msg['relPath'].replace(
                f"{self.all_fxx_dirs[1]}/", self.all_fxx_dirs[0])
            path_dict = self.build_path_dict(self.all_fxx_dirs[2:],
                                             '/' + msg['relPath'])
            ext = self.get_extension('/' + msg['relPath'])
            logger.info(f"looking at: {msg['relPath']}")
            logger.info(f'path_dict: {path_dict}')

            for fxx_dir, path in path_dict.items():
                # f90 test
                logger.info(f'for looping: {path}')
                if not (os.path.isfile(path) or os.path.islink(path)):
                    # propagation check to all path except f20 which is the origin
                    err_msg = "file not in folder {} with {:.3f}s elapsed"
                    lag = nowflt() - timestr2flt(msg['pubTime'])
                    logger.error(err_msg.format(fxx_dir, lag))
                    logger.debug(f"file missing={path}")
                    result = False
                    worklist.failed.append(msg)
                    break
                elif ext not in self.test_extension_list and not filecmp.cmp(
                        f20_path, path):
                    # file differ check: f20 against others
                    logger.error(
                        f"skipping, file differs from f20 file: {path}")
                    with open(f20_path, 'r', encoding='iso-8859-1') as f:
                        f20_lines = f.readlines()
                    with open(path, 'r', encoding='iso-8859-1') as f:
                        f_lines = f.readlines()
                    diff = Differ().compare(f20_lines, f_lines)
                    diff = [d for d in diff
                            if d[0] != ' ']  # Diffs without context
                    logger.info(f"a: len({f20_path}) = {len(f20_lines)}")
                    logger.info(f"b: len({path}) = {len(f_lines)}")
                    if len(f20_lines) > 10 or len(f_lines) > 10:
                        logger.info(" long diff omitted ")
                    else:
                        logger.info(f"diffs found:\n{''.join(diff)}")

            if not result:
                logger.info('queued for retry because propagation not done yet.')
                continue

            if ext not in self.test_extension_list:
                # prepare next f90 test
                test_extension = self.test_extension_list[self.ext_count % len(
                    self.test_extension_list)]
                self.ext_count += 1
                # pick one test identified by file extension
                src = '/' + msg['relPath']  # src file is in f30 dir
                dest = f"{src}{test_extension}"  # format input file for extension test (next f90)

                try:
                    if test_extension == '.slink':
                        os.symlink(src, dest)
                        logger.info(f'symlinked {src} {dest}')
                    elif test_extension == '.hlink':
                        os.link(src, dest)
                        logger.info(f'hlinked {src} {dest}')
                    elif test_extension == '.moved':
                        os.rename(src, dest)
                        logger.info(f'moved {src} {dest}')
                    else:
                        logger.error(f"test '{test_extension}' is not supported")
                except FileNotFoundError as err:
                    # src is not there
                    logger.error(f"test failed: {err}")
                    logger.debug("Exception details:", exc_info=True)
                    result = False
                except FileExistsError as err:
                    # dest is already there
                    logger.error(
                        f'skipping, found a moving target {err}')
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
        logger.info(f"end len(worklist.incoming) = {len(worklist.incoming)}")
        logger.info(f"end len(worklist.rejected) = {len(worklist.rejected)}")
