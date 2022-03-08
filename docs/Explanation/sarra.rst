==========
Sarracenia
==========

[ `version française <fr/sarra.rst>`_ ]
TODO: Coming soon..

.. contents::

**MetPX-Sarracenia** is a data duplication or distribution engine that leverages existing
standard technologies (file and web servers and AMQP_ brokers) to achieve real-time message
delivery and end to end transparency in file transfers. Whereas in Sundew, each switch
is a standalone configuration which transforms data in complex ways, in Sarracenia, the
data sources establish a file tree hierarchy which is carried through any number of intervening 
pumps until they arrive at a client. The client can provide explicit acknowledgement that
propagates back through the network to the source. Whereas traditional file switching
is a point-to-point affair where knowledge is only between each segment, in Sarracenia,
information flows from end to end in both directions.

Overview
--------


At its heart, Sarracenia exposes a tree of web accessible folders (WAF), using any
standard HTTP server (tested with apache) or SFTP server, with other types of servers as
a pluggable option. Weather applications are soft real-time, where data should be delivered 
as quickly as possible to the next hop, and minutes, perhaps seconds, count. The 
standard web push technologies, ATOM, RSS, etc... are actually polling technologies 
that when used in low latency applications consume a great deal of bandwidth and overhead.
For exactly these reasons, those standards stipulate a minimum polling interval of five 
minutes. Advanced Message Queueing Protocol (AMQP) messaging brings true push 
to notifications, and makes real-time sending far more efficient.

.. image:: Concepts/e-ddsr-components.jpg

Sources of data announce their products, pumping systems pull the data using HTTP
or SFTP onto their WAF trees, and then announce their trees for downstream clients.
When clients download data, they may write a report message back to the server. Servers
are configured to forward those client report messages back through the intervening
servers back to the source. The Source can see the entire path that the data took
to get to each client. With traditional switching applications, sources only see
that they delivered to the first hop in a chain. Beyond that first hop, routing is
opaque, and tracing the path of data required assistance from administrators of each
intervening system. With Sarracenia's report forwarding, the switching network is
relatively transparent to the sources. Diagnostics are vastly simplified.

For large files / high performance, files are segmented on ingest if they are sufficiently
large to make this worthwhile. Each file can traverse the data pumping network independently,
and reassembly is only needed at end points. A file of sufficient size will announce
the availability of several segments for transfer, multiple threads or transfer nodes
will pick up segments and transfer them. The more segments available, the higher
the parallelism of the transfer. In many cases, Sarracenia manages parallelism
and network usage without explicit user intervention. As intervening pumps
do not store and forward entire files, the maximum file size which can traverse
the network is maximized.

Where Sundew supports a wide variety of file formats, protocols, and conventions
specific to the real-time meteorology, Sarracenia takes a step further away from
specific applications and is a ruthlessly generic tree replication engine, which
should allow it to be used in other domains. The initial prototype client, dd_subscribe,
in use since 2013, was replaced in 2016 by the full blown Sarracenia package,
with all components necessary for production as well as consumption of file trees.

Sarracenia is expected to be a far simpler application than sundew from every
point of view: Operator, Developer, Analyst, Data Sources, Data Consumers.
Sarracenia imposes a single interface mechanism, but that mechanism is
completely portable and generic. It should run without issue on any modern
platform (Linux, Windows, Mac).

For more information about Sarra, view the
`Sarracenia in 10 Minutes Video <https://www.youtube.com/watch?v=G47DRwzwckk>`_
or proceed to the detailed `documentation <../Reference/sr3.1.rst#documentation>`_

Implementations
---------------

Part of Sarracenia defines an application layer message over AMQP as a transport.
Sarracenia has multiple implementations:

- Sarracenia itself ( http://github.com/MetPX/sarracenia ) a complete reference implementation in Python >= 3.4. It runs on Linux, Mac, and Windows.

- sarrac ( https://github.com/MetPX/sarrac ) is a C implementation of data insertion (post & watch). It is Linux only. There is also a libcshim to be able to tranparently implement data insertion with this tool, and libsarra allows C programs to post directly. There is consumer code as well (to read queues) but no downloading so far. This subset is meant to be used where python3 environments are impractical (some HPC environments). 

- node-sarra ( https://github.com/darkskyapp/node-sarra ) An embryonic implementation for node.js.

- ecpush ( https://github.com/TheTannerRyan/ecpush ) an simple client in Go ( http://golang.org ) 

- dd_subscribe ( https://github.com/MetPX/sarracenia ) python2 stripped-down download-only client.  The predecessor of Sarracenia. Still compatible.

- PySarra ( https://github.com/JohnTheNerd/PySarra ) a very dumbed-down client for python3, allowing you to abstract away all the complexity.

More implementations are welcome.

Downloading Sarracenia
----------------------

Steps for downloading the latest version of Sarracenia are available on our `downloads page <../Tutorials/Install.rst>`_ .

Getting The Source Code
-----------------------

The source code is available from our `git repository <https://github.com/MetPX/sarracenia>`_ .

Documentation
-------------

The documentation for Sarracenia can be found on our `documentation <../Reference/sr3.1.rst#documentation>`_ .


Deployments/Use Cases
---------------------

Deployment status in 2015: `Sarracenia in 10 Minutes Video (5:26 in) <https://www.youtube.com/watch?v=G47DRwzwckk&t=326s>`_

Deployment status in 2018: `Deployments as of January 2018 <../../doc/deployment_2018.rst>`_

Mailing Lists
-------------

* `metpx-devel <http://lists.sourceforge.net/lists/listinfo/metpx-devel>`_  : Discussions about development. 
* `metpx-commit <http://lists.sourceforge.net/lists/listinfo/metpx-commit>`_ : Shows logs of commits to the repository


Why?
----

Why Not Just Use Rsync?
~~~~~~~~~~~~~~~~~~~~~~~

There are a number of tree replication tools that are widely used, why invent another?
`RSync <https://rsync.samba.org/>`_, for example is a fabulous tool, and we 
recommend it highly for many use cases. But there are times when Sarracenia can
go 72 times faster than rsync: Case Study: `HPC Mirroring Use Case <hpc_mirroring_use_case.rst>`_

Rsync and other tools are comparison based (dealing with a single Source and Destination). Sarracenia, while it does 
not require or use multi-casting, is oriented towards delivery to multiple receivers, particularly when the source
does not know who all the receivers are (pub/sub). Where rsync synchronization is typically done by walking a 
large tree, that means that the synchronization interval is inherently limited to the frequency at which you 
can do the file tree walks (in large trees, that can be a long time.) Each file tree walk reads 
the entire tree in order to generate signatures, so supporting larger numbers of clients causes 
large overhead. Sarracenia avoids file tree walks by having writers calculate the checksums once, and 
signal their activity directly to readers by messages, reducing overhead by orders of magnitude. 
`Lsyncd <https://github.com/axkibe/lsyncd>`_ is a tool that leverages the INOTIFY features of Linux 
to achieve the same liveness, and it might be more suitable but it is obviously not portable.
Doing this through the file system is thought to be cumbersome and less general than explicit
middleware message passing, which also handles the logs in a straight-forward way.

One of the design goals of Sarracenia is to be end-to-end. Rsync is point-to-point,
meaning it does not support the *transitivity* of transfers across multiple data pumps that
is desired. On the other hand, the first use case for Sarracenia is the distribution of
new files. Updates to files were not common initially. `ZSync <http://zsync.moria.org.uk/>`_ 
is much closer in spirit to this use case. Sarracenia now has a similar 
approach based on file partitions (or blocks), but with user selectable size
(50M is a good choice), generally much larger than Zsync blocks (typically 4k),
more amenable to acceleration. Using an announcement per checksummed block 
allows transfers to be accelerated more easily. 

The use of the AMQP message bus enables use of flexible third party transfers,
straight-forward system-wide monitoring and integration of other features such as security
scanning within the flow.

Another consideration is that Sarracenia doesn't actually implement any transport. It is completely agnostic 
to the actual protocol used to tranfer data. Once can post arbitrary protocol URLs, and add plugins to work 
with those arbitrary protocols, or substitute accelerated downloaders to deal with certain types of downloads. 
The `download_scp <download_scp.py>`_ plugin, included with the package, shows
the use of the built-in python transfer mechanisms, but the simple use of a 
binary to accellerate downloads when the file exceeds a threshold size, making
that method more efficient. Use of another compatible binary, such as `dd <download_dd.py>`_ or 
`cp <accel_cp.py>`_, (for local files), `scp <download_scp.py>`_, or `wget <accel_wget.py>`_ via 
plugins is also straightforward.

.. TODO: All the links above are broken?

Why No FTP?
~~~~~~~~~~~

The transport protocols fully supported by Sarracenia are http(s) and SFTP (SSH File Transfer Protocol).
In many cases, when public data is being exchanged, `FTP <https://tools.ietf.org/html/rfc959>`_ 
is a lingua franca that is used. The main advantage being relatively simple
programmatic access, but that advantage is obviated by the use of Sarracenia
itself. Further, these days, with increased security concerns, and with cpu
instructions for encryption and multiple cores something of a cpu glut, 
it no longer makes much sense not to encrypt traffic. Additionally, to 
support multi-streaming, Sarracenia makes use of byte-ranges, which are
provided by SFTP and HTTP servers, but not FTP. So we cannot support file 
partitioning on FTP. So while FTP sort-of-works, it is not now, nor ever will
be, fully supported.


AMQP
~~~~

AMQP is the Advanced Message Queuing Protocol, which emerged from the financial trading industry and has gradually
matured. Implementations first appeared in 2007, and there are now several open source ones. AMQP implementations
are not JMS plumbing. JMS standardizes the API programmers use, but not the on-the-wire protocol. So 
typically, one cannot exchange messages between people using different JMS providers. AMQP standardizes 
for interoperability, and functions effectively as an interoperability shim for JMS, without being 
limited to Java. AMQP is language neutral, and message neutral. There are many deployments using 
Python, C++, and Ruby. One could adapt WMO-GTS protocols very easily to function over AMQP. JMS 
providers are very Java oriented.


* `www.amqp.org <http://www.amqp.org>`_ - Defining AMQP.
* `www.openamq.org <http://www.openamq.org>`_ - Original GPL implementation from JPMorganChase
* `www.rabbitmq.com <http://www.rabbitmq.com>`_ - Another free implementation. The one we use and are happy with.
* `Apache Qpid <http://cwiki.apache.org/qpid>`_ - Yet another free implementation.
* `Apache ActiveMQ <http://activemq.apache.org/>`_ - This is really a JMS provider with a bridge for AMQP. They prefer their own openwire protocol.

Sarracenia relies heavily on the use of brokers and topic based exchanges, which were prominent in AMQP standards efforts prior
to version 1.0, at which point they were removed. It is hoped that these concepts will be re-introduced at some point. Until
that time, the application will rely on pre-1.0 standard message brokers, such as rabbitmq.


References & Links
~~~~~~~~~~~~~~~~~~

Other, somewhat similar software, no endorsements or judgements should be taken from these links:

- Manual on the Global Telecommunications´ System: WMO Manual 386. The standard reference for this domain. (a likely stale copy is  `here <WMO-386.pdf>`_.) Try http://www.wmo.int for the latest version.
- `Local Data Manager <http://www.unidata.ucar.edu/software/ldm>`_ LDM includes a network protocol, and it fundamentally wishes to exchange with other LDM systems.  This package was instructive in interesting ways, in the early 2000's there was an effort called NLDM which layered meteorological messaging over a standard TCP/IP protocol.  That effort died, however, but the inspiration of keeping the domain (weather) separate from the transport layer (TCP/IP) was an important motivation for MetPX.
- `Automatic File Distributor  <http://www.dwd.de/AFD>`_ - from the German Weather Service.  Routes files using the transport protocol of the user's choice.  Philosophically close to MetPX Sundew.
- `Corobor <http://www.corobor.com>`_ - commercial WMO switch supplier. 
- `Netsys  <http://www.netsys.co.za>`_ - commercial WMO switch supplier.
- `IBLSoft <http://www.iblsoft.com>`_ - commercial WMO switch supplier.
- variety of file transfer engines: Standard Networks Move IT DMZ, Softlink B-HUB & FEST, Globalscape EFT Server, Axway XFB, Primeur Spazio, Tumbleweed Secure File Transfer, Messageway.
- `Quantum <https://www.websocket.org/quantum.html>`_ about HTML5 web sockets. A good discussion of why traditional web push is awful, showing how web sockets can help.  AMQP is a pure socket solution that has the same advantages websockets for efficiency. Note: KAAZING wrote the piece, not disinterested.
- `Rsync  <https://rsync.samba.org/>`_ provides fast incremental file transfer.
- `Lsyncd <https://github.com/axkibe/lsyncd>`_ Live syncing (Mirror) Daemon.
- `Zsync <http://zsync.moria.org.uk>`_ optimised rsync over HTTP.
