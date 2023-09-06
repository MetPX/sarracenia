"""
Plugin renamewhatfn.py:
    This plugin is no longer needed.  Sundew compoatibility was added to Sarracenia, 
    so now can get the same effect by using the *filename* option which works like it
    does in Sundew:

    filename WHATFN

    what it was used for:
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
        super().__init__(options,logger)

    def after_accept(self, worklist):
        for message in worklist.incoming:
            parts = message['new_file'].split(':')

            # join mets les ':' entre les parts... donc ajout de ':' au debut
            extra = ':' + ':'.join(parts[1:])
            message['new_file'] = message['new_file'].replace(extra, '')
            message['rename'] = message['rename'].replace(extra, '')
