#!/usr/bin/python3
""" msg_pclean_f90 module: file propagation test for Sarracenia components (in flow test)
"""
from sarra.plugins.msg_pclean import Msg_Pclean
from sarra.sr_util import nowflt, timestr2flt


class Msg_Pclean_F90(Msg_Pclean):
    """ This plugin class receive a msg from xflow_public and check propagation of the underlying file

     - it checks if the propagation was ok
     - it randomly set a new test file with a different type in the watch dir (f31 amqp)
     - it posts the product to be treated by f92
     - when the msg for the extension file comes back, recheck the propagation

    When a product is not fully propagated, the error is reported and the test is considered as a
    failure. It also checks if the file differs from original
    """
    def on_message(self, parent):
        import filecmp
        import os
        import random

        from difflib import Differ

        parent.logger.info("msg_pclean_f90.py on_message")

        result = True
        msg_relpath = parent.msg.relpath
        f20_path = msg_relpath.replace("{}/".format(self.all_fxx_dirs[1]), self.all_fxx_dirs[0])
        path_dict = self.build_path_dict(self.all_fxx_dirs[2:], msg_relpath)
        ext = self.get_extension(msg_relpath)

        for fxx_dir, path in path_dict.items():
            # f90 test
            if not os.path.exists(path):
                # propagation check to all path except f20 which is the origin
                err_msg = "file not in folder {} with {:.3f}s elapsed"
                lag = nowflt() - timestr2flt(parent.msg.headers['pubTime'])
                parent.logger.error(err_msg.format(fxx_dir, lag))
                parent.logger.debug("file missing={}".format(path))
                result = False
                break
            elif ext not in self.test_extension_list and not filecmp.cmp(f20_path, path):
                # file differ check: f20 against others
                parent.logger.warning("skipping, file differs from f20 file: {}".format(path))
                with open(f20_path, 'r', encoding='iso-8859-1') as f:
                    f20_lines = f.readlines()
                with open(path, 'r', encoding='iso-8859-1') as f:
                    f_lines = f.readlines()
                diff = Differ().compare(f20_lines, f_lines)
                diff = [d for d in diff if d[0] != ' ']  # Diffs without context
                parent.logger.debug("diffs found:\n{}".format("".join(diff)))

        if ext not in self.test_extension_list:
            # prepare next f90 test
            test_extension = random.choice(self.test_extension_list)  # pick one test identified by file extension
            src = msg_relpath  # src file is in f30 dir
            dest = "{}{}".format(src, test_extension)  # format input file for extension test (next f90)

            try:
                if test_extension == '.slink':
                    os.symlink(src, dest)
                elif test_extension == '.hlink':
                    os.link(src, dest)
                elif test_extension == '.moved':
                    os.rename(src, dest)
                else:
                    parent.logger.error("test '{}' is not supported".format(test_extension))
            except FileNotFoundError as err:
                # src is not there
                parent.logger.error("test failed: {}".format(err))
                parent.logger.debug("Exception details:", exc_info=True)
                result=False
            except FileExistsError as err:
                # dest is already there
                parent.logger.error('skipping, found a moving target {}'.format(err))
                parent.logger.debug("Exception details:", exc_info=True)
                result=False

        if 'toolong' in parent.msg.headers:
            # cleanup
            del parent.msg.headers['toolong']

        return result


self.plugin = 'Msg_Pclean_F90'
