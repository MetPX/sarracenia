import logging
import os
from sarracenia.flowcb import FlowCB
import time


logger = logging.getLogger(__name__)


class Delete(FlowCB):
    """
    
    callback flowcp.work.delete

        delete working files after download.
        options:
    
        delete_source -- delete the original input file that was present initially and transformed.
        delete_destination -- delete the downloaded file (presumably after other processing has occurred.)
    
    Usage:
        callback work.delete
    
    """
    def __init__(self, options):
        super().__init__(options,logger)
        logger.debug("initialized")
        self.o.add_option('delete_source', 'flag', True)
        self.o.add_option('delete_destination', 'flag', False)
        self.dirsOfDeletion=set([])

         # dirs not to be deleted.
        self.sacredDirs=set([])
        if hasattr(self.o, 'baseDir'):
            self.sacredDirs.add(self.o.baseDir)
        if hasattr(self.o, 'post_baseDir'):
            self.sacredDirs.add(self.o.post_baseDir)


    def after_accept(self, worklist):
        new_incoming = []
        if self.o.delete_source:
            for message in worklist.incoming:
                message['_deleteOnPost'] |= set(['delete_source'])

                #FIXME: there should be some reference to baseDir here... for url's that aren't file ones.
                #   just getting it to work for particular case for now 2021/12/09 - pas
                message['delete_source'] = message['baseUrl'].lstrip(
                    'file:') + message['relPath']

    def after_work(self, worklist):

        for message in worklist.ok:

            # don't remove files that have already been removed.
            if 'fileOp' in message and 'remove' in message['fileOp']:
                continue

            files_to_delete = []

            if self.o.delete_source:
                files_to_delete.append(message['delete_source'])

            if self.o.delete_destination:
                self.dirsOfDeletion |= set(message['new_dir'])
                files_to_delete.append(
                    "%s/%s" % (message['new_dir'], message['new_file']))

            for f in files_to_delete:
                logger.info("deleting %s" % f)
                try:
                    os.unlink(f)
                except OSError as err:
                    logger.error("could not unlink {}: {}".format(f, err))
                    logger.debug("Exception details:", exc_info=True)

    def on_housekeeping(self):

        dirlist=self.dirsOfDeletion

        logger.info('scan for directories to cleanup')
        for d in dirlist:
            if d in self.sacredDirs:
                self.dirsOfDeletion.remove(d)
                continue
            if os.path.isdir(d):
                l = os.listdir(d)
                if len(l) == 0: # empty directory
                    logger.info( f"found {d} is empty.")
                    s = os.stat(d)
                    age = time.time() - s.st_mtime
                    if age > self.o.housekeeping:
                        try:
                            os.rmdir(d)
                            self.dirsOfDeletion.remove(d)
                            self.dirsofDeltion.add(dirname(d))
                            logger.info( f"deleted {d}")
                        except Exception as err:
                            logger.error("could not unlink {}: {}".format(f, err))
                            logger.debug("Exception details:", exc_info=True)
                    else:
                        logger.info( f"but not for long enough yet.")

