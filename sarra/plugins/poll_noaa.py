#!/usr/bin/python3
"""
Posts updated files of NOAA water level/temperature hydrometric data. Station site IDs provided
in the poll_noaa_stn_file. Compatible with Python 3.5+.

usage:
	in an sr_poll configuration file:
	destination http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station={0:}&product={1:}&units=metric&time_zone=gmt&application=web_services&format=csv

	poll_noaa_stn_file [path/to/stn/file]
	do_poll poll_noaa.py

	If poll_noaa_stn_file isn't set, it'll grab an up-to-date version of all station site code data from the 
	NOAA website. The station list file is in the following format:
	SourceID | SiteID | SiteCode | SiteName | CountryID | StateID | UTCOffset
	Each station on its own line.
	Posts the file on the exchange if the request returns a valid URL. 
"""

import logging, urllib.request
import xml.etree.ElementTree as ET


class NOAAPoller(object):
    def __init__(self, parent):
        parent.declare_option('poll_noaa_stn_file')

    def do_poll(self, parent):
        import logging, urllib.request
        import xml.etree.ElementTree as ET

        logger = parent.logger

        # Make list of site codes to pass to http get request
        sitecodes = []
        if hasattr(parent, 'poll_noaa_stn_file'):
            stn_file = parent.poll_noaa_stn_file[0]

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

        # Every hour, form the link of water level/temp data to post
        for site in sitecodes:
            # Water temp request
            resp = urllib.request.urlopen(
                parent.destination.format(site,
                                          'water_temperature')).getcode()
            logger.info("poll_noaa file posted: %s" % \
              parent.destination.format(site,'water_temperature'))
            parent.msg.new_baseurl = parent.destination.format(
                site, 'water_temperature')
            parent.msg.new_file = 'CO-OPS__{0}__wt.csv'.format(site)
            parent.msg.sumflg = 'z'
            parent.msg.sumstr = 'z,d'
            parent.msg.set_parts()
            parent.to_clusters = 'ALL'
            parent.post(parent.exchange,parent.msg.new_baseurl,parent.msg.new_file,\
              parent.to_clusters,sumstr=parent.msg.sumstr)

            # Water level request
            resp = urllib.request.urlopen(parent.destination.format(site,'water_level')\
                +'&datum=STND').getcode()
            logger.info("poll_noaa file posted: %s" % \
              parent.destination.format(site,'water_level')+'&datum=STND')
            parent.msg.new_baseurl = parent.destination.format(
                site, 'water_level') + '&datum=STND'
            parent.msg.new_file = 'CO-OPS__{0}__wl.csv'.format(site)
            parent.msg.sumflg = 'z'
            parent.msg.sumstr = 'z,d'
            parent.msg.set_parts()
            parent.to_clusters = 'ALL'
            parent.post(parent.exchange,parent.msg.new_baseurl,parent.msg.new_file,\
              parent.to_clusters,sumstr=parent.msg.sumstr)


noaapoller = NOAAPoller(self)
self.do_poll = noaapoller.do_poll
