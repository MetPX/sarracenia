
Deployment Status 2018
----------------------

The slide below corresponds to deployed data flows in support of Environment Canada, mostly
for operational weather forecasting, in place in January 2018.

.. image:: E-services_data-volume_pas.png

Sarracenia is being used operationally to acquire about four terabytes observations from automated weather 
observing systems, Weather RADARS which deliver data directly to our hubs, international peer operated public 
file services, which provide satellite imagery and numerical products from other national weather centres.

Within the main high performance computing (HPC) data centre, there are two supercomputers, two site stores, 
and two pre and post processing clusters. Should a component in one chain fail, the other can take over. The input
data is sent to a primary chain, and then processing on that chain is mirrored, using sarracenia to copy
the data to the other chain. That´s about 16 of the 25 terabytes of the data centre traffic in this diagram.

A distillation of the data acquired, and the analysis and forecasts done in HPC, is the seven terabytes
at the top right, that is sent to the seven regional Storm Prediction Centres (SPC´s.)

The products of the SPC´s and the central HPC are then shared with the public and partners in industry, academia,
and other governements.


RADAR Data Flows
----------------

If we begin with RADAR data acquisition as an example, individual RADAR systems use FTP and/or SFTP to send files
to eastern and western communications hubs. Those hubs run the directory watching component (sr_watch) and
determine checksums for the volume scans as they arrive. The Unified RADAR Processing (URP) systems are sr_subscribed
to one hubs, listening for new volume scans, and download new data from the hubs as soon as they are posted.
URP systems then derive new products and advertise them to the local hub using the sr_post component.

In regional offices, the NinJo visualization servers download volume scans and processed data from URP 
using identical subscriptions, pulling the data from whichever national hub makes the data available first.
The failure of a national hub is transparent for RADAR data in that the volume scans will be downloaded
from the other hub, and the other URP processor will produce the products needed.

.. image:: RADAR_DI_LogicFlow_Current.gif 
    :scale: 25%

Each site has multiple ninjo servers. We use http-based file servers, or web accessible folders to serve data. 
This allows easy integration of web-proxy caches, which means that only the first ninjo server to request data 
will download from the national hub. Other Ninjo servers will get their data from the local proxy cache.
The use of Sarracenia for notifications when new products are available is completely independent of the 
method used to serve and download data. Data servers can be implemented with a wide variety of tools
and very little integration is needed.  



