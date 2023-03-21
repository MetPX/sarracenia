import json
import logging
import sarracenia
from sarracenia.postformat import PostFormat

logger = logging.getLogger(__name__)


class V03(PostFormat):
    """
       A class for controlling the format of messages are sent.
       internally All messages are represented as v03. 
       post format implement translations to other protocols for interop.

   """

    @staticmethod
    def content_type():
        return 'application/json'

    @staticmethod
    def mine(payload, headers, content_type) -> bool:
        """
          return true if the message is in this post format.
       """
        if content_type == V03.content_type():
            return True
        return False

    @staticmethod
    def importMine(body, headers) -> sarracenia.Message:
        """
          given a message in a wire format, with the given properties (or headers) in a dictionary,
          return the message as a normalized v03 message.
       """
        msg = sarracenia.Message()
        msg["_format"] = __name__.split('.')[-1].lower()
        try:
            msg.copyDict(json.loads(body))
        except Exception as ex:
            logger.warning('expected json, decode error: %s' % ex)
            logger.warning( f'body: {body}' )
            logger.debug('Exception details: ', exc_info=True)
            return None

        """ early sr3 versions used retPath, name changed by https://github.com/MetPX/sarracenia/issues/628
        """
        if 'retPath' in msg:
            msg['retrievePath'] = msg['retPath']
            del msg['retPath']

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
