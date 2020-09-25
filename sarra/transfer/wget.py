#!/usr/bin/python3
"""
This plugin launches the UNIX 'wget' command with appropriate arguments to perform a file transfer.
Sample usage:

  plugin accel_wget

One should invoke the more efficient binary downloader only when it makes sense to do so in place
of the built-in python interpreted downloader, typically for larger files. By default, the threshold
is 1M (one megabyte.) The accel_wget_threshold option can be used to change it. 

Options
-------

If a file larger than the threshold is advertised, on_message routine replaces the URL 
scheme 'http' with 'download'.  That change causes the do_download plugin to be invoked 
for that file.  'http' is the default, but the initial url is 'sftp', then the 
accel_wget_protocol option should be set, to have that protocol substituted instead.

  accel_wget_threshold 6M
  accel_wget_protocol  'sftp'

Means that the do_download routine will be called for sftp url's representing files larger than 
six megabytes.  While the wget command is used by default, it can be overridden with the 
accel_wget_command option.

  accel_wget_command /usr/bin/wget -p 

Instead of invoking wget, it will invoke the wget -p command. To the command will be 
See end of file for performance considerations.

"""

import logging
import os
import subprocess
from pathlib import Path
from urllib.parse import urljoin

import sarra
from sarra.config import init_plugin_option
from sarra.transfer.https import Https

logger = logging.getLogger(__name__)


class WGET(Https, schemes=['http', 'https']):
    def __init__(self, proto, options):
        super().__init__(proto, options)
        init_plugin_option(self.o, 'accel_wget_command', 'str', '/usr/bin/wget')
        init_plugin_option(self.o, 'accel_wget_threshold', 'size', '1M')
        init_plugin_option(self.o, 'accel_wget_protocol', 'str', 'https')

    def do_get(self, msg, remote_file, local_file, remote_offset, local_offset,
               length):
        """
        FIXME: this ignores offsets, so it does not work for partitioned files.
        """
        logger.debug(f'msg={msg}, remote_file={remote_file}, local_file={local_file}, '
                     f'remove_offset={remote_offset}, local_offset={local_file}, length={length}')

        if self.get_size(msg) < self.o.accel_wget_threshold:
            return super().get(remote_file, local_file, remote_offset, local_offset, length)
        else:
            os.chdir(msg['new_dir'])
            remote = urljoin(msg['baseUrl'], msg['relPath'])
            cmd = self.o.accel_wget_command.split() + [remote]
            logger.debug(f"new_dir={msg['new_dir']}, new_file={msg['new_file']}, "
                         f"rel_path={msg['relPath']}, cmd={cmd}")
            p = subprocess.Popen(cmd)
            p.wait()
            return self.check_results(p, msg, os.stat, str(Path(msg['new_dir'], msg['new_file'])))

    def get_size(self, msg):
        if 'blocks' in msg:
            return msg['blocks']['size']
        else:
            return msg['size']

    def check_results(self, p, msg, fct, filepath):
        if p.returncode != 0:
            if hasattr(self.o, 'reportback') and self.o.reportback:
                msg.report_publish(499, 'wget download failed')
        elif hasattr(self.o, 'reportback') and self.o.reportback:
            sarra.msg_set_report(msg, 201, 'Downloaded')
        try:
            size = fct(filepath).st_size
        except FileNotFoundError as err:
            size = 0
        return size


"""
Caveats:

     FIXME: on testing with python 3.6, if I don't re-direct to DEVNULL, it hangs.  
     would like to see output of command in the log.

     This downloader invokes wget with only the remote url.
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
