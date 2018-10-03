#!/usr/bin/python3

"""
Downloads files sourced from the baseurl of the poster, and saves them in the 
directory specified in the config. Created to use with the poll_nexrad.py 
plugin to download files uploaded in the NEXRAD US Weather Radar public dataset.
Compatible with Python 3.5+.

msg_download_baseurl: a sample do_download option for sr_subscribe.
		downloads the file located at parent.msg.baseurl and
		saves it
usage:
	on_message msg_download_baseurl.py
	
"""

import logging,urllib.request,os

class BaseURLDownloader(object):

	def __init__(self, parent):
		parent.logger.debug("msg_download_baseurl initialized")

	def on_message(self, parent):
		import logging,urllib.request,os

		logger = parent.logger
		
		# if mirror is set to True, comment these two lines out	
		keypath, key = os.path.split(parent.new_dir+parent.msg.new_file)
		if not os.path.exists(keypath): os.makedirs(keypath)

		with open(keypath+'/'+key, 'wb') as f:
			with urllib.request.urlopen(parent.msg.baseurl) as k:
				f.write(k.read())
				return True

baseurldownloader = BaseURLDownloader(self)
self.on_message = baseurldownloader.on_message
