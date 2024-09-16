import logging

import sarracenia
from sarracenia.filemetadata import FmdStat
from sarracenia.flowcb import FlowCB
from sarracenia.flowcb.scheduled import Scheduled

import requests
import datetime


logger = logging.getLogger(__name__)

class Http_with_metadata(Scheduled):

    """
    Same as a normal scheduled flow, except this will do an HTTP HEAD request to try to get the file size,
    modification time, etc. and add that to the message.
     
    Options:
        post_whenNoMetadata (default False): when True, post URLs *without metadata* (when HEAD request returns an error) 

    Example config: 
    https://github.com/MetPX/sarracenia/tree/development/sarracenia/examples/flow/scheduled_aviation_wind_fax_charts.conf

    NOTE: Set the ``nodupe_ttl`` setting to something non-zero to filter out files that haven't changed
    since the last time they were posted.

    """

    def __init__(self, options, logger=logger):
        super().__init__(options,logger)
        self.o.add_option('post_whenNoMetadata', 'flag', False)

    def gather(self,messageCountMax):

        if not self.ready_to_gather():
            return (False, [])

        logger.info('time to run')

        # always post the same file at different time
        gathered_messages = []

        for relPath in self.o.path:
            st = FmdStat()

            # Do variable expansion on the path
            relPath = self.o.variableExpansion(relPath)

            if self.o.post_baseUrl[-1] == '/':
                url = self.o.post_baseUrl + relPath
            else:
                url = self.o.post_baseUrl + '/' + relPath
            
            try:
                resp = requests.head(url)
                resp.raise_for_status()

                # parse the HTTP header response into the stat object used by sr3
                # {... 'Content-Length': '549872', ... , 'Last-Modified': 'Mon, 03 Jun 2024 15:42:02 GMT', ... }
                # logger.debug(f"{resp} {resp.headers}")
                if resp.status_code == 200:
                    have_metadata = False
                    if "Last-Modified" in resp.headers:
                        # Mon, 03 Jun 2024 15:42:02 GMT
                        lm = datetime.datetime.strptime(resp.headers['Last-Modified'], '%a, %d %b %Y %H:%M:%S GMT')
                        lm = lm.timestamp()
                        # logger.debug(f"parsed date: {lm}")
                        st.st_atime = lm
                        st.st_mtime = lm
                        have_metadata = True
                    if "Content-Length" in resp.headers:
                        size = int(resp.headers['Content-Length'])
                        # logger.debug(f"file size: {size}")
                        st.st_size = size
                        have_metadata = True
                    if not have_metadata and not self.o.post_whenNoMetadata:
                        logger.warning(f"HEAD request returned {resp.status_code} but metadata was " +
                                       f"not available for {url}, not posting")
                        continue
                    logger.debug(f"modified stat: {st} for {url}")
            except Exception as e:
                if not self.o.post_whenNoMetadata:
                    logger.debug(f"Failed to get metadata for {url} ({e}), not posting")
                    continue
                else:
                    logger.info(f"Failed to get metadata for {url} ({e}), posting anyways")
            
            m = sarracenia.Message.fromFileInfo(relPath, self.o, st)
            gathered_messages.append(m)

        return (True, gathered_messages)
