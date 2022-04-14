
import logging
import sarracenia

logger = logging.getLogger(__name__)


class Encoding:
    """
       A class for controlling how Sarracenia messages are sent.
       internally All messages are represented as v03.  encodings 

       to add new encodings just add sub-classes. they will be discovered at run-time.

       subclasses have encode and decode routines with different signatures.

       def decode(payload, headers, topic, topicPrefix) -> sarracenia.Message:
            given this wire payload, return a native data structure (v03 in a dictionary)

       def encode(msg) -> ( body (str), headers (dict), contenty_typ (str) ) :
            opposite of decode, take a v03 message and encode it for sending on the wire.
            returns a tuple to be passed to mqp apis.
    """

    def content_type():
        return self.mimetype

    @staticmethod
    def decode(payload, headers, content_type, topic, topicPrefix ) -> sarracenia.Message:
        """
          given a message in a wire format, with the given properties (or headers) in a dictionary,
          return the message as a normalized v03 message.
       """
        for sc in Encoding.__subclasses__():
            #logger.info( f" sc={sc}, scct={sc.content_type()}, content_type={content_type} " )
            if sc.mine(payload, headers, content_type):
                return sc.decode(payload, headers, topic, topicPrefix)
        return None

        pass

    @staticmethod
    def encode(msg, encoding_format='v03') -> (str, dict, str):
        """
          return a tuple of the encoded message body, a headers dict, and content_type
       """
        for sc in Encoding.__subclasses__():
            if encoding_format == sc.__name__.lower():
                return sc.encode( msg ) 

        return None, None, self.mimetype

# test for v04 first, because v03 may claim all other JSON.
import sarracenia.encoding.v04
import sarracenia.encoding.v03
import sarracenia.encoding.v02

