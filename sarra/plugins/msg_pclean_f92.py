#!/usr/bin/python3
""" msg_pclean_f90 module: second file propagation test for Sarracenia components (in flow test)
"""
from sarra.plugins.msg_pclean import Msg_Pclean


class Msg_Clean_F92(Msg_Pclean):
    """ This plugin that manage the removal of every file

     - it fails if one removal failed
    """
    def on_message(self, parent):
        import os

        parent.logger.info("msg_pclean_f92.py on_message")

        result = True
        msg_relpath = parent.msg.relpath
        ext = self.get_extension(msg_relpath)


        if ext in self.test_extension_list:
            f20_path = msg_relpath.replace("{}/".format(self.all_fxx_dirs[1]), self.all_fxx_dirs[0])
            f20_path = f20_path.replace(ext, '')
            try:
                os.unlink(f20_path)
            except FileNotFoundError as err:
                parent.logger.error("could not unlink in {}: {}".format(f20_path, err))
                parent.logger.debug("Exception details:", exc_info=True)
                result = False
            fxx_dirs = self.all_fxx_dirs[1:2] + self.all_fxx_dirs[6:]
            path_dict = self.build_path_dict(fxx_dirs, msg_relpath)
            for fxx_dir, path in path_dict.items():
                try:
                    os.unlink(path)
                    if ext != '.moved':
                        os.unlink(path.replace(ext, ''))
                except OSError as err:
                    parent.logger.error("could not unlink in {}: {}".format(fxx_dir, err))
                    parent.logger.debug("Exception details:", exc_info=True)
                    result = False
        return result


self.plugin = 'Msg_Clean_F92'
