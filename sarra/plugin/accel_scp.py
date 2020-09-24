#!/usr/bin/python3
"""
This plugin launches the UNIX 'scp' command with appropriate arguments to perform a file transfer.
Sample usage:

  plugin accel_scp

One should invoke the more efficient binary downloader only when it makes sense to do so in place
of the built-in python interpreted downloader, typically for larger files. By default, the threshold
is 10M (ten megabyte.) The accel_scp_threshold option can be used to change it. 

Options
-------

If a file larger than the threshold is advertised, on_message routine replaces the URL 
scheme 'sftp' with 'download'.  That change causes the do_download plugin to be invoked 
for that file.  'sftp' is the default, but the initial url is 'sftp', then the 
accel_scp_protocol option should be set, to have that protocol substituted instead.

  accel_scp_threshold 10M
  accel_scp_protocol  'sftp'

Means that the do_download routine will be called for sftp url's representing files larger than 
ten megabytes.  While the scp command is used by default, it can be overridden with the 
accel_scp_command option.

  accel_scp_command /usr/bin/scp -p 

Instead of invoking scp, it will invoke the scp -p command. To the command will be 
See end of file for performance considerations.

"""

import logging
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import sarra

from sarra.plugin import Plugin
from sarra.config import declare_plugin_option
from sarra.transfer.sftp import Sftp

logger = logging.getLogger(__name__)


class ACCEL_SCP(Plugin, Sftp, schemes=['scp', 'sftp']):
    def __init__(self, options, **kwargs):
        super().__init__(options)
        super(Plugin, self).__init__(options, **kwargs)
        self.scheme = kwargs.get('scheme') if 'scheme' in kwargs else 'sftp'

        declare_plugin_option('accel_scp_command', 'str')
        declare_plugin_option('accel_scp_threshold', 'size')
        declare_plugin_option('accel_scp_protocol', 'str')

    def on_start(self):
        logger.info("on_start accel_scp")
        if not hasattr(self.o, 'accel_scp_command'):
            self.o.accel_scp_command = '/usr/bin/scp'
        if not hasattr(self.o, "accel_scp_threshold"):
            self.o.accel_scp_threshold = '10M'
        if not hasattr(self.o, "accel_scp_protocol"):
            self.o.accel_scp_protocol = self.scheme
        if isinstance(self.o.accel_scp_threshold, str):
            self.o.accel_scp_threshold = sarra.chunksize_from_str(
                self.o.accel_scp_threshold)
        return True

    def on_messages(self, worklist):
        logger.info(self.o)
        for m in worklist.incoming:
            if m['integrity']['method'] in ['link', 'remove']:
                continue
            sz = self.get_size(m)
            logger.debug("scp sz:%d, threshold: %d download: %s to %s, "
                         % (sz, self.o.accel_scp_threshold, m['baseUrl'], m['new_file']))

    def do_get(self, msg, remote_file, local_file, remote_offset, local_offset,
               length):
        """
        """
        logger.debug(f'msg={msg}, local_file={local_file}, remote_file={remote_file}, '
                     f'local_offset={local_file}, remove_offset={remote_offset}, length={length}')
        if self.get_size(msg) < self.o.accel_scp_threshold:
            return super().get(remote_file, local_file, remote_offset, local_offset, length)
        else:
            netloc = urlparse(self.o.destination).netloc
            remote = re.escape(f"{netloc}:{Path(msg['relPath'])}")  # Remote needs escape
            local = str(Path(msg['new_dir'], msg['new_file']))
            cmd = self.o.accel_scp_command.split() + [remote, local]
            logger.info("accel_scp :  %s" % ' '.join(cmd))

            p = subprocess.Popen(cmd)
            p.wait()
            return self.check_results(p, msg, os.stat, local)

    def do_put(self, msg, local_file, remote_file, local_offset, remote_offset,
               length):
        """
        """
        logger.debug(f'msg={msg}, local_file={local_file}, remote_file={remote_file}, '
                    f'local_offset={local_file}, remove_offset={remote_offset}, length={length}')
        if self.get_size(msg) < self.o.accel_scp_threshold:
            return super().put(local_file, remote_file, local_offset, remote_offset, length)
        else:
            netloc = urlparse(self.o.destination).netloc
            local = str(Path('/', msg['relPath']).resolve())
            remote = re.escape(f"{netloc}:{Path(msg['new_dir'], msg['new_file'])}")  # Remote needs escape
            cmd = self.o.accel_scp_command.split() + [local, remote]
            logger.info("accel_scp :  %s" % ' '.join(cmd))

            p = subprocess.Popen(cmd)
            p.wait()
            return self.check_results(p, msg, self.sftp.stat, remote)

    def get_size(self, msg):
        if 'blocks' in msg:
            return msg['blocks']['size']
        else:
            return msg['size']

    def check_results(self, p, msg, fct, filename):
        # FIXME for remote files (put) this is awkward to have to reconnect as the tool provided
        #  the result of the command by itself. Maybe just parsing it would be more efficient
        #  while being an accurate way of returning the size
        logger.debug(f'p={p}')
        if p.returncode != 0:
            if hasattr(self.o, 'reportback') and self.o.reportback:
                msg.report_publish(499, 'wget download failed')
        elif hasattr(self.o, 'reportback') and self.o.reportback:
            sarra.msg_set_report(msg, 201, 'Downloaded')
        try:
            return fct(filename).st_size
        except FileNotFoundError as err:
            return 0


"""
Caveats:

     FIXME: on testing with python 3.6, if I don't re-direct to DEVNULL, it hangs.  
     would like to see output of command in the log.

     This downloader invokes scp with only the remote url.
     no options about local file naming are implemented.

     If you have python >= 3.5, replace 'subprocess.call' by subprocess.run, and the stout and stderr will 
     do the right thing. For 'call' also need to change result == 0 to result.returncode == 0 .

APPLICATION NOTES:

    - The built-in downloading logic is pretty good in almost all cases. It is rarely adviseable to use
      this functionality from a performance perspective.

    - Ideal use case:  LAN/Short-haul link with very high bandwidth, where lare peak i/o rates are achievable
      given adequate disk and network connections, such as a high speed LAN. Even there, it should only
      be used for larger files.  

    - Where there is a large tree with many small files, it is very likely that the built-in downloader
      is more efficient than forking any other downloader because, in addition to saving the fork/exec/reap
      overhead, the built-in downloader preserves connections to be used for multiple downloads, so 
      connection establishement, log-in etc.. is not needed for every file. It is actually going
      to be about as efficient as possible for the small file case, as those overheads dominate
      the transfer time.
 
    - As a file gets bigger, the transfer time will eventually dominate the setup-time, and at that
      point, it can make sense to switch to a forking download. Experience with actual configurations
      is needed to pick a good threshold for that. Default of 1M is a reasonable first guess.

    - The native downloader does partitioning of files for passage through multiple pumps and is preferable
      for that case to avoid the 'capybara through an anaconda' syndrome. In cases 'dataless' transfers.
      Where the data does not traverse any pump, this is not a consideration.
     
    - For most long-haul use cases, the bounding constraint is the bandwidth on the link so again
      the built-in downloader is likely close to optimal. Partitioning of the file enables portions of it
      to be delivered and for post-processing tasks, such as anti-virus to overlap with the file transfer.
      when using alternate schemes wihout partitioning, one must await until the complet file has arrived.

"""
