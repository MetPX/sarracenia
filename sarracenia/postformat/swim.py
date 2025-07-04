import json
import logging
import sarracenia
from sarracenia.postformat import PostFormat
import urllib
import uuid

logger = logging.getLogger(__name__)

class Swim(PostFormat):
    """
        MET-SWIM message format (Meteorological System Wide Information Management)
        https://github.com/iblsoft/swimdemo/blob/main/MET-SWIM-AMQP-Guidance.md

        Used for aviation related data.
   """

    @staticmethod
    def content_type():
        return 'unknown'

    @staticmethod
    def mine(payload, headers, content_type, options) -> bool:
        """
            Determine if the message is in SWIM format. If we've received a SWIM message, headers
            will contain conformsTo, and the conformsTo value will contain 'swim'.
            Maybe there's a better way. This works for now.

            payload is the message data (i.e. inline content), not always present, useless
                for determining the type of message we received
            headers is the "Application Properties" data from an AMQP 1.0 message. We use
                data from the headers to determine if we've received a SWIM format message.
            content_type is the content type of payload/data itself, also useless here
        """
        return (headers and 'conformsTo' in headers and 'swim' in headers['conformsTo'].lower())

    @staticmethod
    def importMine(body, headers, options) -> sarracenia.Message:
        """
            given a message in a wire format, with the given properties (or headers) in a dictionary,
            return the message as a normalized v03 message.

            Example App Properties:
            properties: {'_AMQ_DUPL_ID': 'e02ac6977e3ecba847e4eb2262e99ea5e76e5ecbbb8786c8c967396ea0b99afd4a67eb9b8fcadf9f78879ac5f96b7fd1a67afef2c79732f2e20ff16fb5ae7ea7',
                       'conformsTo': 'https://eur-registry.swim.aero/services/eurocontrol-iwxxm-metar-speci-subscription-and-request-service-10',
                       'links[0].href': 'https://swim.iblsoft.com/filedb/METAR_BIGR_NORMAL_20250704170000_1.xml',
                       'links[0].rel': 'canonical',
                       'links[0].type': 'application/xml',
                       'links[1].href': 'https://edr.swim.iblsoft.com/edr/collections/iwxxm-metar/locations/icao:BIGR?datetime=2025-07-04T17:00:00Z',
                       'links[1].rel': 'item',
                       'links[1].type': 'application/zip',
                       'properties.datetime': '2025-07-04T17:00:00Z',
                       'properties.icao_location_identifier': 'BIGR',
                       'properties.icao_location_type': 'AD',
                       'properties.integrity.method': 'sha512',
                       'properties.integrity.value': 'e02ac6977e3ecba847e4eb2262e99ea5e76e5ecbbb8786c8c967396ea0b99afd4a67eb9b8fcadf9f78879ac5f96b7fd1a67afef2c79732f2e20ff16fb5ae7ea7',
                       'properties.pubtime': '2025-07-04T17:00:00Z',
                       'topic': 'origin.a.wis2.com-ibl.data.core.weather.aviation.metar'
                       }

        """
        msg = sarracenia.Message()
        msg["_format"] = __name__.split('.')[-1].lower()
        logger.error(f"GOT A SWIM MESSAGE!! {headers}")

        # FIXME: not really sure why this is done here and not in Message constructor?
        msg['local_offset'] = 0
        msg['_deleteOnPost'].add('local_offset')

        # properties.pubtime -> pubTime: mandatory in sr3 and SWIM
        if 'properties.pubtime' in headers:
            msg['pubTime'] = headers['properties.pubtime'].replace('-','').replace(':','')
            msg['pubTime'] = msg['pubTime'].replace('Z', '.00').replace('T', '')
        else:
            logger.error("message missing mandatory properties.pubtime")

        # in SWIM, links are required *ONLY* when the payload does not contain the data
        # links[x].rel "canonical" is the "primary data link"
        #              "item" is alternative (e.g. EDR API, JSON, zipped, etc.)
        #              "update" for amended or corrected reports
        # We'll map the canonical link to baseUrl and relPath when it's available.
        # but baseUrl and relPath are always mandatory in sr3. FIXME what to do when links not avail?
        i = 0
        while True:
            if f'links[{i}].rel' in headers:
                rel = headers[f'links[{i}].rel']
                typ = headers[f'links[{i}].type']
                href = headers[f'links[{i}].href']
                logger.debug(f'links[{i}] .rel={rel} .type={typ} .href={href}')
                if rel.lower() == 'canonical':
                    urlparts = href.split('://')
                    if len(urlparts) != 2:
                        logger.error(f'problem with links[{i}] .rel={rel} .type={typ} .href={href}')
                        # FIXME what else to do
                    scheme, rest = urlparts
                    domain = rest[:rest.find('/')+1]
                    msg['relPath'] = rest[rest.find('/')+1:]
                    msg['baseUrl'] = f"{scheme}://{domain}"
                    msg['contentType'] = typ
                    break # currently ignoring other URLs
            else:
                logger.warning(f'links[{i}].rel not found')
                break
            i += 1
        # FIXME: sr3 will crash when there's no baseUrl

        # properties.integrity -> identity
        if 'properties.integrity.method' in headers and 'properties.integrity.value' in headers:
            # FIXME: SWIM requires support for sha512, sha256
            #             "should" support sha384 and "may" support sha3-256, 384, 512
            # sr3 does not support all of these right now, but it shouldn't be too hard to add them
            msg['identity'] = { "method": headers['properties.integrity.method'],
                         "value": headers['properties.integrity.value'],
                       }




        return msg
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
    def exportMine(body, options) -> tuple[str, dict, str]:
        """
           given a v03 (internal) message, produce an encoded SWIM version.
        """
        logger.critical("NOT IMPLEMENTED!!!")
        return (None, None, None)