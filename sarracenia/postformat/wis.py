import json
import logging
import sarracenia
from sarracenia.postformat import PostFormat
import urllib
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
    def mine(payload, headers, content_type, options) -> bool:
        """
          return true if the message is in this encoding.
       """
        if content_type == Wis.content_type():
            return True
        return False

    @staticmethod
    def importMine(body, headers, options) -> sarracenia.Message:
            """
          given a message in a wire format, with the given properties (or headers) in a dictionary,
          return the message as a normalized v03 message.

          Since I can't figure out a baseUrl, I can't import any messages. so import is broken for now.
          for now:  just parse the first url in 'links', assign the host part to baseUrl, and make
          the path a retrieval one.

       """
            msg = sarracenia.Message()
            msg["_format"] = __name__.split('.')[-1].lower()
            try:
                GeoJSONBody=json.loads(body)
            except Exception as ex:
                logger.warning('expected geojson, decode error: %s' % ex)
                logger.debug('Exception details: ', exc_info=True)
                return None

            if 'properties' in GeoJSONBody:
                if 'pubtime' in GeoJSONBody['properties']: 
                    t=GeoJSONBody['properties']['pubtime']
                    msg['pubTime'] = t[0:4]+t[5:7]+t[8:13]+t[14:16]+t[17:-1]
                else:
                    logger.error( 'invalid message missing pubtime (WMO mandatory field)' )
  
                for h in GeoJSONBody['properties']:
                    if h not in [ 'pubtime' ]:
                        msg[h] = GeoJSONBody['properties'][h]

            #logger.warning( f" headers: {headers}, msg: {msg}  ... GeoJSONBody: {GeoJSONBody}  ")
            if not 'type' in GeoJSONBody:
                logger.warning( 'invalid message missing type (WMO mandatory field)' )

            if 'geometry' in GeoJSONBody :
                if GeoJSONBody['geometry'] is not None:
                    msg['geometry'] = GeoJSONBody['geometry']
            else:
                logger.warning( 'invalid message missing geometry (WMO mandatory field)' )

            if not ( 'version' in GeoJSONBody and GeoJSONBody['version'] == 'v04' ):
                logger.warning( 'invalide message missing version (WMO Mandatory field)' )

            if ('data_id' in msg) and ('topic' in headers):
                msg['relPath'] = headers['topic'] + '/' + msg['data_id']
            else:
                logger.warning( 'invalid message missing data_id (WMO mandatory field)' )
           
            if 'links' in GeoJSONBody:
                urlstr = GeoJSONBody['links'][0]['href']
                url = urllib.parse.urlparse( urlstr )
                msg['size']  = GeoJSONBody['links'][0]['length']
                if 'type' in GeoJSONBody['links'][0]:
                    msg['contentType']  = GeoJSONBody['links'][0]['type']
                msg['links'] = GeoJSONBody['links']
                msg['baseUrl'] = url.scheme + '://' + url.netloc
                msg['retrievePath' ] = urlstr[len(msg['baseUrl']):] 
            else:
                logger.warning( 'message missing links (WMO mandatory field)' )

            return msg

    @staticmethod
    def exportMine(body, options) -> (str, dict, str):
            """
           given a v03 (internal) message, produce an encoded version.
       """
            GeoJSONBody={ 'type': 'Feature', 'geometry': None, 'properties':{}, 'version':'v04' }

            for literal in [ 'geometry', 'properties' ]:
                if literal in body:
                    GeoJSONBody[literal] = body[literal]

            if 'topic' in body:
                topic = body['topic'].split('/')
            elif 'topic' in options:
                topic=options['topic'].split('/')
            else:
                topic= []

            headers = { 'topic' : topic }
            """
                  topicPrefix and body['subtopic'] could be used to build a topic...

            """
            for h in body:
                if h not in [ 'contentType', 'geometry', 'properties', 'size', 'baseUrl', 'relPath', 'retrievePath', 'subtopic', 'pubTime', 'to_clusters', 'from_cluster', 'filename', 'sundew_extension', 'mtime', 'atime', 'mode', 'identity', 'topic' ]:
                    GeoJSONBody['properties'][h] = body[h]

            t=body['pubTime']
            GeoJSONBody['properties']['pubtime'] = t[0:4]+'-'+t[4:6]+'-'+t[6:11]+':'+t[11:13]+':'+t[13:] + 'Z'

            if 'geometry' in body:
                GeoJSONBody['geometry'] = body['geometry']

            if 'id' not in body:
                GeoJSONBody['id'] =  str(uuid.uuid4())

            if 'retrievePath' in body :
                url = body['baseUrl'] + "/" + body['retrievePath']
            else:
                url = body['baseUrl'] + "/" + body['relPath']

            if not 'links' in GeoJSONBody:

                GeoJSONBody['links'] = [{
                    'rel': 'canonical',
                    #'type': 'unknown',, mime content-type of data, not available in message.
                    'href': url,
                    'length': body['size']
                }]
                if 'contentType' in body:
                    GeoJSONBody['links'][0]['type'] = body['contentType']

            raw_body = json.dumps(GeoJSONBody)
            return raw_body, headers, Wis.content_type()
