

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
        """ The key is the first thing checked when doing duplicate suppression.
            If the keys do not match, nodupe doesn't bother looking at the path/name/anything else.
            i.e. if the keys for two messages don't match, they are not duplicates.
                 if the keys *do* match, it doesn't necessarily mean that they are duplicates, nodupe
                 then has to check if the path/name/something else matches (see _not_in_cache method)
        """

        key=None

        # 1st priority: use the key from nodupe_override in the msg
        if ('nodupe_override' in msg) and ('key' in msg['nodupe_override']):
            key = msg['nodupe_override']['key']

        # 2nd: derive from fileOp if fileOp is link or is a non-remove directory op
        elif 'fileOp' in msg :
            if 'link' in msg['fileOp']:
                key = msg['fileOp']['link']
            elif 'directory' in msg['fileOp']:
                if 'remove' not in msg['fileOp']:
                    key = msg['relPath']

        # 3rd: use identity (checksum) if available (cod = calculate on download, i.e. no checksum yet)
        elif ('identity' in msg) and not (msg['identity']['method'] in ['cod']):
            key = msg['identity']['method'] + ',' + msg['identity']['value'].replace('\n', '')

        # 4th: use relPath and time (and size, if known)
        #   This is usually the case for polls, where we don't have the file's 
        #   checksum, but the size and modification time are known
        if not key:
            # time comes from file modification time when available, or msg pubTime (required field in all msgs)
            if 'mtime' in msg:
                t = msg['mtime']
            else:
                t = msg['pubTime']

            if 'nodupe_override' in msg and 'path' in msg['nodupe_override']:
                path = msg['nodupe_override']['path']
            else:
                path = msg['relPath']

            # if file size is known, use it
            if 'size' in msg:
                key = f"{path},{t},{msg['size']}"
            else:
                key = f"{path},{t}"

        return key
