
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

Weather Application Flows
-------------------------

FIXME: picture?

There is a number (perhaps a dozen?) older applications (most prominent ones being BULLPREP and Scribe) used 
for decades in the Storm Prediction Centres to create forecast and warning products. These applications are 
based on a file tree that they read and write. Formerly, each application had it's own backup strategy with 
one of the six other offices and bi-lateral arrangements were made to copy specific data among the trees.

In January 2017, complete 7-way replication of the state file trees of the applications was implemented
so that all offices have copies of files in real-time. This is accomplished using Sarracenia through 
the eastern hub. Any forecast office can now take over work on any product for any other, with no specific 
application work needed at all.


GOES-R Acquisition
------------------

Acquisition of simulated and real GOES-R products from NOAA's PDA, as well as via local downlinks was entirely mediated
by Sarracenia. The operational deployment of GOES-R happenned in the first week of January, 2018.


HPC Acquisition Feeds
---------------------

FIXME: picture?

There supercomputing environment was entirely replaced in 2017. As part of that, the client Environmental Data acquisition suite (ADE french acronym) was re-factored to work with much higher performance than formerly, and to accept Sarracenia feeds directly, rather than accepting feeds from previous generation pump (Sundew.)  The volume and speed of data acquisition has been substantially improved as a result.


RADAR Data Flows
----------------

If we begin with RADAR data acquisition as an example, individual RADAR systems use FTP and/or SFTP to send files
to eastern and western communications hubs. Those hubs run the directory watching component (sr_watch) and
determine checksums for the volume scans as they arrive. The Unified RADAR Processing (URP) systems sr_subscribes to a hub, listening for new volume scans, and downloads new data as soon as they are posted. 
URP systems then derive new products and advertise them to the local hub using the sr_post component.
In time, we hope to have a second URP fully at the western hub.

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


HPC Mirroring
-------------

All through 2017, work was proceeding to implement high speed mirroring between the supercomputer site stores
to permit failover. That work is now in a final deployment phase, and should be in operations by spring 2018.
For more details see: `HPC Mirroring Use Case <mirroring_use_case.html>`_


Application Changes in 2017
---------------------------

Development of Sarracenia had been exploratory over a number of years. The use cases initially attacked
were those with a high degree of expert involvement. It proceeded following the minimum viable product (mvp)
model for each use case, acquiring features to deal with next use case prior to deployment. In 2016,
national deployment of NinJo and the Weather.  

Expanded use cases explored:

* mirroring.  Formerly tool was used for raw data dissemination without regard for permissions, 
  ownership, symbolic links, etc...  For the mirroring use case, exact metadata replication was 
  a suprisingly complex requirement.

* C-implementation:  In exploring mirroring, it became obvious that for sufficiently large 
  trees ( 27 Million files), the only practical method available was the use of a C shim library.  
  Having all user codes invoke a python3 script, is complete nonsense in an HPC environment, so 
  it was necessary to implement a C version of sarracenia posting code for use by the shim library.  
  Once the C implementation was begun it was only a little additional work to implement a C version 
  of sr_watch which was much more memory and cpu efficient than the python original.

* node.js implementation:  A client of the public datamart decided to implement enough of sarracenia 
  to download warnings in real-time.

* The application was re-factored to maximize consistency through code re-use, reducing about 20% of 
  the code size at one point. The code returned to the initial size when new features were added.
  but it remains quite compact at less than 20kloc.

* end-user usage: All of the deployments thus far are implemented by analysts with a deep understanding 
  of Sarracenia, and extensive support and background. This year, we went through several iterations 
  of having users deploy their flows, collecting feedback, and then making it easier end users at 
  the next iteration. Many of these changes were *breaking* changes, in that options and ways or 
  working were still prototypes and required revision.

  Changes for end user case:

   - exchanges were an administrator-defined resource. Permission model changed: users can now declare exchanges.
   - One had to look on web sites to find examples. Now the *list* command shows many examples included with the package.
   - It was hard to find where to put settings files. The *list/add/remove/edit* commands simplify that. 
   - Different variables were available in different plugins. Re-factored for consistency.
   - partitioning specifications were arcane. They have been replaced with the *blocksize* option, which has only three possibilities: 0,1,many.
   - Users needed to understand routing across multiple pumps, which was quite complex. Now optional, with good defaults, so uses can usually ignore it. 
   - an improved, much more elegant, plugin interface is available to have multiple routines that work together specified in a single plugin.

* save/restore/retry: In operations, if a destination has a problem, there is substantial risk of overloading AMQP brokers by letting queues of products to transfer build into millions of entries. Functionality to efficiently (in parallel) offload broker queues to local disk was implemented to address this. At first, recovery needed to be manually triggerred (restore) but by the end of the year,
  an automated recovery (retry) mechanism is working it's way to deployment, which will reduce requirements for
  oversight and intervention in operations.

Coming in 2018
--------------

As of release 2.18.01a5, all of the use cases targetted have been explored and reasonable solutions are available, so 
there should be no further changes to the existing configuration language or options.  
No changes to existing configuration settings are to be done. Some minor additions may still occur, but not at the cost
of breakage of any existing configurations.  The core application is now complete.

Expect 2.18.01a5 to be the last alpha release of the package and for subsequent work to be on a beta version
with a target of a much more long-lived stable version some time in 2018.  

- HPC mirroring use case deployment will be completed.

- The Permanent File Depot use case to be deployed. Currently this is used to cover a short time horizon.
  One can extend it arbitrarily into the past by persisting the time-based tree to nearline storage.
  FIXME?

- improve deployment consistency: The changes in 2017 were confusing for the expert analysts, as significant changes in details occurred across versions. Different deployments currently use different operational versions, and most issues arising in operations are addressed by the existing code, but are not yet deployed to that use case. In 2018, we will revisit early deployments to bring them uptodate.

- more examples, and documentation: Incorporation of mirroring plugins into provided examples.

- reporting. While reporting was baked in from the start, it proved to be very expensive, and so deployments to date
  have omitted it. Now that deployment loads are quieting down, this year should allow us to add real-time report
  routing to deployed configurations.  There is no functionality to develop, as everything is already in the application,
  but mostly not used. Use may uncover additional issues.

- pluggable checksum algorithms. Currently checksum algorithms are baked into the implementations. There is a need
  to support plugins to support user-defined checksum algorithms.

- Continued progressive replacement of legacy application configurations (RPDS, Sundew) 

- Continued adaptation of applications to Sarracenia (DMS, GOES-R)

- deployment of additional instances:  flux.weather.gc.ca, hpfx.collab.science.gc.ca, etc...
  
- introduction to end users of stable version.

- Continued work on the corporate approval and funding of the western hub (aka. Project Alta.)

