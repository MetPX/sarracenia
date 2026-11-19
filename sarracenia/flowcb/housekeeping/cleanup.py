import logging
import os
import stat
import time

from sarracenia.flowcb import FlowCB


logger = logging.getLogger(__name__)


class Cleanup(FlowCB):
    """Delete regular files older than cleanup_age from watched paths."""

    def __init__(self, options):
        super().__init__(options, logger)
        self.o.add_option('cleanup_age', 'duration', 0)

    def on_housekeeping(self):
        if self.o.cleanup_age <= 0:
            return

        now = time.time()
        for configured_path in getattr(self.o, 'postpath', []):
            path = self.o.variableExpansion(configured_path)
            root = os.path.abspath(path)

            if os.path.islink(root) or not os.path.isdir(root):
                logger.debug('skipping cleanup path that is not a directory: %s', root)
                continue

            for directory, subdirectories, filenames in os.walk(root, followlinks=False):
                subdirectories[:] = [
                    name for name in subdirectories
                    if not os.path.islink(os.path.join(directory, name))
                ]

                for filename in filenames:
                    file_path = os.path.join(directory, filename)
                    try:
                        file_stat = os.stat(file_path, follow_symlinks=False)
                        if not stat.S_ISREG(file_stat.st_mode):
                            continue
                        if now - file_stat.st_mtime < self.o.cleanup_age:
                            continue

                        os.unlink(file_path)
                        logger.info('cleanup_age expired; deleted %s', file_path)
                    except FileNotFoundError:
                        continue
                    except OSError as err:
                        logger.warning('could not clean up %s: %s', file_path, err)