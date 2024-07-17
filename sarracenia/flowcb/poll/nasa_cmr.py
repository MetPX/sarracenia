#!/usr/bin/python3

"""
Plugin to poll NASA using the CMR "Common Metadata Repository" API
=====================================================================================

What is CMR?

    NASA's Common Metadata Repository (CMR) is a high-performance, high-quality, 
    continuously evolving metadata system that catalogs all data and service metadata 
    records for NASA's Earth Observing System Data and Information System (EOSDIS) 
    system and will be the authoritative management system for all EOSDIS metadata. 
    These metadata records are registered, modified, discovered, and accessed through
    programmatic interfaces leveraging standard protocols and APIs.
    
    -- https://www.earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/cmr

.. IMPORTANT::
    Most URLs posted by this plugin will require an Earthdata account to download the data.
    https://urs.earthdata.nasa.gov/  The corresponding download configuration (e.g. a sarra or
    subscribe config) will need to use the ``authenticate.nasa_earthdata`` plugin.

    See here: https://github.com/MetPX/sarracenia/blob/development/sarracenia/flowcb/authenticate/nasa_earthdata.py

This code is based on https://github.com/podaac/tutorials/blob/master/notebooks/opendap/MUR-OPeNDAP.ipynb


  
Configurable Options:
----------------------

``collectionConceptId`` Collection Concept IDs:
^^^^^^^^^^^^^^^^^^^^^^^^

    Determine where the data comes from. You can find the CCID from a page like
    this one: https://podaac.jpl.nasa.gov/dataset/VIIRS_NPP-STAR-L3U-v2.80

    You can define multiple ``collectionConceptId`` s in your config file.

``dap_urlExtension`` URL extension:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    **Ignored when** ``dataSource`` **is NOT opendap**.  

    From OpenDAP:

    Here is a list of the six URL extensions that are be recognized by all DAP servers:
        - dds - The DAP2 syntactic (structural) metadata response.
        - dds - The DAP2 semantic metadata response.
        - dods - The DAP2 data response.
        - info - The DAP2 HTML dataset information page.
        - html - The DAP2 HTML data request form.
        - ascii - The DAP2 ASCII data response.

    In addition Hyrax and other new servers support the following DAP4 URL extensions:
        - dmr - The DAP4 dataset metadata response.
        - dap - The DAP4 data response.
        - dsr - The DAP4 dataset services response.
        - ddx - The DAP3.2 dataset metadata response.

``dap_fileType`` File type:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    **Ignored when** ``dataSource`` **is NOT opendap**.  The PO.DAAC and other URLs will already 
    include a file extension.

    You can see the file types if you browse to the raw "post_urls" URLs, for example
    https://opendap.earthdata.nasa.gov/providers/POCLOUD/collections/GHRSST%20Level%204%20MUR%20Global%20Foundation%20Sea%20Surface%20Temperature%20Analysis%20(v4.1)/granules/20190101090000-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1.dmr.html

    The supported options are:
        - nc - NetCDF-3
        - nc4 - NetCDF-4
        - csv - CSV 
        - dap4b - DAP4 binary (the plugin will interpret this and set the extension in the URL to nothing)

``timeNowMinus`` Temporal (Time) Range:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The API requires that a date time range is specified when polling. The plugin will always use the current 
    date/time as the "end time" and the "start time" is determined by the ``timeNowMinus`` duration option.

    This is a duration option. It will accept a floating point number, or a floating point number suffixed with
    a unit. Examples:
        - Bare number: ``timeNowMinus 3600`` --> 3600 seconds
        - ``s`` Seconds: ``timeNowMinus 3600`` --> 3600 seconds
        - ``m`` Minutes: ``timeNowMinus 120m`` --> 120 minutes
        - ``h`` Hours: ``timeNowMinus 24h`` --> 24 hours
        - ``d`` Days: ``timeNowMinus 5d`` --> 5 days
        - ``w`` Weeks: ``timeNowMinus 1w`` --> 1 week

    For example, if the poll is running at 2023-04-26 12:35:00Z and ``timeNowMinus`` is ``1d``, 
    the temporal range to poll would be: ::

        start,end
        2023-04-25T12:35:00Z,2023-04-26T12:35:00Z

Configurable data source:
^^^^^^^^^^^^^^^^^^^^^^^^^^

    The API returns multiple "related URLs" for each item. For the PO.DAAC data that this plugin was originally 
    written to acquire, there are both PO.DAAC sources (archive.podaac.earthdata.nasa.gov) and OPeNDAP.

    When ``dataSource`` in the poll config is set to ``podaac``, these pre-set parameters are used to find the URL:
        - Type: "GET DATA" (the API also provides "EXTENDED METADATA" URLs that can be used to get the md5sum)
        - Description: should contain "Download"
        - URL: should contain podaac

        For PO.DAAC, the plugin will also attempt to get and post the file's md5sum in the message.

    When ``dataSource`` is set to ``opendap``, the pre-set parameters are:
        - Description: contains "OPeNDAP"

        For OPeNDAP, you must set the ``dap_urlExtension`` and ``dap_fileType`` options in the poll config.
    
    When ``dataSource`` is ``other``, the parameters must be set in the config file:
        - Type: must be equal to ``relatedUrl_type`` option (required).
        - Description: contains ``relatedUrl_descriptionContains`` option, if defined.
        - URL: contains ``relatedUrl_urlContains`` option, if defined.

        ``relatedUrl_type`` must be set in the poll config. The other ``related_url...`` settings are optional.


*Potential Room For Improvement*: 
----------------------------------

    - To allow multiple dap_urlExtension and dap_fileTypes in one config, maybe post URLs with all items in the
      self.o.dap_urlExtension and self.o.dap_fileType lists, and then use accept and reject to filter...?
    - Also convert relatedUrl_type to list to support multiple types.

How to set up your poll config:
--------------------------------
 
    Use ``callback poll.nasa_cmr``, and read about the config options above.
    
    For examples, see https://github.com/MetPX/sarracenia/tree/development/sarracenia/examples/poll files named ``*nasa_cmr*.conf``. 

Change log:
-----------

    - 2023-10-10: finished porting poll code, now the poll is in a working state.
    - 2023-06-29: ported to sr3, split into poll_NASA_CMR (incomplete) and download plugin.
    - 2023-06-14: added ``other`` dataSource. Renamed to nasa_cmr from nasa_opendap.
    - 2024-06-25: bug fixes, renamed from Poll_NASA_CMR to nasa_cmr.
"""

import sarracenia
import datetime
import logging
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class Nasa_cmr(sarracenia.flowcb.FlowCB):
    def __init__(self, options):
        super().__init__(options, logger)
        
        # Allow setting a logLevel *only* for this plugin in the config file:
        # set poll.NASA_CMR.logLevel debug
        if hasattr(self.o, 'logLevel'):
            logger.setLevel(self.o.logLevel.upper())

        logger.debug("plugin: NASA_CMR __init__")

        self.o.add_option('collectionConceptId', kind='list') # required
        self.o.add_option('dataSource',          kind='str')  # required
        self.o.add_option('timeNowMinus',        kind='duration', default_value=3600.0) # 3600 sec = 1 hour
        self.o.add_option('pageSize',            kind='count', default_value=2000) 

        # Specific to dataSource=opendap
        self.o.add_option('dap_urlExtension', kind='str')
        self.o.add_option('dap_fileType',     kind='str')

        # Specific to dataSource=other
        self.o.add_option('relatedUrl_type',                kind='str') # Required, when dataSource=other
        self.o.add_option('relatedUrl_descriptionContains', kind='list') # Optional
        self.o.add_option('relatedUrl_urlContains',         kind='list') # Optional

        # Allowed settings for dataSource
        self._dataSource_options = ["podaac", "opendap", "other"]

        # pollUrl - if not specified by the user in the config, it should be this
        self._defaultPollUrl = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"
        if not self.o.pollUrl:
            self.o.pollUrl = self._defaultPollUrl
        
        # The default of setting post_baseUrl = pollUrl is invalid for this plugin.
        # The baseUrl is never cmr.earthdata.nasa.gov... and there can be multiple different baseUrls, depending on
        # what URLs are returned by the API. The post_baseUrl setting will be set by the poll for each URL.
        self.o.post_baseUrl = None

        # Check required options
        if not self.o.dataSource or self.o.dataSource not in self._dataSource_options:
            logger.error(f"dataSource unknown: {self.o.dataSource}")
 
        if not self.o.collectionConceptId or len(self.o.collectionConceptId) < 1:
            logger.error(f"collectionConceptId is a required option. " +
                         f"{self.o.collectionConceptId} is invalid.")
        
        # dap_urlExtension and dap_fileType are required when using dataSource opendap
        if self.o.dataSource == "opendap":
            if not self.o.dap_urlExtension or len(self.o.dap_urlExtension) <= 0:
                logger.error(f"dap_urlExtension option must be set when using dataSource opendap.")
            if not self.o.dap_fileType or len(self.o.dap_fileType) <= 0:
                logger.error(f"dap_fileType option must be set when using dataSource opendap.")

        # relatedUrl_type is required when using dataSource other
        if self.o.dataSource == "other":
            if not self.o.relatedUrl_type or len(self.o.relatedUrl_type) <= 0:
                logger.error(f"relatedUrl_type option must be set when using dataSource other.")
        
        # end __init__

    def poll(self) -> list:
        """Poll NASA_CMR
        polling doesn't require authentication, only downloading does
        """
        logger.info("plugin: NASA_CMR starting poll")

        gathered_messages = []

        ### SETUP 

        # Build CMR URL to poll
        # Expecting https://cmr.earthdata.nasa.gov/search/granules.umm_json
        if self.o.pollUrl[-1] == '/':
            url_head = self.o.pollUrl[:-1]
        else:
            url_head = self.o.pollUrl
        if url_head != self._defaultPollUrl:
            logger.warning(f"The destination URL is {url_head}, is this right?")
        
        # No extension used if you want a DAP4 Binary File
        if self.o.dataSource == "opendap" and hasattr(self.o, "dap_fileType") and self.o.dap_fileType == "dap4b":
            dap_fileType = ""
        elif self.o.dataSource == "opendap": 
            dap_fileType = self.o.dap_fileType
        else:
            dap_fileType = ""
        
        # Check page size, 2000 is max
        pg_size = int(self.o.pageSize)
        if pg_size < 1 or pg_size > 2000:
            pageSize = "2000"
        else:
            pageSize = str(int(self.o.pageSize))

        # Figure out the date range
        # Format: start,end   2019-01-01T10:00:00Z,2019-02-01T00:00:00Z
        t_now = datetime.datetime.utcnow()
        t_range_end = t_now.strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            n_seconds = float(self.o.timeNowMinus)
        except:
            logger.error("invalid timeNowMinus option")
            n_seconds = 0

        t_now_minus = t_now - datetime.timedelta(seconds=n_seconds)
        t_range_start = t_now_minus.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        temporal_range = t_range_start + "," + t_range_end
        logger.debug(f"Temporal range: {temporal_range} (timeNowMinus={self.o.timeNowMinus})")

        ### DO THE POLL

        # Example URL from GitHub:
        # https://cmr.earthdata.nasa.gov/search/granules.umm_json?collectionConceptId=C1625128926-GHRC_CLOUD&temporal=2019-01-01T10:00:00Z,2019-12-31T23:59:59Z

        for cci in self.o.collectionConceptId:
            url = url_head + "?collectionConceptId=" + cci
            # Date Time Range
            url += "&temporal=" + temporal_range
            url += "&pageSize=" + pageSize 
            logger.info(f"Polling URL: {url}")
            r = requests.get(url)
            response_body = r.json()

            # The response contains multiple URLs and other info.

            # Now can get the URLs
            for itm in response_body['items']:
                # There are different types of related URLs, including the actual files from PODAAC and OPeNDAP,
                # and metadata (e.g. md5 check sums)
                data_url = None
                md5_url = None
                if 'RelatedUrls' not in itm['umm']:
                    logger.debug(f"No RelatedUrls in {itm['umm']}")
                    continue
                for url in itm['umm']['RelatedUrls']:
                    if self.stop_requested:
                        logger.info("Received a request to stop. Aborting poll and returning an empty list.")
                        return []

                    logger.debug("inspecting potential URL: " + str(url))

                    # Use the kind of URL that was specified in the config
                    # Unknown
                    if self.o.dataSource not in self._dataSource_options:
                        logger.error(f"NASA_CMR plugin: NOT posting because dataSource unknown: {self.o.dataSource}")

                    # OPeNDAP
                    elif (self.o.dataSource == "opendap" and 'OPeNDAP' in url['Description'] ):
                        logger.debug(f"OPENDAP URL {url['URL']}")
                        # Add dap url extension and file type
                        data_url = url['URL'] + "." + self.o.dap_urlExtension + "." + dap_fileType

                    # PO.DAAC DATA
                    elif (self.o.dataSource == "podaac" and 
                            'GET DATA' in url['Type'] and
                            'Download' in url['Description'] and
                            'podaac' in url['URL']):
                        logger.debug(f"PODAAC data URL {url['URL']}")
                        data_url = url['URL']

                    # PO.DAAC md5
                    elif (self.o.dataSource == "podaac" and 
                            'EXTENDED METADATA' in url['Type'] and
                            'Download' in url['Description'] and
                            'md5' in url['Description'] and
                            'podaac' in url['URL']):
                        logger.debug(f"PODAAC md5 URL {url['URL']}")
                        md5_url = url['URL']
                    
                    # Other
                    elif (self.o.dataSource == "other" and 
                            self.o.relatedUrl_type == url['Type'] ):
                        logger.debug(f"Other ({self.o.relatedUrl_type}) URL {url['URL']}")
                        # Skip this URL when other options are defined and don't match
                        logger.debug(f"remove {self.o.relatedUrl_descriptionContains}")
                        if ( (self.o.relatedUrl_descriptionContains is not None and 'Description' in url and
                                all(desc not in url['Description'] for desc in self.o.relatedUrl_descriptionContains))
                              or (self.o.relatedUrl_urlContains is not None and
                                all(url_c not in url['URL'] for url_c in self.o.relatedUrl_urlContains)) ):
                            description = url['Description'] if 'Description' in url else "(Not Available)"
                            logger.debug(f"Skipping {url['URL']} with Description {description}..." + 
                                " doesn't match relatedUrl_descriptionContains relatedUrl_urlContains options")
                        else:
                            data_url = url['URL']
                
                # Now that above loop is done, should have a data URL and maybe an md5_url
                new_identity = None
                if md5_url and self.o.dataSource == "podaac":
                    try:
                        md5_resp = requests.get(md5_url)
                        md5 = md5_resp.text.split(" ")[0]
                        logger.debug(f"MD5 Checksum: {md5}")
                        new_identity = {"method":"md5", "value":md5}
                    except Exception as e:
                        logger.debug("Exception details:", exc_info=True)
                        logger.warning(f"Could not get MD5 Checksum for {data_url}, posting without it. {e}")
                        new_identity = {"method":"cod", "value":"md5"}
                # source is podaac but md5_url isn't available
                elif self.o.dataSource == "podaac":
                    # tell downloads to use md5
                    new_identity = {"method":"cod", "value":"md5"}

                # finally create the message!
                if data_url:
                    # The message is created using the post_baseUrl and relative path
                    url = urlparse(data_url)
                    baseUrl = url.scheme + "://" + url.netloc + "/"
                    self.o.post_baseUrl = baseUrl
                    m = sarracenia.Message.fromFileInfo(url.path, self.o)
                    # When Sarracenia runs updatePaths again later, from sarracenia.Flow, self.o.post_baseUrl will be
                    # different, so set msg['post_baseUrl'] here to override whatever setting it has at that point.
                    m['post_baseUrl'] = baseUrl
                    m['_deleteOnPost'] |= {'post_baseUrl'}
                    if m:
                        if new_identity:
                            logger.debug(f"Changing identity from {m['identity']} to {new_identity} for {data_url}")
                            m['identity'] = new_identity
                        logger.debug(f"message for {data_url} is\t{m}")
                        gathered_messages.append(m)
                    else:
                        logger.error(f"failed to create message for {data_url}")
                else:
                    logger.debug(f"couldn't find a URL to post")
        
        return gathered_messages
