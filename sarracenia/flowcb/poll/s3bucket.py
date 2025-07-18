
"""

Retrieves file keys from an Amazon AWS S3 bucket.

callback poll.s3bucket

pollUrl https://s3-us-west-1.amazonaws.com//files.airnowtech.org/airnow/today/HourlyData_${YYYYMMDD-70m}

( https://metpx.github.io/sarracenia/Reference/sr3_options.7.html#variables ) for details on variable substitutions )

to poll AWS for a particular site's level 2 nexrad data:

#check for the RKJK radar site
declare env Site RKJK

#for readar products from the current date as of seven minutes ago.
varTimeOffset -7m
pollUrl https://s3-us-east-1.amazonaws.com//nexrad-level-2/${YYYY}/${MM}/${DD}/${Site}

#check every five minutes.
sleep 300


"""
import boto3
from botocore import UNSIGNED
from botocore.client import Config
import datetime
import logging
import paramiko
import sarracenia
from sarracenia.flowcb import FlowCB
import sys
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)


class S3bucket(FlowCB):
    def __init__(self, options):

        super().__init__(options,logger)

        self.minutetracker = datetime.datetime.utcnow() + datetime.timedelta(minutes=-70)
        
        logger.info( f" url: {self.o.pollUrl} " )
        ppu = urllib.parse.urlparse(self.o.pollUrl)

        logger.info( f" host: {ppu.netloc} path:{ppu.path} " )
        self.service = ppu.netloc.split('-')[0]
        self.region = ppu.netloc.split('.')[0][3:]
        self.bucket = ppu.path.split('/')[2]
        self.prefix = '/'.join(ppu.path.split('/')[3:])
        logger.info( f" service: {self.service} region: {self.region} bucket:{self.bucket}  prefix={self.prefix}" )

    def poll(self):

        last_hour_date_time = datetime.datetime.now() - datetime.timedelta(hours=1)
        keys = []
        keysizes = []

        current_prefix = self.o.variableExpansion( self.prefix )
        logger.info("current_prefix: {current_prefix}" )

        # Gets the list of active weather station ICAOs from
        s3 = boto3.client( self.service,
            region_name=self.region, config=Config(signature_version=UNSIGNED, retries={ 'max_attempts': 3 }))
        try:
            for obj in s3.list_objects(Bucket=self.bucket, Prefix=current_prefix)['Contents']:
                keys.append(obj['Key'])
                keysizes.append(obj['Size'])
        except KeyError as e:
            print(e)

        i = 0
        gathered_messages = []
        while i < len(keys):
            logger.info("found {}".format(keys[i]))

            fakestat = paramiko.SFTPAttributes()
            fakestat.st_size = keysizes[i]

            m = sarracenia.Message.fromFileInfo(keys[i].replace(self.prefix,'',1), self.o, fakestat)
            gathered_messages.append(m)

            i += 1
        return gathered_messages
