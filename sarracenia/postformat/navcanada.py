import logging
import sarracenia
import uuid
from sarracenia.postformat import PostFormat
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class NavCanada(PostFormat):
    """
        NAV CANADA NAVCANHub format.
    """

    MSG_TYPE = 'METPX-SR3-NAVCAN'

    @staticmethod
    def content_type():
        return 'unknown'

    @staticmethod
    def mine(payload, headers, content_type, options) -> bool:
        """
            Determine if the message is in NAV CANADA format.

            payload is the message data (i.e. inline content), not always present, useless
                for determining the type of message we received
            headers is the "Application Properties" data from an AMQP 1.0 message. We use
                data from the headers to determine if we've received a SWIM format message.
            content_type is the content type of payload/data itself, also useless here
        """
        return ( ('MSG_TYPE' in headers and (headers['MSG_TYPE'] in ['NCFILESHARE', NavCanada.MSG_TYPE] 
                                            or headers['MSG_TYPE'].startswith("TAC-") ))
                # we don't know all of NC's MSG_TYPE possibilities, so add a fallback on other known things in the msg
                or ('MSG_TYPE' in headers and 'MSG_UUID' in headers)
                or ('MSG_TYPE' in headers and 'MSG_PUBLISH_TIME' in headers)
                )

    @staticmethod
    def parseNavCanTime(time):
        """ parse any NAV CANADA time format into an sr3 time string (YYYYmmddTHHMMSS.sss)
            Example inputs:
                epoch: 1772657588 (string or int)
                ISO:   2026-08-18T08:13:08.399Z or # 2026-08-18T08:13:08.399
        """
        try:
            if isinstance(time, str):
                time = time.replace('Z', '')
                if 'T' in time and ':' in time and '-' in time and '.' in time:
                    dt = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%f')
                    return dt.strftime("%Y%m%dT%H%M%S.%f")[:-3]
                elif 'T' in time and ':' in time and '-' in time:
                    dt = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S')
                    return dt.strftime("%Y%m%dT%H%M%S.%f")[:-3]
                else:
                    try:
                        dt = datetime.fromtimestamp(int(time), tz=timezone.utc)
                        return dt.strftime("%Y%m%dT%H%M%S.%f")[:-3]
                    except Exception as e:
                        # ERROR message below will be logged
                        logger.debug(f"{e}", exc_info=True)

            elif isinstance(time, int):
                dt = datetime.fromtimestamp(time, tz=timezone.utc)
                return dt.strftime("%Y%m%dT%H%M%S.%f")[:-3]
        except Exception as e:
            logger.error(f"Time parsing failed: {time} reason: {e}")
            logger.debug("Exception details:", exc_info=True)

        logger.error(f"unsupported time format: {time}, USING CURRENT TIME")
        return sarracenia.nowstr()

    @staticmethod
    def importMine(body, headers, options) -> sarracenia.Message:
        """
            given a message in NAV CANADA format return the message as a normalized v03 message.
            headers is the app properties from the AMQP1.0 message.
            body is the data itself (inline content).

            There are multiple message formats from NC. This code is trying to do the bare minimum to import
            a usable sr3 message. An internal plugin will be used for additional path derivation/renaming, etc.
            as required. The plugin can be easily modified without needing to release and deploy a new version
            of sr3.

            Example App Properties:
            properties={
                'NCFILESHARE_FILE_NAME':    'SPCN61_CZUM_042052__CZUM_41605:CZUM:SP:CZUM:Direct',
                'MSG_TYPE':                 'NCFILESHARE',
                'MSG_SCHEMA_VERSION':       '1',
                'DESTINATION_TYPE':         'Topic',
                'MSG_SCHEMA_NAMESPACE':     'https://navacanada.ca/ncfileshare',
                'NCFILESHARE_FILE_MTIME':   '1772657588',
                'DESTINATION':              'NCFILESHARE/ALL/CERT/WEATHER/CN/CZUM/SP/61/',
                'MSG_PUBLISH_TIME':         '2026-03-04T20:57:51.829Z',
                'UUID':                     'bc057636-2399-4818-abdc-fb6e775b8e57',
                'MSG_VERSION':              'V1',
                'MSG_ORIGINATOR':           'NCFILESHARESERVICE'
                },

            Example WOS (JSON) Message:
            Message(address='ODEX/CZEG/CYEG/CYEG/WOS/V2',
                properties={
                    'DESTINATION_TYPE': 'Topic',
                    'MSG_TYPE': 'WOS',
                    'MSG_ORIGINATOR': 'ODEX',
                    'FIR': 'CZEG',
                    'SITE_ID': 'CYEG',
                    'SENSOR_ID': 'CYEG',
                    'DESTINATION': 'CYEG',
                    'MSG_UUID': 'cd3d0c8c-68dd-4b10-b5f4-b5f5d08d8278',
                    'MSG_PUBLISH_TIME': '2026-10-14T19:47:24.000363Z',
                    'OBSERVATION_TIME': '2026-10-14T19:47:00.000000Z'},
                body='{ json stuff here }')

            Example METCAM message:
            Message(priority=4, id=2,
                properties={
                    'UUID': 'a5fa5a52-7ae5-4511-901c-e1f1dd334616',
                    'MSG_ID': 'CYXH_N_2026-10-15T09:00:13.404091+00:00',
                    'DESTINATION': 'topic://METCAM/REPORT/V2/CYXH/N/PUBLIC/JSON/',
                    'MSG_PUBLISH_TIME': '2026-10-15T09:00:13.404091+00:00',
                    'MSG_TYPE': 'METCAM_REPORT',
                    'MSG_ORIGINATOR': 'METCAM_ADMIN',
                    'DESTINATION_TYPE': 'Topic',
                    'MSG_METCAM_PAYLOAD_TYPE': 'JSON',
                    'METCAM_ORIGINATOR_ADDRESS': 'METCAM_ADMIN'},
                body='{ json stuff here }')

        """
        msg = sarracenia.Message()
        msg["_format"] = __name__.split('.')[-1].lower()
        logger.debug(f"received a NAVCAN message headers={headers}")

        # store all AMQP1 properties in case they are useful later
        msg['_amqp1_properties'] = headers
        msg['_deleteOnPost'].add('_amqp1_properties')

        # MSG_PUBLISH_TIME -> pubTime: mandatory in sr3
        # YYYYMMDDTHHMMSS.s
        if 'MSG_PUBLISH_TIME' in headers:
            msg['pubTime'] = NavCanada.parseNavCanTime(headers['MSG_PUBLISH_TIME'])
        else:
            logger.error("message missing MSG_PUBLISH_TIME, using current time")
            msg['pubTime'] = sarracenia.nowstr()

        # build relPath
        # NOTE: we currently do not expect to receive messages with URLs from NC, inline data only
        msg['relPath'] = ''
        # build relPath from DESTINATION and NCFILESHARE_FILE_NAME, so we can at least have a file path and
        # name to work with (mirror) when writing the data from the message.
        if 'DESTINATION' in headers:
            msg['relPath'] += headers['DESTINATION']
        if len(msg['relPath']) > 0 and msg['relPath'][-1] != '/':
            msg['relPath'] += '/'
        if 'NCFILESHARE_FILE_NAME' in headers:
            msg['relPath'] += headers['NCFILESHARE_FILE_NAME']
        elif 'FILE_NAME' in headers:
            msg['relPath'] += headers['FILE_NAME']
        # if there's no FILE_NAME, we can end up with a relPath that ends in /, get rid of that
        if msg['relPath'][-1] == '/':
            msg['relPath'] = msg['relPath'].rstrip('/')
        # some messages include the topic:// in DESTINATION
        if 'topic://' in msg['relPath']:
            msg['relPath'] = msg['relPath'].replace('topic://', '')

        # if we can't get a useful relPath then we can't download the data
        if len(msg['relPath']) == 0:
            logger.error("could not derive relPath from incoming message")
            return None

        # File mtime, have seen both '1772657588' and '2026-06-22T18:49:40.445Z' format.
        if 'NCFILESHARE_FILE_MTIME' in headers or 'FILE_MTIME' in headers:
            mt = headers['NCFILESHARE_FILE_MTIME'] if 'NCFILESHARE_FILE_MTIME' in headers else headers['FILE_MTIME']
            msg['mtime'] = NavCanada.parseNavCanTime(mt)

        # handle inline content from AMQP1.0
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

            msg['size'] = len(payload)

            decoded_payload = None
            # Only expecting to receive UTF-8 encoded data from NC
            try:
                decoded_payload = payload.decode('utf-8')
                msg['content'] = {
                    'encoding': 'utf-8',
                    'value': decoded_payload
                }
            except Exception as e:
                logger.error(f"failed to decode inline content in message: {e}")
                logger.debug("Exception Details", exc_info=True)
                return None

        else:
            logger.error(f"inline content missing from message, message is invalid, cannot import")
            return None

        # baseUrl is mandatory and sr3 will crash without it
        msg['baseUrl'] = "none://"

        msg['topic'] = headers['amqp1_address'].replace("topic://", "")

        return msg

    @staticmethod
    def exportMine(sr3_msg, options) -> dict:
        """
            given a v03 (internal) message, produce an encoded NAVCAN version.

            returns: body, headers, content_type

            body: inline content in UTF-8 encoding

            headers: see PDF doc
        """

        # NAVCANADA broker requires topic:// prefix, rather than hardcoding that, we'll add it in the configured
        # post_topicPrefix option and then only include it in the address when needed.
        post_topicPrefix = '/'.join(options['post_topicPrefix'])
        clean_topicPrefix = post_topicPrefix.replace("topic://", "")

        # Static:
        headers = {
            'MSG_TYPE':         NavCanada.MSG_TYPE, # default, normally overridden by a plugin, see below
            'MSG_ORIGINATOR':   clean_topicPrefix.split('/')[0], # should be ECCC when publishing to NC
            'DESTINATION_TYPE': 'Topic',
        }

        # Set topic / DESTINATION
        # Normally, this message format will be used in combination with a plugin that sets msg['topic']
        # and topicDerive will return that value. When topic is returned from the message, the topicPrefix is
        # *not* already in the topic, so we add it here. If topic is not in the message, it will be derived from
        # the relPath or msg['subtopic'], and topicPrefix *will* be added. We have to handle both possibilities.

        # topic must be uppercase, but the topic:// part can't be
        post_topic = '/'.join(PostFormat.topicDerive(sr3_msg, options)).upper()
        if post_topicPrefix.upper() in post_topic:
            post_topic = post_topic.replace(post_topicPrefix.upper(), post_topicPrefix)

        if post_topicPrefix not in post_topic:
            post_topic = post_topicPrefix + '/' + post_topic

        # NAVCAN's doc says it must end with /
        if post_topic[-1] != '/':
            post_topic += '/'

        logger.debug(f"derived topic {post_topic}")

        headers['topic'] = post_topic
        headers['DESTINATION'] = post_topic.replace(post_topicPrefix, clean_topicPrefix)

        relPath_split = sr3_msg['relPath'].split('/')

        if 'new_file' in sr3_msg:
            headers['FILE_NAME'] = sr3_msg['new_file']
        else:
            headers['FILE_NAME'] = relPath_split[-1]

        # mtime is optional
        if 'mtime' in sr3_msg:
            try:
                mtime = NavCanada.__sarra_timestr_to_dt(sr3_msg['mtime'])
                headers['FILE_MTIME'] = NavCanada.__dt_to_nc_timestr(mtime)
            except Exception as e:
                logger.warning(f"failed to parse mtime {sr3_msg['mtime']} {e}")

        if 'pubTime' in sr3_msg:
            try:
                pubTime = NavCanada.__sarra_timestr_to_dt(sr3_msg['pubTime'])
            except Exception as e:
                logger.warning(f"failed to parse pubTime {sr3_msg['pubTime']}")
                pubTime = datetime.now()
        else:
            pubTime = datetime.now()
        headers['MSG_PUBLISH_TIME'] = NavCanada.__dt_to_nc_timestr(pubTime)

        headers['UUID'] = str(uuid.uuid4())

        # inline content (AMQP1.0 body) must be UTF-8
        if 'content' in sr3_msg and sr3_msg['content'] and sr3_msg['content']['encoding'] == 'utf-8':
            raw_body = sr3_msg['content']['value']
        elif 'content' in sr3_msg and sr3_msg['content'] and sr3_msg['content']['encoding'] != 'utf-8':
            logger.error("cannot export to NAV CANADA format; content is not UTF-8 encoded for "
                         + f"{sr3_msg.get('baseUrl', '')} {sr3_msg.get('relPath', '')}")
            return None, None, None
        else:
            logger.error(f"inline content missing from {sr3_msg}")
            return None, None, None

        # NAV CANADA requires that embedded content is <30 MB but leave it up to the person
        # writing the config to enforce that with fileSizeMax.
        content_size = sr3_msg['size'] if 'size' in sr3_msg else len(raw_body)
        if content_size > 31457280:
            content_size_mb = content_size / 1024 / 1024
            logger.warning(f"content size {content_size_mb} is larger than 30 MB (set fileSizeMax)")

        # content-type in AMQP1 message is the type of the body
        # for NAVCANADA, the message body is the data itself
        contentType = sr3_msg.get('contentType', 'text/plain')

        # Allow plugins to set and/or override properties in the exported message.
        # For example: sr3_msg['navcan_properties_override'] = { 'AMHS_FILENAME': 'something' }
        # will either set or overwrite the AMHS_FILENAME header.
        # A plugin is used to set the message type to one of the following:
        # TAC-FA - Aviation Area Forecasts
        # TAC-FB - Forecast upper winds and temperatures
        # TAC-FD - Wind and temperatures aloft forecasts
        # TAC-FN - Space Weather Advisories
        # TAC-FT - Aviation Terminal Forecasts
        # TAC-SA - Hourly aviation weather reports
        # TAC-SM - Main hour synoptic reports
        # TAC-SP - Special aviation weather reports
        # TAC-UA - Pilot weather reports
        # TAC-WA - AIRMET messages and/or US flight advisories
        # TAC-WS - SIGMET messages - WSCNxx, WCCNxx (tropical cyclone)
        # TAC-WC - Tropical Cyclone messages
        # TAC-WV - VA SIGMET messages
        # This is so we can just change the plugin if we need to support different msg types, without needing
        # to release a whole new version of sr3.
        if 'navcan_properties_override' in sr3_msg:
            if isinstance(sr3_msg['navcan_properties_override'], dict):
                headers.update(sr3_msg['navcan_properties_override'])
            else:
                logger.error("navcan_properties_override is defined but is not a dict")

        return raw_body, headers, contentType

    @staticmethod
    def __sarra_timestr_to_dt(sarra_time_str):
        if '.' not in sarra_time_str:
                sarra_time_str += '.0'
        # sometimes we get times like this: 20260309T191032.404855967
        # so use only the first 22 characters
        dt = datetime.strptime(sarra_time_str[:22], "%Y%m%dT%H%M%S.%f")
        return dt

    @staticmethod
    def __dt_to_nc_timestr(dt):
        """ convert a datetime object to NAV CANADA's time string.
            e.g. 2026-10-08T17:42:38.456Z
        """
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
