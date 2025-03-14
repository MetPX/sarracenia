"""
    This plugin filters messages based on the content (mime) type.

    It will attempt to filter based on the contentType field in the message. 

    If contentType is not available from the message, it will check if the file already exists locally and will
    set the contentType. For this to work, the python-magic package must be installed (you can check by using
    ``sr3 features``) and the ``baseDir`` must be set in the config.

    Options:

    filterContentType_rejectUnknown (default: True) - rejects messages where the contentType is not available.
                                                      Note that this is different than rejectUndefined. This is
                                                      only when the contentType is not present in the message
                                                      **and** when this plugin can't set it using magic.

    filterContentType_acceptType (list) - these are the content types to accept
    filterContentType_rejectType (list) - these are the content types to reject
    filterContentType_rejectUndefined (default: True) - acceptType types will always be accepted, rejectType types
                                                        will always be rejected. This chooses what happens with the
                                                        rest. When True, types not defined in either list will be
                                                        rejected (default). When False, types not defined in either
                                                        list will be accepted.
                                                        Note: this is used when the contentType of the file **is**
                                                        known, but it's not defined in either the acceptType or 
                                                        rejectType lists.
"""

import logging
import os
import urllib.parse
from sarracenia.flowcb import FlowCB

from sarracenia.featuredetection import features

if features['filetypes']['present']:
    import magic

logger = logging.getLogger(__name__)

class Content_type(FlowCB):
    def __init__(self, options):

        super().__init__(options, logger)

        self.o.add_option('filterContentType_rejectUnknown',   kind='flag', default_value=True)
        self.o.add_option('filterContentType_acceptType',      kind='list', default_value=[])
        self.o.add_option('filterContentType_rejectType',      kind='list', default_value=[])
        self.o.add_option('filterContentType_rejectUndefined', kind='flag', default_value=True)

        if not features['filetypes']['present']:
            logger.debug("python-magic not available")

        # ensure there's no whitespace
        tmp = []
        for t in self.o.filterContentType_acceptType:
            tmp.append(t.strip())
        self.o.filterContentType_acceptType = tmp

        tmp = []
        for t in self.o.filterContentType_rejectType:
            tmp.append(t.strip())
        self.o.filterContentType_rejectType = tmp
        
        # check for overlap in the lists
        accept  = set(self.o.filterContentType_acceptType)
        reject  = set(self.o.filterContentType_rejectType)
        in_both = accept.intersection(reject)
        if len(in_both) > 0:
            logger.warning(f"{in_both} are in both acceptType and rejectType, check your config file!")


    def set_content_type(self, msg):
        """ If contentType is not set in the message, try to set it.
        """
        if not features['filetypes']['present']:
            return False

        # copied from sarracenia.Message.getContent
        path = msg['relPath']
        if msg['baseUrl'].startswith('file:'):
            pu = urllib.parse.urlparse(msg['baseUrl'])
            path = pu.path + msg['relPath']
            logger.debug(f"path from file: URL: {path}")
        elif hasattr(self.o, 'baseDir') and self.o.baseDir:
            path = os.path.join(self.o.baseDir, msg['relPath'])
            logger.debug(f"path from baseDir + relPath: {path}")
        
        if not os.path.exists(path):
            logger.debug(f"can't set contentType, local file {path} does not exist ({msg.getIDStr()})")
            return False
        
        # theoretically we have a path we can read
        try:
            msg['contentType'] = magic.from_file(path, mime=True)
            logger.debug(f"successfully set contentType from local file {path} ({msg.getIDStr()})")
            return True
        except Exception as e:
            logger.error(f"failed to set contentType from local file {path} ({msg.getIDStr()})")
            logger.debug("Exception details:", exc_info=True)
            return False

        return False

    def after_accept(self, worklist):
        """ Accept or reject a message based on the contentType.
        """
        
        accepting = []
        for msg in worklist.incoming:
            
            # UNKNOWN contentType, try to set it
            if 'contentType' not in msg:
                if not self.set_content_type(msg):
                    if self.o.filterContentType_rejectUnknown:
                        logger.debug(f"{msg.getIDStr()} has unknown contentType, rejecting")
                        msg.setReport(415, "contentType unknown")
                        worklist.rejected.append(msg)
                    else:
                        logger.debug(f"{msg.getIDStr()} has unknown contentType, accepting")
                        accepting.append(msg)
                    continue
            
            logger.debug(f"{msg.getIDStr()} has contentType {msg['contentType']}")

            # Now we know the message has the contentType field
            if msg['contentType'] in self.o.filterContentType_acceptType:
                accepting.append(msg)
                continue
            elif msg['contentType'] in self.o.filterContentType_rejectType:
                msg.setReport(415, f"contentType {msg['contentType']} defined as a rejectType")
                worklist.rejected.append(msg)
                continue
            else:
                if self.o.filterContentType_rejectUndefined:
                    msg.setReport(415, f"contentType {msg['contentType']} undefined")
                    worklist.rejected.append(msg)
                    continue
                else:
                    accepting.append(msg)
                    continue

        worklist.incoming = accepting
