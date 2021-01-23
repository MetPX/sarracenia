#!/usr/bin/python3
"""
  Trigger an alternate method for downloading bigger files.

  This is a means of invoking a more efficienty binary downloader when it makes sense to do so in place
  of the built-in downloader, typically for larger files.   Set the msg_download_threshold to the
  maximum size of the file to download using built in methods.  Default: 10M (ten megabytes)

  if a file larger than 10M is advertised, then the URL scheme is replaced 'http' -> 'download'

  This means the do_download plugin (download_wget) will be invoked for that file.

  example, if you see a file url with an sftp protocol, and larger than 10 megabytes, the trigger the substition:

  msg_download_threshold 10M
  msg_download_protocol  'sftp'

  on_message msg_download

  do_download download_wget

  APPLICATION NOTES:

    - The built-in downloading logic is pretty good in almost all cases. It is rarely adviseable to use
      this functionality from a performance perspective.

    - Ideal use case:  LAN/Short-haul link with very high bandwidth, where lare peak i/o rates are achievable
      given adequate disk and network connections, such as a high speed LAN. Even there, it should only
      be used for larger files.  

    - Where there is a large tree with many small files, it is very likely that the built-in downloader
      is more efficient than forking any other downloader because, in addition to saving the fork/exec/reap
      overhead, the built-in downloader preserves connections to be used for multiple downloads, so 
      connection establishement, log-in etc.. is not needed for every file.  It is actually going
      to be about as efficienty as possible for the small file case, as those overheads dominate
      the transfer time.
 
    - As a file gets bigger, the transfer time will eventually dominate the setup-time, and at that
      point, it can make sense to switch to a forking download.  Need experience with cases to pick
      a good threshold for that.  Made it a setting defaulting to 10M for now.

    - the native downloader does partitioning of files for passage through multiple pumps and is preferable
      for that case to avoid the 'capybara through an anaconda' syndrome.  In cases 'dataless' transfers,
      where the data does not traverse any pump, this is not a consideration.
     
    - For most long-haul use cases, the bounding constraint is the bandwidth on the link so again
      the built-in downloader is likely close to optimal. Partitioning of the file enables portions of it
      to be delivered and for post-processing tasks, such as anti-virus to overlap with the file transfer.
      when using alternate schemes wihout partitioning, one must await until the complet file has arrived.
      

"""

import os, stat, time
import calendar


class DOWNLOAD_REWRITE(object):

    import urllib.parse

    def __init__(self, parent):

        parent.declare_option('msg_download_threshold')
        if not hasattr(parent, "msg_download_threshold"):
            parent.msg_download_threshold = ["10M"]

        parent.declare_option('msg_download_protocol')
        if not hasattr(parent, "msg_download_protocol"):
            parent.msg_download_protocol = ["http"]

    def on_message(self, parent):
        logger = parent.logger
        msg = parent.msg

        if type(parent.msg_download_threshold) is list:
            parent.msg_download_threshold = parent.chunksize_from_str(
                parent.msg_download_threshold[0])

        if msg.headers['sum'][0] == 'L' or msg.headers['sum'][0] == 'R':
            return True

        parts = msg.partstr.split(',')
        if parts[0] == '1':
            sz = int(parts[1])
        else:
            sz = int(parts[1]) * int(parts[2])

        logger.debug("msg_download sz: %d, threshold: %d download: %s to %s, " % ( \
              sz, parent.msg_download_threshold, parent.msg.urlstr, msg.new_file ) )
        if sz >= parent.msg_download_threshold:
            for p in parent.msg_download_protocol:
                parent.msg.urlstr = msg.urlstr.replace(p, "download")

            parent.msg.url = urllib.parse.urlparse(msg.urlstr)
            logger.info(
                "msg_download triggering alternate method for: %s to %s, " %
                (parent.msg.urlstr, msg.new_file))

        return True


download_rewrite = DOWNLOAD_REWRITE(self)
self.on_message = download_rewrite.on_message
