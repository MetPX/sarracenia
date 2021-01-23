#!/usr/bin/python3
"""
	Downloads files retrieved from USGS polls. 

	usage:
		do_download download_usgs.py
	
"""

import logging, urllib.request, os


class BaseURLDownloader(object):
    def __init__(self, parent):
        parent.logger.debug("download_usgs initialized")

    def do_download(self, parent):
        import logging, urllib.request, os

        logger = parent.logger
        if parent.msg.new_dir[-1] != '/': parent.msg.new_dir += '/'

        keypath, key = os.path.split(parent.msg.new_dir + parent.msg.new_file)
        if not os.path.exists(keypath): os.makedirs(keypath)

        with open(keypath + '/' + key, 'wb') as f:
            with urllib.request.urlopen(parent.msg.baseurl) as k:
                logger.info("download_usgs: file %s" % key)
                f.write(k.read())
                parent.msg.set_parts()
                return True

    def registered_as(self):
        return ['http', 'https']


baseurldownloader = BaseURLDownloader(self)
self.do_download = baseurldownloader.do_download
