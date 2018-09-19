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
http://environment.alberta.ca/apps/Basins/data/figures/river/abrivers/stationdata/L_HG_05BE005_table.json,
the base URL in this case would be considered the http://environment.alberta.ca/apps/Basins/data/figures/river/abrivers/stationdata/ part, and the filename the L_HG_05BE005_table.json part. Since the base URL doesn't
contain a nice directory with all the JSON files, if you wanted to check if new water level data has 
been added at the locator above, since it's a JSON file, you could check the last-modified header to
see if it has been modified since you last polled. From there, you would need to set the new_baseurl to the 
first part, and the new_file set to the second, and an sr_subscribe instance would know how to assemble 
them to locate the file and download it. 

Extending Polling Protocols
~~~~~~~~~~~~~~~~~~~~~~~~~~~
If the data source doesn't abide to this convention (see `NOAA CO-OPS API`_ and `USGS Instantaneous Values 
Web Service`_ for examples of two data sources that don't), a module **registered_as** can be included at 
the bottom of a plugin file to define the list of protocols being extended or implemented. 

:code:`def registered_as(self):
           return ['http','https']`

It would then overload the method of transfer and use the one as described in the plugin.

Examples of Integrating APIs into Plugins
-----------------------------------------
NOAA CO-OPS API
~~~~~~~~~~~~~~~
The National Oceanic and Atmospheric Administration Tides and Currents Department releases their CO-OPS 
station observations and predictions data through a GET RESTful web service, available at 
https://tidesandcurrents.noaa.gov/api/. For example, if you want to access the water temperature data 
from the last hour in Honolulu, you can navigate to https://tidesandcurrents.noaa.gov/api/datagetter?range=1&station=1612340&product=water_temperature&units=metric&time_zone=gmt&application=web_services&format=csv.
A new observation gets recorded every six minutes, so if you wanted to advertise solely new data through
Sarracenia, you would configure an sr_poll instance to connect to the API, sleep every hour, and build
it a GET request to announce every time it woke up (this operates under the potentially misguided assumption 
that the data source is maintaining their end of the bargain). To download this shiny new file, you would connect
an sr_subscribe to the same exchange it got announced on, and it would retrieve the URL, which a **do_download**
plugin could then take and download. An example polling plugin which grabs all water temperature and water level 
data from the last hour, from all CO-OPS stations, and publishes them is included under **plugins/** as 
**poll_noaa.py**. A corresponding **do_download** plugin for a sarra instance to download this file is included 
as **download_noaa_hydro.py**. Example configurations for both sr_poll and sr_subscribe are included under 
**examples/**, named **pollnoaa.conf** and **subnoaa.conf**. To run, add both plugins and configurations
using the :code:`add` action, edit the proper variables in the config (the flowbroker, destination among others. 
If running off a local RabbitMQ server, some of the documentation under **doc/Dev.rst** on how to set up the
server might be useful), then open two terminals and run:

:code:`sr_poll foreground pollnoaa.conf foreground`

in one and:

:code:`sr_subscribe foreground subnoaa.conf foreground`

in the other. If everything was configured correctly, the output should look something like this:
FIXME: run this stuff and put your logs here

SHC SOAP Web Service
~~~~~~~~~~~~~~~~~~~~
A SOAP web service (Simple Object Access Protocol) uses an XML-based messaging system to supply requested 
data over a network. The client can specify parameters for a supported operation on the web service (for 
example a search), denoted with a wdsl file extension, and the server will return an XML-formatted SOAP 
response. The Service Hydrographique du Canada (SHC) uses this web service as an API to get hydrometric
data depending on the parameters sent. It

USGS Instantaneous Values Web Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

