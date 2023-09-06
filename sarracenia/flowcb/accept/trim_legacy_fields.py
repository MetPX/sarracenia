"""
Plugin :
    This plugin is aesthetic... some users want less cluttered messages, remove fields
    that are not needed in the non-file replication case, and where sundew_compatibility
    is irrelevant.

Usage:
    callback accept.trim_legacy_fields
"""

import logging
import os, stat, time
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Trim_legacy_fields(FlowCB):
    def __init__(self, options):
        super().__init__(options,logger)

    def after_accept(self, worklist):
        for message in worklist.incoming:
            for h in [ 'atime', 'filename', 'from_cluster', 'mtime', 'source', 'sundew_extension', 'to_clusters' ]:
                if h in message:
                    del message[h]
