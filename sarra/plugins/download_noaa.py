#!/usr/bin/python3
"""
	Renames and downloads NOAA products from a NOAA poll. Renames files as:
		CO-OPS__<sitecode>__<wt|wl>.csv -> noaa_YYYYmmdd_HHMM_<sitecode>_<TP|WL>.csv
	where YYYYmmdd_HHMM is the current time at runtime

	usage:
		do_download download_noaa.py
	
"""

import logging, urllib.request, os, datetime


class BaseURLDownloader(object):
    def __init__(self, parent):
        parent.logger.debug("download_noaa initialized")

    def do_download(self, parent):
        import logging, urllib.request, os, datetime

        logger = parent.logger
        if parent.msg.new_dir[-1] != '/': parent.msg.new_dir += '/'

        mtime = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M')

        # Get sitecode from new_file
        site = parent.msg.new_file.split('__')[1]

        # Get datatype from new_file, either wt or wl
        filedatatype = parent.msg.new_file.split('__')[2][:2]
        if filedatatype == 'wt':
            datatype = 'TP'
        elif filedatatype == 'wl':
            datatype = 'WL'
        else:
            logger.debug("download_noaa: unknown file data type %s" %
                         filedatatype)
            datatype = 'XX'

        keypath, key = os.path.split(
            parent.msg.new_dir +
            'noaa_{0}_{1}_{2}.csv'.format(mtime, site, datatype))
        if not os.path.exists(keypath): os.makedirs(keypath)

        with open(keypath + '/' + key, 'wb') as f:
            with urllib.request.urlopen(parent.msg.baseurl) as k:
                logger.info("download_noaa: file %s" % key)
                f.write(k.read())
                parent.msg.set_parts()
                return True

    def registered_as(self):
        return ['http', 'https']


baseurldownloader = BaseURLDownloader(self)
self.do_download = baseurldownloader.do_download
