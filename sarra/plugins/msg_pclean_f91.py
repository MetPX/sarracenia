#!/usr/bin/python3
""" msg_pclean_f90 module: second file propagation test for Sarracenia components (in flow test)
"""
from sarra.plugins.msg_pclean import Msg_Pclean
from sarra.sr_util import nowflt, timestr2flt


class Msg_Clean_F91(Msg_Pclean):
    """ This plugin receives the message from shovel pclean_f90 test which passed

     - it checks the propagation of this other file type (fails if it miss one)
     - it posts the product again

    when a product is not fully propagated, it also reports the error
    """

    def on_message(self, parent):
        import os

        parent.logger.info("msg_pclean_f91.py on_message")

        result = True
        msg_relpath = parent.msg.relpath.strip('/')
        ext = self.get_extension(parent.msg)

        if ext in self.test_extension_list:
            # checks all paths except f20, f30 which are not tested here, f30 is the origin
            path_dict = self.build_path_dict(parent.currentDir, self.all_fxx_dirs[3:], msg_relpath, ext)
            for fxx_dir, path in path_dict.items():
                if not os.path.exists(path):
                    err_msg = "file not in folder {} for {} test with {:.3f}s elapsed"
                    lag = nowflt() - timestr2flt(parent.msg.headers['fdelay'])
                    parent.logger.error(err_msg.format(fxx_dir[:-6], fxx_dir[-6:], lag))
                    parent.logger.debug("file missing={}".format(path))
                    result = False
        else:
            self.log_msg_details(parent)
            return False

        del parent.msg.headers['fdelay']
        return result


self.plugin = 'Msg_Clean_F91'
