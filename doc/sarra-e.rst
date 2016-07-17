==========
Sarracenia
==========

.. contents::
            
**MetPX-Sarracenia** is a data duplication or distribution engine that leverages existing
standard technologies (web servers and the AMQP_ brokers) to achieve real-time message
delivery and end to end transparency in file transfers.  Whereas in Sundew, each switch
is a standalone configuration which transforms data in complex ways, in sarracenia, the
data sources establish a structure which is carried through any number of intervening pumps
until they arrive at a client.  The client can provide explicit acknowledgement that
propagates back through the network to the source.  Whereas traditional file switching
is a point-to-point affair where knowledge is only between each segment, in Sarracenia,
information flows from end to end in both directions.
                    
Overview
--------

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

For more information about Sarra, Please proceed to the `documentation <sarra-docs-e.html>`_


Why Not Just Use Rsync?
-----------------------

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
meaning it does not support the &quot;transitivity&quot; of transfers across multiple data pumps that
is desired.  On the other hand, the first use case for Sarracenia is the distribution of
new files.  Updates to files are not common, and so file deltas are not yet dealt with
efficiently.  ZSync is much closer in spirit to this use case, and Sarracenia may
adopt zsync as a means of handling deltas, but it would likely place the signatures in
the announcements.  Using an announcement per checksummed block allows transfers to be
parallelized easily.   The use of the AMQP message bus also allows for system-wide
monitoring to be straight-forward, and to integrate other features such as security
scanning within the flow transparently.


Why No FTP?
-----------

The transport protocols fully supported by sarracenia are http(s) and SFTP (SSH File Transfer Protocol.)  
In many cases, when public data is being exchanged, FTP is a lingua franca that is used.  The main advantage
being relatively simple programmatic access, but that advantage is obviated by the use of sarracenia itself.
Further, these days, with increased security concerns, and with cpu power becoming extremely available, it 
no longer makes much sense not to encrypt traffic.   Additionally, to support multi-streaming, sarracenia 
makes use of byte-ranges, which are provided by SFTP and HTTP servers, but not FTP.  So we cannot support 
file partitioning on FTP.  So while FTP sort-of-works, it is not now and never will be fully supported, 
and the partial support that is there is not recommended.

AMQP
----

AMQP is the Advanced Message Queuing Protocol, which emerged from the financial trading industry and has gradually
matured.  Implementations first appeared in 2007, and there are now several open source ones.  AMQP implementations
are not JMS plumbing.  JMS standardizes the API programmers use, but not the on the wire protocol.  So typically, one cannot
exchange messages between people using different JMS providers.  AMQP standardizes for interoperability, and functions
effectively as an interoperability shim for JMS, without being limited to Java.  AMQP is language neutral, and message
neutral.  there are many deployments using python, C++, and ruby.  One could adapt WMO-GTS protocols very easily to
function over AMQP.  JMS providers are very Java oriented.


* `www.amqp.org <http://www.amqp.org>`_  - Defining AMQP.
* `www.openamq.org <http://www.openamq.org>`_ - Original GPL implementation from JPMorganChase
* `www.rabbitmq.com <http://www.rabbitmq.com>`_ - Another free implementation.  The one we use and are happy with.
* `Apache Qpid <http://cwiki.apache.org/qpid>`_ - Yet another free implementation.
* `Apache ActiveMQ <http://activemq.apache.org/>`_ - This is really a JMS provider with a bridge for AMQP. They prefer their own openwire protocol.

Sarracenia relies heavily on the use of brokers and topic based exchanges, which were prominent in AMQP standards efforts prior
to version 1.0, at which point they were removed.  It is hoped that these concepts will be re-introduced at some point.  Until 
that time, the application will rely on pre-1.0 standard message brokers, such as rabbitmq.
