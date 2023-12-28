#!/usr/bin/python3

"""
Plugin to poll an OData REST API
=====================================================================================

This plugin is for polling an OData REST API (https://www.odata.org/). It was written
for, and only tested with Copernicus' OData Catalogue API: 
https://dataspace.copernicus.eu/analyse/apis/catalogue-apis

This code is based on https://dataspace.copernicus.eu/news/2023-9-28-accessing-sentinel-mission-data-new-copernicus-data-space-ecosystem-apis

Filtering can be done using the default accept/reject options in Sarracenia.

URLs posted by this plugin may need authentication (e.g. with a bearer token).

  
Configurable Options:
----------------------

``pollUrl`` (required):
^^^^^^^^^^^^^^^^^^^^^^^^
    
    The ``pollUrl`` option should be set to the base URL for the API you want to query. For Copernicus, it is:
    ``pollUrl https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=``

``post_baseUrl`` (required):
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The ``post_baseUrl`` should be set to the base URL for the file download. For Copernicus, it is:
    ``post_baseUrl https://zipper.dataspace.copernicus.eu/odata/v1/``

``post_urlTemplate``:
^^^^^^^^^^^^^^^^^^^^^^

    The URL used to download the file (retrievePath) will be ``post_baseUrl`` + 
    ``post_urlTemplate.replace("--PRODUCT_ID--", "$the_product_id_from_the_API")``.

    For Copernicus, use ``post_urlTemplate Products(--PRODUCT_ID--)/$value``
    
``dataCollection``:
^^^^^^^^^^^^^^^^^^^^

    Which data collection you want to poll. 

    For Copernicus, the available options at the time of writing are: ``SENTINEL-1``, ``SENTINEL-2``, ``SENTINEL-3``,
    and ``SENTINEL-5P``.

        https://documentation.dataspace.copernicus.eu/Data.html

    You can define multiple ``dataCollections`` s in your config file.

    The ``dataCollection`` option is added to the URL as ``Collection/Name eq 'YOUR_DATA_COLLECTION_HERE'``.

    This is optional. If ``dataCollection`` is not used by the OData endpoint you are polling, leave it blank. 
    ``queryString`` can be used to manually define the query.

``timeNowMinus`` Time Range (required):
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Provides a time range to poll. The plugin will always use the current 
    date/time as the "end time" and the "start time" is determined by the ``timeNowMinus`` duration option.

    The default value is 1 hour.

    This is a duration option. It will accept a floating point number, or a floating point number suffixed with
    a unit. Examples:
        - Bare number: ``timeNowMinus 3600`` --> 3600 seconds
        - ``s`` Seconds: ``timeNowMinus 3600`` --> 3600 seconds
        - ``m`` Minutes: ``timeNowMinus 120m`` --> 120 minutes
        - ``h`` Hours: ``timeNowMinus 24h`` --> 24 hours
        - ``d`` Days: ``timeNowMinus 5d`` --> 5 days
        - ``w`` Weeks: ``timeNowMinus 1w`` --> 1 week

    For example, if the poll is running at 2023-04-26 12:35:00Z and ``timeNowMinus`` is ``1d``, 
    the time range to poll would be: ::

        ContentDate/Start gt 2023-04-25T12:35:00.000Z and ContentDate/Start lt 2023-04-26T12:35:00.000Z

``queryString``:
^^^^^^^^^^^^^^^^^

    You can use this list option to add anything to the URL. Multiple ``queryString`` s can be defined.

    For example, the URL to be polled could be: 
    ``.../odata/v1/Products?$filter=Collection/Name eq 'SENTINEL-1' and ContentDate/Start gt 2023-01-01T00:00:00.000Z and ContentDate/Start lt 2023-01-02T00:00:00.000Z``

    If you set ``queryString and OData.CSC.Intersects(area=geography'SRID=4326;POLYGON((4.220581 50.958859,4.521264 50.953236,4.545977 50.906064,4.541858 50.802029,4.489685 50.763825,4.23843 50.767734,4.192435 50.806369,4.189689 50.907363,4.220581 50.958859))')``
    the ``and OData.CSC....`` string will be appended to the URL to be polled.

    When multiple ``queryStrings`` are set, they will all be appended to the URL.
    

*Potential Room For Improvement*: 
----------------------------------

    - Let ``timeNowMinus`` be disabled to build a query without a start and end time?
    - Support checksums other than MD5

How to set up your poll config:
--------------------------------
 
    Use ``callback poll.odata``, and read about the config options above.
    
    For examples, see https://github.com/MetPX/sarracenia/tree/main/sarracenia/examples/poll files named ``*odata*.conf``. 

Change log:
-----------

    - 2023-12: first attempt
"""

import sarracenia
import datetime
import logging
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Can use ContentLength, Checksum, ID is for Downloading, need to set name somehow. If online is not true log a warning?. S3Path would be interesting.l

class Odata(sarracenia.flowcb.FlowCB):
    def __init__(self, options):
        super().__init__(options, logger)
        
        # Allow setting a logLevel *only* for this plugin in the config file:
        # set poll.odata.logLevel debug
        if hasattr(self.o, 'logLevel'):
            logger.setLevel(self.o.logLevel.upper())

        logger.debug("plugin: odata __init__")

        self.o.add_option('dataCollection', kind='list', default_value=None)
        self.o.add_option('timeNowMinus', kind='duration', default_value=3600.0) # 3600 sec = 1 hour
        self.o.add_option('queryString',  kind='list', default_value=None)
        self.o.add_option('post_urlTemplate', kind='str', default_value="--PRODUCT_ID--")
        
        # end __init__

    def poll(self) -> list:
        """Poll odata
        polling doesn't require authentication, only downloading does
        """
        logger.debug("starting poll")

        gathered_messages = []

        ### SETUP 

        # Figure out the date range
        # Format: ContentDate/Start gt 2023-04-25T12:35:00.000Z and ContentDate/Start lt 2023-04-26T12:35:00.000Z
        t_now = datetime.datetime.utcnow()
        t_range_end = t_now.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        try:
            n_seconds = float(self.o.timeNowMinus)
        except:
            logger.error("invalid timeNowMinus option")
            n_seconds = 0

        t_now_minus = t_now - datetime.timedelta(seconds=n_seconds)
        t_range_start = t_now_minus.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        time_range = f"ContentDate/Start gt {t_range_start} and ContentDate/Start lt {t_range_end}"
        logger.debug(f"Time range: {time_range} (timeNowMinus={self.o.timeNowMinus})")

        # Build the query
        query = f"{time_range}"

        # dataCollection can be empty, one thing or multiple things
        if self.o.dataCollection:
            if len(self.o.dataCollection) > 1:
                query += ' and ('
                for dc in self.o.dataCollection:
                    query += f"Collection/Name eq '{dc}' or "
                query = query[:-3] + ')' # remove the trailing or
            else:
                query += f" and Collection/Name eq '{self.o.dataCollection[0]}' "
        
        # add any query strings
        if self.o.queryString:
            for qs in self.o.queryString:
                query += f" {qs}"
        
        logger.debug(f"Full Query: {query}")
        
        ### DO THE POLL
        url = self.o.pollUrl + requests.utils.quote(query.strip())
        while url:
            logger.info(f"Polling URL: {url}")
            try:
                r = requests.get(url)
                data = r.json()

                # https://documentation.dataspace.copernicus.eu/APIs/ReleaseNotes.html#odata-catalog-api-updates
                # Sometimes the response will have a value key with list of things
                if 'value' in data:
                    for val in data['value']:
                        result = self.parse_json_to_msg(val)
                        if result:
                            gathered_messages.append(result)
                # When there's only one result, the data will be directly in the json
                elif 'Id' in data:
                    result = self.parse_json_to_msg(data)
                    if result:
                        gathered_messages.append(result)
                else:
                    logger.warning(f"Found nothing in: {data}")

                # the API only gives ~20 responses at a time. If there's more, there will be @odata.nextLink
                if '@odata.nextLink' in data:
                    url = data['@odata.nextLink']
                else:
                    url = None # stop the loop

            except Exception as e:
                logger.error(f"Error while polling URL: {url}")
                logger.debug("Exception details:", exc_info=True)
                url = None
        
        return gathered_messages

    def parse_json_to_msg(self, jdata):
        """ Build a Sarracenia message using the json data returned by the API and configured options in self.o.
        """
        msg = None

        data_path = self.o.post_urlTemplate.replace('--PRODUCT_ID--', jdata['Id'])
        msg = sarracenia.Message.fromFileInfo(data_path, self.o)

        # Set optional fields in the message

        # Give the file a nice name, if possible
        if 'Name' in jdata and len(jdata['Name']) > 0:
            msg['retrievePath'] = msg['relPath']
            msg['relPath'] = jdata['Name']
            logger.debug(f"baseUrl: {msg['baseUrl']}, relPath: {msg['relPath']}, retrievePath: {msg['retrievePath']}")
        
        if 'ContentLength' in jdata:
            msg['size'] = jdata['ContentLength']

        # TODO: support checksums other than MD5. Copernicus also provides BLAKE3, which sr3 doesn't support.
        if 'Checksum' in jdata:
            for c in jdata['Checksum']:
                if 'Algorithm' in c and c['Algorithm'].upper() == "MD5":
                    msg['identity'] = {'method':'md5', 'value':c['Value']}
                    break
            
        if 'ContentType' in jdata:
            msg['contentType'] = jdata['ContentType']

        if 'ModificationDate' in jdata:
            msg['mtime'] = jdata['ModificationDate'].replace('Z', '').replace(':', '').replace('-', '')

        if 'GeoFootprint' in jdata:
            msg['type'] = 'Feature'
            msg['geometry'] = jdata['GeoFootprint']
        
        return msg
