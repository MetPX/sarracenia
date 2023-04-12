from base64 import b64decode, b64encode
from codecs import decode, encode

from sarracenia.flowcb import v2wrapper

import logging
import sarracenia
from sarracenia.postformat import PostFormat

logger = logging.getLogger(__name__)


class V02(PostFormat):
    """
       A class for controlling the format of messages are sent.
       internally All messages are represented as v03. 
       post format implement translations to other protocols for interop.

   """

    @staticmethod
    def content_type():
        return 'text/plain'

    @staticmethod
    def mine(payload, headers, content_type) -> bool:
        """
          return true if the message is in this post format.
       """
        if content_type == V02.content_type() :
            return True
        return False

    @staticmethod
    def importMine(body, headers) -> sarracenia.Message:
        """
          given a message in a wire format, with the given properties (or headers) in a dictionary,
          return the message as a normalized v03 message.

          the topic and topicPrefix should be lists, not protocol specific strings.
       """
        msg = sarracenia.Message()
        msg["_format"] = __name__.split('.')[-1].lower()
        msg.copyDict(headers)
    
        try:
            pubTime, baseUrl, relPath = body.split(' ')[0:3]
        except Exception as ex:
            logger.error( f"body should have three space separated fields: {body}, error: {ex}" )
            return None

        msg['pubTime'] = sarracenia.timev2tov3str(pubTime)
        msg['baseUrl'] = baseUrl.replace('%20', ' ').replace('%23', '#')
        msg['relPath'] = relPath
        msg['subtopic'] = relPath.split('/')
        msg['to_clusters'] = 'ALL'
        msg['_deleteOnPost'] |= set(['subtopic'])

        for t in ['atime', 'mtime']:
            if t in msg:
                try: 
                    msg[t] = sarracenia.timev2tov3str(msg[t])
                except Exception as ex:
                    logger.warning( f"invalid time field: {t} value: {msg['t']}, error: {ex}" )
        try:
            if 'sum' in msg:
                sum_algo_map = {
                    "0": "random",
                    "a": "arbitrary",
                    "d": "md5",
                    "L": "link",
                    "m": "mkdir",
                    "n": "md5name",
                    "r": "rmdir",
                    "R": "remove",
                    "s": "sha512",
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
                    if sm in ['mkdir']:
                        msg['fileOp']['mkdir'] = ''
                    elif sm in ['link']:
                        msg['fileOp']['link'] = msg['link']
                    else:
                        msg["integrity"] = {"method": sm, "value": sv}
                elif sm == 'remove':
                    msg['fileOp'] = { 'remove': '' }
                elif sm == 'mkdir':
                    msg['fileOp'] = { 'directory': '' }
                elif sm == 'rmdir':
                    msg['fileOp'] = { 'remove':'', 'directory': '' }
                elif 'link' in msg:
                    msg['fileOp'] = { 'link': msg['link'] }
                    del msg['link']
                elif sm == 'md5name':
                    pass
                else:
                    msg["integrity"] = {"method": sm, "value": sv}
    
                del msg['sum']
        except Exception as ex:
            logger.warning( f"sum field corrupt: {msg['sum']} ignored: {ex}" )

        try:
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
        except Exception as ex:
            logger.warning( f"parts field corrupt: {msg['parts']}, ignored: {ex}" )
    
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
