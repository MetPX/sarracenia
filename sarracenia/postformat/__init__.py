
import logging
import sarracenia

logger = logging.getLogger(__name__)


class PostFormat:
    """
       A class for controlling the content of notification messages when received or sent,
       as opposed to internal represenation in the Sarracenia.

       Internally All messages are represented as python dictionaries with
       fields identical to v03 messages. 

       PostFormats convert between message payload protocols and in-memory Sarracenia.Message
       formats.

       To add new post formats just add sub-classes. they will be discovered at run-time.

       Every message read in will have include the *_format* field, identifying the format
       of the incoming message.

       each subclass implements:

       def mine(payload, headers, content_type) -> bool:

       which returns True of the message is in the given post format.

       subclasses have encode and decode routines with different signatures.

       def import(payload, headers, topic, topicPrefix) -> sarracenia.Message:
            given this wire payload, return a native data structure (v03 in a dictionary)

       def export(msg) -> ( body (str), headers (dict), contenty_typ (str) ) :
            opposite of decode, take a v03 message and encode it for sending on the wire.
            returns a tuple to be passed to mqp apis.

       These are used by the Any routines in this class.
    """

    def content_type(post_format):
        for sc in PostFormat.__subclasses__():
            if post_format == sc.__name__.lower():
                return sc.content_type() 
        return None

        return self.mimetype

    @staticmethod
    def importAny(payload, headers, content_type, options ) -> sarracenia.Message:
        """
          given a message in a wire format, with the given properties (or headers) in a dictionary,
          return the message as a normalized v03 message.

          msg['_format'] will be set to the name of the postformat detected and decoded.
       """
        for sc in PostFormat.__subclasses__():
            #logger.info( f" sc={sc}, scct={sc.content_type()}, content_type={content_type} " )
            if sc.mine(payload, headers, content_type, options ):
                return sc.importMine(payload, headers, options )
        return None

        pass

    @staticmethod
    def exportAny(msg, post_format='v03', topicPrefix=[ 'v03' ], options={ 'post_format': 'v03', 'topicPrefix':'v03' } ) -> (str, dict, str):
        """
          return a tuple of the encoded message body, a headers dict, and content_type
          and a completed topic as a list as one header.
       """
        for sc in PostFormat.__subclasses__():
            if post_format == sc.__name__.lower():
                return sc.exportMine( msg, options ) 

        return None, None, None

    def topicDerive(msg, options ) -> list:
        """
           Sarracenia standard topic derivation.

           https://metpx.github.io/sarracenia/Explanation/Concepts.html#amqp-v09-rabbitmq-settings

        """

        if options['broker'].url.scheme.startswith('mqtt'):
            if ( 'exchange' in options ) and ( 'topicPrefix' in options ):
                if 'exchangeSplit' in options and options['exchangeSplit'] > 1:
                    idx = sum( bytearray(msg['identity']['value'], 'ascii')) % len(options['exchange'])
                    exchange = options['exchange'][idx]
                else:
                    exchange = options['exchange'][0]
            topic_prefix = [exchange] + options['topicPrefix']
            topic_separator='/'
        else:
            topic_prefix = options['topicPrefix']
            topic_separator='.'

        if 'topic' in msg:
            if type(msg['topic']) is list:
                topic = msg['topic']
            else:
                topic = msg['topic'].split(topic_separator)
        elif 'topic' in options and options['topic'] and (type(options['topic']) is not list):
            topic = options['topic'].split(topic_separator)
        else:
            if 'relPath' in msg: 
                topic = topic_prefix + msg['relPath'].split('/')[0:-1]
            elif 'subtopic' in msg:
                topic = topic_prefix + msg['subtopic']  
            else:
                topic = topic_prefix
        return topic

   

# test for v04 first, because v03 may claim all other JSON.
import sarracenia.postformat.wis
import sarracenia.postformat.v03
import sarracenia.postformat.v02

