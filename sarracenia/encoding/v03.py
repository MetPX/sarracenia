import json
import logging
import sarracenia
from sarracenia.encoding import Encoding

logger = logging.getLogger(__name__)


class V03(Encoding):
    """
       A class for controlling the format of messages are sent.
       internally All messages are represented as v03. 
       encodings implement translations to other protocols for interop.

   """

    @staticmethod
    def content_type():
        return 'application/json'

    @staticmethod
    def mine(payload, headers, content_type) -> bool:
        """
          return true if the message is in this encoding.
       """
        if content_type == V03.content_type():
            return True
        return False

    @staticmethod
    def importMine(body, headers, topic, topicPrefix) -> sarracenia.Message:
        """
          given a message in a wire format, with the given properties (or headers) in a dictionary,
          return the message as a normalized v03 message.
       """
        msg = sarracenia.Message()
        msg["version"] = 'v03'
        try:
            msg.copyDict(json.loads(body))
        except Exception as ex:
            logger.warning('expected json, decode error: %s' % ex)
            logger.warning( f'body: {body}' )
            logger.debug('Exception details: ', exc_info=True)
            return None
        """
              observed Sarracenia v2.20.08p1 and earlier have 'parts' header in v03 messages.
              bug, or implementation did not keep up. Applying Postel's Robustness principle: normalizing messages.
            """
        if ('parts' in msg
            ):  # bug in v2 code makes v03 messages with parts header.
            (m, s, c, r, n) = msg['parts'].split(',')
            if m == '1':
                msg['size'] = int(s)
            else:
                if m == 'i': m = 'inplace'
                elif m == 'p': m = 'partitioned'
                msg['blocks'] = {
                    'method': m,
                    'size': int(s),
                    'count': int(c),
                    'remainder': int(r),
                    'number': int(n)
                }

            del msg['parts']
        elif ('size' in msg):
            if (type(msg['size']) is str):
                msg['size'] = int(msg['size'])
        return msg

    @staticmethod
    def exportMine(body) -> (str, dict, str):
        """
           given a v03 (internal) message, produce an encoded version.
       """
        raw_body = json.dumps(body)
        return raw_body, None, V03.content_type()
