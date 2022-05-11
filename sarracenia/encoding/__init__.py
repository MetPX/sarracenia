
import logging
import sarracenia

logger = logging.getLogger(__name__)


class Encoding:
    """
       A class for controlling how Sarracenia messages are sent.
       internally All messages are represented as python dictionaries with
       fields identical to v03 messages. 

       Encodings convert between message payload protocols and in-memory Sarracenia.Message
       formats.

       To add new encodings just add sub-classes. they will be discovered at run-time.

       subclasses have encode and decode routines with different signatures.

       def import(payload, headers, topic, topicPrefix) -> sarracenia.Message:
            given this wire payload, return a native data structure (v03 in a dictionary)

       def export(msg) -> ( body (str), headers (dict), contenty_typ (str) ) :
            opposite of decode, take a v03 message and encode it for sending on the wire.
            returns a tuple to be passed to mqp apis.
    """

    def content_type(encoding_format):
        for sc in Encoding.__subclasses__():
            if encoding_format == sc.__name__.lower():
                return sc.content_type() 
        return None

        return self.mimetype

    @staticmethod
    def importAny(payload, headers, content_type, topic, topicPrefix ) -> sarracenia.Message:
        """
          given a message in a wire format, with the given properties (or headers) in a dictionary,
          return the message as a normalized v03 message.
       """
        for sc in Encoding.__subclasses__():
            #logger.info( f" sc={sc}, scct={sc.content_type()}, content_type={content_type} " )
            if sc.mine(payload, headers, content_type):
                return sc.importMine(payload, headers, topic, topicPrefix)
        return None

        pass

    @staticmethod
    def exportAny(msg, encoding_format='v03') -> (str, dict, str):
        """
          return a tuple of the encoded message body, a headers dict, and content_type
       """
        for sc in Encoding.__subclasses__():
            if encoding_format == sc.__name__.lower():
                return sc.exportMine( msg ) 

        return None, None, self.mimetype

# test for v04 first, because v03 may claim all other JSON.
import sarracenia.encoding.v04
import sarracenia.encoding.v03
import sarracenia.encoding.v02

