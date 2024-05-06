#!/usr/bin/python3

"""
Plugin to poll a EUMETSAT's API
=====================================================================================

Developed for bladoc#1563

Uses the EUMETSAT Data Store Browse REST API
 https://eumetsatspace.atlassian.net/wiki/spaces/DSDS/pages/1660977169/The+Data+Store+Browse+REST+API
 https://eumetsatspace.atlassian.net/wiki/spaces/DSDS/pages/315818088/Using+the+APIs

EUMETSAT Service Status: https://uns.eumetsat.int/

URLs posted by this plugin may need authentication (e.g. with a bearer token).

NOTE: this poll doesn't post file sizes. Setting ``acceptSizeWrong True`` in the config that consumes messages
posted by this plugin will suppress warnings saying there was no length given.

  
Configurable Options:
----------------------

``collectionId`` (required):
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Which collection ID(s) you want to poll.

``acceptMediaType`` (required):
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The type(s) of media you want to post URLs for. E.g. ``application/x-netcdf``, ``image/jpeg``, etc.

``timeNowMinus`` Time Range (required):
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Provides a time range to poll. The plugin will always use the current 
    date/time as the "end time" and the "start time" is determined by the ``timeNowMinus`` duration option.

    The default value is 3 hours.

    This is a duration option. It will accept a floating point number, or a floating point number suffixed with
    a unit. Examples:
        - Bare number: ``timeNowMinus 3600`` --> 3600 seconds
        - ``s`` Seconds: ``timeNowMinus 3600`` --> 3600 seconds
        - ``m`` Minutes: ``timeNowMinus 120m`` --> 120 minutes
        - ``h`` Hours: ``timeNowMinus 24h`` --> 24 hours
        - ``d`` Days: ``timeNowMinus 5d`` --> 5 days
        - ``w`` Weeks: ``timeNowMinus 1w`` --> 1 week
    
    The minimum time interval is 1 hour.


*Potential Room For Improvement*: 
----------------------------------

    - ??

How to set up your poll config:
--------------------------------
 
    Use ``callback poll.eumetsat``, and read about the config options above.
    
    For examples, see https://github.com/MetPX/sarracenia/tree/main/sarracenia/examples/poll files named ``*eumetsat*.conf``. 

Change log:
-----------

    - 2022-09: first version, for v2
    - 2023-02: first port to sr3 (Peter Silva)
    - 2023-12: updated sr3 plugin, split into separate poll and auth plugins, made a lot more universal (old code
               would only post NetCDF files, this allows any type, configurable time range, multiple collection IDs
               in one config, includes mtime, md5sum, GeoJSON, contentType in messages when available)
    - 2024-04: un-URL-encode the posted relPath
"""
import requests
import datetime
import logging
import sarracenia

logger = logging.getLogger(__name__)

class Eumetsat(sarracenia.flowcb.FlowCB):
    def __init__(self, options):
        super().__init__(options,logger)

        # Allow setting a logLevel *only* for this plugin in the config file:
        # set poll.eumetsat.logLevel debug
        if hasattr(self.o, 'logLevel'):
            logger.setLevel(self.o.logLevel.upper())

        self.o.add_option('collectionId', kind='list', default_value=[])
        self.o.add_option('acceptMediaType', kind='list', default_value=[])
        self.o.add_option('timeNowMinus', kind='duration', default_value=3*3600.0) # 3600 sec = 1 hour

        # Default URL options
        if not self.o.pollUrl:
            self.o.pollUrl = 'https://api.eumetsat.int/data/browse/collections/'
        
        if not self.o.post_baseUrl or self.o.post_baseUrl.endswith('browse/collections'):
            self.o.post_baseUrl = 'https://api.eumetsat.int/data/download/1.0.0/collections/'
        
        if self.o.post_baseUrl[-1] != '/':
            self.o.post_baseUrl += '/'

        # add placeholder for the collection ID
        self._cid_placeholder = '---COLLECTION_ID---'
        if self.o.pollUrl[-1] != '/':
            self.o.pollUrl = self.o.pollUrl + '/' + self._cid_placeholder + '/'
        else:
            self.o.pollUrl = self.o.pollUrl + self._cid_placeholder + '/'

        # Collection IDs need to be URL encoded
        self._encoded_collectionIds = [ cid if '%' in cid else requests.utils.quote(cid) 
                                        for cid in self.o.collectionId ]

    def poll(self) -> list:
        """Poll the EUMETSAT browse API documented here:
        https://eumetsatspace.atlassian.net/wiki/spaces/DSDS/pages/315785396/Swagger+UI+Browse+REST+API
        """
        gathered_messages=[]

        # API requires the date and time to retrieve results for. Check the current hour and previous n_hours.
        n_hours = int(self.o.timeNowMinus//3600) + 1
        t_now = datetime.datetime.utcnow()
        # Build strings YYYY/mm/dd/times/hh. now - 1 hour = t_str[1], now - 2 hours = t_str[2], ...
        t_str = []
        for i in range(0, n_hours):
            t_now_minus_i_hours = t_now - datetime.timedelta(hours=i)
            t_str.append(t_now_minus_i_hours.strftime("%Y/%m/%d/times/%H"))

        url_head = self.o.pollUrl
        if 'dates' not in url_head:
            url_head = url_head + "dates/"

        # Now url_head should end with dates/
        # e.g. https://api.eumetsat.int/data/browse/collections/EO:EUM:DAT:0412/dates/
        
        # Other formats can be requested, but json is easiest to work with for this
        url_tail = "/products?format=json"
        
        # valid URL to poll = url_head.replace('---COLLECTION_ID---', cid) + t_str[i] + url_tail

        # Request results for the last n_hours, for each collection ID
        # Each item will have a "Product details" URL which we have to get
        details_hrefs = []
        for cid in self._encoded_collectionIds:
            for i in range(0, n_hours):
                req_url = url_head.replace(self._cid_placeholder, cid) + t_str[i] + url_tail
                logger.info("polling URL {}".format(req_url))
                resp = requests.get(req_url)
                if not resp or "products" not in resp.json().keys():
                    logger.warning(f"Something went wrong: no products found at {req_url}")
                else:
                    for item in resp.json()['products']:
                        if 'links' in item:
                            for link in item['links']:
                                # Looking for the "Product details" link
                                if 'title' in link and link['title'] == 'Product details' and 'href' in link:
                                    details_hrefs.append(link['href'])
                                    break

        # The actual file download links are on the "Product details" page. Need to get the page, then find the 
        # download link within. This part is slow. Poll could post the details_hrefs, and the download could get
        # the page, find the file link and download it, but then the download would be slower.
        logger.info(f"getting file properties URLs for {len(details_hrefs)} files")
        for details_link in details_hrefs:
            if self.stop_requested:
                logger.info("Stop requested. Stopping.")
                break
            details_page = requests.get(details_link)
            msgs = self.msgs_from_details_page(details_page.json())
            logger.debug(f"created {len(msgs)} message(s) from 1 details_link {details_link}")
            gathered_messages += msgs
            
        return gathered_messages
    
    def msg_from_link_info_json(self, link_info) -> sarracenia.Message:
        m = None
        try:
            parts = link_info['href'].split(self.o.post_baseUrl)
            logger.debug(f"making a message for {parts[1]}" )
            m = sarracenia.Message.fromFileInfo(parts[1], self.o)
            m['contentType'] = link_info['mediaType']
            # The download links in .../entry?name=FILENAME which would download files named entry?name=FILENAME
            # Override this by changing relPath (used to name the file) and setting retrievePath (used to download)
            m['retrievePath'] = m['relPath']
            temp_relPath = requests.utils.unquote(m['relPath'].replace('entry?name=', '')).split('/')
            relPath = []
            # remove duplicates from the path
            for i in range(len(temp_relPath)):
                if i == 0 or temp_relPath[i] != temp_relPath[i-1]:
                    relPath.append(temp_relPath[i])
            m['relPath'] = '/'.join(relPath)
        except Exception as e:
            logger.error(f"Failed to create message from {link_info}")
            logger.debug("Exception details", exc_info=True)
        return m

    def msgs_from_details_page(self, product_details) -> list:
        """ Process a product details page into messages.
            Example: https://api.eumetsat.int/data/browse/1.0.0/collections/EO%3AEUM%3ADAT%3A0412/products/S3A_SL_2_WST____20231229T001228_20231229T001528_20231229T020124_0179_107_173_2700_MAR_O_NR_003.SEN3?format=json
        """
        if 'properties' not in product_details:
            logger.error(f"Problem with details page {product_details}")
            return []
        
        msgs = []
        gtype = None # GeoJSON type (Feature)
        geom = None # GeoJSON geometry
        mtime = None # product_details['properties']['updated'] time
        # It might be possible to get the size and md5sum for sip-entries files from one of the xml files in
        # the sip-entries list, but it requires authentication and this poll plugin doesn't authenticate
        md5 = None # product_details['properties']['extraInformation']['md5'], this is only for the zip
        size = None # [kB] product_details['properties']['productInformation']['size'], this is only for the zip
        if 'type' in product_details and 'geometry' in product_details:
            gtype = product_details['type']
            geom = product_details['geometry']
        
        if 'updated' in product_details['properties']:
            # example: "updated": "2023-12-29T02:06:33.451Z",
            mtime = product_details['properties']['updated'].replace('Z', '').replace(':', '').replace('-', '')

        if ('extraInformation' in product_details['properties'] 
            and 'md5' in product_details['properties']['extraInformation']):
            md5 = product_details['properties']['extraInformation']['md5']

        if ('productInformation' in product_details['properties'] 
            and 'size' in product_details['properties']['productInformation']):
            size = product_details['properties']['productInformation']['size']

        # Generate messages for the available links that match the accepted mediaTypes
        for link_group in product_details['properties']['links']:
                if type(product_details['properties']['links'][link_group]) != list:
                    continue
                for link_info in product_details['properties']['links'][link_group]:
                    if link_info['mediaType'] in self.o.acceptMediaType:
                        result = self.msg_from_link_info_json(link_info)
                        if result:
                            msgs.append(result)
                    else:
                        logger.debug(f"Ignoring link_info {link_info} with mediaType not in {self.o.acceptMediaType}")
                        if len(self.o.acceptMediaType) <= 0:
                            logger.warning(f"acceptMediaType option not set. Ignoring {link_info}.")
        
        # Add any available extra info to the messages
        for m in msgs:
            if gtype and geom:
                m['type'] = gtype
                m['geometry'] = geom
            if mtime:
                m['mtime'] = mtime
            if md5 and m['contentType'] == 'application/zip':
                m['identity'] = {'method':'md5', 'value':md5}
            # The size is in kB, so it's not useful.
            # if size and m['contentType'] == 'application/zip':
            #     m['size'] = size

        return msgs         
