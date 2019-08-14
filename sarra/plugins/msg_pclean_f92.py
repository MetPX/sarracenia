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
        msg_relpath = parent.msg.relpath.strip('/')
        ext = self.get_extension(parent.msg)
        if ext is None:
            self.log_msg_details(parent)
            return False

        if ext == '.moved':
            # f30 watched file moved then does not need to delete it and it has propagated the move to f50, f60, f61
            fxx_dirs = [self.all_fxx_dirs[0]] + self.all_fxx_dirs[6:]
            path_dict = self.build_path_dict(parent.currentDir, fxx_dirs, msg_relpath)
        else:
            # f30 watched file hasnt moved now deleting it
            fxx_dirs = self.all_fxx_dirs[0:3] + self.all_fxx_dirs[6:]
            path_dict = self.build_path_dict(parent.currentDir, fxx_dirs, msg_relpath)

        # we did the extension test (f91), then we need to remove the result files with the same propagation pattern
        fxx_dirs = [self.all_fxx_dirs[1]] + self.all_fxx_dirs[6:]
        path_dict.update(self.build_path_dict(parent.currentDir, fxx_dirs, msg_relpath, ext))

        for fxx_dir, path in path_dict.items():
            try:
                os.unlink(path)
            except OSError as err:
                parent.logger.error("could not unlink in {}: {}".format(fxx_dir, err))
                parent.logger.debug("Exception details:", exc_info=True)
                result = False

        return result


self.plugin = 'Msg_Clean_F92'
