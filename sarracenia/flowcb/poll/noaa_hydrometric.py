"""
Posts updated files of NOAA water level/temperature hydrometric data. Station site IDs provided
in the poll_noaa_stn_file. Compatible with Python 3.5+.

usage:
sample url: https://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=9450460&product=water_temperature&units=metric&time_zone=gmt&application=web_services&format=csv

in an sr_poll configuration file::

	pollUrl http://tidesandcurrents.noaa.gov/api
        retrievePathPattern /datagetter?range=1&station={0:}&product={1:}&units=metric&time_zone=gmt&application=web_services&format=csv

	poll_noaa_stn_file [path/to/stn/file]
	callback noaa_hydrometric

sample station file::

        7|70678|9751639|Charlotte Amalie|US|VI|-4.0
        7|70614|9440083|Vancouver|US|WA|-8.0

The poll:
If poll_noaa_stn_file isn't set, it'll grab an up-to-date version of all station site code data from the 
NOAA website. The station list file is in the following format:
SourceID | SiteID | SiteCode | SiteName | CountryID | StateID | UTCOffset
Each station on its own line.
Posts the file on the exchange if the request returns a valid URL. 

in v2, one needed a matching downloader plugin, but in sr3 we can leverage the retrievePath feature
so that normalk downloader works, so only the poll one needed.

"""

import copy
import datetime
import logging

import os
import sarracenia
from sarracenia.flowcb import FlowCB
import urllib.request
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class Noaa_hydrometric(FlowCB):
    def __init__(self, options):

        super().__init__(options,logger)

        # these options are only for the poll.
        self.o.add_option(option='poll_noaa_stn_file', kind='str')
        self.o.add_option( option='retrievePathPattern', kind='str', \
              default_value='datagetter?range=1&station={0:}&product={1:}&units=metric&time_zone=gmt&application=web_services&format=csv' )

        if self.o.identity_method.startswith('cod,'):
            m, v = self.o.identity_method.split(',')
            self.identity = {'method': m, 'value': v}

    def poll(self) -> list:

        # Make list of site codes to pass to http get request
        sitecodes = []
        if hasattr(self.o, 'poll_noaa_stn_file'):
            stn_file = self.o.poll_noaa_stn_file

            # Parse file to make list of all site codes
            try:
                with open(stn_file) as f:
                    for line in f:
                        items = line.split('|')
                        sitecodes.append(items[2])
                logger.info("poll_noaa used stn_file %s" % stn_file)

            except IOError as e:
                logger.error("poll_noaa couldn't open stn file: %s" % stn_file)

        else:
            # Grab station site codes from https://opendap.co-ops.nos.noaa.gov/stations/stationsXML.jsp
            tree = ET.parse(urllib.request.urlopen\
               ('https://opendap.co-ops.nos.noaa.gov/stations/stationsXML.jsp'))
            root = tree.getroot()
            for child in root:
                sitecodes.append(child.attrib['ID'])

        incoming_message_list = []
        # Every hour, form the link of water level/temp data to post
        for site in sitecodes:

            retrievePath = self.o.retrievePathPattern.format(site, 'water_temperature')
            url = self.o.pollUrl + retrievePath
            logger.info(f'polling {site}, polling: {url}')
            # Water temp request
            resp = urllib.request.urlopen(url).getcode()
            logger.info(f"poll_noaa file posted: {url} %s")
            mtime = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')

            fname = f'noaa_{mtime}_{site}_WT.csv'
            m = sarracenia.Message.fromFileInfo(fname, self.o)
            m['identity'] = self.identity
            m['retrievePath'] = retrievePath
            m['new_file'] = fname

            incoming_message_list.append(m)

            # Water level request
            retrievePath = self.o.retrievePathPattern.format(
                site, 'water_level') + '&datum=STND'
            url = self.o.pollUrl + retrievePath
            resp = urllib.request.urlopen(url).getcode()
            logger.info(f"poll_noaa file posted: {url}")

            fname = f'noaa_{mtime}_{site}_WL.csv'
            m = sarracenia.Message.fromFileInfo(fname, self.o)
            m['identity'] = self.identity
            m['retrievePath'] = retrievePath
            m['new_file'] = fname

            incoming_message_list.append(m)

        return incoming_message_list
