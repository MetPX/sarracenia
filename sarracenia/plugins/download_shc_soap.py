#!/usr/bin/python3
"""
Downloads files by taking the SOAP arguments passed through the baseurl of the poster
and feeding it to the SHC SOAP query service. Saves the corresponding file with the correct
format and file extension (.dat).
Compatible with Python 3.5+.

usage:
	download_shc_soap_stn_file [path/to/station/file]
	do_download download_shc_soap.py

	If station file isn't given, then there will be a blank column where 'siteID' should
	be when creating the dat file. If it is given, it'll look up the site code and construct
	the dat file with its corresponding site ID (used for the CANHYS database parsing).
	
"""

import logging, os, datetime, zeep, pytz


class BaseURLDownloader(object):
    def __init__(self, parent):
        parent.declare_option('download_shc_soap_stn_file')
        parent.logger.debug("download_shc_soap initialized")

    def do_download(self, parent):
        import logging, os, datetime, zeep, pytz

        logger = parent.logger
        if parent.msg.new_dir[-1] != '/': parent.msg.new_dir += '/'
        keypath, key = os.path.split(parent.msg.new_dir + parent.msg.new_file)
        if not os.path.exists(keypath): os.makedirs(keypath)

        # If file is given, create dictionary of sitecode: siteID
        stn_data = {}
        if hasattr(parent, 'download_shc_soap_stn_file'):
            stn_file = parent.msg_shc_soap_downloader_stn_file[0]
            try:
                with open(stn_file) as f:
                    for line in f:
                        items = line.split('|')
                        stn_data[items[2]] = items[1]
                logger.info("download_shc_soap stn_file used: %s" % stn_file)
            except IOError:
                logger.error("download_shc_soap file not found: %s" % stn_file)

        # Form the arguments from the baseurl, looks something like:
        # wl,40.0,85.0,-145.0,-50.0,0.0,0.0,2018-08-10_10:36:49,2018-08-10_14:36:49,1,1000,true,station_id=02145,asc
        args = parent.msg.baseurl.split(',')
        # Convert dates back from %Y-%m-%d_%H:%M:%S to %Y-%m-%d %H:%M:%S
        args[7] = datetime.datetime.strptime(
            args[7], "%Y-%m-%d_%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
        args[8] = datetime.datetime.strptime(
            args[8], "%Y-%m-%d_%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
        client = zeep.Client(
            'https://ws-shc.qc.dfo-mpo.gc.ca/observations?wsdl')
        wdata = client.service.search(args[0], float(args[1]), float(args[2]),
                                      float(args[3]), float(args[4]),
                                      float(args[5]), float(args[6]),
                                      args[7], args[8], int(args[9]),
                                      int(args[10]), args[11], args[12],
                                      args[13])

        # Write all data received in return to msg.new_file
        try:
            with open(keypath + '/' + key, 'w') as f:
                stn_id = parent.msg.baseurl.split("station_id=")[1].split(
                    ",")[0]
                for point in wdata.data:
                    # Original script has this kind of processing that is supposed to deal
                    # with daylight savings discrepancies I guess? mostly does nothing
                    date = datetime.datetime.strptime(
                        point.boundaryDate['max'], '%Y-%m-%d %H:%M:%S')
                    utc = pytz.timezone('UTC')
                    date = utc.normalize(
                        utc.localize(date)).strftime('%Y-%m-%d %H:%M:%S')
                    # If station file given, write each station ID to the file. If not
                    # provided, write a blank where the station ID should be.
                    if stn_id in stn_data:
                        logger.debug("download_shc_soap station ID used")
                        f.write('3|' + stn_data[stn_id] + '|100|' + date +
                                '|' + point.value + '\n')
                    else:
                        logger.debug("download_shc_soap station ID not found")
                        f.write('3||100|' + date + '|' + point.value + '\n')
        except IOError:
            logger.error("download_shc_soap: file couldn't be written to: %s" %
                         (keypath + '/' + key))

        logger.info("download_shc_soap: file %s" % key)
        parent.msg.set_parts()
        return True

    def registered_as(self):
        return ['http', 'https']


baseurldownloader = BaseURLDownloader(self)
self.do_download = baseurldownloader.do_download
