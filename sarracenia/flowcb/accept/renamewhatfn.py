"""
Plugin renamewhatfn.py:
    This renamer strips everything from the first colon in the file name to the end.
    This does the same thing as a 'WHATFN' config on a sundew sender.

Example:
    takes px name     : /apps/dms/dms-metadata-updater/data/international_surface/import/mdicp4d:pull-international-metadata:CMC:DICTIONARY:4:ASCII:20160223124648
    rename for        : /apps/dms/dms-metadata-updater/data/international_surface/import/mdicp4d

Usage:
    flowcb sarracenia.flowcb.accept.renamewhatfn.RenameWhatFn

"""

import logging
import sys, os, os.path, time, stat
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class RenameWhatFn(FlowCB):
    def __init__(self, options):
        self.o = options

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:
            parts = message['new_file'].split(':')
    
            # join mets les ':' entre les parts... donc ajout de ':' au debut
            extra = ':' + ':'.join(parts[1:])
            message['new_file'] = message['new_file'].replace(extra, '')
            message['headers']['rename'] = message['headers']['rename'].replace(extra, '')
            new_incoming.append(message)
        worklist.incoming = new_incoming




