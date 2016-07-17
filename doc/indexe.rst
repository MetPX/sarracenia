
.. |Date| date::

=============
MetPX welcome
=============

MetPX - Meteorological Product eXchanger
========================================

Date: |Date|

 [ français_. ]

.. _français: indexf.html 

MetPX is a collection of tools created to support data acquisition, routing, and dissemination in a meteorological context.
There are two main applications in the MetPX suite: MetPX-Sundew_ is the legacy WMO-GTS supporting message switching system.
`MetPX-Sundew`_ transfers accepts, transforms, and delivers individual 
products.  `MetPX Sarracenia`_ is the next generation *data pump*,
currently under development.
Sarracenia transfers directory trees of products on behalf of data sources 
across a sequence of switches.  While Sarracenia leaves legacy 
compatibility behind in order to address more modern concerns, sundew remains 
necessary to interface to legacy systems.  


[ `Sarracenia Documentation`_ ] [ `Sundew Documentation`_ ] [ Downloads_ ] [ Download_ ] [ `Getting Source Code`_ ] [ Links_ ]
[ mailing-lists: `metpx-devel <http://lists.sourceforge.net/lists/listinfo/metpx-devel>`_ , 
`metpx-commit <http://lists.sourceforge.net/lists/listinfo/metpx-commit>`_ ]
[ Main Project page: `Sourceforge <http://www.sourceforge.net/projects/metpx>`_ ]

MetPX Sarracenia
================

**MetPX-Sarracenia** is a data duplication or distribution engine that leverages existing 
standard technologies (web servers and the AMQP_ brokers) to achieve real-time message 
delivery and end to end transparency in file transfers.  Whereas in Sundew, each switch 
is a standalone configuration which transforms data in complex ways, in sarracenia, the 
data sources establish a structure which is carried through any number of intervening pumps 
until they arrive at a client.  The client can provide explicit acknowledgement that 
propagates back through the network to the source.  Whereas traditional file switching 
is a point-to-point affair where knowledge is only between each segment, in Sarracenia, 
information flows from end to end in both directions.

At it's heart, sarracenia exposes a tree of web accessible folders (WAF), using any 
standard HTTP server (tested with apache).  Weather applications are soft real-time, 
where data should be delivered as quickly as possible to the next hop, and minutes, 
perhaps seconds, count.  The standard web push technologies, ATOM, RSS, etc... are 
actually polling technologies that when used in low latency applications consume a 
great deal of bandwidth an overhead.  For exactly these reasons, those standards 
stipulate a minimum polling interval of five minutes.   Advanced Message Queueing 
Protocol (AMQP) messaging brings true push to notifications, and makes real-time 
sending far more efficient.


.. image:: e-ddsr-components.jpg


Sources of data announce their products, pumping systems pull the data using HTTP 
or SFTP onto their WAF trees, and then announce their trees for downstream clients.  
When clients download data, they may write a report message back to the server.  Servers 
are configured to forward those client report messages back through the intervening 
servers back to the source.  The Source can see the entire path that the data took 
to get to each client.  With traditional switching applications, sources only see 
that they delivered to the first hop in a chain. Beyond that first hop, routing is 
opaque, and tracing the path of data required assistance from administrators of each 
intervening system.  With Sarracenia's report forwarding, the switching network is 
relatively transparent to the sources.  Diagnostics are vastly simplified.

For large files / high performance, files are segmented on ingest if they are sufficiently
large to make this worthwhile.  Each file can traverse the data pumping network independently,
and reassembly is only needed at end points.   A file of sufficient size will announce
the availability of several segments for transfer, multiple threads or transfer nodes
will pick up segments and transfer them.  The more segments available, the higher
the parallelism of the transfer.   In many cases, Sarracenia manages parallelism
and network usage without explicit user intervention.  As intervening pumps
do not store and forward entire files, the maximum file size which can traverse
the network is maximized.

Where sundew supports a wide variety of file formats, protocols, and conventions 
specific to the real-time meteorology, sarracenia takes a step further away from 
specific applications and is a ruthlessly generic tree replication engine, which 
should allow it to be used in other domains.  The prototype client, dd_subscribe, 
in use since 2013, implements the consumer end of the switch's functions, and is 
the only component present in current packages.  The rest of MetPX-Sarracenia should 
be included in packages by the Spring of 2016.

Sarracenia is expected to be a far simpler application than sundew from every 
point of view: Operator, Developer, Analyst, Data Sources, Data consumers.  
Sarracenia imposes a single interface mechanism, but that mechanism is 
completely portable and generic.  It should run without issue on any modern 
platform (Linux, Windows, Mac)

Sarracenia Documentation
========================

Man Pages
---------

Traditional Unix style manual pages for commands:

  - `sr_subscribe(1) <sr_subscribe.1.html>`_ - the http/https subscription client.
  - `sr_post(1) <sr_post.1.html>`_ - the tool to post individual files.
  - `sr_watch(1) <sr_watch.1.html>`_ - the tool to post all changes to a given directory.
  - `sr_report(1) <sr_report.1.html>`_ - (Does not exist yet!) the tool to read report messages.

administrative daemons:
  - `sr_sarra(8) <sr_sarra.8.html>`_ - Subscribe, Acquire And Re-Advertise...  the main pump.
  - `sr_report2clusters(8) <sr_report2clusters.8.html>`_ - daemon to copy report messages to other clusters.
  - `sr_report2source(8) <sr_report2source.8.html>`_ - daemon to copy report messages to the originating source.

and formats/protocols:

  - `sr_post(7) <sr_post.7.html>`_ - the format of postings.   Posted by watch and post, consumed by subscribe.
  - `sr_report(7) <sr_report.7.html>`_ - the format of report messages.  Sent by consumers, for sources to measure reach.
  - `report2clusters(7) <report2clusters.7.html>`_ - configuration of report routing between clusters.


Why not just use Rsync?
=======================

There are a number of tree replication tools that are widely used, why invent another?  Rsync and other tools are
comparison based (dealing with a single Source and Destination)  Sarracenia, while it does not require or use multi-casting,
is oriented towards a delivery to multiple receivers.  Where rsync synchronization is typically done by walking a
large tree, that means that the synchronization interval is inherently limited to the frequency at which you can
do the file tree walks (in large trees, that can be a long time.) Each file tree walk reads the entire tree
in order to generate signatures, so supporting larger numbers of clients causes large overhead.  Sarracenia avoids 
file tree walks by having writers calculate the checksums once, and signal their activity directly to readers 
by messages, reducing overhead by orders of magnitude.  Lsync is a tool that leverages the INOTIFY features of 
Linux to achieve the same liveness, and it might be more suitable but it is obviously not portable. Doing this 
through the file system is thought to be cumbersome and less general than explicit middleware message passing, 
which also handles the logs in a straight-forward way.

One of the design goals of sarracenia is to be end-to-end.  Rsync is point-to-point, 
meaning it does not support the "transitivity" of transfers across multiple data pumps that 
is desired.  On the other hand, the first use case for Sarracenia is the distribution of 
new files.  Updates to files are not common, and so file deltas are not yet dealt with 
efficiently.  ZSync is much closer in spirit to this use case, and Sarracenia may 
adopt zsync as a means of handling deltas, but it would likely place the signatures in 
the announcements.  Using an announcement per checksummed block allows transfers to be 
parallelized easily.   The use of the AMQP message bus also allows for system-wide 
monitoring to be straight-forward, and to integrate other features such as security 
scanning within the flow transparently. 

MetPX-Sundew
============

MetPX-sundew is a message switching system for use with `World Meteorological Organization (WMO) <http://www.wmo.int>`_ 
`Global Telecommunications System (GTS) <http://www.wmo.ch/pages/prog/www/TEM/XGTS/gts.html>`_ 
circuits based on TCP/IP.  The system is already production quality for a limited set of features and is in production 
use at the CMC as the core of our national switching infrastructure for bulletins, as well as file data (satellite, 
RADAR, numerical outputs, charts & imagery...) It is used to ingest from a NOAAPORT feed, as well as two GTS protocol 
links, feed several hundred clients in both socket and file based feeds, provide Canadian participation 
in `Unidata <http://www.unidata.ucar.edu/>`_ and `TIGGE via an LDM bride <http://tigge.ecmwf.int>`_
as well as `NAEFS <http://www.emc.ncep.noaa.gov/gmb/ens/NAEFS.html>`_ via direct file transfer.
MetPX is unique in its ability to run fine-grained routing with low latency and high performance.  
Developed at the Canadian Meteorological Centre of `Environment Canada <http://www.ec.gc.ca>`_ 
for our own use.  Licensed under GPL for collaborative development, MetPX aims to be 
to meteorological switching what apache is to web serving.

Protocol support:

 - AM (Canadian proprietary socket protocol) 
 - WMO (see manual 386 for the WMO TCP/IP socket protocol.)
 - FTP (for transport, no support for WMO naming yet (but trivial to add.))
 - SFTP (similar to FTP.)
 - AFTN/IP bridge (NavCanada version of AFTN running on IP networks.) 
 - AMQP bridge (open standard protocol, comes from the business messaging world.)


features:

 - detailed routing (in production with 30,000 distinct entries in the routing table.)
 - unified/similar for bulletins and files.
 - sub-second latency (with 28,000 routing entries.)
 - high speed routing and delivery. (was &gt;300 messages per second, but that was a year ago, and many features which might slow it down have been added, a re-test is in order.)
 - no message size limit.
 - message segmentation (for protocols such as AM &amp; WMO which have message length limits.)
 - duplicate suppression (on send.)
 - bulletin collections, NMC function for WMO. 
 - generalized filter mechanism.  (collections will be modified to fit this general mechanism.)

There are three modules in the project right now.  Modules of 
MetPX are named after species of plant which are endangered in 
Canada (see `Species At Risk <http://www.speciesatrisk.gc.ca>`_  for more details.)

 - sundew: the WMO switching component.
 - columbo: the web based monitoring component, for both sundew, and the older (not released) PDS.
 - stats: collection and display of statistics... (ok so it's not a flower...)

Platform: we build packages for Debian Derived Linux (Debian Sarge, Etch. any Ubuntu will do).  
Any modern Linux should do. (stock 2.6 or 2.4 with many patches.)   Python &gt;2.3

Licensing: GPLv2

Sundew Documentation
====================

 - `User's Guide <Guide.html>`_ 
 - `Contributor's Guide <DevGuide.html>`_

Man Pages:

 -  `px.1 <px.1.html>`_ (main startup wrapper)
 -  `pxReceiver.1 <pxReceiver.1.html>`_ 
 -  `pxSender.1 <pxSender.1.html>`_
 -  `pxTranceiver.1 <pxTransceiver.1.html>`_
 -  `pxFilter.1 <pxFilter.1.html>`_
 -  `pxTransmit.1 <pxRetransmit.1.html>`_
 -  `pxRouting.5 <pxRouting.conf.5.html>`_
 -  `pxRouting.7 <pxRouting.7.html>`_



.. _Download: 

Download Packages
=================

[ Downloads_ ]

.. _Downloads: http://sourceforge.net/project/showfiles.php?group_id=165061

Sundew is rather stable for now, current work is on improving the installation process by 
implementing Debian packages.  A package for the sundew module is available from
the sourceforge site, in either source or .deb form.  We hope to produce packages for 
columbo at some point.  


Getting Source Code
===================

Currently internal installations are done, one at a time, from source.  Development
is done on the trunk release.  When we install operationally, the process consists
of creating a branch, and running the branch on a staging system, and then implementing
on operational systems.  There are README and INSTALL files that can be used for 
installation of sundew.  One can follow those instructions to get an initial installed 
system.  

To run sundew, it is critical to install the cron cleanup jobs (mr-clean) since otherwise the 
server will slow down continuously over time until it slows to a crawl.  
It is recommended to subscribe to the mailing list and let us know what is stopping you from 
trying it out, it could inspire us to work on that bit faster to get some collaboration 
going.  

with those explanations, feel free to grab a snapshot can be obtained using subversion via:

    git clone git://git.code.sf.net/p/metpx/git metpx

Available for anonymous read-only access.  One can also obtain a stable release by checking
out a release branch.


AMQP
====

AMQP is the Advanced Message Queuing Protocol, which emerged from the financial trading industry and has gradually 
matured.  Implementations first appeared in 2007, and there are now several open source ones.  AMQP implementations 
are not JMS plumbing.  JMS standardizes the API programmers use, but not the on the wire protocol.  So typically, one cannot 
exchange messages between people using different JMS providers.  AMQP standardizes for interoperability, and functions 
effectively as an interoperability shim for JMS, without being limited to Java.  AMQP is language neutral, and message 
neutral.  there are many deployments using python, C++, and ruby.  One could adapt WMO-GTS protocols very easily to 
function over AMQP.  JMS providers are very Java oriented.

 - `www.amqp.org <http://www.amqp.org>`_  defining AMQP. 
 - `www.openamq.org <http://www.openamq.org>`_ original GPL implementation from JPMorganChase
 - `www.rabbitmq.com <http://www.rabbitmq.com>`_ Another free implementation.  The one we use and are happy with.
 - `Apache Qpid <http://cwiki.apache.org/qpid>`_ yet another free implementation.
 - `Apache ActiveMQ <http://activemq.apache.org/>`_ - This is really a JMS provider with a bridge for AMQP.  They prefer their own openwire protocol. 

Sarracenia relies heavily on the use of brokers and topic based exchanges, which were prominent in AMQP standards efforts prior
to version 1.0, at which point they were removed.  It is hoped that these concepts will be re-introduced at some point.  Until
that time, the application will rely on pre-1.0 standard message brokers, such as rabbitmq.

.. _Links:

References & Links
==================

Other, somewhat similar software, no endorsements or judgements should be taken from these links:

 - Manual on the Global Telecommunications´ System: WMO Manual 386. The standard reference for this domain. (a likely stale copy is  `here <WMO-386.pdf>`_.) Try http://www.wmo.int for the latest version.
 - `Local Data Manager <http://www.unidata.ucar.edu/software/ldm>`_ LDM includes a network protocol, and it fundamentally wishes to exchange with other LDM systems.  This package was instructive in interesting ways, in the early 2000's there was an effort called NLDM which layered meteorological messaging over a standard TCP/IP protocol.  That effort died, however, but the inspiration of keeping the domain (weather) separate from the transport layer (TCP/IP) was an important motivation for MetPX.
 - `Automatic File Distributor  <http://www.dwd.de/AFD>`_ - from the German Weather Service.  Routes files using the transport protocol of the user's choice.  Philosophically close to MetPX.
 - `Corobor <http://www.corobor.com>`_ - commercial WMO switch supplier. 
 - `Netsys  <http://www.netsys.co.za>`_ - commercial WMO switch supplier.
 - `IBLSoft <http://www.iblsoft.com>`_ - commercial WMO switch supplier.
 - variety of file transfer engines: Standard Networks Move IT DMZ, Softlink B-HUB & FEST, Globalscape EFT Server, Axway XFB, Primeur Spazio, Tumbleweed Secure File Transfer, Messageway.
 - `Quantum <https://www.websocket.org/quantum.html>`_ about HTML5 web sockets. A good discussion of why traditional web push is awful, showing how web sockets can help.  AMQP is a pure socket solution that has the same advantages websockets for efficiency. Note: KAAZING wrote the piece, not disinterested.
 - `Rsync  <https://rsync.samba.org/>`_ provides fast incremental file transfer.
 - `Lsyncd <https://code.google.com/p/lsyncd>`_ Live syncing (Mirror) Daemon.
 - `Zsync <http://zsync.moria.org.uk>`_ optimised rsync over HTTP.

