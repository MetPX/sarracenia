import json
import logging
import sarracenia
from sarracenia.postformat import PostFormat
import urllib
import gzip
from datetime import datetime
import xml.etree.ElementTree as ET


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
            will contain conformsTo (mandatory), and the conformsTo value will contain 'swim'.
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
        # Otherwise we use update.
        # but baseUrl and relPath are always mandatory in sr3. FIXME what to do when links not avail?
        i = 0
        while True:
            if f'links[{i}].rel' in headers:
                rel = headers[f'links[{i}].rel'].lower()
                typ = headers[f'links[{i}].type']
                href = headers[f'links[{i}].href']
                logger.debug(f'links[{i}] .rel={rel} .type={typ} .href={href}')
                if rel == 'canonical' or rel == 'update':
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

        # handle inline content
        # based on https://github.com/iblsoft/swimdemo/blob/main/amqp_client_example.py
        if body:
            if 'amqp1_content_type' in headers:
                msg['contentType'] = str(headers['amqp1_content_type'])

            if isinstance(body, memoryview):
                payload = body.tobytes()
            elif isinstance(body, (bytes, bytearray)):
                payload = bytes(body)
            else:
                payload = str(body).encode()

            decompressed_payload = payload
            decoded_payload = None
            # Detect if the payload is gzipped
            try:
                # FIXME: i think we should support gzip as an inline content encoding and unzip somewhere else
                # in the code, but leaving this here for now.
                # content_encoding is only mandatory when compression is used
                if 'amqp1_content_encoding' in headers and headers['amqp1_content_encoding'] == "gzip":
                    if payload[:2] == b'\x1f\x8b':  # GZIP magic number
                        decompressed_payload = gzip.decompress(payload)
                        decoded_payload = decompressed_payload.decode('utf-8')
                    else:
                        print("Payload does not appear to be gzipped, but content encoding is set to gzip!")
                        decoded_payload = payload.decode('utf-8')
                else:
                    decoded_payload = payload.decode('utf-8')
            except Exception as e:
                logger.error(f"failed to read inline content in SWIM message")
                logger.debug("Exception Details", exc_info=True)

            if decoded_payload:
                msg['content'] = {
                    'encoding': 'utf-8',
                    'value': decoded_payload
                }
                # FIXME: sr3 bug:   File "/net/local/home/sunderlandr/sr3/sarracenia/flow/__init__.py", line 1424, in write_inline_file
                #                   if ((msg['size'] > 0) and len(data) != msg['size']):
                #                   KeyError: 'size'
                # inline data download does not work when size is not set
                msg['size'] = len(decoded_payload)

        if 'baseUrl' not in msg or 'relPath' not in msg:
            msg['baseUrl'] = 'http://fake/'
            # the subject seems to be the filename, without the extension
            msg['relPath'] = headers['amqp1_subject']


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
    def exportMine(body, options) -> dict:
        """
            given a v03 (internal) message, produce an encoded SWIM version.

            Data specific details::
                properties.datetime 
                    METAR/SPECI data only. Observation time in RFC 3339 format
                properties.{end,start}_datetime
                    TAF/SIGMET data only. Start,end of validity period in RFC 3339 format


            Mandatory fields::
                topic
                content-type
                subject
                properties.pubtime (extracted from iwxxm:issueTime)
                properties.datetime (for observations)
                properties.{start,end}_datetime (for TAR/SIGMET)
            Conditional fields::
                content-encoding (defaults to `identity` - for uncompressed data)
                properties.icao_location_identifier
                properties.icao_location_type
                properties.integrity.* (sha512 recommended)
                links.*
                geometry.*
                    

            Improvements::
                - Add amendment support. Some fields like the subject and the links[x].rel value 
                    can be based off of the data is an amendment or not
                - Add a technical message field?
                    https://github.com/iblsoft/swimdemo/blob/main/MET-SWIM-AMQP-Guidance.md#technical-messages
                - Add geometry coordinates support?
        """

        # What TODO with data that isn't in the sarracenia messages' contents?
        # We'd need a way to get information for the subject, topic, etc. some other way and pass it to the downstream message

        logger.critical(f"Incoming sarracenia message {body}")
        logger.critical(f"Options: {'.'.join(options['post_topicPrefix'][:])}")

        raw_body = {}
        # Generate datetime
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        if 'content' in body and body['content']:
            for datatype in [ 'METAR', 'TAF', 'SIGMET', 'SPECI']:
                # Try to find data type and assign values according to data type
                # https://github.com/iblsoft/swimdemo/blob/main/MET-SWIM-AMQP-Guidance.md#document-structure-overview
                if body['content']['value'].find(f'iwxxm:{datatype}') != -1:
                    if datatype == 'METAR' or datatype == 'SPECI':
                        raw_body['properties.datetime'] = now
                        raw_body['conformsTo'] = 'https://eur-registry.swim.aero/services/eurocontrol-iwxxm-metar-speci-subscription-and-request-service-10'
                        if datatype == 'SPECI': raw_body['amqp1_default_priority'] = 7
                        if datatype == 'METAR': raw_body['amqp1_default_priority'] = 4
                    if datatype == 'SIGMET' or datatype == 'TAF':
                        # FIXME: Use XML parsing to fetch values
                        raw_body['properties.end_datetime'] = now
                        raw_body['properties.start_datetime'] = now
                        raw_body['conformsTo'] = f'https://eur-registry.swim.aero/services/eurocontrol-iwxxm-{datatype.lower()}-subscription-and-request-service-10'
                        if datatype == 'SIGMET': raw_body['amqp1_default_priority'] = 7
                        if datatype == 'TAF': raw_body['amqp1_default_priority'] = 5
                        
                    # Topic in WIS2 format : https://community.wmo.int/en/activity-areas/wis/WIS2-overview
                    # metpx-sarracenia as center-id
                    # core data, being free and unrestricted
                    if options['post_topicPrefix']:
                        raw_body['topic'] = '.'.join(options['post_topicPrefix'][:]) + f'.weather.{datatype.lower()}'
                        #raw_body['topic'] =  f'origin.a.wis2.ca-eccc-msc.data.core.weather.{datatype.lower()}'
                    else:
                        raw_body['topic'] = ''


            try:
                # Get pubtime
                xml_root = ET.fromstring(body['content']['value'])
                # Based on what we receive from the DMS
                issue_time = xml_root.find('.//{http://icao.int/iwxxm/3.0}issueTime')
                time_instant = issue_time.find('TimeInstant')
                time_position = time_instant.find('{http://www.opengis.net/gml/3.2}timePosition')
                raw_body['properties.pubtime'] = time_position.text

            except Exception as e:
                # FIXME? Give sarracenia pubTime instead. Needs to conform to
                logger.error("Unable to fetch pubtime from source.")
                logger.error("Exception Details", exc_info=True)
                raw_body['properties.pubtime'] = now

            # Default location to CWAO for now
            # FIXME: Add specific 4 letter code. Extract from XML
            # FIXME: Amendment support
            # raw_body['properties.pubtime'] = 2025-07-25T21:01:23Z
            YYYY = raw_body['properties.pubtime'][0:4]
            MM = raw_body['properties.pubtime'][5:7]
            DD = raw_body['properties.pubtime'][8:10]
            HH = raw_body['properties.pubtime'][11:13]
            mm = raw_body['properties.pubtime'][14:16]
            SS = raw_body['properties.pubtime'][17:19]
            raw_body['amqp1_subject'] = f"DATA_{datatype}_CWAO_NORMAL_{YYYY}{MM}{DD}{HH}{mm}{SS}"

            try:
                # Default data to be gzipped
                encoded_content = body['content']['value'].encode('utf-8')
                compressed_content = gzip.compress(encoded_content)

                raw_body['amqp1_content_encoding'] = "gzip"
                raw_body['body'] = compressed_content

            except Exception:
                # Default to identity if can't gzip
                raw_body['amqp1_content_encoding'] = 'identity'
                raw_body['body'] = body['content']['value'].encode('utf-8')
                
        # If we don't have a payload in the incoming sarracenia message, we need to include a link to the data.
        # We should still add an external link to the data even if we don't have the payload in the incoming sarracenia message.
        # We're only going to include 1 link (for now) to conform with sarracenia standards.
        # https://github.com/iblsoft/swimdemo/blob/main/MET-SWIM-AMQP-Guidance.md#conditional-properties---external-links


        if 'baseUrl' in body and body['baseUrl'] and 'relPath' in body and body['relPath']:
            # Advertised linked data should be XML formatted
            raw_body['links[0].type'] = 'application/xml'

            # Canonical - primary data link
            # Update - For amendments
            raw_body['links[0].rel'] = 'canonical'
            raw_body['links.count'] = 1
            if body['baseUrl'][-1] == '/' or body['relPath'][0] == '/': 
                raw_body['links[0].href'] = f"{body['baseUrl']}{body['relPath']}"
            else:
                raw_body['links[0].href'] = f"{body['baseUrl']}/{body['relPath']}"


        # Topic in WIS2 format : https://community.wmo.int/en/activity-areas/wis/WIS2-overview
        # metpx-sarracenia as center-id
        # core data, being free and unrestricted
        if options['post_topicPrefix'] and 'topic' not in raw_body:
            raw_body['topic'] = '.'.join(options['post_topicPrefix'][:]) + '.weather'
            #raw_body['topic'] = 'origin.a.wis2.ca-eccc-msc.data.core.weather'

        #TODO: Should this be different from the topic??
        raw_body['amqp1_address'] = raw_body['topic']

        if 'amqp1_default_priority' not in raw_body:
            raw_body['amqp1_default_priority'] = 3

        # Assume its a METAR/SPECI for now I guess?
        if 'properties.datetime' not in raw_body and 'properties.start_datetime' not in raw_body:
            raw_body['properties.datetime'] = now
        # Give a fake value for now as well
        if 'properties.pubtime' not in raw_body:
            raw_body['properties.pubtime'] = now

        if 'amqp1_subject' not in raw_body:
             raw_body['amqp1_subject'] = f"DATA_NOTDEFINED_CWAO_NORMAL_{YYYY}{MM}{DD}{HH}{mm}{SS}"

        if 'identity' in body and body['identity']:
            raw_body['properties.integrity.method'] = body['identity']['method']
            raw_body['properties.integrity.value'] = body['identity']['value']

        if 'contentType' in body:
            if 'xml' in body['contentType'] and 'content' in body and body['content'] is not None:
                body['amqp1_content_type'] = 'application/xml'
            # Only assign uri-list when data only available from link
            else:
               body['amqp1_content_type'] = 'application/uri-list'

            # For technical messages
            if 'json' in body['contentType']:
                raw_body['amqp1_content_type'] = 'application/json'

        logger.critical(f"SWIM Message : {raw_body}")

        return raw_body