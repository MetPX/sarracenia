import json
import logging
import sarracenia
from sarracenia.postformat import PostFormat

logger = logging.getLogger(__name__)


class Wis(PostFormat):
    """

       WMO Information Service

       WMO - World Meteorological Organization

       a standard in development for exchange of weather data.

       A class for controlling the format of messages are sent.
       internally All messages are represented as v03. 
       post format implement translations to other protocols for interop.

   """

    @staticmethod
    def content_type():
        return 'application/geo+json'

    @staticmethod
    def mine(payload, headers, content_type) -> bool:
        """
          return true if the message is in this encoding.
       """
        if content_type == Wis.content_type():
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
            GeoJSONBody['properties']['version'] = 'v04'
            raw_body = json.dumps(GeoJSONBody)
            return raw_body, None, V03.content_type()
