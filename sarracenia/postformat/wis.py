import json
import logging
import sarracenia
from sarracenia.postformat import PostFormat
import uuid

#from pywis_pubsub.publish import create_message


logger = logging.getLogger(__name__)


class Wis(PostFormat):
    """

       WMO Information Service

       WMO - World Meteorological Organization

       a standard in development for exchange of weather data.

       A class for controlling the format of messages are sent.
       internally All messages are represented as v03. 
       post format implement translations to other protocols for interop.

       STATUS: creates bogus, but "correctly" formatted messages
           not working... can't even figure out what the WMO wants... 

       * there is no algorithm for the topic yet. just post a bogus one.
       * data-id field... no algorithm to derive it yet... uuid was once suggested.
       * geometry field should be set before calling.
       
       from internal format:
       * sarracenia does not include the content-type of the data in the message, so that is omitted for now.
         (reading up on relevant mime-type standards, when you do not know, you are supposed to omit.)


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
    def xxximportMine(body, headers) -> sarracenia.Message:
            """
          given a message in a wire format, with the given properties (or headers) in a dictionary,
          return the message as a normalized v03 message.

          Since I can't figure out a baseUrl, I can't import any messages. so import is broken for now.
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
    def exportMine(body,topicPrefix) -> (str, dict, str):
            """
           given a v03 (internal) message, produce an encoded version.
       """
            GeoJSONBody={ 'type': 'Feature', 'geometry': None, 'properties':{}, 'version':'v04' }

            for literal in [ 'geometry', 'properties' ]:
                if literal in body:
                    GeoJSONBody[literal] = body[literal]

            headers = { 'topic' : 'origin/a/wis2/can/eccc-msc/data/core/weather/surface-based-observations/synop'.split('/') }
            """
                  topicPrefix and body['subtopic'] could be used to build a topic...

            """
            for h in body:
                if h not in [ 'geometry', 'properties', 'size', 'baseUrl', 'relPath', 'retrievePath', 'subtopic' ]:
                    GeoJSONBody['properties'][h] = body[h]

            if 'geometry' in body:
                GeoJSONBody['geometry'] = body['geometry']

            GeoJSONBody['data_id'] =  str(uuid.uuid4())

            if 'retrievePath' in body :
                url = '/'.join( [ body['baseUrl'], body['retrievePath'] ] )
            else:
                url = '/'.join( [ body['baseUrl'], body['relPath'] ] )

            GeoJSONBody['links'] = [{
                'rel': 'canonical',
                #'type': 'unknown',, mime content-type of data, not available in message.
                'href': url,
                'length': body['size']
            }]

            raw_body = json.dumps(GeoJSONBody)
            return raw_body, headers, Wis.content_type()
