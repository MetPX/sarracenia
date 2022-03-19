
Status: Draft

=================
 Strawman Design
=================

.. section-numbering::

This document reflects the current design resulting from discussions and thinking
at a more detailed level that the outline document.  See `Outline <Outline.html>`_ 
for an overview of the design requirements.  See `use-cases <use-cases.html>`_ for 
an exploration of functionality of how this design works in different situations.
The way to make progress towards a working implementation is described in `plan <plan.html>`_.

.. contents::

Assumptions/Constraints
-----------------------

 - Are there cluster file systems available everywhere? No.

 - an operational team might want to monitor/alert when certain transfers experience difficulty.

 - security may want to run different scanning on different traffic (each block?)
   security might want us to refuse certain file types, so they go through heavier scanning.
   or perform heavier scanning on those file types.

 - extranet zones cannot initiate connections to internal zones.  
   extranet zones receive inbound connections from anywhere.

 - Government operations zones can initiate connections anywhere.
   however, Science is considered a sort of extranet to all the partners.

 - No-one can initiate connections into partner networks, but all partner departments can initiate
   connections into science.gc.ca zone.  Within the science zones, there is the shared file system
   area, where servers access a common cluster oriented file system, as well as some small restricted
   zones, where very limited access is afforded to ensure availability.

 - Within NRC, there are labs with equipment which cannot be maintained, software-wise,
   to address disclosed vulnerabilities because of excessive testing dependencies (ie. certifying
   that a train shaker still works after applying a patch.)  These systems are not given access
   to the internet, only to a few other systems on the site.

 - collaborators are academic, other-governmental, or commercial entities which which government
   scientists exchange data.

 - collaborators connect to extranet resources from their own networks.  Similarly to partners,
   (subject to exceptions) no connections can be initiated into any collaborator network.

 - There are no proxies, no systems in the extranet are given exceptional permissions to
   initiate inbound connections.  File storage protocols etc... are completely isolated between
   them.  There are no file systems that cross network zone boundaries. 

 - One method of improving service reliability is to use internal services for internal use
   and reserve public facing services for external users.  Isolated services on the inside
   are completely impervious to internet ´weather´ (DDOS of various forms, load, etc...)
   internal and external loads can be scaled independently.


Number of Switches 
------------------

The application is supposed to support any number of topologies, that is any number of pumps S=0,1,2,3
may exist between origin and final delivery, and do the right thing.

Why isn´t everything point to point, or when do you insert a pumps?

 - network topology/firewall rules sometimes require being at rest in a transfer area between two
   organizations.  Exception to these rules create vulnerabilities, so prefer to avoid.
   whenever traffic prevents initiating a connection, that indicates a store & forward pumps
   may be needed.

 - physical topology.  While connectivity may be present, optimal bandwidth use may involve 
   not taking the default path from A to B, but perhaps passing through C.

 - when the transfer is not 1:1, but 1:<source does not know how> many. The pumping takes
   care of sending it to multiple points.

 - when the source data needs to be reliably available.  This translates to making many copies,
   rather than just one, so it is easier for the source to post once, and have the network
   take care of replication.

 - for management reasons, you want to centrally observe data large transfers.

 - for management reasons, to have transfers  routed a certain way.

 - for management reasons, to ensure that transfer failures are detected and escalated
   when appropriate. They can be fixed rather than waiting for ad-hoc monitoring to detect
   the issue.

 - For asynchronous transfers.  If the source has many other activities, it may want
   to give responsibility to another service to do potentially lengthy file transfers.
   the pump is inserted very near to the source, and is full store & forward. sr_post
   completes (nearly instant), and from then on the pumping network manages transfers.


AMQP Feature Selection
----------------------

AMQP is a universal message passing protocol with many different options to support many 
different messaging patterns.  MetPX-sarracenia specifies and uses a small subset of AMQP 
patterns.  Indeed an important element of sarracenia development was to select from the 
many possibilities a small subset of methods are general and easily understood, in order 
to maximize potential for interoperability.

Specifying the use of a protocol alone may be insufficient to provide enough information for
data exchange and interoperability.  For example when exchanging data via FTP, a number of choices
need to be made above and beyond the basic protocol.

 - authenticated or anonymous use?
 - how to signal that a file transfer has completed (permission bits? suffix? prefix?)
 - naming convention.
 - text or binary transfer.

Agreed conventions above and beyond simply FTP (IETF RFC 959) are needed.

Similar to the use of FTP alone as a transfer protocol is insufficient to specify a complete data
transfer procedure, use of AMQP, without more information, is incomplete.

AMQP 1.0 standardizes the on the wire protocol, but leaves out many features of broker interaction.
As the use of brokers is key to sarracenia´s use of, was a fundamental element of earlier standards,
and as the 1.0 standard is relatively controversial, this protocol assumes a pre 1.0 standard broker,
as is provided by many free brokers, such as rabbitmq, often referred to as 0.8, but 0.9 and post
0.9 brokers are also likely to inter-operate well.

In AMQP, many different actors can define communication parameters. To create a clearer
security model, sarracenia constrains that model: sr_post clients are not expected to declare
Exchanges.  All clients are expected to use existing exchanges which have been declared by
broker administrators.  Client permissions are limited to creating queues for their own use,
using agreed upon naming schemes.  Queue for client: qc_<user>.????

Topic-based exchanges are used exclusively. AMQP supports many other types of exchanges,
but sr_post have the topic sent in order to support server side filtering by using topic
based filtering.  The topics mirror the path of the files being announced, allowing
straight-forward server-side filtering, to be augmented by client-side filtering on
message reception.

The root of the topic tree is the version of the message payload. This allows single brokers
to easily support multiple versions of the protocol at the same time during transitions. v02
is the third iteration of the protocol and existing servers routinely support previous versions
simultaneously in this way. The second topic in the topic tree defines the type of message.
at the time of writing:  v02.post is the topic prefix for current post messages.

The AMQP messages contain announcements, no actual file data. AMQP is optimized for and assumes
small messages. Keeping the messages small allows for maximum message throughtput and permits
clients to use priority mechanisms based on transfer of data, rather than the announcements.
Accomodating large messages would create many practical complications, and inevitably require
the definition of a maximum file size to be included in the message itself, resulting in
complexity to cover multiple cases.

sr_post is intended for use with arbitrarily large files, via segmentation and multi-streaming.
blocks of large files are announced independently. and blocks can follow different paths
between initial pump and final delivery.

AMQP vhosts are not used. Never saw any need for them. The commands support their optional 
use, but there was no visible purpose to using them is apparent.

Aspects of AMQP use can be either constraints or features:

 - interaction with a broker are always authenticated.

 - We define the *anonymous* for use in many configurations.

 - users authenticate to local cluster only. We don´t impose any sort of credential or identity propagation
   or federation, or distributed trust.

 - pumps represent users by forwarding files on their behalf, there is no need to include
   information about the source users later on in the network. 

 - This means that if user A from S0 is defined, and a user is given the same name on S1, then they may 
   collide. sad. Accepted as a limitation.


Application 
-----------

Description of application logic relevant to discussion. There is a ´control plane´ where posts about new 
data available are made, and log messages reporting status of transfers of the same data are routed among 
control plane users and pumps. A pump is an AMQP broker, and users authenticate to the broker. Data 
may (most of the time does) have a different other authentication method.

There are very different security use cases for file transfer:

 1. **Public Dissemination** data is being produced, whose confidentiality is not an issue, the purpose is to 
    disseminate to all who are interested as quickly and reliably as possible, potentially involving many 
    copies. The data authentication is typically null for this case. Users just issue HTTP GET requests with 
    no authentication. For AMQP authentication, it can be done as anonymous, with no ability for providers to
    monitor.  If there is to be support from the data source, then the source would assign a non-anonymous user
    for the AMQP traffic, and the client would ensure logging was working, enabling the provider to monitor and 
    alert when problems arise.

 2. **Private Transfer** proprietary data is being generated, and needs to be moved to somewhere where it can be 
    archived and/or processed effectively, or shared with specific collaborators.  AMQP and HTTP traffic must
    be encrypted with SSL/TLS.  Authentication is typically common between AMQP and HTTPS. For Apache httpd
    servers, the htpasswd/htaccess method will need to be continuously configured by the delivery system.
    These transfers can have requirements for be high availability. 

 3. **Third Party Transfer** the control plane is explicitly used only to control the transfer, authentication
    at both ends is done separately.  Users authenticate to the data-less, or SEP pump with AMQP, but the
    authentication at both ends is outside sarracenia control.  Third-party transfer is limited to S=0.
    If the data does not cross the pump, it cannot be forwarded. So no routing is relevant to this case.
    Also dependent on the availability of the two end points throughout, so more difficult to assure in practice.

Both public and private transfers are intended to support arbitrary chains of pumps between *source* and *consumer*.
The cases depend on routing of posts and log messages. 

.. NOTE::
   forward routing...  Private and Public transfers... not yet clear, still considering.
   what is written here on that subject is tentative. wondering if split, and do public
   first, then private later?

To simplify discussions, names will be selected with a prefix things according to the type
of entity: 

 - exchanges start with x.
 - queues start with q.
 - users start with u. users are also referred to as *sources*
 - servers start with svr
 - clusters start with c
 - ´pumps´ is used as a synonym for cluster, and they start with S (capital S.): S0, S1, S2...

on pumps:
 - users that pumps used to authenticate to each other are **interpump accounts**. Another word: **feeder** , **concierge**  ?
 - users that inject data into the network are called **sources**.
 - users that subscribe to data are called **consumers**.


Routing
-------

There are two distinct flows to route: posts, and logs. 
The following header in messages relate to routing, which are set in all messages.

 - *source* - the user that injected the original post.
 - *source_cluster* - the cluster where the source injected the post.
 - *to_clust* - the comma separated list of destination clusters.
 - *private* - the flag to indicate whether the data is private or public.

An important goal of post routing is that the *source* decides where posts go, so 
pumping of individual products must be done only on the contents of the posts, not
some administrator configuration.

Administrators configure the inter pump connections (via SARRA and other components)
to align with network topologies, but once set up, all data should flow properly with 
only source initiated routing commands. Some configuration may be needed on all pumps
whenever a new pump is added to the network.


Routing Posts
~~~~~~~~~~~~~

Post routing is the routing of the post messages announced by data *sources*.
The data corresponding to the source follows the same sequence of pumps as the posts
themselves.  When a post is processed on a pump, it is downloaded, and then the posting
is modified to reflect that´s availability from the next-hop pump.

Post messages are defined in the sr_post(7) man page.  They are initially emitted by *sources*,
published to xs_source.  After Pre-Validation, they go (with modifications described in Security) to 
either xPrivate or xPublic.

.. note::
   FIXME: Tentative!?
   if not separate exchange, then anyone can see any post (not the data, but yes the post)
   I think that´s not good.

For Public data, *feeders* for downstream pumps connect to xPublic.
They look at the to_clust Header in each message, and consult a post2cluster.conf file.
post2cluster.conf is just a list of cluster names configured by the administrator::

        ddi.cmc.ec.gc.ca
        dd.weather.gc.ca
        ddi.science.gc.ca 

This list of clusters is supposed to be the clusters that are reachable by traversing
this pump.  If any cluster in post2cluster.conf is listed in the to_clust of the 
message field, then the data needs to tr

Separate Downstream *feeders* connect to xPrivate for private data.  Only *feeders* are
allowed to connect to xprivate.

.. Note::
   FIXME: perhaps feed specific private exchanges for each feeder?  x2ddiedm, x2ddidor, x2ddisci ?
   using one xPrivate means pumps can see messages they may not be allowed to download
   (lesser issue than with xPublic, but depends how trusted downstream pump is.)

Routing Logs
~~~~~~~~~~~~

Log messages are defined in the sr_log(7) man page.  They are emitted by *consumers* at the end, 
as well as *feeders* as the messages traverse pumps.  log messages are posted to 
the xl_<user> exchange, and after log validation queued for the xlog exchange.

Messages in xlog destined for other clusters are routed to destinations by 
log2cluster component using log2cluster.conf configuration file.  log2cluster.conf 
uses space separated fields: First field is the cluster name (set as per soclust in 
post messages, the second is the destination to send the log messages for posting 
originating from that cluster to) Sample, log2cluster.conf::

      clustername amqp://user@broker/vhost exchange=xlog

Where message destination is the local cluster, log2user (log2source?) will copy
the messages where source=<user> to sx_<user>.

When a user wants to view their messages, they connect to sx_<user>. and subscribe.
this can be done using *sr_subscribe -n  --topic_prefix=v02.log* or the equivalent *sr_log*.


Security Model
--------------



Users, Queues & Exchanges 
~~~~~~~~~~~~~~~~~~~~~~~~~

Each user Alice, on a broker to which she has access:
 - has an exchange xs_Alice, where she writes her postings, and reads her logs from. 
 - has an exchange xl_Alice, where she writes her log messages.
 - can create queues qs_Alice\_.* to bind to exchanges.

Switches connect with one another using inter-exchange accounts.
 - Alice can create and destroy her own queues, but no-one else's.  
 - Alice can only write to her xs_exchange, 
 - Exchanges are managed by the administrator, and not any user.
 - Alice can only post data that she is publishing (it will refer back to her) 

..NOTE:: 
   tester  ^q_tester.*     ^q_tester.*|xs_tester   ^q_tester.*|^xl_tester$
   leaving all permissions for queues for an amqp users also gives the permission
   do create/configure/write any amqp objects with a name starting with q_tester
   in this example.


Pre-Validation
~~~~~~~~~~~~~~

Pre-Validation refers to security and correctness checks performed on 
the information provided by the post message before the data itself is downloaded.
Some tools may refer to this as *message validation*

 - input sanitizing (looking for errors/malicious input.)
 - an undefined number of checks that need to be configurable (script?)
 - vary per configuration, and installation (sizes)

When reading from a source:
 - a post message arrives on xs_Alice, from a user logged in as Alice.
 - overwrites the source to be Alice: source=Alice ... or reject?
 - sets some headers that we do not trust users to do: cluster=
 - set cluster header to local one.

Reading from a feeder:
 - source doesn´t matter. (feeders can represent other users)
 - do not overwrite source.
 - ensure cluster is not local cluster (as that would be a lie.) ?

Regardless:
 - check the partitioning size, if it exceeds pump maximum, Reject.
 - check the bandwidth limitations in place. If exceeded, Hold.
 - check the disk usage limit in place. If exceeded, Hold.
 - If the private flag is set, then accept by copying to xPrivate
 - If the private flag is not set, then accept by copy to xPublic

Results:
 - Accept means: queue the message to another exchange (xinput) for downloading.
 - Reject means: do not copy message (still accept & ack so it leaves queue) product log message.
 - Hold means:  do not consume... but sleep for a while.

Hold is for temporary failure type reasons, such as bandwidth of disk space reasons. 
as these reasons are independent of the particular message, hold applies for
the entire queue, not just the message.

After Pre-Processing, a component like sr_sarra assumes the post message is good,
and just processes it.  That means it will fetch the data from the posting source.
Once the data is downloaded, it goes through Post-Validation.


Post-Validation
~~~~~~~~~~~~~~~
 
When a file is downloaded, before re-announcing it for later hops it goes
through some analysis.  The tools may call this *file validation*:

 - when a file is downloaded, it goes through post-validation,
 - invoke one or more virus scanners chosen by security  
 - the scanners will not be the same everywhere, even different locations within
   same org, may have different scanning standards (function on security zone.)

 - Accept means:  it is OK to send this data to further hops in the network.
 - Reject menas:  do not forward this data (potentially delete local copy.) Essentially *quarantine*


Log Validation
~~~~~~~~~~~~~~

When a client like sarra or subscribe completes an operation, it creates a log message 
corresponding to the result of the operation.  (This is much lower granularity than a 
local log files.) It is important for one client not to be able to impersonate another
in creating log messages.  

 - Messages in exchanges have no reliable means of determining who inserted them.
 - so users publish their log messages to sl_<user> exchange.
 - For each user, log reader reads the message, and overwrites the consuminguser to force match. (if reading a message from sl_Alice, it forces the consuminguser field to be Alice) see sr_log(7) for user field
 - sl_* are write-only for all users, they cannot read their own posts for that.
 - is there some check about consuminghost?
 - Accepting a log message means publishing on the xlog exchange.
 - Only admin functions can read from xlog.
 - downstream processing is from xlog exchange which is assumed clean.
 - Rejecting a log message means not copying it anywhere. 

 - sourcce check does not make sense when channels are used for inter-pump log routing.
   Essentially, all downstream pumps can do is forward to the source cluster.
   The pumps receiving the log messages must not convert the consuminguser on those links.
   evidence of need of some sort of setting: user vs. inter-pump setting.

... NOTE::
   FIXME: if you reject a log message, does it generate a log message?
   Denial of service potential by just generating infinite bogs log messages.
   It is sad that if a connection is mis-configured as a user one, when it is inter-pump,
   that will cause messages to be dropped.  how to detect configuration error?


Private vs. Public Data Transfer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Transfers in the past have been public, just a matter of sharing public information.
A crucial requirement of the package is to support private data copies, where the
ends of the transfer are not sharing with arbitrary others.

.. NOTE::
   FIXME: This section is a half-baked idea! not sure how things will turn out.
   basic problem:  Alice connecting to S1 wants to share with Bob, who has an
   account on S3.  To get from S1 to S3, one needs to traverse S2.  the normal
   way such routing is done is via a sr_sarra subscription to xpublic on S1, and
   S2.  So Eve, a user on S1 or S2, can see the data, and presumably download it.
   unless the http permissions are set to deny on S1 and S2. Eve should not have
   access.  Implement via http/auth permitting inter-pump accounts on S2
   to access S1/<private> and S3 account to S2/<private>. then permit bob on
   S3.

There are two modes of sending products through a network, private vs. public.
With public sending, the information transmitted is assumed to be public and available
to all comers,  If someone sees the data on an intervening pump, then they are likely
to be able to download it at will without further arrangements.  public data is posted
for inter-pump copies using the xPublic exchange, which all users may access as well.

Private data is only made available to those who are explicitly permitted access.
private data is made available only on the xPrivate exchange.  Only Interpump channel
users are given access to these messages.

.. NOTE::
   - Is two exchanges needed, or is setting permissions enough?
   - if nobody on B is permitted, then only C is able to download from B, which just works.
   - This only works with http because setting sftp permissions is going to be hell.  
   - If only using http, then Even can still see all postings, just not get data, unless xprivate happens.

For SEP topologies (see Topologies) things are much simpler as end users can just use mode bits.


HTTPS Private Access
~~~~~~~~~~~~~~~~~~~~

.. NOTE:: 
   FIXME: Not designed yet.
   Really not baked yet.  For https, need to create/manage .htaccess (canned but generated every day) 
   and .htpasswd (generated every day) files.  
 
Need some kind of adm message that sources can send N pumps later to alter the contents of .htpasswd
CRUD? or just overwrite every time?  query?

Sarra likely needs to look at this and add the ht* files every day.   Need to talk with the webmailteam guys.

How to change passwords


Topologies
----------

Questions... There are many choices for cluster layout. One can do simple H/A on a pair of nodes, 
simple active/passive?  One can go to scalable designs on an array of nodes, which requires a load 
balancer ahead of the processing nodes.  The disks of a cluster can be shared or individual to 
the processing nodes, as can broker state.  Exploring whether to support any/all configurations, 
or to determine if there is a particular design pattern that can be applied generally.

To make these determinations, considerable exploration is needed.

We start with naming the topologies so they can be referred to easily in further discussions.
None of the topologies assume that disks are pumped among servers in the traditional HA style.

Based on experience, disk pumping is considered unreliable in practice, as it involves complex
interaction with many layers, including the application.  Disks are either dedicated to nodes, 
or a cluster file system is to be used. The application is expected to deal with those two
cases.

Some document short-hand:

Bunny
       A shared/clustered broker instance, where multiple nodes use a common broker to co-ordinate.


Capybara Effect
      *capybara through a snake*  where a large rodent distorts the body of a snake 
      as it is being digested.  Symbolic of poor load balancing, where one node 
      experiences a spike in load and slows down inordinately.

Fingerprint Winnowing
      Each product has a checksum and size intended to identify it uniquely, referred to as
      as fingerprint.  If two products have the same fingerprint, they are considered 
      equivalent, and only one may be forwarded.  In cases where multiple sources of equivalent 
      data are available but downstream consumers would prefer to receive single announcements 
      of products, processes may elect to publish notifications of the first product 
      with a given fingerprint, and ignore subsequent ones.

      This is the basis for the most robust strategy for high availability, but setting up
      multiple sources for the same data, accepting announcements for all of them, but only
      forwarding one downstream.  In normal operation, one source may be faster than the
      other, and so the second source's products are usually 'winnowed'. When one source 
      disappears, the other source's data is automatically selected, as the fingerprints 
      are now *fresh* and used, until a faster source becomes available. 

      The advantage of this method is that now A/B decision is required, so the time
      to *pumpover* is zero.  Other strategies are subject to considerable delays        
      in making the decision to pumpover, and pathologies one could summarize as flapping,
      and/or deadlocks.


Standalone
~~~~~~~~~~

In a standalone configuration, there is only one node in the configuration.  I runs all components 
and shares none with any other nodes.  That means the Broker and data services such as sftp and 
apache are on the one node.  

One appropriate usage would be a small non-24x7 data acquisition setup, to take responsibility of data 
queueing and transmission away from the instrument.


DDSR: Switching/Routing Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a more scalable configuration involving several data mover nodes, and potentially several brokers.
These clusters are not destinations of data transfers, but intermediaries.  Data flows through them, but
querying them is more complicated because no one node has all data available.   The downstream clients
of DDSR's are essentially other sarracenia instances.

There are still multiple options available within this configuration pattern.
ddsr one broker per node?  (or just one broker ( clustered,logical ) broker?)

On a pumping/router, once delivery has occurred to all contexts, can you delete the file?
Just watch the log files and tick off as each scope confirms receipt.
when last one confirmed, delete. (makes re-xmit difficult ;-)

Based on a file size threshold? if the file is too big, don´t keep it around?

The intended purpose has a number of implementation options, which must be further sub-divided for analysis.


Independent DDSR 
~~~~~~~~~~~~~~~~

In Independent DDSR, there is a load balancer which distributes each incoming connection to
an individual broker running on a single node.

ddsr - broker 

pre-fetch validation would happen on the broker.  then re-post for the sarra's on the movers.


 - each node broker and transfer engines act independently. Highest robustness to failure.
 - load balancer removes mover nodes from operation on detection of a failure.
 - individual files land, mostly entirely on single nodes.
 - no single data mover sees all of the files of all of the users in a cluster.

CONFIRM: Processes running on the individual nodes, are subscribed to the local broker.
Highly susceptible to the *Capybara Effect* where all of the blocks of 
the large file are channelled though a single processing node.  Large file transfers
with trigger it.

CONFIRM: Maximum performance for a single transfer is limited to a single node.


Shared Broker DDSR
~~~~~~~~~~~~~~~~~~

While the data nodes disk space remain independent, the brokers are clustered together to
form a single logical entity.

on all nodes, the mover processes use common exchanges and queues.

 - each node transfers independently, but dependent on the broker cluster.
 - load balancer removes nodes (broker or mover) from operation.
 - external users connect to shared queues, not node specific ones.
 - transfer engines connect to cluster queues, obtaining blocks.
 - no single data mover sees all of the files of all of the users in a cluster.
 - requires broker to be clustered, adding complexity there.

In Shared Broker DDSR, *Capybara Effect* is minimized as individual blocks of a transfer
are distributed across all the mover nodes.  When a large file arrives, all of the movers
on all of the nodes may pick up individual blocks, so the work automatically is 
distributed across them.

This assumes that large files are segmented.  As different transfer nodes will have
different blocks of a file, and the data view is not shared, no re-assembly of files 
is done.

Broker clustering is considered mature technology, and therefore relatively trustworthy.



DD: Data Dissemination Configuration (AKA: Data Mart)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The sr deployment configuration is more of an end-point configuration.  Each node is expected to
have a complete copy of all the data downloaded by all the nodes.   Giving a unified view makes
it much more compatible with a variety of access methods, such as a file browser (over http,
or sftp) rather than being limited to AMQP posts.  This is the type of view presented by
dd.weather.gc.ca.

Given this view, all files must be fully reassembled on receipt, prior to announcing downstream
availability.  files may have been fragmented for transfer across intervening pumps.

There are multiple options for achieving this end user visible effect, each with tradeoffs.
In all cases, there is a load balancer in front of the nodes which distributes incoming
connection requests to a node for processing.

 - multiple server nodes.  Each standalone.

 - sr - load balancer, just re-directs to a sr node?
   dd1,dd2, 

   broker on sr node has connection thereafter.


Independent DD
~~~~~~~~~~~~~~

 - The load balancer hands the incoming requests to multiple Standalone_ configurations. 

 - Each node downloads all data.  Disk space requirements for nodes in this configuration 
   are far larger than for DDSR nodes, where each node only has 1/n of the data.

 - Each node announces each product that it has downloaded, using it's own node name, because
   it does not know if other nodes have that product.

 - Once a connection is established, the client will communicate exclusively with that node.
   ultimate performance is limited by the individual node performance.

 - The data movers can (for maximum reliability) be configured independently, but if inputs 
   are across the WAN, one can reduce bandwidth usage N times by havng N nodes 
   share queues for distant sources and then have local transfers between the nodes.

   CONFIRM: is *Fingerprint Winnowing* required for intra-cluster copies?

   When a single node fails, it ceases to download, and the other n-1 nodes continue transferring.

.. NOTE::
  FIXME: shared broker and shared file system... hmm...  Could use second broker
  instance to do cooperating download via fingerpring winnowing. 



Shared-Broker DD
~~~~~~~~~~~~~~~~

 - a single clustered broker is shared by all nodes.

 - Each node downloads all data.  Disk space requirements for nodes in this configuration 
   are far larger than for DDSR nodes, where each node only has 1/n of the data.

 - clients connect to a cluster-wide broker instance, so the download links can be from any
   node in the cluster.

 - if the clustered broker fails, the service is down. (should be reliable)

 - A node cannot announce each product that it has downloaded, using it's own node name, because
   it does not know if other nodes have that product.   (announce as dd1 vs. dd)

 - Either:

    -- Can only announce a product once it is clear that every active node has the product.
    -- 1st come, 1st serve:  apply fingerprint winnowing. Announce only node that got the data first. 
  

 - as in the independent configuration, nodes share queues and download a fraction upstream data.
   They therefore need to exchange data amongst each other, but that means using a non-clustered
   broker. So likely there will be two brokers access by the nodes, one node local, and one shared.

 - this is more complicated, but avoids the need for a clustered file system. hmm... pick your poison.
   demo both?

Shared-Data DD
~~~~~~~~~~~~~~

 - The load balancer hands the incoming request to multiple nodes.

 - Each node has read/write access to a shared/cluster file system.

 - clustered broker configuration, all nodes see the same broker.

 - downloaded once means available everywhere (written to a shared disk)

 - so can advertise immediately with shared host spec (dd vs. dd1)

 - if the clustered broker fails, the service is down. (should be reliable)

 - if the clustered file system fails, the service is down. (??)



SEP: Shared End-Point Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The SEP configuration, all of the mover nodes are directly accessible to users.
The broker does not provide data service, just a pure message broker. Can be called
*data-less* pump, or a *bunny*.

The broker is run clustered, and nothing can be said about the mover nodes.
Consumers and watchers can be started up by anyone on any collection of nodes, 
and all data visible from any node where cluster file systems provide that benefit.

Disk space administration is entirely a user configuration setting, not in
control of the application (users set ordinary quotas for their file systems directly)

