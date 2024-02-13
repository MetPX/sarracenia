"""
Posts updated files of airnowtech. 
Compatible with Python 3.5+.

usage:
	in an sr3 poll configuration file:

    # OLD URL
	pollUrl http://files.airnowtech.org/?prefix=airnow/today/
    # NEW URL
    https://s3-us-west-1.amazonaws.com//files.airnowtech.org/airnow/today

	callback poll/airnow

STATUS: unknown... need some authentication, or perhaps the method has changed.
        does not seem to work out of the box.

        Update (2024/02/08) - Working, but poor error handling.
"""

import datetime
import logging
import paramiko
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sarracenia
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Airnow(FlowCB):

    def poll(self):

        sleep = self.o.sleep

        gathered_messages = []
        for Hours in range(1, 3):
            try:
                last_hour_date_time = datetime.datetime.now() - datetime.timedelta(
                    hours=Hours)
                Filename = 'HourlyData_%s.dat' % last_hour_date_time.strftime(
                    '%Y%m%d%H')
                logger.debug("poll_airnow_http Filename: %s" % Filename)
                URL = self.o.pollUrl + '/' + Filename
                logger.info('INFO %s ' % URL)
                
                #resp = requests.get(self.o.pollUrl + '/' + Filename)

                # Setup an HTTP session. Set it up where we can retry 3 times if ever it fails and have exponential backoff applied.
                # Backoff_factor set to 1 so normal exponential backoff.
                session = requests.Session()
                retry = Retry(connect=3, backoff_factor=1)
                adapter = HTTPAdapter(max_retries=retry)
                session.mount('http://', adapter)
                session.mount('https://', adapter)

                resp = session.get(URL)

                if resp.ok:
                    mtime = datetime.datetime.strptime(resp.headers['last-modified'],\
                         '%a, %d %b %Y %H:%M:%S %Z')
                    last_poll = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=-sleep)
                    logger.info(mtime)
                    logger.info(last_poll)

                    fakeStat = paramiko.SFTPAttributes()
                    fakeStat.st_size = int(resp.headers['content-length'])

                    # convert datetime to numeric timestamp from beginning of POSIX epoch.
                    fakeStat.st_mtime = mtime.timestamp()
                    fakeStat.st_atime = mtime.timestamp()
                    fakeStat.st_mode = 0o644

                    m = sarracenia.Message.fromFileInfo(Filename, self.o, fakeStat)
                    gathered_messages.append(m)

                    logger.info('mtime: %s  last_poll %s' % (mtime, last_poll))
            
            except requests.exceptions as e:
                logger.error(f"Could not fetch airnow data from {URL}. Exception: {e}")
                

        return gathered_messages
