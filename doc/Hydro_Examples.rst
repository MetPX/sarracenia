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
the bottom of a plugin file to define the list of protocols being extended or implemented. 

`def registered_as(self):
    return ['http','https']`

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
an sr_subscribe to the same exchange it got announced on, and it would retrieve the URL, which a **do_download**
plugin could then take and download. An example polling plugin which grabs all water temperature and water level 
data from the last hour, from all CO-OPS stations, and publishes them is included under **plugins** as 
**poll_noaa.py**. A corresponding **do_download** plugin for a sarra instance to download this file is included 
as **download_noaa_hydro.py**. Example configurations for both sr_poll and sr_subscribe are included under 
**examples**, named **pollnoaa.conf** and **subnoaa.conf**. To run, add both plugins and configurations
using the :code:`add` action, edit the proper variables in the config (the flowbroker, destination among others. 
If running off a local RabbitMQ server, some of the documentation under **doc/Dev.rst** on how to set up the
server might be useful), then open two terminals and run:

:code:`[aspymap:~]$ sr_poll foreground pollnoaa.conf`

in one and:

:code:`[aspymap:~]$ sr_subscribe foreground subnoaa.conf`

in the other. If everything was configured correctly, the output should look something like this:
FIXME: run this stuff and put your logs here

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
notice, which a sarra **do_download** plugin could then decipher and process the data into a file user-side. 
In order to only advertise new data from SHC, a polling instance could be configured to sleep every 30 minutes,
and a **do_poll** plugin could set the start-end range to the last half hour before forming the request. 
Each request is returned with a status message confirming if it was a valid function call. The plugin could 
then check the status message is ok before posting the message advertising new data to the exchange.
A **do_download** plugin takes these parameters passed in the message, forms a SOAP query with them, and
extracts the data/saves it to a file. Examples of plugins that do both of these steps can be found under
**plugins**, named **poll_shc_soap.py** and **download_shc_soap.py**. Example configurations for running
both are included under **examples**, named **pollsoapshc.conf** and **subsoapshc.conf**. 

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
method of passing them, so the plugin code that determines which station IDs to use differs. 

To run this example, the configs and plugins can be found under **plugins** (**poll_usgs.py** and 
**download_usgs.py**) and **examples** (**pollusgs.conf** and **subusgs.conf**).

Use Case
--------
The hydrometric plugins were developed for the EC canhys use case, where files containing station metadata
would be used as input to gather the hydrometric data. Each plugin also works by generating all valid 
station IDs from the water authority itself and plugging those inputs in. This option can be toggled by
omitting the plugin config variable that would otherwise specify the station metadata file. 

Most of these sources have disclaimers that this data is not quality assured, but it is gathered in soft
realtime (advertised seconds/minutes from when it was recorded).
