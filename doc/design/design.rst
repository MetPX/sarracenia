
Status: Pre-Draft

=================
 Strawman Design
=================

.. section-numbering::

This document reflects the current design at a more detailed level that the outline
document.  See `Outline <Outline.html>`_ for an overview of the design requirements.  
See `use-cases <use-cases.html>`_ for an exploration of functionality of how
this design works in different situations.


=======================
Assumptions/Constraints
=======================

 - Are there cluster file systems available everywhere?

 - an operational team might want to monitor/alert when certain transfers esperience difficulty.

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
   them.  There are no file systems available from OperationsOZ to CollabXRZ

 - One method of improving service reliability is to use internal services for internal use
   and reserve public facing services for external users.  Isolated services on the inside
   are completely impervious to internet ´weather´ (DDOS of various forms, load, etc...)
   internal and external loads can be scaled independently.


Number of Switches 
------------------

The application is supposed to support any number of topologies, that is any number of switches S=0,1,2,3
may exist between origin and final delivery, and do the right thing.

Why isn´t everything point to point, or when do you insert a switch?

        - network topology/firewall rules sometimes require being at rest in a transfer area between two
          organizations.  Exception to these rules create vulnerabilities, so prefer to avoid.
          whenever traffic prevents initiating a connection, that indicates a store & forward switch
          may be needed.

        - when the transfer is not 1:1, but 1:<source does not know how> many. The switching takes
          care of sending it to multiple points.

        - when the source data to be reliably available.  This translates to making many copies,
          rather than just one, so it is easier for the source to post once, and have the network
          take care of replication.

        - for management reasons, you want to centrally observe data large transfers.

        - for management reasons, to have transfers  routed a certain way.

        - for management reasons, to ensure that transfer failures are detected and escalated
          when appropriate. They can be fixed rather than waiting for ad-hoc monitoring to detect
          the issue.

        - For asynchronous transfers.  If the source has many other activities, it may want
          to give responsibility to another service to do potentially lengthy file transfers.
          the switch is inserted very near to the source, and is full store & forward. dd_post
          completes (nearly instant), and from then on the switching network manages transfers.


AMQP Feature Selection
----------------------

AMQP is a universal message passing protocol with many different options to support many 
different messaging patterns.  MetPX-sarracenia specifies and uses a small subset of AMQP 
patterns.  Indeed an important element of sarracenia development was to select from the 
many possibilities a small subset of methods are general and easily understood, in order 
to maximize potential for interoperability.

Specifying the use of a protocol alone may be insufficient to provide enough information for
data exchange and interoperability.  For example when exchanging data via FTP, a number of choices
need to be made above and beyond the protocol.

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
security model, sarracenia constrains that model: dd_post clients are not expected to declare
Exchanges.  All clients are expected to use existing exchanges which have been declared by
broker administrators.  Client permissions are limited to creating queues for their own use,
using agreed upon naming schemes.  Queue for client: qc_<user>.????

Topic-based exchanges are used exclusively.  AMQP supports many other types of exchanges,
but dd_post have the topic sent in order to support server side filtering by using topic
based filtering.  The topics mirror the path of the files being announced, allowing
straight-forward server-side filtering, to be augmented by client-side filtering on
message reception.

The root of the topic tree is the version of the message payload.  This allows single brokers
to easily support multiple versions of the protocol at the same time during transitions.  v02
is the third iteration of the protocol and existing servers routinely support previous versions
simultaneously in this way.  The second topic in the topic tree defines the type of message.
at the time of writing:  v02.post is the topic prefix for current post messages.

The AMQP messages contain announcements, no actual file data.  AMQP is optimized for and assumes
small messages.  Keeping the messages small allows for maximum message throughtput and permits
clients to use priority mechanisms based on transfer of data, rather than the announcements.
Accomodating large messages would create many practical complications, and inevitably require
the definition of a maximum file size to be included in the message itself, resulting in
complexity to cover multiple cases.

dd_post is intended for use with arbitrarily large files, via segmentation and multi-streaming.
blocks of large files are announced independently. and blocks can follow different paths
between initial switch and final delivery.

AMQP vhosts are not used.  Never saw any need for them. The commands support their optional 
use, but there was no visible purpose to using them is apparent.


===========
Application 
===========

Description of application logic relevant to discussion.



Conventions
-----------

To simplify discussions, names will be selected with a prefix things according to the type
of entity: 

 - exchanges start with x.
 - queues start with q.
 - users start with u. users are also referred to as *sources*
 - servers start with svr
 - clusters start with c





Users, Queues & Exchanges 
-------------------------

 - Each group or person that transfers files needs a user name.
 - All users are authenticated 
 -  *anonymous* is a valid user in many configurations.
 - users authenticate to local cluster only.
 - switches represent users by forwarding files on their behalf.

Each user Alice on a server to which she has access:
 - has an exchange xs_Alice, where she writes her postings, and reads her logs from. 
 - has an exchange xl_Alice, where she writes her log messages.
 - can create queues qs_Alice_.* to bind to exchanges.

Switches connect with one another and 

Security Model
--------------

 - Alice can create and destroy her own queues, but no-one else's.  
 - Alice can only write to her xs_exchange, 
 - Exchanges are managed by the administrator, and not any user.
 - Alice can only post data that she is publishing (it will refer back to her) 

Pre-Validation
--------------

 - when a post message arrives on xs_Alice, it is read by FIXME  
 - FIXME overwrites the source to be Alice, and sets the cluster header.
	- source=Alice
	- cluster=
 - That process validates copies the posting to xFIXME2
 - It adds the header

==========
Topologies
==========

Questions... There are many choices for cluster layout. One can do simple H/A on a pair of nodes, 
simple active/passive?  One can go to scalable designs on an array of nodes, which requires a load 
balancer ahead of the processing nodes.  The disks of a cluster can be shared or individual to 
the processing nodes, as can broker state.  Exploring whether to support any/all configurations, 
or to determine if there is a particular design pattern that can be applied generally.

To make these determinations, considerable exploration is needed.

We start with naming the topologies so they can be referred to easily in further discussions.
None of the topologies assume that disks are switched among servers in the traditional HA style.

Based on experience, disk switching is considered unreliable in practice, as it involves complex
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
      to *switchover* is zero.  Other strategies are subject to considerable delays        
      in making the decision to switchover, and pathologies one could summarize as flapping,
      and/or deadlocks.


Standalone
----------

In a standalone configuration, there is only one node in the configuration.  I runs all components 
and shares none with any other nodes.  That means the Broker and data services such as sftp and 
apache are on the one node.  

One appropriate usage would be a small non-24x7 data acquisition setup, to take responsibility of data 
queueing and transmission away from the instrument.


DDSR: Switching/Routing Configuration
-------------------------------------

This is a more scalable configuration involving several data mover nodes, and potentially several brokers.
These clusters are not destinations of data transfers, but intermediaries.  Data flows through them, but
querying them is more complicated because no one node has all data available.   The downstream clients
of DDSR's are essentially other sarracenia instances.

There are still multiple options available within this configuration pattern.
ddsr one broker per node?  (or just one broker ( clustered,logical ) broker?)

on a switching/router, once delivery has occurred to all contexts, can you delete the file?
Just watch the log files and tick off as each scope confirms receipt.
when last one confirmed, delete. (makes re-xmit difficult ;-)

based on a file size threshold? if the file is too big, don´t keep it around?

The intended purpose has a number of implementation options, which must be further sub-divided for analysis.


----------------
Independent DDSR 
----------------

In Independent DDSR, there is a load balancer which distributes each incoming connection to
an individual broker running on a single node.

ddsr - broker 

pre-fetch validation would happen on the broker.  then re-post for the sara's on the movers.


 - each node broker and transfer engines act independently. Highest robustness to failure.
 - load balancer removes mover nodes from operation on detection of a failure.
 - individual files land, mostly entirely on single nodes.
 - no single data mover sees all of the files of all of the users in a cluster.

CONFIRM: Processes running on the individual nodes, are subscribed to the local broker.
Highly susceptible to the *Capybara Effect* where all of the blocks of 
the large file are channelled though a single processing node.  Large file transfers
with trigger it.

CONFIRM: Maximum performance for a single transfer is limited to a single node.


------------------
Shared Broker DDSR
------------------

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



DD: Data Dissemination Configuration
------------------------------------

The dd deployment configuration is more of an end-point configuration.  Each node is expected to
have a complete copy of all the data downloaded by all the nodes.   Giving a unified view makes
it much more compatible with a variety of access methods, such as a file browser (over http,
or sftp) rather than being limited to AMQP posts.  This is the type of view presented by
dd.weather.gc.ca.

Given this view, all files must be fully reassembled on receipt, prior to announcing downstream
availability.  files may have been fragmented for transfer across intervening switches.

There are multiple options for achieving this end user visible effect, each with tradeoffs.
In all cases, there is a load balancer in front of the nodes which distributes incoming
connection requests to a node for processing.

 - multiple server nodes.  Each standalone.

 - dd - load balancer, just re-directs to a dd node?
   dd1,dd2, 

   broker on dd node has connection thereafter.

--------------
Independent DD
--------------

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



----------------
Shared-Broker DD
----------------

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
    -- 1st come, 1st serve:  apply fingerprint winnowing. Announce only node that got the data 
       first. 
  

- as in the independent configuration, nodes share queues and download a fraction upstream data.
  They therefore need to exchange data amongst each other, but that means using a non-clustered
  broker. So likely there will be two brokers access by the nodes, one node local, and one shared.

- this is more complicated, but avoids the need for a clustered file system. hmm... pick your poison.
  demo both?

--------------
Shared-Data DD
--------------

- The load balancer hands the incoming request to multiple nodes.

- Each node has read/write access to a shared/cluster file system.

- clustered broker configuration, all nodes see the same broker.

- downloaded once means available everywhere (written to a shared disk)

- so can advertise immediately with shared host spec (dd vs. dd1)

- if the clustered broker fails, the service is down. (should be reliable)

- if the clustered file system fails, the service is down. (??)



SEP: Shared End-Point Configuration
-----------------------------------

In this configuration, all of the mover nodes are directly accessible to users.
The broker does not provide data mover service, just a pure message broker.

The broker is run clustered, and all of the mover nodes have access to the same
cluster file systems.  subscribers and watchers can be started up by anyone on
any collection of nodes, and all data visible from any node.

disk space administration is entirely a user configuration setting, not in
control of the application (users set ordinary quotas for their file systems directly)

