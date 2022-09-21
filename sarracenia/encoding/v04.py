import json
import logging
import sarracenia
from sarracenia.encoding import Encoding

logger = logging.getLogger(__name__)


class V04(Encoding):
    """
       A class for controlling the format of messages are sent.
       internally All messages are represented as v03. 
       encodings implement translations to other protocols for interop.

   """

    @staticmethod
    def content_type():
        return 'application/geo+json'

    @staticmethod
    def mine(payload, headers, content_type) -> bool:
        """
          return true if the message is in this encoding.
       """
        if content_type == V04.content_type():
            return True
        return False

    @staticmethod
    def importMine(body, headers, topic, topicPrefix) -> sarracenia.Message:
            """
          given a message in a wire format, with the given properties (or headers) in a dictionary,
          return the message as a normalized v03 message.
       """
            msg = sarracenia.Message()
            msg["version"] = 'v04'

            try:
                GeoJSONBody=json.loads(body)
            except Exception as ex:
                logger.warning('expected geojson, decode error: %s' % ex)
                logger.debug('Exception details: ', exc_info=True)
                return None

            for literal in [ 'geometry', 'properties' ]:
                if literal in GeoJSONBody:
                    msg[literal] = GeoJSONBody[literal]
            for h in GeoJSONBody['properties']:
                if h not in [ 'geometry', 'properties' ]:
                    msg[h] = GeoJSONBody['properties'][h]
            if 'type' in msg:
                del msg['type']

            return msg

    @staticmethod
    def exportMine(body) -> (str, dict, str):
            """
           given a v03 (internal) message, produce an encoded version.
       """
            GeoJSONBody={ 'type': 'Feature', 'geometry': None, 'properties':{} }
            for literal in [ 'geometry', 'properties' ]:
                if literal in body:
                    GeoJSONBody[literal] = body[literal]
            for h in body:
                if h not in [ 'geometry', 'properties' ]:
                    GeoJSONBody['properties'][h] = body[h]
            raw_body = json.dumps(GeoJSONBody)
            return raw_body, None, V03.content_type()
