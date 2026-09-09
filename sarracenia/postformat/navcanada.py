import logging
import sarracenia
import gzip
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
        return ('MSG_TYPE' in headers and (headers['MSG_TYPE'] in ['NCFILESHARE', NavCanada.MSG_TYPE] 
                                            or headers['MSG_TYPE'].startswith("TAC-") ) )
    @staticmethod
    def parseNavCanTime(time):
        """ parse any NAV CANADA time format into an sr3 time string (YYYYmmddTHHMMSS.sss)
            Example inputs:
                epoch: 1772657588 (string or int)
                ISO:   2026-08-18T08:13:08.399Z or # 2026-08-18T08:13:08.399
        """
        if isinstance(time, str):
            time = time.replace('Z', '')
            if 'T' in time and ':' in time and '-' in time:
                dt = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%f')
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

        logger.error(f"unsupported time format: {time}, USING CURRENT TIME")
        return sarracenia.nowstr()

    @staticmethod
    def importMine(body, headers, options) -> sarracenia.Message:
        """
            given a message in NAV CANADA format return the message as a normalized v03 message.
            headers is the app properties from the AMQP1.0 message.
            body is the data itself (inline content).

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

            decompressed_payload = payload
            decoded_payload = None
            # Detect if the payload is gzipped
            try:
                # FIXME: i think we should support gzip as an inline content encoding and unzip somewhere else
                # in the code, but leaving this here for now. (Derived from the SWIM code).
                # content_encoding is only mandatory when compression is used
                if 'amqp1_content_encoding' in headers and headers['amqp1_content_encoding'] == "gzip":
                    if payload[:2] == b'\x1f\x8b':  # GZIP magic number
                        decompressed_payload = gzip.decompress(payload)
                        msg['size'] = len(decompressed_payload)  # size should be the size in bytes of the content
                        decoded_payload = decompressed_payload.decode('utf-8')
                    else:
                        logger.warning("Payload does not appear to be gzipped, but content encoding is set to gzip!")
                        decoded_payload = payload.decode('utf-8')
                else:
                    decoded_payload = payload.decode('utf-8')
            except Exception as e:
                logger.error(f"failed to read inline content in NAV CANADA message")
                logger.debug("Exception Details", exc_info=True)

            if decoded_payload:
                msg['content'] = {
                    'encoding': 'utf-8',
                    'value': decoded_payload
                }

        # baseUrl is mandatory and sr3 will crash without it
        msg['baseUrl'] = "none://"

        msg['topic'] = headers['amqp1_address'].replace("topic://", "")

        return msg

    @staticmethod
    def exportMine(sr3_msg, options) -> dict:
        """
            given a v03 (internal) message, produce an encoded NAVCAN version.

            returns: body, headers, content_type

            body: inline content in FIXME encoding

            headers: see PDF doc for now
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
        if 'navcan_msg_type' in sr3_msg:
            headers['MSG_TYPE'] = sr3_msg['navcan_msg_type']

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

        if 'mtime' in sr3_msg:
            mtime = NavCanada.__sarra_timestr_to_dt(sr3_msg['mtime'])
            try:
                headers['FILE_MTIME'] = mtime.isoformat()[:-3] + 'Z'
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
        headers['MSG_PUBLISH_TIME'] = pubTime.isoformat()[:-3] + 'Z'

        headers['UUID'] = str(uuid.uuid4())

        if 'content' in sr3_msg and sr3_msg['content']:
            raw_body = sr3_msg['content']['value']
            # TODO content encoding (and contentType below)
        else:
            raw_body = ''

        # NAV CANADA requires that embedded content is <30 MB but leave it up to the person
        # writing the config to enforce that with fileSizeMax.
        content_size = sr3_msg['size'] if 'size' in sr3_msg else len(raw_body)
        if content_size > 31457280:
            content_size_mb = content_size / 1024 / 1024
            logger.warning(f"content size {content_size_mb} is larger than 30 MB (set fileSizeMax)")

        # content-type in AMQP1 message is the type of the body
        # for NAVCANADA, the message body is the data itself
        contentType = sr3_msg.get('contentType', 'text/plain')

        # Set schema info when the data is IWXXM
        if 'iwxxm' in raw_body:
            ns_start = raw_body.find('xmlns:iwxxm="')
            if ns_start > 0:
                try:
                    schema_ns = raw_body[ns_start:].split('"')[1]
                    schema_ver = schema_ns.split('/')[-1]
                    headers['MSG_NAMESPACE'] = schema_ns
                    if schema_ver.count('.') < 2:
                        schema_ver += '.0'
                    headers['MSG_SCHEMA_VERSION'] = schema_ver
                except Exception as e:
                    logger.debug(f"Could not set schema namespace {e}")
        else:
            headers['MSG_VERSION'] = 'V1'

        return raw_body, headers, contentType

    @staticmethod
    def __sarra_timestr_to_dt(sarra_time_str):
        if '.' not in sarra_time_str:
                sarra_time_str += '.0'
        # sometimes we get times like this: 20260309T191032.404855967
        # so use only the first 22 characters
        dt = datetime.strptime(sarra_time_str[:22], "%Y%m%dT%H%M%S.%f")
        return dt
