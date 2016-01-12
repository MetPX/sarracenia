======
Sundew
======

.. contents::

**MetPX-sundew** is a message switching system for use with `World Meteorological Organization (WMO) <http://www.wmo.int>`_ 
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

Protocol support
----------------

- AM (Canadian proprietary socket protocol) 
- WMO (see manual 386 for the WMO TCP/IP socket protocol.)
- FTP (for transport, no support for WMO naming yet (but trivial to add.))
- SFTP (similar to FTP.)
- AFTN/IP bridge (NavCanada version of AFTN running on IP networks.) 
- AMQP bridge (open standard protocol, comes from the business messaging world.)


Features
--------

- detailed routing (in production with 30,000 distinct entries in the routing table.)
- unified/similar for bulletins and files.
- sub-second latency (with 28,000 routing entries.)
- high speed routing and delivery. (was &gt;300 messages per second, but that was a year ago, and many features which might slow it down have been added, a re-test is in order.)
- no message size limit.
- message segmentation (for protocols such as AM &amp; WMO which have message length limits.)
- duplicate suppression (on send.)
- bulletin collections, NMC function for WMO. 
- generalized filter mechanism.  (collections will be modified to fit this general mechanism.)

Modules
-------
There are three modules in the project right now.  Modules of 
MetPX are named after species of plant which are endangered in 
Canada (see `Species At Risk <http://www.speciesatrisk.gc.ca>`_  for more details.)

- sundew: the WMO switching component.
- columbo: the web based monitoring component, for both sundew, and the older (not released) PDS.
- stats: collection and display of statistics... (ok so it's not a flower...)

Platform
--------

We build packages for Debian Derived Linux (Debian Sarge, Etch. any Ubuntu will do).  
Any modern Linux should do. (stock 2.6 or 2.4 with many patches.)   Python > 2.3

Licensing: GPLv2


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