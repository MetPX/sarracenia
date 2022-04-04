========
Overview
========

**MetPX-Sarracenia is a publication/subscription management toolkit for publication of real-time data.**

Sarracenia adds a message queueing protocol layer of file availability notifications to file and web servers to drive workflows that transfer and transform data continuously in a real-time and mission-critical context.

A main goal of the toolkit is to link together processes so that they avoid having to poll (repeatedly query, list, and then filter) servers or directories. Sarracenia can also be used to implement an initial upstream poll, which is still win because tasks beyond initial identification of the file to process can be driven by notifications, which are substantially cheaper (in i/o and processing) than polling even local directories.

This management layer provides simple methods to get parallellism in file transfers, robustness in the face of failures, load balancing among steps in a workflow, and takes care of many failure modes, so application developers do not need to. Hundreds of such flows can be composed together into large data pumps and operated using common methods familiar to Linux System Administrators.

Design Video from 2015: `Sarracenia in 10 Minutes Video <https://www.youtube.com/watch?v=G47DRwzwckk>`_

Longer Overview
---------------

**MetPX-Sarracenia** is a configuration file and command line driven service to download files as they are made available. One can subscribe to a Sarracenia enabled web server (called a data pump) and select data to stream from it, using linux, Mac, or Windows. More than that:

*  It avoids people having to poll the web server to know if their data is there yet (can be 100x less work for client and server from just this).

*  It is faster at downloading by using true pub/sub. It receives notifications exactly when the file is ready.

*  It is naturally parallel: when one process is not enough, just add more. They will share the same selections seamlessly.

*  One can daisy-chain multiple data pumps together, so that people can maintain independent real-time copied trees for service redundancy and also for network topology reasons (to serve private networks, for example).

*  Multiple copies means de-coupled availability. One server being down does not affect the entire web of interlocking APIS. Data pumps form meshes, where the data is transferred so that each one can have a copy if they want it. It's a very simple way to achieve that.

*  It can also push trees (using a sender instead of a subscriber) which is great for transfers across network demarcations (firewalls).

*  Using only configuration, files can be renamed on the fly and the directory structure can be changed completely. 

*  With the extensive plugin API, can transform the tree or the files in the tree. The output tree can bear no resemblance to the input tree.

*  The plugin API can be used to implement efficient data-driven workflows, reducing or eliminating polling of directories and scheduled tasks that impose heavy loads and increase transfer latency.

*  Multi-step workflows are naturally implemented with it as an adjunct of connecting producers with consumers. Transformation is a consumer within the data pump,
   while external consumers access end products. Queues between components provides co-ordination of entire workflows.

*  You can set up a *poll* to make any web site act like a Sarracenia Data pump. So the workflow can work even without a Sarracenia pump to start with.

*  Sarracenia is robust. It operates 24x7 and makes extensive provision to be a civilised participant in mission critical data flows:

   * When a server is down, it uses exponential backoff to avoid punishing it. 
   * When a transfer fails, it is placed in a retry queue. Other transfers continue and the failed transfer is retried later as real-time flows permit.
   * Reliability is tunable for many use cases.

*  Since Sarracenia takes care of transient failures and queueing, your application just deals with normal cases.

*  It uses message queueing protocols (currently AMQP and/or MQTT) to send file advertisements, and file transfers can be done over SFTP, HTTP, or any other web service.

*  It does not depend on any proprietary technologies at all. Completely free to use for any purpose whatever.

*  Is a sample implementation following the `World Meteorological Organizations <WMO>`_ work to replace the Global Teleceommunications System (GTS) with modern solutions.


At its heart, Sarracenia exposes a tree of web accessible folders (WAF), using any standard HTTP server (tested with apache) or SFTP server, with other types of servers as a pluggable option. Weather applications are soft real-time, where data should be delivered as quickly as possible to the next hop, and minutes, perhaps seconds, count. The standard web push technologies, ATOM, RSS, etc... are actually polling technologies that when used in low latency applications consume a great deal of bandwidth and overhead. For exactly these reasons, those standards stipulate a minimum polling interval of five minutes. Advanced Message Queueing Protocol (AMQP) messaging brings true push to notifications, and makes real-time sending far more efficient.

.. image:: Concepts/sr3_flow_example.svg
    :scale: 100%
    :align: center

Sources of data announce their products, pumping systems pull the data using HTTP or SFTP onto their WAF trees, and then announce their trees for downstream clients. When clients download data, they may write a report message back to the server. Servers are configured to forward those client report messages back through the intervening servers to the source. The Source can see the entire path that the data took to get to each client. With traditional data switching applications, sources only see that they delivered to the first hop in a chain. Beyond that first hop, routing is opaque, and tracing the path of data required assistance from administrators of each intervening system. With Sarracenia's report forwarding, the switching network is relatively transparent to the sources. Diagnostics are vastly simplified.


For large files / high performance, files are segmented on ingest if they are sufficiently large to make this worthwhile. Each file can traverse the data pumping network independently, and reassembly is only needed at end points. A file of sufficient size will announce the availability of several segments for transfer, multiple threads or transfer nodes will pick up segments and transfer them. The more segments available, the higher the parallelism of the transfer. In many cases, Sarracenia manages parallelism and network usage without explicit user intervention. As intervening pumps do not store and forward entire files, the maximum file size which can traverse the network is maximized.

* **NOTE:** For v03, segmentation functionality was removed temporarily. Planned to return in version 3.1.


Implementations
---------------

Part of Sarracenia defines an application layer message over AMQP as a transport. Sarracenia has multiple implementations:

- Sarracenia itself ( http://github.com/MetPX/sarracenia ) a complete reference implementation in Python >= 3.4. It runs on Linux, Mac, and Windows.

- sarrac ( https://github.com/MetPX/sarrac ) is a C implementation of data insertion (post & watch). It is Linux only. There is also a libcshim to be able to tranparently implement data insertion with this tool, and libsarra allows C programs to post directly. There is consumer code as well (to read queues) but no downloading so far. This subset is meant to be used where python3 environments are impractical (some HPC environments). 

- node-sarra ( https://github.com/darkskyapp/node-sarra ) An embryonic v2 implementation for node.js.

- ecpush ( https://github.com/TheTannerRyan/ecpush ) an simple v2 client in Go ( http://golang.org ) 

- dd_subscribe ( https://github.com/MetPX/sarracenia ) python2 stripped-down download-only v2 client.  The predecessor of Sarracenia. Still compatible. TODO fix link

- PySarra ( https://github.com/JohnTheNerd/PySarra ) a very dumbed-down v2 client for python3, allowing you to abstract away all the complexity.

More implementations are welcome.


Why Not Just Use Rsync?
~~~~~~~~~~~~~~~~~~~~~~~

There are a number of tree replication tools that are widely used, why invent another? `RSync <https://rsync.samba.org/>`_, for example is a fabulous tool, and we 
recommend it highly for many use cases. But there are times when Sarracenia can go 72 times faster than rsync: Case Study: `HPC Mirroring Use Case <History/hpc_mirroring_use_case.html>`_

Rsync and other tools are comparison based (dealing with a single Source and Destination). Sarracenia, while it does not require or use multi-casting, is oriented towards delivery to multiple receivers, particularly when the source does not know who all the receivers are (pub/sub). Where rsync synchronization is typically done by walking a large tree, that means that the synchronization interval is inherently limited to the frequency at which you can do the file tree walks (in large trees, that can be a long time.) Each file tree walk reads the entire tree in order to generate signatures, so supporting larger numbers of clients causes 
large overhead. Sarracenia avoids file tree walks by having writers calculate the checksums once, and signal their activity directly to readers by messages, reducing overhead by orders of magnitude. `Lsyncd <https://github.com/axkibe/lsyncd>`_ is a tool that leverages the INOTIFY features of Linux to achieve the same liveness, and it might be more suitable but it is obviously not portable. Doing this through the file system is thought to be cumbersome and less general than explicit middleware message passing, which also handles the logs in a straight-forward way.

One of the design goals of Sarracenia is to be end-to-end. Rsync is point-to-point, meaning it does not support the *transitivity* of transfers across multiple data pumps that is desired. On the other hand, the first use case for Sarracenia is the distribution of new files. Updates to files were not common initially. `ZSync <https://zsync.moria.org.uk>`_ is much closer in spirit to this use case. Sarracenia now has a similar approach based on file partitions (or blocks), but with user selectable size (50M is a good choice), generally much larger than Zsync blocks (typically 4k), more amenable to acceleration. Using an announcement per checksummed block allows transfers to be accelerated more easily. 

The use of the AMQP message bus enables use of flexible third party transfers, straight-forward system-wide monitoring and integration of other features such as security scanning within the flow.

Another consideration is that Sarracenia doesn't actually implement any transport. It is completely agnostic to the actual protocol used to tranfer data. Once can post arbitrary protocol URLs, and add plugins to work with those arbitrary protocols, or substitute accelerated downloaders to deal with certain types of downloads. The built-in transfer drivers include binary accellerators and tunable criteria for using them.

**Caveat file segmentation was dropped. FIXME**

.. TODO: All the links above are broken?

Why No FTP?
~~~~~~~~~~~

The transport protocols fully supported by Sarracenia are http(s) and SFTP (SSH File Transfer Protocol). In many cases, when public data is being exchanged, `FTP <https://tools.ietf.org/html/rfc959>`_ is a lingua franca that is used. The main advantage being relatively simple programmatic access, but that advantage is obviated by the use of Sarracenia itself. Further, these days, with increased security concerns, and with cpu instructions for encryption and multiple cores something of a cpu glut, it no longer makes much sense not to encrypt traffic. Additionally, to support multi-streaming, Sarracenia makes use of byte-ranges, which are provided by SFTP and HTTP servers, but not FTP. So we cannot support file partitioning on FTP. So while FTP sort-of-works, it is not now, nor ever will be, fully supported.


References & Links
~~~~~~~~~~~~~~~~~~

Other, somewhat similar software, no endorsements or judgements should be taken from these links:

- `Local Data Manager <https://www.unidata.ucar.edu/software/ldm>`_ LDM includes a network protocol, and it fundamentally wishes to exchange with other LDM systems.  This package was instructive in interesting ways, in the early 2000's there was an effort called NLDM which layered meteorological messaging over a standard TCP/IP protocol.  That effort died, however, but the inspiration of keeping the domain (weather) separate from the transport layer (TCP/IP) was an important motivation for MetPX.
- `Automatic File Distributor  <https://www.dwd.de/AFD>`_ - from the German Weather Service.  Routes files using the transport protocol of the user's choice.  Philosophically close to MetPX Sundew.
- `Corobor <https://www.corobor.com>`_ - commercial WMO switch supplier. 
- `Netsys  <https://www.netsys.co.za>`_ - commercial WMO switch supplier.
- `IBLSoft <https://www.iblsoft.com>`_ - commercial WMO switch supplier.
- variety of file transfer engines: Standard Networks Move IT DMZ, Softlink B-HUB & FEST, Globalscape EFT Server, Axway XFB, Primeur Spazio, Tumbleweed Secure File Transfer, Messageway.
- `Quantum <https://www.websocket.org/quantum.html>`_ about HTML5 web sockets. A good discussion of why traditional web push is awful, showing how web sockets can help.  AMQP is a pure socket solution that has the same advantages websockets for efficiency. Note: KAAZING wrote the piece, not disinterested.
- `Rsync  <https://rsync.samba.org/>`_ provides fast incremental file transfer.
- `Lsyncd <https://github.com/axkibe/lsyncd>`_ Live syncing (Mirror) Daemon.
- `Zsync <https://zsync.moria.org.uk>`_ optimised rsync over HTTP.
