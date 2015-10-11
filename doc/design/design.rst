
Status: Pre-Draft

=================
 Strawman Design
=================

.. section-numbering::

This document should define/reflect the current design at a more detailed level that the outline
document.  In order to explore functionality and make configuration choices, one needs to make assumptions
and work through them to determine whether the choices are a reasonable basis for further actions.

===========
Application 
===========

Description of application logic relevant to discussion.

All users are authenticated but *anonymous* is may be a valid user in some configurations.


Queues & Exchange 
-----------------

Each user Alice on a server to which she has access:

 - has an exchange xs_Alice, where she writes her postings, and reads her logs from.
 - has an exchange xl_Alice, where she writes her log messages.


Security Model
--------------

 - Alice can create and destroy her own queues, but no-one else's.  
 - Alice can only write to her xs_exchange, 
 - Exchanges are managed by the administrator, and not any user.
 - Alice can only post data that she is publishing (it will refer back to her) 


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

- A node cannot announce each product that it has downloaded, using it's own node name, because
  it does not know if other nodes have that product.  

- Either:

    -- Can only announce a product once it is clear that every active node has the product.
    -- 1st come, 1st serve:  apply chksum winnowing. announce only node that got the data first. 
  

- as in the independent configuration, nodes share queues and download a fraction upstream data.
  They therefore need to exchange data amongst each other, but that means using a non-clustered
  broker. So likely there will be two brokers access by the nodes, one node local, and one shared.

--------------
Shared-Data DD
--------------

- The load balancer hands the incoming request to multiple nodes.

- Each node has read/write access to a shared/cluster file system.

- clustered broker configuration, all 





SEP: Shared End-Point Configuration
-----------------------------------

dd - one broker.
dd1,dd2, ... all share the one big file system.


=========
Use Cases
=========

Describe the types of usage which are to be addressed by the design. What sorts of 

universal considerations/constraints
------------------------------------

   There are cluster file systems available everywhere.

   an operational team might want to monitor/alert when certain transfers esperience difficulty.

   security will want to run a scanner on it (each block?)
   security might want us to refuse certain file types, so they go through heavier scanning.
   or perform heavier scanning on those file types.


Use Cases / Deployment Scenarios 
--------------------------------

propose some strawman problems with a variety of cluster configurations to address them.
explore strengths and weaknesses.

Questions to examine for each:

   Three layers of diagram for each case:   
		post/subscribe, transport (sftp/http), log

   1. Storage Distribution
       how is storage provisioned (1 per server, common, grouped?)
       where do the files (or blocks) reside?

   2. Server Software Distribution 
       where are brokers and http/sftp servers? (together? separate scopes? )

   3. Authentication Distribution
       does it make sense to share auth between amqp and sftp? (plan to do that for http.)
       note which credentials are used where.

   4. Naming/scopes?
       what is a good name for this use case/scope?

   5. Retention quota strategy?
       how long does one keep each file/block?  
       delete immediately after passing on?  for big stuff, this makes sense.
       if in user space, upto the user.

       where do quotas apply?
  
   6. bandwidth/scaling.
       what are the limits to bandwidth for this configuration?
       where will the choke points be.
       where is a reasonable place to insert bandwidth controls?

	




Use Case 1: Transfer a 3 TiB file
---------------------------------

   
        more info:
          it will take a long time, over a wan link, latency such that single thread is slow.  Want multiple threads.
          probably want it monitored so that someone will notice if it breaks.
	  probably want it logged so that people can see what happenned when it breaks.
	  bunny style, one broker for all servers.

       likely:
	  do not want to store the entire file on an intervening server.

	  do not want separate storage from user space for the file.
		-- have disk quotas within the switching network that force
		   a retention (or discard) policy.
	
	  one broker for the configuration.


       compromises one might make:
          can mix with random user code (interactive service) because duplicating space too expensive. 
             service level is therefore limited (not op0hr)

	suggestion:
	   it stores on normal user space... no on switch storage at all.
           no special authentication, just use normal accounts?

	   just use the switch to monitor and log transfers.

	   suitable within GoC?
	


Use Case 2: somebody wants rock solid, op0hr PDS/PX style service
-----------------------------------------------------------------

       likely
	   have multiple independent servers.  each have own disk.
           data can route through any server, but space not shared for improved reliability.

	   want full dev/stage/ops for change management.
		no user code anywhere.


Use Case 2.1: Send a weather warning
------------------------------------
  

Use Case 3: a web server where users can see the files sent (dd style)
----------------------------------------------------------------------

       data dissemination...

       likely:
          have multiple independent servers for op0hr service.
		- like current dd, requires broker per server.
          
          have a multiple servers with a cluster file system for op3hr service.
		- one broker for all servers.

	  have a single server with a shared or file system for opDay service
		- one broker on the server.


Use Case 4:   send a continuous feed of tiny files. (px-paz case...)
--------------------------------------------------------------------

   acquisition ... not sure if this is different from pds/px case.

   someone (outside org) wants to send us data.
	- using straight sftp.
	- using dd_aware method.
	- using dd_watch.

   someone inside Gov. wants to do same.


Use Case 5: Acquire 1 TiB file from the internet to internal..
--------------------------------------------------------------

   as above, but the file is really big.


Name the scopes after the zones they serve?
	escience-operationsHPC-OZ
		- but there might be one for op0hr, and a second for opDay

	escience-collaborationHPC-XZ
		

Use Case 6: Notifications for Local Files
-----------------------------------------


References:
-----------

    http://spring.io/blog/2011/04/01/routing-topologies-for-performance-and-scalability-with-rabbitmq/
   
    scaling rabbitmq to 11: http://www.slideshare.net/gavinmroy/scaling-rabbitmq-to-11

    interesting bits:
	https://www.rabbitmq.com/community-plugins.html
   
		rabbitmq_delayed_message_exchange



==================
Number of Switches 
==================

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


========
Diagrams
========

The diagrams are meant to represent the network environment in which data transfers need to occur.
In General, there are many networks with firewalls that prevent direct connection from one end point
to another.  The organizations exchanging data have no trust relationship between one another, and
little technological co-operation.

This results in a a table with nine sections, reminiscent of a tic-tac-toe game, with three columns,
the side columns representing partner department networks, and the centre one representing science.gc.ca 
networks.  the three rows correspond to the the level of external access.  The top row is government
only, the middle row is extranet, where government and external collaborators work together, and the
final row is the home networks of those collaborators to which government has little or no access or
control.

The ->| sign shows traffic going from the left to the right, but not the other direction.
unidirectional flows which are staples for network zoning.

To simplify discussions, names will be selected with a prefix things according to the type
of entity: 

	- exchanges start with x.
	- queues start with q.
	- users start with u.
	- servers start with svr

As a rule:

 - extranet zones cannot initiate connections.  They receive inbound connections from anywhere.

 - Government operations zones can initiate connections anywhere.
   however, Science is considered a sort of extranet to all the partners.  

 - No-one can initiate connections into partner networks, but all partner departments can initiate
   connections into science.gc.ca zone.  within the science zones there is the shared file system
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




Thought Experiment 0
--------------------



Thought Experiment 1
--------------------

    Overview:

	user Earnest is at EC-Burlington site on the Econet (which is fairly flat.).
	he is in the cloudmechanics group (made up example)
	wants to transfer a file to the high performance computing science.gc.ca 
	
    AMQP layer:
	So Earnest fires up dd-post on server svrEC-Burlington...  
			broker target: amqp://uearnest@svrsftp.science.gc.ca/
				which means he posts on the xac_earnest exchange.

	now... science.gc.ca cannot initiate a connection to svrEC-Burlington (no inbound to EC)
        so to send it, one must do::

	    dd-sender,   
		subscribed to xac_earnest... and then sending the files
		posting the log to xac_earnest as well.
				
   Data Layer:
	local auth on server in EC using EC credentials and permissions.

	sftp -> sftp.sciencec.gc.ca ... posting to the normal science domain.


   log layer:
        log messages posted to xac_earnest... copied to system-wide xlog.   dd-src2log  ?

   1. Storage Distribution
        The storage is on the two end servers, and is normal user space no server specific storage.

   2. Server s/w Distribution.
        the user would have dd-sarracenia available to run the dd_post, and dd_sender binaries.
        it would upload using SFTP.

	sftp.science.gc.ca would be a collection of nodes with inbound SSH permitted.
	this initial address is LB´d to any of N nodes for SSH service.  AMQP goes to only 1p/1s 
	that run the broker in primary/failover mode::

		- all the nodes run SSH server (which includes SFTP service)
		- login shells or something to restrict access to file transfer only.
		- they all access a common, shared/distributed file system.
		- one rabbitmq running, shared by all.

    3. Authentication Distribution.
	The user has partner:
		 authentication on their own system.

	do dd-post they authenticate to the sftp´s rabbitmq server.
		username  u
 
        so Earnest has  uNRCernest@nrc.ca,  ucloudmech@sftpsw? for the broker, and ear001@science.


    4. Naming/Scopes
       there is the sftp nodes::

		svrsftp1, svrsftp2, .. svrsftpN,   
		svrsftpB1, svrsftpB2 (broker nodes)  shared with sftp, or on the side?
		svrlb1, svrlb2 -- load balancers to assign connections.

		the whole scope is called ´sftp´ ?	

     5. Retention/Quota strategy.

	There is no store/forward in this case.  it goes from user space on one end to user space
	on the other.  Let normal user quotas take care of it. the ftp_sender can report
	problems via logging.

	these logs can automatically trigger alerts to netops.


     6. bandwidth/scaling
	If you fire up n-dd_senders, they will initiate n connections to sftp. the lb´s with
	assign them to different nodes.


     Observations:
	this is not a compelling use case for this application because it is easily served
	by a direct bbcp or sftp.  this case is perhaps more illustrative than useful.

	On the other hand, the comprehensive logging means that even if the process is entirely
	under user control, monitoring processes can see it, and we may be able to alert if
	anomalies are observed.   another benefit might be that using group account for AMQP,
	there might be a means of implementing bandwidth quota on the transfer. (not as
	currently described.)

	This transfer methods allows for virtually unlimited file size to be transferred,
	as there is no intervening store and forward.

	Parallelism for performance can be achieved by blocking and sending the blocks independently.
	similar to bbcp/gridftp


Diagram 2
---------

    Overview:
	Gerald @ Genetech has produced a sequence from a sample provided by Norman @ NRC.
	Gerald uploads the sequence to our extranet facing ingest system.

	Norman works on the HPC side to analyse the sequence, but he also might use it on
	his own local processing.

	variations:

	.1 Gerald uses dd_post/dd_send

	.2 Gerald uses dd_post (no send) we fetch via 

	.3 Gerald just sftp´s it in, and we use dd_watch.


	once it is on dd.collab, it is announced ...

	inside, user uNor001 is running a dd_subscribe to dd.collab,
	sees the data is available, and downloads it directly to his
	file system.  

	he could use dd_sara to do , in which case it will re-announce 
	the file on sftp for availability from his nrc account.

	this is good because within his file space he has total control
	over removal policies, and placement.

	So it is announces as available on sftp... which his NRC user
	is subscribed to, and so can be used to copy it to his NRC
	account.


    AMQP layer::

	.1 dd_post to xac_Gerald
	   dd_send sends the file 
		when done it emits  v01.log.uGerald.uGerald ...

	   dd_something ...  dd_ingest?  
		notices the log.u.u.
		does pre&post validation check on the file received.
		moves (day and client subtree, for example)
		and chowns it to a dd.science owned directory.
		then re-announces it to downstream-broker.

	
	.2 dd_post


    Data Layer:
	genentech disk to dd.collab disk as uGer001
	
    Log Layer:
    1. Storage Distribution
    2. Server s/w Distribution.
    3. Authentication Distribution.
    4. Naming/Scopes
    5. Retention/Quota strategy.
    6. bandwidth/scaling
    Observations:


Diagram 3
---------

    Overview:
	Edmond from Environment Canada, from the climate research wants to make data available both to the public
	and colleagues within government in a reliable way (24x7)

    AMQP layer:
        dd_post to ddsr.science.gc.ca to xclimate_research
		dd_sara/validates & dispatch.
		
		svrddsr1 fetchs a file via sftp to post on local http svr.
			(assuming possible ... see data layer)

		works as uddsr on the AMQP level...

		readvertises as ddsr1 to:  xto_ddi, xto_dd

		ddi1, ddi2, are subscribed to xto_ddi, and they pull the data down.

		dd_sender is subscribed to put the files on dd.collab.
			posts to xfrom_ddsr on dd.collab ?
				or just straight to xPublic?
				as amqp user uddsr?

			or as amqp user udd  ?


    Data Layer::
	
        .1 switch in EC
	ddsr initiates an sftp retrieval from the EC to Science system 
		(will not work, blocked by fw)
		this does work if there is a switching level within EC.

	  .0 no switching layer within EC:
		EC user uses dd_send to upload.

        once on svrDDSRx
		ddiX will pull via http from svrDDSRx
		svrDDSRx will sftp to dd.collab.

	clients pull from dd and ddi via http


    Log Layer:
	
	.1
		v01.log.uclimate_research.uddsr 200  -- retrieved by ddsr
	.0
		v01.log.uclimate_research.uclimate_research 200  -- delivered by client.

		(dispatch is silent?)

		v01.log.uclimate_research.uddi 200  -- delivered to ddi
		v01.log.uclimate_research.udd 200   -- delivered to dd

FIXME:
	so when uploaded by client you see log message v01.log.u.u 200 
		something watches the xac_u exchange, and when it sees that, it
		triggers a validation step (pre and post), and if it is OK,
		it moves it to a waf accessible directory and re-announce
		as normal.


    1. Storage Distribution
		user EC auth on EC server at source.

	.1
		copies directly to the right place by ddsr (trusted process)

	.0
		client copies to sftp upload area (not trusted)
		<this needs to move to a ´trusted´ area (ie. www visible.)

    2. Server s/w Distribution.
	remote host has dd-sarracenia clients, dd_post (.0) and dd_send (.1)
	ddsr needs sftp server, and one (H/A) rabbit per cluster?
	 


    3. Authentication Distribution.
	 EC auth on EC system.  (.0) EC assigns auth for ddsr to connect to EC system.
		in (.1) ddsr assigns auth for EC user on ddsr for upload

	in .0
	 once on the switch, it somehow becomes ddsr property (a chown?)
		then needs to pu

    4. Naming/Scopes


    5. Retention/Quota strategy.
    6. bandwidth/scaling

    Observations:
	While Edmond makes a single post, this could result in many different servers copying
	the data.  It is simply an injection into a file propagation network.



Diagram 4
---------

::

    Overview:
    AMQP layer:
    Data Layer:
    Log Layer:
    1. Storage Distribution
    2. Server s/w Distribution.
    3. Authentication Distribution.
    4. Naming/Scopes
    5. Retention/Quota strategy.
    6. bandwidth/scaling
    Observations:

Diagram 5
---------

::

    Overview:
    AMQP layer:
    Data Layer:
    Log Layer:
    1. Storage Distribution
    2. Server s/w Distribution.
    3. Authentication Distribution.
    4. Naming/Scopes
    5. Retention/Quota strategy.
    6. bandwidth/scaling
    Observations:

Diagram 6
---------

::

    Overview:
    AMQP layer:
    Data Layer:
    Log Layer:
    1. Storage Distribution
    2. Server s/w Distribution.
    3. Authentication Distribution.
    4. Naming/Scopes
    5. Retention/Quota strategy.
    6. bandwidth/scaling
    Observations:

Diagram 7
---------

::

    Overview:
    AMQP layer:
    Data Layer:
    Log Layer:
    1. Storage Distribution
    2. Server s/w Distribution.
    3. Authentication Distribution.
    4. Naming/Scopes
    5. Retention/Quota strategy.
    6. bandwidth/scaling
    Observations:


