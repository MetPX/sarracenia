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
    modification time, etc. and add that to the message. BUT, if the file doesn't exist at the source (404)
    it won't post it.

    If it can't get the headers, it will still post the file without the metadata.

    Example config: 
    https://github.com/MetPX/sarracenia/tree/development/sarracenia/examples/flow/scheduled_aviation_wind_fax_charts.conf

    NOTE: Set the ``nodupe_ttl`` setting to something non-zero to filter out files that haven't changed
    since the last time they were posted.

    """

    def gather(self,messageCountMax):

        # for next expected post
        self.wait_until_next()

        if self.stop_requested or self.housekeeping_needed:
            return (False, [])

        logger.info('time to run')

        # always post the same file at different time
        gathered_messages = []

        for relPath in self.o.path:
            st = FmdStat()

            if self.o.post_baseUrl[-1] == '/':
                url = self.o.post_baseUrl + relPath
            else:
                url = self.o.post_baseUrl + '/' + relPath
            
            try:
                resp = requests.head(url)
                if resp.status_code == 404:
                    logger.warning(f"Got 404 error - file at {url} does not exist, not posting!")
                    continue
                resp.raise_for_status()

                # parse the HTTP header response into the stat object used by sr3
                # {... 'Content-Length': '549872', ... , 'Last-Modified': 'Mon, 03 Jun 2024 15:42:02 GMT', ... }
                logger.debug(f"{resp} {resp.headers}")
                if resp.status_code == 200:
                    if "Last-Modified" in resp.headers:
                        # Mon, 03 Jun 2024 15:42:02 GMT
                        lm = datetime.datetime.strptime(resp.headers['Last-Modified'], '%a, %d %b %Y %H:%M:%S GMT')
                        lm = lm.timestamp()
                        # logger.debug(f"parsed date: {lm}")
                        st.st_atime = lm
                        st.st_mtime = lm
                    if "Content-Length" in resp.headers:
                        size = int(resp.headers['Content-Length'])
                        # logger.debug(f"file size: {size}")
                        st.st_size = size
                    logger.debug(f"modified stat: {st} for {url}")
            except Exception as e:
                logger.warning(f"Failed to get metadata for {url} ({e})")
            
            m = sarracenia.Message.fromFileInfo(relPath, self.o, st)
            gathered_messages.append(m)

        return (True, gathered_messages)
