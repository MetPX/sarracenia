"""
Retrieves file keys in the NEXRAD US Weather Radar public dataset.
Can be adjusted slightly for other public datasets on the AWS S3 platform.
Compatible with Python 3.5+.

sarracenia/flowcb/poll/nexrad.py: a sample gather option for sr3 poll.
	        connects to a public aws s3 bucket and posts all the keys
	        corresponding to files uploaded since it last woke up 

usage:
	in an sr_poll configuration file:
	poll_nexrad_day [YYYY-MM-DD]
	callback poll.nexrad
	
	If poll_nexrad_day is set, it'll post all the keys from that day. Specify a day between 1991-06-05 
	to now (if the current date is specified, it'll post all the keys from today that have been posted
	so far). If not set, it'll post any files uploaded in the last minute (sleep must be set to 51 in 
	the config) and continuously check every minute if a file has been uploaded in the last minute. It 
	takes about ~5 minutes from the timestamp on the file to when it actually gets updated in the bucket,
	and ~9s for the API to make all the requests to check for keys, so the counter starts at now - 7 
	minutes and sleep must be ~51s to work properly.

status: working.
"""

import boto3
from botocore import UNSIGNED
from botocore.client import Config
import datetime
import logging
import paramiko
import sarracenia
from sarracenia.flowcb import FlowCB
import urllib.request

logger = logging.getLogger(__name__)


class Nexrad(FlowCB):
    def __init__(self, options):

        self.o = options
        self.o.add_option('poll_nexrad_day', 'str', "")
        self.minutetracker = datetime.datetime.utcnow() + datetime.timedelta(
            minutes=-7)

    def poll(self):

        # If a valid day wasn't specified, it just won't return any keys or throw an error here ¯\_(ツ)_/¯
        day = self.o.poll_nexrad_day
        if day:
            daypts = day.split('-')
            YYYY = daypts[0].zfill(2)
            MM = daypts[1].zfill(2)
            DD = daypts[2].zfill(2)

        # Gets the list of active weather station ICAOs from
        # https://www.aviationweather.gov/docs/metar/stations.txt
        # According to the website's disclaimer:
        #		" This server is available 24 hours a day, seven days a week.
        #		  Timely delivery of data and products from this server through
        # the Internet is not guaranteed."
        # Considered the primary resource for up-to-date ICAO information.
        # Currently only scrapes US weather station ICAOs, but can be adjusted to pull
        # from Canada/worldwide sites.
        ICAOs = set()
        with urllib.request.urlopen(
                'https://www.aviationweather.gov/docs/metar/stations.txt'
        ) as f:
            lines = f.readlines()
            for line in lines:
                line = line.decode("utf-8", "ignore")
                if len(line) > 80:
                    if line.endswith("US\n") and line[65] == 'X':
                        if line[20:24] != "    ": ICAOs.add(line[20:24])

        # Not all sites from the Nexrad data set are covered from the official source
        #(some foreign US bases are included in the NEXRAD dataset), so add the missing ones from this list:
        # https://www.roc.noaa.gov/WSR88D/Program/NetworkSites.aspx
        ICAOs.update(['RKJK', 'PAEC', 'RODN', 'RKSG', 'KGRK'])

        # And for some reason FOP1/NOP4 show up in the dataset, doesn't correlate to active ICAOs though
        ICAOs.update(['FOP1', 'NOP4'])
        # As of 2018/07 this set has 161 elements

        keys = []
        keysizes = []
        s3 = boto3.client('s3',
                          region_name='us-east-1',
                          config=Config(signature_version=UNSIGNED,
                                        retries={'max_attempts': 3}))
        if day:
            # Takes all files uploaded on the specified day. Takes ~161 API calls = ~9s. A full day's worth
            # of keys is around ~37000. Meant to be run once to grab a day's worth of keys. Works as long
            # as a day's worth on a single ICAO doesn't exceed 1000 (the API limit, and as of 2018/07 each
            # ICAO uploads about ~300).
            for station in ICAOs:
                try:
                    for obj in s3.list_objects(Bucket='noaa-nexrad-level2',
                                               Prefix=YYYY + '/' + MM + '/' +
                                               DD + '/' + station +
                                               '/')['Contents']:
                        keys.append(obj['Key'])
                        keysizes.append(obj['Size'])
                except KeyError as e:
                    continue

        else:
            # Forces sleep value to be a minute. Takes ~161 API calls, runs in ~9s.
            self.minutetracker = self.minutetracker + datetime.timedelta(
                minutes=1)
            YYYY = str(self.minutetracker.year)
            MM = str(self.minutetracker.month).zfill(2)
            DD = str(self.minutetracker.day).zfill(2)
            HH = str(self.minutetracker.hour).zfill(2)
            mm = str(self.minutetracker.minute).zfill(2)
            logger.info("Date: %s" % self.minutetracker)

            for station in ICAOs:
                try:
                    for obj in s3.list_objects(
                            Bucket='noaa-nexrad-level2',
                            Prefix=YYYY + '/' + MM + '/' + DD + '/' + station +
                            '/' + station + YYYY + MM + DD + '_' + HH +
                            mm)['Contents']:
                        keys.append(obj['Key'])
                        keysizes.append(obj['Size'])
                except KeyError as e:
                    continue

        # To download a file, you'd append the key to the end of the bucket link, e.g:
        # https://s3.amazonaws.com/noaa-nexrad-level2/2018/06/09/KARX/KARX20180609_000228_V06
        i = 0
        gathered_messages = []
        while i < len(keys):
            logger.info("poll_nexrad: key received {}".format(keys[i]))

            fakeStat = paramiko.SFTPAttributes()
            fakeStat.st_size = keysizes[i]

            m = sarracenia.Message.fromFileInfo(keys[i], self.o, fakeStat)
            gathered_messages.append(m)
            i += 1
        logger.info( f"Done, {len(gathered_messages)} messages to post" )
        return gathered_messages
