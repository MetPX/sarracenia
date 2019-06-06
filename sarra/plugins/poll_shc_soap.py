#!/usr/bin/python3

"""
Posts dat files of SHC hydrometric data obtained through its SOAP web service. Station site IDs 
provided in the poll_shc_soap_stn_file. Compatible with Python 3.5+.

usage:
	in an sr_poll configuration file:
	destination http://ws-shc.qc.dfo-mpo.gc.ca/observations?wdsl

	poll_shc_soap_stn_file [path/to/stn/file]
	poll_shc_soap_deltat time_interval
	do_poll poll_shc_soap.py

	If poll_shc_soap_stn_file isn't set, it'll default to pulling all the station IDs from 
	http://tides.gc.ca/eng/station/list. (This will work provided the website doesn't get
	a massive overhaul and every station ID is still accessible by grabbing all the tags
	with a class name of 'id').
	If the file is set, it should be in the following format:
	SourceID | SiteID | SiteCode | SiteName | CountryID | StateID | UTCOffset
	Each station on its own line.
	time_interval should be hours back from the current time (delta t) that observations
	will cover. It must be specified in order to form the SOAP query.
"""

import datetime,logging,zeep,urllib.request
from bs4 import BeautifulSoup

class SHCSOAPPoller(object):

	def __init__(self,parent):
		parent.declare_option('poll_shc_soap_stn_file')
		parent.declare_option('poll_shc_soap_deltat')

	def do_poll(self,parent):
		import datetime,logging,zeep,urllib.request
		from bs4 import BeautifulSoup

		logger = parent.logger

		# Make list of sitecodes either from provided file or tides.gc.ca
		sitecodes = []
		if hasattr(parent, 'poll_shc_soap_stn_file'):
			stn_file = parent.poll_shc_soap_stn_file[0]
			try:
				with open(stn_file) as f:
					for line in f:
						items = line.split('|')
						sitecodes.append(items[2])
				logger.info("poll_shc_soap used stn_file %s" % stn_file)
			except IOError as e:
				logger.error("poll_shc_soap couldn't open stn file: %s" % stn_file)
				
		else:
			with urllib.request.urlopen('http://tides.gc.ca/eng/station/list') as f:
				page = f.read()
			soup = BeautifulSoup(page,'html.parser')
			for elem in soup.find_all(class_="id"):
				sitecodes.append(elem.get_text())

		if not hasattr(parent, 'poll_shc_soap_deltat'):
			logger.error("poll_shc_soap_deltat must be specified to form soap query")
			return
		deltat = parent.poll_shc_soap_deltat[0]		

		# Form mindate and maxdate part of soap query, with the deltat param provided
		run_time = datetime.datetime.utcnow()
		run_time_file = run_time.strftime('%Y%m%d_%H%M')
		fetch_date_end = run_time
		fetch_date_start = fetch_date_end - datetime.timedelta(hours=int(deltat))
		end = fetch_date_end.strftime('%Y-%m-%d %H:%M:%S')
		start = fetch_date_start.strftime('%Y-%m-%d %H:%M:%S')
		client = zeep.Client('https://ws-shc.qc.dfo-mpo.gc.ca/observations?wsdl')

		for site in sitecodes:
			# from the wdsl page: <wsdl:operation name="search" parameterOrder="dataName latitudeMin 
			# latitudeMax longitudeMin longitudeMax depthMin depthMax dateMin dateMax start sizeMax 
			# metadata metadataSelection order">
			wdata = client.service.search('wl',40.0,85.0,-145.0,-50.0,0.0,0.0,start,end,1,1000,'true','station_id='+site,'asc')
			if wdata['status']['status'] == 'ok':
				# new_baseurl contains the query parameters to download the file. It messes up
				# sarracenia to transmit a new_baseurl with spaces, so I took the spaces out of
				# the dates to transmit
				logger.info("poll_shc_soap file ready %s" % \
						'shc_{0}_{1}.dat'.format(run_time_file,site))
				mstart = datetime.datetime.strptime(start,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d_%H:%M:%S')
				mend = datetime.datetime.strptime(end,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d_%H:%M:%S')
				parent.msg.new_baseurl = """wl,40.0,85.0,-145.0,-50.0,0.0,0.0,{0},{1},1,1000,true,station_id={2},asc""".format(mstart,mend,site)
				parent.msg.new_file = 'shc_{0}_{1}.dat'.format(run_time_file,site) 
				parent.to_clusters = 'ALL'
				parent.msg.sumstr = 'z,d'
				parent.post(parent.exchange,parent.msg.new_baseurl,parent.msg.new_file,\
						parent.to_clusters,sumstr=parent.msg.sumstr)
			else:
				logger.error("poll_shc_soap query malformed: %s" % wdata['status']['message'])
		
shcsoappoller = SHCSOAPPoller(self)
self.do_poll = shcsoappoller.do_poll
