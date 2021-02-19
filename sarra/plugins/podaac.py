#!/usr/bin/python3

import datetime
import logging
import easywebdav

class PODAAC(object):

	def __init__(self, parent):
		parent.declare_option('podaac_key')

	def do_poll(self, parent):
		import logging
		from datetime import datetime, timedelta
		import easywebdav as ewd
		import os.path
		from urllib.parse import urlparse
		yesterday = datetime.now() - timedelta(days=1)
		twodaysago = datetime.now() - timedelta(days=2)
		threedaysago = datetime.now() - timedelta(days=3)
		juliandate2days = str(twodaysago.timetuple().tm_yday).zfill(3)
		juliandate3days = str(threedaysago.timetuple().tm_yday).zfill(3)
		juliandateY = str(yesterday.timetuple().tm_yday).zfill(3)
		juliandate = str(datetime.now().timetuple().tm_yday).zfill(3)
		yearY3 = str(threedaysago.year)
		yearY2 = str(twodaysago.year)
		yearY = str(yesterday.year)
		year = str(datetime.now().year)
		logger = parent.logger
		remote = []
		for key in parent.podaac_key:
			remote.append(key + yearY3 + "/" + juliandate3days + "/")
			remote.append(key + yearY2 + "/" + juliandate2days + "/") 
			remote.append(key + yearY + "/" + juliandateY + "/")
			remote.append(key + year + "/" + juliandate + "/")

		ok, details = parent.credentials.get(parent.destination)
		if not ok:
			logger.error( "podaac: post_broker credential lookup failed for %s" % parent.destination )
			return

		url = details.url
		username = url.username
		password = url.password
		site = url.hostname
		protocol = url.scheme
		currentDir = parent.currentDir
		webdav = ewd.connect(site, username=username, password=password, protocol=protocol, path=currentDir)
		for path in remote:
			try:
				files = webdav.ls(path)
			except:
				logger.error("Remote Path does not exist: {0}".format(str(currentDir + path)))
				continue
			for filea in files:
				if filea[0].strip(currentDir + path) != '':
					parent.msg.new_baseurl = url.geturl()
					parent.to_clusters = 'ALL'
					parent.msg.new_file = str(filea[0])
					logger.info("Downloading: {0}".format(str(filea[0])))
					parent.msg.set_parts()
					parent.msg.sumflg = 'z'
					parent.msg.sumstr = 'z,d'
					parent.post(parent.exchange, parent.msg.new_baseurl, parent.msg.new_file,
					        parent.to_clusters, parent.msg.partstr, parent.msg.sumstr)


	def do_download(self, parent):
		import logging
		import urllib.request
		import os.path
		import datetime
		import easywebdav as ewd
		ewd.basestring = str
		ewd.client.basestring = str
		logger = parent.logger

		ok, details = parent.credentials.get(parent.msg.url.geturl())

		if not ok:
			logger.error( "podaac: post_broker credential lookup failed for podaac" )
			return True

		url = details.url
		username = url.username
		password = url.password
		site = url.hostname
		path = parent.msg.url.path
		dirname = os.path.dirname(path)
		basename = os.path.basename(path)
		localdir = parent.msg.new_dir
		if not os.path.exists(localdir):
			os.makedirs(localdir)
		logger.info("basename: {0}".format(str(basename)))
		with open(localdir+'/'+basename, 'wb') as f:
			webdav = ewd.connect(site, protocol=parent.msg.url.scheme,
			                     username=username, password=password, path=dirname)
			webdav.download(basename, f)
			parent.msg.set_parts()
			return True

	def registered_as(self):
		return ['http', 'https']

podaac = PODAAC(self)
self.do_poll = podaac.do_poll
self.do_download = podaac.do_download
