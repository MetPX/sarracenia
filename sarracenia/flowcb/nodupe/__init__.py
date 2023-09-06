

import logging

from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class NoDupe(FlowCB):
    """
        duplicate suppression family of modules.

        invoked with:

        callback sarracenia.flowcb.nodupe.disk

        or:
        callback sarracenia.flowcb.nodupe.redis

        with default being loaded depdending on the presence of a

        nodupe_driver "redis"

        setting (defaults to disk.)

    """


    def deriveKey(self, msg) -> str:

        key=None
        if ('nodupe_override' in msg) and ('key' in msg['nodupe_override']):
            key = msg['nodupe_override']['key']
        elif 'fileOp' in msg :
            if 'link' in msg['fileOp']:
                key = msg['fileOp']['link']
            elif 'directory' in msg['fileOp']:
                if 'remove' not in msg['fileOp']:
                    key = msg['relPath']
        elif ('identity' in msg) and not (msg['identity']['method'] in ['cod']):
            key = msg['identity']['method'] + ',' + msg['identity']['value'].replace('\n', '')

        if not key:
            if 'mtime' in msg:
                t = msg['mtime']
            else:
                t = msg['pubTime']
            if 'size' in msg:
                key = f"{msg['relPath']},{t},{msg['size']}"
            else:
                key = f"{msg['relPath']},{t}"

        return key


