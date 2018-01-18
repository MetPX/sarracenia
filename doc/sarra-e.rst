==========
Sarracenia
==========

.. contents::

**MetPX-Sarracenia** is a data duplication or distribution engine that leverages existing
standard technologies (web servers and the AMQP_ brokers) to achieve real-time message
delivery and end to end transparency in file transfers.  Whereas in Sundew, each switch
is a standalone configuration which transforms data in complex ways, in Sarracenia, the
data sources establish a file tree hierarchy which is carried through any number of intervening 
pumps until they arrive at a client.  The client can provide explicit acknowledgement that
propagates back through the network to the source.  Whereas traditional file switching
is a point-to-point affair where knowledge is only between each segment, in Sarracenia,
information flows from end to end in both directions.

Overview
--------

At it's heart, sarracenia exposes a tree of web accessible folders (WAF), using any
standard HTTP server (tested with apache) or SFTP server, with other types of servers as
a pluggable option.  Weather applications are soft real-time, where data should be delivered 
as quickly as possible to the next hop, and minutes, perhaps seconds, count.  The 
standard web push technologies, ATOM, RSS, etc... are actually polling technologies 
that when used in low latency applications consume a great deal of bandwidth and overhead.  
For exactly these reasons, those standards stipulate a minimum polling interval of five 
minutes.   Advanced Message Queueing Protocol (AMQP) messaging brings true push 
to notifications, and makes real-time sending far more efficient.

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

Where Sundew supports a wide variety of file formats, protocols, and conventions
specific to the real-time meteorology, sarracenia takes a step further away from
specific applications and is a ruthlessly generic tree replication engine, which
should allow it to be used in other domains.  The initial prototype client, dd_subscribe,
in use since 2013, was replaced in 2016 by the full blown sarracenia package,
with all components necessary for production as well as consumption of file trees.

Sarracenia is expected to be a far simpler application than sundew from every
point of view: Operator, Developer, Analyst, Data Sources, Data consumers.
Sarracenia imposes a single interface mechanism, but that mechanism is
completely portable and generic.  It should run without issue on any modern
platform (Linux, Windows, Mac)

For more information about Sarra, Please proceed to the `documentation <sarra-docs-e.html>`_

Implementations
---------------

Part of Sarracenia defines an application layer message over AMQP as a transport.  
Sarracenia's has multiple implementations:

- Sarracenia itself ( http://metpx.sf.net ) a complete reference implementation in Python >= 3.4.  It runs on Linux, Mac, and Windows.

- csarra (c subdirectory in the main git repo) is a C implementation of data insertion (post & watch.)  It is Linux only.  There is also a libcshim to be able to tranparently implement data insertion with this tool, and libsarra allows C programs to post directly.  There is consumer code as well (to read queues) but no downloading so far.  This subset is meant to be used where python3 environments are impractical (some HPC environments.) 

- node-sarra ( https://github.com/darkskyapp/node-sarra ) An embryonic implementation  for node.js.

More implementations are welcome.


The Python Implementation
-------------------------

Another part of Sarracenia is the python version which is where prototyping of features
and all deployments have occurred so far.

.. table:: **Table 1: The Algorithm for All Components**
 :align: center

 +----------+-------------------------------------------------------------+
 |          |                                                             |
 |  PHASE   |                 DESCRIPTION                                 |
 |          |                                                             |
 +----------+-------------------------------------------------------------+
 | *List*   | Get information about an initial list of files              |
 |          |                                                             |
 |          | from: a queue, a directory, a polling script.               |
 +----------+-------------------------------------------------------------+
 | *Filter* | Reduce the list of files to act on.                         |
 |          |                                                             |
 |          | Apply accept/reject clauses                                 |
 |          |                                                             |
 |          | Check duplicate receipt cache                               |
 |          |                                                             |
 |          | run on_msg scripts                                          |
 +----------+-------------------------------------------------------------+
 | *Do*     | process the message by downloading or sending               |
 |          |                                                             |
 |          | run do_send,do_download                                     |
 |          |                                                             |
 |          | run on_part,on_file (download only)                         |
 +----------+-------------------------------------------------------------+
 | *Post*   | run on_post scripts                                         |
 |          |                                                             |
 |          | Post announcement of file downloads/sent to post_broker     |
 +----------+-------------------------------------------------------------+
 | *Report* | Post report of action to origin (to inform source)          |
 +----------+-------------------------------------------------------------+

The main components of the python implementation of Sarracenia all implement the same 
algorithm described above.  The algorithm has various points where custom processing
can be inserted using small python scripts called on_*, do_*.

The components just have different default settings:

.. table:: **Table 2: How Each Component Uses the Common Algorithm**  
 :align: center

 +------------------------+--------------------------+
 | Component              | Use of the algorithm     |
 +------------------------+--------------------------+
 | *sr_subscribe*         | List=read from queue     |
 |                        |                          |
 |   Download file from a | Filter                   |
 |   pump. If the local   |                          |
 |   host is a pump,      | Do=Download              |
 |   post the downloaded  |                          |
 |   file.                | Post=optional            |
 |                        |                          |
 |                        | Report=optional          |
 |                        |                          |
 +------------------------+--------------------------+
 | *sr_poll*              | List=run do_poll script  |
 |                        |                          |
 |   Find files on other  | Filter                   |
 |   servers to post to   |                          |
 |   a pump.              | Do=nil                   |
 |                        |                          |
 |                        | Post=yes                 |
 |                        |                          |
 |                        | Report=no                |
 +------------------------+--------------------------+
 | *sr_shovel/sr_winnow*  | List=read from queue     |
 |                        |                          |
 |   Move posts or        | Filter (shovel cache=off)|
 |   reports around.      |                          |
 |                        | Do=nil                   |
 |                        |                          |
 |                        | Post=yes                 |
 |                        |                          |
 |                        | Report=optional          |
 +------------------------+--------------------------+
 | *sr_post/watch*        | List=read file system    |
 |                        |                          |
 |   Find file on a       | Filter                   |
 |   local server to      |                          |
 |   post                 | Do=nil                   |
 |                        |                          |
 |                        | Post=yes                 |
 |                        |                          |
 |                        | Report=no                |
 +------------------------+--------------------------+
 | *sr_sender*            | List=read queue          |
 |                        |                          |
 |   Send files from a    | Filter                   |
 |   pump. If remote is   |                          |
 |   also a pump, post    | Do=sendfile              |
 |   the sent file there. |                          |
 |                        | Post=optional            |
 |                        |                          |
 |                        | Report=optional          |
 +------------------------+--------------------------+

Components are easily composed using AMQP brokers, which create elegant networks
of communicating sequential processes. (in the `Hoare <http://dl.acm.org/citation.cfm?doid=359576.359585>`_ sense)


Why Not Just Use Rsync?
-----------------------

There are a number of tree replication tools that are widely used, why invent another?  
RSync, for example is a fabulous tool, and we recommend it highly for many use cases.  but there are times
when Sarracenia can go 72 times faster than rsync: Case Study: `HPC Mirroring Use Case <mirroring_use_case.html>`_

Rsync and other tools are comparison based (dealing with a single Source and Destination) Sarracenia, while it does 
not require or use multi-casting, is oriented towards a delivery to multiple receivers, particularly when the source
does not know who all the receivers are (pub/sub.) Where rsync synchronization is typically done by walking a 
large tree, that means that the synchronization interval is inherently limited to the frequency at which you 
can do the file tree walks (in large trees, that can be a long time.) Each file tree walk reads 
the entire tree in order to generate signatures, so supporting larger numbers of clients causes 
large overhead. Sarracenia avoids file tree walks by having writers calculate the checksums once, and 
signal their activity directly to readers by messages, reducing overhead by orders of magnitude.  Lsync 
is a tool that leverages the INOTIFY features of Linux to achieve the same liveness, and it might be more 
suitable but it is obviously not portable. Doing this through the file system is thought to be cumbersome 
and less general than explicit middleware message passing, which also handles the logs in a straight-forward way.

One of the design goals of sarracenia is to be end-to-end. Rsync is point-to-point,
meaning it does not support the *transitivity* of transfers across multiple data pumps that
is desired. On the other hand, the first use case for Sarracenia is the distribution of
new files. Updates to files are not common, and so file deltas are not yet dealt with
efficiently. ZSync is much closer in spirit to this use case. Sarracenia has a similar
approach based on file partitions, but user settable to much larger than Zsync blocks, more
amenable to accelleration. Using an announcement per checksummed block allows transfers to be 
parallelized easily. 

The use of the AMQP message bus also allows for completely flexible third party transfers to be configured
and for system-wide monitoring to be straight-forward, and to easily integrate other features such as security
scanning within the flow.

Another consideration is that Sarracenia doesn't actually implement any transport. It is completely agnostic 
to the actual protocol used to tranfer data. Once can post arbitrary protocol URLs, and add plugins to work 
with those arbitrary protocols, or substitute accellerated downloaders to deal with certain types of downloads. 
The download_scp plugin, included with the package, shows the use of the built-in python transfer mechanisms, 
but the simple use of a binary to accellerate downloads when the file exceeds a threshold size, making that 
method more efficient. Use of another compatible binary, such as BBCP, is also straightforward.



Why No FTP?
-----------

The transport protocols fully supported by sarracenia are http(s) and SFTP (SSH File Transfer Protocol.)
In many cases, when public data is being exchanged, FTP is a lingua franca that is used.  The main advantage
being relatively simple programmatic access, but that advantage is obviated by the use of sarracenia itself.
Further, these days, with increased security concerns, and with cpu power becoming extremely available, it
no longer makes much sense not to encrypt traffic.   Additionally, to support multi-streaming, sarracenia
makes use of byte-ranges, which are provided by SFTP and HTTP servers, but not FTP.  So we cannot support
file partitioning on FTP.  So while FTP sort-of-works, it is not now, nor ever will be, fully supported.



AMQP
----

AMQP is the Advanced Message Queuing Protocol, which emerged from the financial trading industry and has gradually
matured.  Implementations first appeared in 2007, and there are now several open source ones.  AMQP implementations
are not JMS plumbing.  JMS standardizes the API programmers use, but not the on the wire protocol.  So 
typically, one cannot exchange messages between people using different JMS providers.  AMQP standardizes 
for interoperability, and functions effectively as an interoperability shim for JMS, without being 
limited to Java.  AMQP is language neutral, and message neutral.  there are many deployments using 
python, C++, and ruby.  One could adapt WMO-GTS protocols very easily to function over AMQP.  JMS 
providers are very Java oriented.


* `www.amqp.org <http://www.amqp.org>`_  - Defining AMQP.
* `www.openamq.org <http://www.openamq.org>`_ - Original GPL implementation from JPMorganChase
* `www.rabbitmq.com <http://www.rabbitmq.com>`_ - Another free implementation.  The one we use and are happy with.
* `Apache Qpid <http://cwiki.apache.org/qpid>`_ - Yet another free implementation.
* `Apache ActiveMQ <http://activemq.apache.org/>`_ - This is really a JMS provider with a bridge for AMQP. They prefer their own openwire protocol.

Sarracenia relies heavily on the use of brokers and topic based exchanges, which were prominent in AMQP standards efforts prior
to version 1.0, at which point they were removed.  It is hoped that these concepts will be re-introduced at some point.  Until
that time, the application will rely on pre-1.0 standard message brokers, such as rabbitmq.

Downloading Sarracenia
----------------------

Steps for downloading the latest version of Sarracenia are available on our `downloads page <download-e.html>`_ .

Getting The Source Code
-----------------------

The source code is available from our `git repository <https://sourceforge.net/p/metpx/sarracenia/ci/master/tree/>`_ .

Documentation
-------------

The documentation for Sarracenia can be found on our `documentation page <sarra-docs-e.html>`_ .
