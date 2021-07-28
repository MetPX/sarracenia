=======================================
Using Plugins to Grab Hydrometric Data 
=======================================

Several different environmental data websites use APIs to communicate data. In order to advertise the
availability of new files and integrate them seamlessly into the Sarracenia stack, a few plugins are
needed to extend the polling functionality.

.. contents::

Polling Protocols Natively Supported
------------------------------------
Out of the box, Sarracenia supports polling of HTTP/HTTPS and SFTP/FTP sources where the filename
gets appended to the end of the base URL. For example, if you're trying to access the water level
data of Ghost Lake Reservoir near Cochrane in Alberta, which can be accessed by navigating to 
`http://environment.alberta.ca/apps/Basins/data/figures/river/abrivers/stationdata/L_HG_05BE005_table.json`,
the base URL in this case would be considered the `http://environment.alberta.ca/apps/Basins/data/figures/river/abrivers/stationdata/` part, and the filename the `L_HG_05BE005_table.json` part. Since the base URL doesn't
contain a nice directory with all the JSON files, if you wanted to check if new water level data has 
been added at the locator above, since it's a JSON file, you could check the last-modified header to
see if it has been modified since you last polled. From there, you would need to set the *new_baseurl* to the 
first part, and the *new_file* set to the second, and an sr_subscribe instance would know how to assemble 
them to locate the file and download it. 

Extending Polling Protocols
~~~~~~~~~~~~~~~~~~~~~~~~~~~
If the data source doesn't abide to this convention (see `NOAA CO-OPS API`_ and `USGS Instantaneous Values 
Web Service`_ for examples of two data sources that don't), a module **registered_as** can be included at 
the bottom of a plugin file to define the list of protocols being extended or implemented:: 

	def registered_as(self):
		return ['http','https']

It would then overload the method of transfer and use the one as described in the plugin.

Examples of Integrating APIs into Plugins
-----------------------------------------
NOAA CO-OPS API
~~~~~~~~~~~~~~~
The National Oceanic and Atmospheric Administration Tides and Currents Department releases their CO-OPS 
station observations and predictions data through a GET RESTful web service, available at `the NOAA Tides
and Currents website <https://tidesandcurrents.noaa.gov/api/>`_. For example, if you want to access the 
water temperature data from the last hour in Honolulu, you can navigate to `https://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1612340&product=water_temperature&units=metric&time_zone=gmt&application=web_services&format=csv`.
A new observation gets recorded every six minutes, so if you wanted to advertise solely new data through
Sarracenia, you would configure an sr_poll instance to connect to the API, sleep every hour, and build
it a GET request to announce every time it woke up (this operates under the potentially misguided assumption 
that the data source is maintaining their end of the bargain). To download this shiny new file, you would connect
an sr_subscribe to the same exchange it got announced on, and it would retrieve the URL, which a *do_download*
plugin could then take and download. An example polling plugin which grabs all water temperature and water level 
data from the last hour, from all CO-OPS stations, and publishes them is included under *plugins* as 
`poll_noaa.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/poll_noaa.py>`_. 
A corresponding *do_download* plugin for a sarra instance to download this file is included 
as `download_noaa.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/download_noaa.py>`_
. Example configurations for both sr_poll and sr_subscribe are included under 
*examples*, named `pollnoaa.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/poll/pollnoaa.conf>`_ 
and `subnoaa.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/subscribe/subnoaa.conf>`_. 
To run, add both plugins and configurations using the :code:`add` action, edit the proper variables in the 
config (the flowbroker, destination among others. If running off a local RabbitMQ server, some of the 
documentation under `doc/Dev.rst <https://github.com/MetPX/sarracenia/blob/master/doc/Dev.rst>`_ 
on how to set up the server might be useful). If everything was configured correctly, the output should 
look something like this::

	[aspymap:~]$ sr_poll foreground pollnoaa.conf 
	2018-09-26 15:26:57,704 [INFO] sr_poll pollnoaa startup
	2018-09-26 15:26:57,704 [INFO] log settings start for sr_poll (version: 2.18.07b3):
	2018-09-26 15:26:57,704 [INFO]  inflight=unspecified events=create|delete|link|modify use_pika=False
	2018-09-26 15:26:57,704 [INFO]  suppress_duplicates=False retry_mode=True retry_ttl=Nonems
	2018-09-26 15:26:57,704 [INFO]  expire=300000ms reset=False message_ttl=None prefetch=25 accept_unmatch=False delete=False
	2018-09-26 15:26:57,705 [INFO]  heartbeat=300 default_mode=400 default_mode_dir=775 default_mode_log=600 discard=False durable=True
	2018-09-26 15:26:57,705 [INFO]  preserve_mode=True preserve_time=True realpath_post=False base_dir=None follow_symlinks=False
	2018-09-26 15:26:57,705 [INFO]  mirror=False flatten=/ realpath_post=False strip=0 base_dir=None report_back=True
	2018-09-26 15:26:57,705 [INFO]  post_base_dir=None post_base_url=http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station={0:}&product={1:}&units=metric&time_zone=gmt&application=web_services&format=csv/ sum=z,d blocksize=209715200 
	2018-09-26 15:26:57,705 [INFO]  Plugins configured:
	2018-09-26 15:26:57,705 [INFO]          on_line: Line_Mode 
	2018-09-26 15:26:57,705 [INFO]          on_html_page: Html_parser 
	2018-09-26 15:26:57,705 [INFO]          do_poll: NOAAPoller 
	2018-09-26 15:26:57,705 [INFO]          on_message: 
	2018-09-26 15:26:57,705 [INFO]          on_part: 
	2018-09-26 15:26:57,705 [INFO]          on_file: File_Log 
	2018-09-26 15:26:57,705 [INFO]          on_post: Post_Log 
	2018-09-26 15:26:57,705 [INFO]          on_heartbeat: Hb_Log Hb_Memory Hb_Pulse 
	2018-09-26 15:26:57,705 [INFO]          on_report: 
	2018-09-26 15:26:57,705 [INFO]          on_start: 
	2018-09-26 15:26:57,706 [INFO]          on_stop: 
	2018-09-26 15:26:57,706 [INFO] log_settings end.
	2018-09-26 15:26:57,709 [INFO] Output AMQP broker(localhost) user(tsource) vhost(/)
	2018-09-26 15:26:57,710 [INFO] Output AMQP exchange(xs_tsource)
	2018-09-26 15:26:57,710 [INFO] declaring exchange xs_tsource (tsource@localhost)
	2018-09-26 15:26:58,403 [INFO] poll_noaa file posted: http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1611400&product=water_temperature&units=metric&time_zone=gmt&application=web_services&format=csv
	2018-09-26 15:26:58,403 [INFO] post_log notice=20180926192658.403634 http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1611400&product=water_temperature&units=metric&time_zone=gmt&application=web_services&format=csv CO-OPS__1611400__wt.csv headers={'source': 'noaa', 'to_clusters': 'ALL', 'sum': 'z,d', 'from_cluster': 'localhost'}
	2018-09-26 15:26:58,554 [INFO] poll_noaa file posted: http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1611400&product=water_level&units=metric&time_zone=gmt&application=web_services&format=csv&datum=STND
	2018-09-26 15:26:58,554 [INFO] post_log notice=20180926192658.554364 http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1611400&product=water_level&units=metric&time_zone=gmt&application=web_services&format=csv&datum=STND CO-OPS__1611400__wl.csv headers={'source': 'noaa', 'to_clusters': 'ALL', 'sum': 'z,d', 'from_cluster': 'localhost'}
	2018-09-26 15:26:58,691 [INFO] poll_noaa file posted: http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1612340&product=water_temperature&units=metric&time_zone=gmt&application=web_services&format=csv
	2018-09-26 15:26:58,691 [INFO] post_log notice=20180926192658.691466 http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1612340&product=water_temperature&units=metric&time_zone=gmt&application=web_services&format=csv CO-OPS__1612340__wt.csv headers={'source': 'noaa', 'to_clusters': 'ALL', 'sum': 'z,d', 'from_cluster': 'localhost'}
	2018-09-26 15:26:58,833 [INFO] poll_noaa file posted: http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1612340&product=water_level&units=metric&time_zone=gmt&application=web_services&format=csv&datum=STND
	2018-09-26 15:26:58,834 [INFO] post_log notice=20180926192658.833992 http://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1612340&product=water_level&units=metric&time_zone=gmt&application=web_services&format=csv&datum=STND CO-OPS__1612340__wl.csv headers={'source': 'noaa', 'to_clusters': 'ALL', 'sum': 'z,d', 'from_cluster': 'localhost'}
	^C2018-09-26 15:26:58,965 [INFO] signal stop (SIGINT)
	2018-09-26 15:26:58,965 [INFO] sr_poll stop

for the polling and::

	[aspymap:~]$ sr_subscribe foreground subnoaa.conf 
	2018-09-26 15:26:53,473 [INFO] sr_subscribe subnoaa start
	2018-09-26 15:26:53,473 [INFO] log settings start for sr_subscribe (version: 2.18.07b3):
	2018-09-26 15:26:53,473 [INFO]  inflight=.tmp events=create|delete|link|modify use_pika=False
	2018-09-26 15:26:53,473 [INFO]  suppress_duplicates=False retry_mode=True retry_ttl=300000ms
	2018-09-26 15:26:53,473 [INFO]  expire=300000ms reset=False message_ttl=None prefetch=25 accept_unmatch=False delete=False
	2018-09-26 15:26:53,473 [INFO]  heartbeat=300 default_mode=000 default_mode_dir=775 default_mode_log=600 discard=False durable=True
	2018-09-26 15:26:53,473 [INFO]  preserve_mode=True preserve_time=True realpath_post=False base_dir=None follow_symlinks=False
	2018-09-26 15:26:53,473 [INFO]  mirror=False flatten=/ realpath_post=False strip=0 base_dir=None report_back=False
	2018-09-26 15:26:53,473 [INFO]  Plugins configured:
	2018-09-26 15:26:53,473 [INFO]          do_download: BaseURLDownloader 
	2018-09-26 15:26:53,473 [INFO]          do_get     : 
	2018-09-26 15:26:53,473 [INFO]          on_message: 
	2018-09-26 15:26:53,474 [INFO]          on_part: 
	2018-09-26 15:26:53,474 [INFO]          on_file: File_Log 
	2018-09-26 15:26:53,474 [INFO]          on_post: Post_Log 
	2018-09-26 15:26:53,474 [INFO]          on_heartbeat: Hb_Log Hb_Memory Hb_Pulse RETRY 
	2018-09-26 15:26:53,474 [INFO]          on_report: 
	2018-09-26 15:26:53,474 [INFO]          on_start: 
	2018-09-26 15:26:53,474 [INFO]          on_stop: 
	2018-09-26 15:26:53,474 [INFO] log_settings end.
	2018-09-26 15:26:53,474 [INFO] sr_subscribe run
	2018-09-26 15:26:53,474 [INFO] AMQP  broker(localhost) user(tsource) vhost(/)
	2018-09-26 15:26:53,478 [INFO] Binding queue q_tsource.sr_subscribe.subnoaa.90449861.55888967 with key v02.post.# from exchange xs_tsource on broker amqp://tsource@localhost/
	2018-09-26 15:26:53,480 [INFO] reading from to tsource@localhost, exchange: xs_tsource
	2018-09-26 15:26:53,480 [INFO] report_back suppressed
	2018-09-26 15:26:53,480 [INFO] sr_retry on_heartbeat
	2018-09-26 15:26:53,486 [INFO] No retry in list
	2018-09-26 15:26:53,488 [INFO] sr_retry on_heartbeat elapse 0.007632
	2018-09-26 15:26:58,751 [INFO] download_noaa: file noaa_20180926_1926_1611400_TP.csv
	2018-09-26 15:26:58,751 [INFO] file_log downloaded to: /home/ib/dads/map/hydro_examples_sarra/fetch/noaa//CO-OPS__1611400__wt.csv
	2018-09-26 15:26:58,888 [INFO] download_noaa: file noaa_20180926_1926_1611400_WL.csv
	2018-09-26 15:26:58,889 [INFO] file_log downloaded to: /home/ib/dads/map/hydro_examples_sarra/fetch/noaa//CO-OPS__1611400__wl.csv
	2018-09-26 15:26:59,026 [INFO] download_noaa: file noaa_20180926_1926_1612340_TP.csv
	2018-09-26 15:26:59,027 [INFO] file_log downloaded to: /home/ib/dads/map/hydro_examples_sarra/fetch/noaa//CO-OPS__1612340__wt.csv
	2018-09-26 15:26:59,170 [INFO] download_noaa: file noaa_20180926_1926_1612340_WL.csv
	2018-09-26 15:26:59,171 [INFO] file_log downloaded to: /home/ib/dads/map/hydro_examples_sarra/fetch/noaa//CO-OPS__1612340__wl.csv
	^C2018-09-26 15:27:00,597 [INFO] signal stop (SIGINT)
	2018-09-26 15:27:00,597 [INFO] sr_subscribe stop

for the downloading.

SHC SOAP Web Service
~~~~~~~~~~~~~~~~~~~~
A SOAP web service (Simple Object Access Protocol) uses an XML-based messaging system to supply requested 
data over a network. The client can specify parameters for a supported operation (for example a search) on 
the web service, denoted with a wdsl file extension, and the server will return an XML-formatted SOAP 
response. The Service Hydrographique du Canada (SHC) uses this web service as an API to get hydrometric
data depending on the parameters sent. It only supports one operation, search, which accepts the following 
parameters: dataName, latitudeMin, latitudeMax, longitudeMin, longitudeMax, depthMin, depthMax, dateMin, 
dateMax, start, end, sizeMax, metadata, metadataSelection, order. For example, a search will return all the
water level data available from Acadia Cove in Nunavut on September 1st, 2018 if your search contains
the following parameters: 'wl', 40.0, 85.0, -145.0, -50.0, 0.0, 0.0, '2018-09-01 00:00:00', 
'2018-09-01 23:59:59', 1, 1000, 'true', 'station_id=4170, 'asc'. The response can then be converted into a 
file and dumped, which can be advertised, or the parameters can be advertised themselves in the report
notice, which a sarra *do_download* plugin could then decipher and process the data into a file user-side. 
In order to only advertise new data from SHC, a polling instance could be configured to sleep every 30 minutes,
and a *do_poll* plugin could set the start-end range to the last half hour before forming the request. 
Each request is returned with a status message confirming if it was a valid function call. The plugin could 
then check the status message is ok before posting the message advertising new data to the exchange.
A *do_download* plugin takes these parameters passed in the message, forms a SOAP query with them, and
extracts the data/saves it to a file. Examples of plugins that do both of these steps can be found under
*plugins*, named `poll_shc_soap.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/poll_shc_soap.py>`_ 
and `download_shc_soap.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/download_shc_soap.py>`_. 
Example configurations for running both are included under *examples*, named 
`pollsoapshc.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/poll/pollsoapshc.conf>`_ and 
`subsoapshc.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/subscribe/subsoapshc.conf>`_. 

USGS Instantaneous Values Web Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The United States Geological Survey publishes their water data through their Instantaneous Values RESTful
Web Service, which uses HTTP GET requests to filter their data. It returns the data in XML files once 
requested, and can support more than one station ID argument at a time (bulk data download). More info on 
the service can be found `at the water services website <https://waterservices.usgs.gov/rest/IV-Service.html>`_. 
They have a long list of parameters to specify based on the type of water data you would like to retrieve as well,
which is passed through the parameterCd argument. For example, if you wanted to fetch water discharge, level, and
temperature data from the last three hours from North Fork Vermilion River near Bismarck, IL, you would use 
the following URL:
https://waterservices.usgs.gov/nwis/iv/?format=waterml,2.0&indent=on&site=03338780&period=PT3H&parameterCd=00060,00065,00011.
A list of parameter codes to use to tailor your results can be found `here <https://help.waterdata.usgs.gov/code/parameter_cd_query?fmt=rdb&inline=true&group_cd=%25>`_.
The plugins for any GET web service can be generalized for use, so the plugins used for the NOAA CO-OPS API
can be reused in this context as well. By default, the station IDs to pass are different, as well as the 
method of passing them, so the plugin code that determines which station IDs to use differs, but the method
conceptually is still the same. You would pass a generalized version of the URL in as the destination in the 
config, e.g. https://waterservices.usgs.gov/nwis/iv/?format=waterml,2.0&indent=on&site={0}&period=PT3H&parameterCd=00060,00065,00011
and in the plugin you would replace the '{0}' (Python makes this easy with string formatting) with the sites
you're interested in, and if any other parameters need to be varied they can be replaced in a similar way.
If a station site ID file wasn't passed as a plugin config option, then the plugin defaults to grabbing all
the registered site IDs from `the USGS website <https://water.usgs.gov/osw/hcdn-2009/HCDN-2009_Station_Info.xlsx>`_.
The IV Web Service supports queries with multiple site IDs specified (comma-separated). If the plugin option
*poll_usgs_nb_stn* was specified to the chunk size in the config, it'll take groups of stations' data based on
the number passed (this reduces web requests and speeds up the data collection if collecting in bulk).  

To run this example, the configs and plugins can be found under *plugins* 
(`poll_usgs.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/poll_usgs.py>`_ 
and `download_usgs.py <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/download_usgs.py>`_) 
and *examples* (`pollusgs.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/poll/pollusgs.conf>`_ 
and `subusgs.conf <https://github.com/MetPX/sarracenia/blob/master/sarra/examples/subscribe/subusgs.conf>`_).

Use Case
--------
The hydrometric plugins were developed for the Environment Canada canhys use case, where files containing 
station metadata would be used as input to gather the hydrometric data. Each plugin also works by generating 
all valid station IDs from the water authority itself and plugging those inputs in. This alternative option can be 
toggled by omitting the plugin config variable that would otherwise specify the station metadata file. 
The downloader plugins also rename the file according to the specific convention of this use case.

Most of these sources have disclaimers that this data is not quality assured, but it is gathered in soft
realtime (advertised seconds/minutes from when it was recorded).
