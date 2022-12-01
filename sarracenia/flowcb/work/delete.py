import logging
import os
from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)


class Delete(FlowCB):
    """
    
    Plugin flowcp.work.delete.py:
        delete working files after download.
        options:
    
        delete_source -- delete the original input file that was present initially and transformed.
        delete_destination -- delete the downloaded file (presumably after other processing has occurred.)
    
    Usage:
        callback work.delete
    
    """
    def __init__(self, options):
        self.o = options
        logger.debug("msg_delete initialized")
        self.o.add_option('delete_source', 'flag', True)
        self.o.add_option('delete_destination', 'flag', False)

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
                files_to_delete.append(
                    "%s/%s" % (message['new_dir'], message['new_file']))

            for f in files_to_delete:
                logger.info("deleting %s" % f)
                try:
                    os.unlink(f)
                except OSError as err:
                    logger.error("could not unlink {}: {}".format(f, err))
                    logger.debug("Exception details:", exc_info=True)
