from base64 import b64decode, b64encode
from codecs import decode, encode

from sarracenia.flowcb import v2wrapper

import logging
import sarracenia
from sarracenia.encoding import Encoding

logger = logging.getLogger(__name__)


class V02(Encoding):
    """
       A class for controlling the format of messages are sent.
       internally All messages are represented as v03. 
       encodings implement translations to other protocols for interop.

   """

    @staticmethod
    def content_type():
        return 'text/plain'

    @staticmethod
    def mine(payload, headers, content_type) -> bool:
        """
          return true if the message is in this encoding.
       """
        if content_type == V02.content_type() :
            return True
        return False

    @staticmethod
    def importMine(body, headers, topic, topicPrefix) -> sarracenia.Message:
        """
          given a message in a wire format, with the given properties (or headers) in a dictionary,
          return the message as a normalized v03 message.
       """
        msg = sarracenia.Message()
        msg.copyDict(headers)
    
        msg['subtopic'] = topic.split('.')[len(topicPrefix):]
        if not '_deleteOnPost' in msg:
            msg['_deleteOnPost'] = set()
        msg['_deleteOnPost'] |= set(['subtopic'])
    
        pubTime, baseUrl, relPath = body.split(' ')[0:3]
        msg['pubTime'] = sarracenia.timev2tov3str(pubTime)
        msg['baseUrl'] = baseUrl.replace('%20', ' ').replace('%23', '#')
        msg['relPath'] = relPath
        msg['subtopic'] = relPath.split('/')
        for t in ['atime', 'mtime']:
            if t in msg:
                msg[t] = sarracenia.timev2tov3str(msg[t])
    
        if 'sum' in msg:
            sum_algo_map = {
                "a": "arbitrary",
                "d": "md5",
                "s": "sha512",
                "n": "md5name",
                "0": "random",
                "L": "link",
                "R": "remove",
                "z": "cod"
            }
            sm = sum_algo_map[msg["sum"][0]]
            if sm in ['random', 'arbitrary']:
                sv = msg["sum"][2:]
            elif sm in ['cod']:
                sv = sum_algo_map[msg["sum"][2:]]
            else:
                sv = encode(decode(msg["sum"][2:], 'hex'),
                            'base64').decode('utf-8').strip()
            if 'oldname' in msg:
                msg['fileOp'] = { 'rename': msg['oldname'] }
                del msg['oldname']
                msg["integrity"] = {"method": sm, "value": sv}
            elif sm == 'remove':
                msg['fileOp'] = { 'remove': '' }
            elif 'link' in msg:
                msg['fileOp'] = { 'link': msg['link'] }
                del msg['link']
            elif sm == 'md5name':
                pass
            else:
                msg["integrity"] = {"method": sm, "value": sv}

            del msg['sum']
    
        if 'parts' in msg:
            (style, chunksz, block_count, remainder,
             current_block) = msg['parts'].split(',')
            if style in ['i', 'p']:
                msg['blocks'] = {}
                msg['blocks']['method'] = {
                    'i': 'inplace',
                    'p': 'partitioned'
                }[style]
                msg['blocks']['size'] = int(chunksz)
                msg['blocks']['count'] = int(block_count)
                msg['blocks']['remainder'] = int(remainder)
                msg['blocks']['number'] = int(current_block)
            else:
                msg['size'] = int(chunksz)
            del msg['parts']
    
        msg["version"] = 'v02'
        return msg

    @staticmethod
    def exportMine(body) -> (str, dict, str):
        """
           given a v03 (internal) message, produce an encoded version.
       """
        v2m = v2wrapper.Message(body)

        # v2wrapp
        for h in [
                    'pubTime', 'baseUrl', 'fileOp', 'relPath', 'size', 
                    'blocks', 'content', 'integrity'
        ]:
            if h in v2m.headers:
                    del v2m.headers[h]
        return v2m.notice, v2m.headers, V02.content_type()
