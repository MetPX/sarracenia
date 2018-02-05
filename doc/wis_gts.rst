
---------------------------------
 Modernizing the WIS-GTS in 2018 
---------------------------------


.. contents::

.. note::
   FIXME: the classic GTS picture... Get one from JF?

The World Meteorological Organization (WMO) Information Service (WIS)'s Global
Telecommunications System (GTS) is the WMO's accepted method to circulate of
weather data in *meteorological real-time* [1]_ It does so by pre-established
bi-lateral agreements about who circulates what to whom, so that when data 
arrives, it is sent to the proper destinations immediately.  In hardware terms,
the GTS used to be a set of point-to-point links that collectively formed an
overlapping set of directed acyclic graphs. 

The GTS successfully and elegantly applied the technologies of the 1940's to
obtain world-wide exchange of weather data, most obviously, to enable 
commercial air travel to expand exponentially over the succeeding decades. It
was made in a world of expensive point-to-point telephone links, very low 
bandwidth, very little computational power, and few existing standards for
reliable data transfer. Today, The underlying technologies embodied by 
Internet and Regional Main Data Communications Network (RMDCN) are completely
different: Bandwidth and storage are relatively cheap, computing power is 
cheaper, point-to-point links are more expensive than multi-point clouds. 
Today's WMO members want to exchange more data types and higher volumes at 
higher speed. 

The weather community has, in the past, needed to create standards because no 
similar need in the rest of industry existed. Over the last few decades, as 
internet adoption has broadened and deepened, horizontal solutions for most of
the technical issues addressed by WMO standards have emerged. The WMO's 
strategic direction always has been and will continue to be to use widely
adopted technologies from the wider world and not define their own standards
unnecessarily.


.. [1] *real-time*, in meteorological circles refers to *immediately* or ASAP,
 which can mean anything between a few seconds, and a few minutes. This is very 
 different from the computing use of the term, where it refers to hard deadlines
 in terms of usually milliseconds. When this document uses *real-time* it uses 
 it in the meteorologically accepted meaning.

Routing in the GTS is Hard and Opaque
-------------------------------------

.. note::
   FIXME: Illustration of GTS with NMC´s and RTH´s.


When new data is made available by a National Meteorological Centre (NMC), it 
needs to issue notices, and likely discuss with their (Regional 
Telecommunications Hub) RTH, about accepting and routing the new data. The 
RTH's must discuss amongst eachother whether to exchange the data, and other 
NMC must further request from their RTH.  so for NMC *A* to make data 
available to NMC *B*, the GTS staff at both NMC's and all intervening RTH's 
must agree and action the request.

Also, the routing tables at each NMC and each RTH may or may not be
inspectable. It may be that the product NMC *B* is looking for is already 
available at their local RTH, but neither *A*, nor *B* have any effective way
of determining that, other than asking the administrators of B's RTH.  Manual
routing is ineffective, opaque and human resource intensive.

The initial WIS, as formulated over a decade ago, was an attempt to address
this opaqueness by introducing some Information Management (IM) concepts, and 
support for DAR: Discovery, Access, and Retrieval. All WMO members want to
know which data is available from which NMC's (or some intermediaries.) So we
publish metadata to Global Information Service Centres, where all the world's
real-time weather information is available and some means of retrieval is 
specified in that metadata.

When dealing in the abstract, without time constraints, add/or with small
datasets, retrieval time does not matter, but the access penalty imposed by
storing using databases for individual retrieval grows with the number of
items stored, and the number of queries or retrievals to be sustained. 
Initially, WIS was most concerned with getting higher visibilty of data, 
understanding what data was available. WIS Part 1 primarily implemented a
metadata layer, while the GTS has persisted to transfer actual data. Once
WIS Part 1 was in service, with DAR available which at first blush appears
much easier and friendlier, why didn't everyone just use DAR to replace the
GTS? 

The WIS architecture tends to concentrate load on GISCS, whether they want it
or not. Even assuming they want it, answering large volumes of queries in such
an architecture is a problem. The mental model for this is a database with an
index per metadata field, and the size of each index grows with the number of
items in the database. From Computational complexity theory, we know that the
best algorithms for looking up a single item in a index of N items requires
log(N) operations to complete. To perform Retrieval (the R in DAR), of all of
the items from an index, one at a time, the best algorithm has complexity 
N*log(N).


Internet Push is Poor Fit for Large Feeds
-----------------------------------------

.. note::
   fixme:  push

So called *Push* technologies, are actually *Pull*. A client asks a server if
they have new data available for them. The server responds with the list of new
data available, then the client pulls the data. This means that an entity
storing data has to retrieve the items from the data store (with a log(N) cost 
to each retrieval.) As the domain is *real-time* processing, the time for data
to be obtained by a client is also relevant, and bound by the maximum frequency
that a client is allowed to ask for updates. In general, the ATOM/RSS protocols
expect a minimum interval between polling events of five minutes. 

Each polling event requires the server to examine it's database for all 
matching entries, this search is likely an order N operation. So the responses
to polling requests are expensive, and the retrievals from the data system are
likewise expensive, which likely motivates the standard discouragement of rapid
polling. Note that the order(N) preparation of a response to a query is
incurred for every client for every polling interval.  

There are likely be ways to optimize this sort of transfer, but as this 
technology is usually deployed in non-realtime domains and for smaller 
datasets, there aren't easily adopted stacks that substantially optimize this.


Store And Forward is Faster/Better/Cheaper
------------------------------------------

Real-time systems such as the GTS get around the retrieval expense problem by
storing and forwarding at the same time. When a datum is received, a table of
interested parties is consulted, and then the forwarding is done based on the 
data already "retrieved". This works as an optimization because one is 
forwarding the message at exactly the time it is received, so the entire lookup
and retrieval process is skipped for all those known consumers.  In addition,
since the products are sent pro-actively, polling traffic is eliminated. 

This is especially acute for weather alert information, where a high polling 
frequency is a business need, but the volume of data is relatively low (alerts
are rare.)  In such cases the polling data can be 10 times or even 100 times the
amount of data transfer needed to send the warnings themselves.

In practice, the load on servers with large real-time flows to many clients will
be orders of magnitude lower with a real push technology, such as the 
traditional GTS, than supporting the same load with Internet Push technologies. 
By forwarding notifications on receipt, rather then having to service polls, one
reduces overall load, eliminating the vast majority of read traffic.

The savings in data transfer is significant in many cases. For example, in 2015,
a German company began retrieving NWP outputs from the Canadian datamart using
web-scraping (periodic polling of the directory) and when they transitioned to
using the AMQP push method, the total bytes downloaded by they went from 90
Gbytes/day to 60 Gbytes per day for the same data being transferred. 30
GBytes/day was just (polling) information about whether new model run outputs
were available.

The requirements for a store and forward system:

- TCP/IP connectivity.
- real-time data transmission 
- per destination queueing to allow asynchrony (clients that operate at different speeds or have transient issues.)
- application level integrity guarantees
- ability to tune subscriptions (what gets placed in each destination's queue.)

In terms of internet technologies, the main protocols for real-time data 
exchange are XMPP and websocket. XMPP provides real-time messaging, but it does
not include any concept of subscriptions, hierarchical or otherwise, or 
queueing. Web sockets are transport level technology. Adopting either of these
standards would mean building a domain specific stack to handle subscriptions
and queueing. This would mean a substantially larger and more complex custom
application would be needed.

The Advanced Message Queueing Protocol (AMQP), is a fairly mature internet
standard, which came from the financial industry and includes all of the
above characteristics. It can be adopted as-is by and a relatively simple AMQP
application can be built to to serve notifications about newly arrived data. 

While AMQP provides a robust messaging and queueing layer, an additional 
application layer is needed. The application is the software that understands
the specific content of the AMQP messages, and that is the value of the
Sarracenia application. Sarracenia sends and receives notifications over AMQP.

.. note::
   fixme: sample message?

An Sarracenia notification contains a Uniform Resource Location (URL) informing 
clients that a particular datum has arrived, and inviting them to download it. 
As these notifications are sent in real-time to clients, they can initiate 
downloads while the datum in question is still in memory and thus benefit 
from optimal retrieval performance. As the clients' time of access to the data 
is more closely clustered in time, overall i/o performed by the server is 
minimized.

A notification also contains a fingerprint, or checksum, that uniquely
identifies a product. This allows nodes to identify whether they have
received a particular datum before or not. This means that the risks of
misrouting data are lower than before because if there are any cycles in the
network, they are resolved automatically. Cycles in the connectivity graph are 
actually a benefit as they indicate multiple routes and redundancy in the 
network.  



With AMQP Notices on a Standard File Server
-------------------------------------------

Many robust and mature protocols and software stacks are available for many
data transport protocols: FTP, HTTP, HTTP(S), SFTP. Transporting data is a 
solved problem with many solutions available from the broader industry. The
existing cloud servers used for the GISC cache are done using FTP, and that is
a reasonable solution. Servers subscribe to each other's advertisements, and
advertisements are transitive, in that each node can advertise whatever it has
downloaded from any other node so that other nodes connected to it can consume
them. This is analogous to implementing mesh networking amongst all 
NC/DCPC/GISCs.

Adding an AMQP notification layer to the existing file transfer network would:

- improve security because users never upload, never have to write to a remote server.
  (all transfers can be done by client initiated subscriptions, no write to peer servers needed.)
- permit ad-hoc exchanges among members across the RMDCN without having to involve third parties.
  (perhaps even end users could understand enough to configure their own subscriptions.)
- provide a like-for-like mechanism to supplant the traditional GTS.
  (similar performance to existing GTS, no huge efficiency penalties.)
- transparent (users can see what data is on a node, without requiring human exchanges.)
  (users can browse an FTP/SFTP/HTTP tree.)
- enable/support arbitrary interconnection topologies among NC/DCPC/GISCs.
  (cycles in the graph are not a problem with fingerprints)
- Shorten the time for data to propagate from NMC to other data centres across the world.
  (fewer hops between nodes than in GTS, load more distributed among nodes.)
- relatively simple to configure for arbitrary topologies.
  (configure subscriptions, little need to configure publication.)
- route around node failures within the network in real-time without human intervention.
  (routing is implicit and dynamic, rather than explicit and static.)



Simple/Scalable Peer Configurations for Nations
-----------------------------------------------

A sample National Server (Linux/UNIX most likely) configuration would include the 
following elements:
- a http server for downloads (plain old apache-httpd, with indexes.)
- an ssh server for management and local uploads by national entities (OpenSSH)
- an AMQP broker ( Rabbitmq - to serve subscription notifications ) 
- Configuration to use AMQP feeds to download interesting subset from other NC/DCPC/GISCs ( Sarracenia )

Example: http://dd.weather.gc.ca

The tree on dd.weather.gc.ca is a prototype one which has been supplanted in 
other deployments. The top directory is the date, followed by the source for 
the data lower in the tree. The tree needs to be tuned to ensure directories
remain efficiently sized ( < 10,000 entries per directory. )  

FIXME: illustration.

The stack consists of entirely free software, and other implementations can be
substituted. The only uncommon element in the stack is Sarracenia, which so far 
as only been used with the RabbitMQ broker. While Sarracenia ( http://metpx.sf.net/sarra-e.html ) 
was inspired by the GISC data exchange problem, it is in no way specialized to weather 
forecasting, and the plan is to offer it to other for in other domains to support high 
speed data transfers. 

Sarracenia's reference implementation is less than 20 thousand lines in Python3,
although a partial implementations in node.js was done by one client, and 
another in C was done to support the High Performance Computing use case.
The `message format is published <http://metpx.sourceforge.net/sr_post.7.html>`_ 
and can be re-implemented any a wide variety of programming languages. 

This stack can be deployed on very small configurations, such as a raspberry pi
or a very inexpensive hosted virtual server. Performance will scale with 
resources available. The main Canadian internal meteorological data pump is
implemented across 10 physical servers (likely too many, as all of them are 
lightly loaded.) 

National centres deploy this stack (with parts replaced to taste) and can have 
as much, or as little, information locally as they see fit. Minimum set is only
the country's own data. Redundancy is achieved by many nations being interested in 
other nations' data sets. If one NC has an issue, the data can likely be
obtained from another node. NC's can also behave *selfishly* if they so choose,
downloading data to internal services without making it available for retransmission
to peers.  


Statelessness/Crawlable
-----------------------

As the file servers in question present static files, transactions with the 
proferred stack are completely stateless. Not only can search engines crawl 
such trees easily, but, given critical mass, one could arrange with search
engines to provide them with a continuous feed of notifications so that a given
user's index could be updated in real time.  These characteristics require no
work or cost once one has an accessible server that offers files.


Programmability/Interoperability
--------------------------------

A new application to process sr_post messages can be re-implemented if there
is a desire to do so as all design and implementation information, for all
three implementations (Python, C, node.js) as well as source code, is 
publically available. The python implementation has an extensive plugin
interface available to customize processing in a wide variety of ways, such as
to add file transfer protocols, and perform pre or post processing before
sending or after receipt of products. Interoperability with Apache NiFi has
been demonstrated by some clients.


Caveat: Solution for This Problem, Not Every Problem
----------------------------------------------------

AMQP brokers work well, with the sarracenia implementations at the Canadian 
meteorological service they are used for tens of millions of file transfers
totally 30 terabytes per day. Adoption is still limited as it is more 
complicated to understand and use than say, rsync. There are additional 
concepts (brokers, exchanges, queues) that make the technical barrier to 
entry relatively high. 

Also, while brokers work well for the moderate volumes we are seeing 
(hundreds of message per second per server.) it is completely unclear if this 
is suitable as a wider Internet technology (ie. for the 10K problem.) For now,
this sort of feed is intended for sophisticated clients with a demonstrated
need for real-time file services. Demonstrating Scaling to an individual scale
deployment is future work.

Note that AMQP has overhead and size limits that make it a poor fit for 
arbitrary file transfers. However, there are many other robust solutions for
the file transfer problem. AMQP is best used only to transfer notifications 
of data, which can be very large in number but individually small, and not 
the data itself.
