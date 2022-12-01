"""
Posts updated files of USGS hydrometric data. Station site IDs provided
in the poll_usgs_stn_file. Compatible with Python 3.5+.

Status: UNTESTED... don't have a working basis (even on v2) to compare against.
        was updated for v3. but don't have credentials to confirm it now works.

usage:
	in an sr3 poll configuration file:
	pollUrl http://waterservices.usgs.gov/nwis/iv/?format=waterml,2.0&indent=on&site={0:}&period=PT3H&parameterCd=00060,00065,00011

	batch [station_chunk]
	poll_usgs_station  station-declaration
	callback gather/usgs

	If multiple usgs stations need to be fetched in one call, station_chunk should specify how big the station
	blocks should be. If not set it'll individually download station data.
	If poll_usgs_stn_file isn't set, it'll default to pulling the siteIDs from: 
	https://water.usgs.gov/osw/hcdn-2009/HCDN-2009_Station_Info.xlsx
	directory. each station declaration is in the following format:
	SourceID | SiteID | SiteCode | SiteName | CountryID | StateID | UTCOffset
	Each station on its own line.

        to reformat into a parseable configuration option, declare poll_usgs_station as a list option,
        so each line looks like::

             poll_usgs_station 7|70026|9014087|Dry Dock, MI|US|MI|-5.0

        then this file can be an *include* directive, and include supports both local and remote url's
        so the db can be admined in some other http accessible git repository.

	More info on the http rest parameters at: https://waterservices.usgs.gov/rest/IV-Service.html
	For writing fault-resistant code that polls from usgs: https://waterservices.usgs.gov/docs/portable_code.html
	Sign up for updates involving if/how the format changes: http://waterdata.usgs.gov/nwis/subscribe?form=email
	Parameter codes to tailor the data you want: 
	https://help.waterdata.usgs.gov/code/parameter_cd_query?fmt=rdb&inline=true&group_cd=%
	Currently the parametercd is set to:
	00060	Physical	Discharge, cubic feet per second
	00065	Physical	Gage height, feet
	00011	Physical	Temperature, water, degrees Fahrenheit	
"""

import datetime
import logging
import pandas as pd
import paramiko
import sarracenia
from sarracenia.flowcb import FlowCB
import urllib.request

logger = logging.getLogger(__name__)


class Usgs(FlowCB):
    def __init__(self, options):

        self.o = options
        self.o.add_option('poll_usgs_station', 'list')

        # Parse sitecodes from file if provided, or the usgs website (turns excel spreadsheet into pandas
        # dataframe, parses from there)
        self.sitecodes = []
        if hasattr(self.o, 'poll_usgs_station'):
            for s in self.o.poll_usgs_station:
                items = s.split('|')
                self.sitecodes.append(items[2])
            logger.info('%d stations declared' % len(self.sitecodes))
        else:
            df = pd.read_excel(
                'https://water.usgs.gov/osw/hcdn-2009/HCDN-2009_Station_Info.xlsx'
            )
            for row in df.iterrows():
                self.sitecodes.append(str(row[1]['STATION ID']).zfill(8))

        if hasattr(self.o, 'batch'):
            mult = True
            chunk_size = int(self.o.batch)

    def poll(self):

        run_time = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')

        gathered_messages = []
        if self.o.batch > 1:
            file_cnt = 0
            for sites in [
                    self.sitecodes[i:i + self.o.batch]
                    for i in range(0, len(self.sitecodes), self.o.batch)
            ]:
                stns = ','.join([s for s in sites])
                file_cnt += 1
                logger.debug('getting: %s' % self.o.pollUrl.format(stns))

                status_code = urllib.request.urlopen(
                    self.o.pollUrl.format(stns)).getcode()
                if status_code == 200:
                    logger.info("poll_usgs file updated %s" %
                                self.o.pollUrl.format(stns))

                    self.o.msg.new_baseurl = self.o.pollUrl.format(stns)

                    m = sarracenia.Message.fromFileInfo(
                        'usgs_{0}_sites{1}.xml'.format(run_time, file_cnt),
                        self.o)
                    gathered_messages.append(m)
                elif status_code == 403:
                    logger.error(
                        '''poll_usgs: USGS has determined your usage is excessive and \ 
							blocked your IP. Use the contact form on their site to be \
							unblocked.''')
                else:
                    logger.debug("poll_usgs file not found: %s" %
                                 self.o.pollUrl.format(stns))
        else:  # Get stations one at a time
            for site in self.sitecodes:
                logger.debug('getting: %s' % self.o.pollUrl.format(site))
                status_code = urllib.request.urlopen(
                    self.o.pollUrl.format(site)).getcode()
                if status_code == 200:
                    logger.info("poll_usgs file updated %s" %
                                self.o.pollUrl.format(site))
                    self.o.msg.new_baseurl = self.o.pollUrl.format(site)
                    m = sarracenia.Message.fromFileInfo(
                        'usgs_{0}_{1}.xml'.format(run_time, site), self.o)
                    gathered_messages.append(m)
                elif status_code == 403:
                    logger.error(
                        '''poll_usgs: USGS has determined your usage is excessive and \
							blocked your IP. Use the contact form on their site to be \
							unblocked.''')
                else:
                    logger.debug("poll_usgs file not found: %s" %
                                 self.o.pollUrl.format(site))
        return gathered_messages
