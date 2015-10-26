
Status: Pre-Draft2

===================
Implementation Plan
===================


Overview
========


focus documents go through status:

  - pre-draft  - document being create/modified, not ready for review.
  - draft1 - document ready for review.
  - approved-draft1 - document reviewed and approved.

	draft1...N
	

Design Principles
-----------------

 - The switching software knows as little as possible about the data being transferred.
   no data parsing should be necessary for the software.  The only data parsed is
   what is defined in the dd_post(7) and dd_log(7) manual pages, and the various 
   configuration files.



Critical Features for Initial Release
-------------------------------------

Trying to figure out when we will be ''done'' for a first release.
After First Release, can roll it out properly.  For now, just rolling things out
to minimal number of systems to have test beds.  It is important for the initial 
release to have sufficient maturity to be usable.  Usable means it would pass 
various hurdles, such as acceptable security, coverage of use cases, etc...


  1. ( *Done* ) **post messages updated**
     The message format to support new features must be implemented.
     (progressed through v01, and v02 designs.) 
 
     criteria:  dd_* tools produce and process v02 messages as described by 
     dd_post.7 man page. 
 
  2. ( *Done* ) **multi-part segmentation/re-assembly** 
     There must be no limitation on maximum file size that can traverse the network.
     Eliminating file size restrictions is accomplished by sending parts of the
     file through the network at a time, so that no intervenining switch is required
     to store the entire file.
 
     On Long-haul links, a single connection suffers greatly from round-trip latency.
     for high performance transfers, a simple speedup is to send the data as multiple
     streams.  segmentation/reassembly enables this easy-win speed up over longhaul links.
 
     criteria: implementation of parts header in dd_post(7), successful transfer
     of multi-part files across a single hop.
 
  3. ( *Waiting* ) **multi-part completion triggering.**
     When a file is segmented (because it is large), the pieces may arrive in arbitrary order.
     Data users need to know when all of the pieces have arrived, so that they can start their
     processing.  Not clear how to do that yet.  Addressing other features while thinking
     about this.
 
     criteria: trigger a post-reception script after the last block is processed
     when a files blocks have not been delivered sequentially.
 
 
  4. ( *Done* ) **log message creation.**
     It isn't enough to deliver data to clients.  Sources must know which clients received
     which data.  Delivery logs are information that data sources are very interested in
     and needs to be granularly deliverable (ie. if Alice injects a product, she can know
     where her data went, but she cannot see where products inserted by Bob went.) 
     current system logs are binary (can see all or none) which makes logs difficult to share.
     Instead of relying on traditional log files, the records of delivery are a flow
     of individual messages which can be granularly routed.
 
     criteria: log messages created, read with dd_subscribe.
 
 
  5. ( *InProgress* ) **user-centric multi-switch log message routing.**
     Using the same mechanisms as the announcements (AMQP messages) but conceptually 
     in the opposite direction (flowing from consumers back to sources.)
     This is accomplished by ensuring that log messages for consumption are sent
     back throught the switching network to get to where the source can view them.
 
  6. ( *Waiting* ) **source data routing (over multiple switches).**
     Currently, routing through multiple switches is done manually by admins.
     Admins manually configure each intervening switch for each data set's routing needs.
     
     A user cannot specify the switches to which data should be sent.
     Giving users that capability is a design goal of the project.
     Need a relatively simple model for the data sources to specify the distribution
     of their data.  This is to be addressed after log message routing.
 
  7. ( *InProgress* ) **multi-user support.**
     In previous iterations, all product insertion was trusted (done by administrators)
     In this version, sources are distinct from adminsitrators, and so a lower
     level of familiarity with the system is expected, greater simplicity is needed,
     and input sanitation is necessary.
 
     Criteria:
     A user should be prevented from inserting (log or post) messages that appear to 
     come from another user.  A user should be able to read their own log messages, 
     but not those of others.
 
 
  8. ( *Waiting* ) **Triggering**
     After a product is received, users must be able to configure scripts to
     trigger their procesing activities.
      
     criteria: dd_subscribe called with a scipt that does a tail on the file received.
     so you can see that the complete file is there before it runs. or run a checksum
     or something.
 
  9. ( *Waiting* ) **Automated Linux Builds & Packaging**
     It should not be separate work to produce packages to/from pypi and for debian/ubuntu. 
     to make packages.  Need to offload packaging to someone else, and have it automated
     so that the process is trivially simple, and so that others have packages they 
     can use the packages built.
 
     Criteria: daily snapshot dpkg files produced if commits are done during the 24 hours. 
     pypi automatically updated from sf.net ? use pypi/stdeb to produce .deb ?  It should
     install documentation and examples also in standard locations.
 
  
 10. ( *Waiting* ) **Manual dd_subscribe windows package**
     A build environment with several windows vm's to build and test dd_subscribe packages.
     require an .msi package containing a nuitka compiled binary.
     a documented in a guide for building a dd_subscribe package manually.
	
     
 11. ( *Waiting* ) **User Initiated HTTPS Private Transfers: Alice to Bob**
     In Contrast to weather data which is mostly public, in NRC, it would appear that
     most data transfers of interest are relatively private.  Just providing unrestricted
     access to data on a web server will not sufficient.
 
     Need to provide the data injector (source) with the ability to restrict which
     users can download data on remote clusters.

     Likely requires implementation of adm messages to configure htpasswd on directories.

     Pending Dependencies: Multi-User Support, Source Data Routing.

     Criteria:  
     dd\_?? command issued on one switch, triggers htpasswd restriction
     on another switch.
     Alice is on SwitchA, Bob has access to SwitchC, data goes from A to C via SwitchB.
     Eve running dd_sub on SwitchB should not be able to intercept.

 12. ( *Waiting* ) **Admin Guide/Functions**
     Need to document all the steps in setting up a switch in whatever cluster configurations
     are deemed appropriate (standalone first, then perhaps ddsr, and others.)
     Perhaps easier to build simple commands, than complicated documentation.
     tradeoffs.
     
     Pending Dependencies: Alice to Bob, Multi-User Support, Source Data Routing, Automated Linux Builds

     Criteria:
     doc tested by someone using it to configure a standalone switch, from vanilla linux server.
     Documented method to add a user, add an interswitch connection, start up all the plumbing 
     processes.  How to configure SARA to read from sx_user and post.  How to configure 
     pre-fetch (message), and post-fetch (file) validation. 

 12. ( *Waiting* ) **User Guide/Functions?**
     Walk through some use cases, to show how to apply the tool to a variety of problems
     at hand.  Perhaps just beef up the use cases?  Perhaps some demos?

     Criteria:
        someone manages to set up a file transfer using only the guides.
        Example...

 13. ( *Done* ) **End-User Operating Mode**
     Should be easy to use in a way where no cron jobs or other accessories are required, 
     just set the config files and go.  One user just invokes it, like rsync or scp.

 14. ( *Waiting* ) **Service Provider Operating Mode**
     Ability to start up the configuration of a whole series of components together.
     Stop them together. like what was done for Sundew, cups, nqs, etc...
     put all the logs in a common place, the configs in one place, start up ten different
     configurations together...

 15. ( *Waiting* ) **Bandwidth Limiting**
     Need to be able to avoid saturating long links by limiting bandwidth usage.
     This needs to work over multiple nodes in DDSR, or SEP topologies.
     Suspect best path is to throttle message posting out of pre-validation?



Parking Lot For Initial Release
-------------------------------

Items which can be deferred past initial deployment. Items which are *Waiting* will need
to be initiated as quickly as possible after initial release.  *Deferred* issues have no
specific time line.

(offset numbering to keep separate from initial ones.)

 20. ( *Waiting* ) Nagios integration, via speedos?
     If we get the thing running, once there are users, this becomes important, but
     for initial release, not clear that this is critical.

 21. ( *Waiting* ) **Automated Windows client builds & packaging**
     It is very much expected that a number of uses will want to obtain data from windows
     laptops or servers.  the dd-subscribe command is the minimum tool needed to
     do that effectively.

     Configuring python as a dependency is rather complicated on windows.
     Simplified dd_subscribe client (http-only) can be compiled using nuitka and then rolled
     into an MSI.  Need to put in place an automated process to build those.
    
     Criteria:  dd_subscribe package for windows built automatically (daily?) 

 22. ( *Waiting* ) **Redhat Linux Packaging**
     Add to the automated build something that builds rpm packages for centos/redhat/scil.

 23. ( *Deferred* ) **Websocket Gateway**
     Using Kazaa or some other technology to make connections possible from web sockets.
     This would remove the need for a separate protocol (AMQP, usually port 5672) as all
     the control traffic would occur over a web connection.  One could implement
     clients directly in a browser.

 24. ( *Deferred* ) **GUI for dd_subscribe configuration**
     Graphical user interface to create configuration files might be handy for end users.
     Not clear how useful/important this is.  
   
 25. ( *Waiting* ) **web config file inclusion**
     Ideally, sources could provide configuration snippets for their data types that could
     be on the switches, and directly referenced on the web sites by config files.
     So sources could move directories around, and just publish updated configurations to
     reflect the change.
     

Critical Deployment Elements
----------------------------

The initial release does not just need to be ready, it needs to be deployed.  Deployment and development are linked, in that we do not encounter difficulties unless something is deployed, and we do not achieve business deliverables unless we deploy.  So there is an iterative loop, and we expect to upgrade frequently since the package is so young.

To upgrade frequently, we need to reduce the friction to producing upgrades.

ddi.cmc.ec.gc.ca
~~~~~~~~~~~~~~~~

The Dorval ddi (Data Distribution - Internal) needs to be compatible with the existing
public dd (Data Distribution, aka Data Mart) but also provide a model from which copies
to Edmonton are made.  The model for edmonton is under the ´sources/´ directory.

The root directory of ddi.cmc.ec.gc.ca
 - Demonstrates Independent DD Topology.
 - Demonstrates cross-feed DD Topology.
 - Provides source for Fingerprint Winnowing for Storm Prediction Centres



ddi.edm.ec.gc.ca
~~~~~~~~~~~~~~~~

The Edmonton version of ddi is the test bed for the ´next´ layout of data.

 - Demonstrates Independent DD Topology. 
 - Demonstrates cross-feed DD Topology.
 - Provides source for Fingerprint Winnowing for Storm Prediction Centres


Convert urp to dd_post ?
~~~~~~~~~~~~~~~~~~~~~~~~

FIXME: Is this a good dog-fooding exercise?  The URP people are asking about this.
We need to figure out if/when data feed methods will change.


Figure our URP 2.9.2 Data Feed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

URP people are asking questions about data feeds.  SPC´s using FTP today, inbound
and outbound.  NURP is using FTP inbound, but fingerprint winnowing and a prototype
version of posting via Sundew scripting.   What is reasonable in the time available?

The ambitious plan:
 - Measure the difference in arrival time, SPC vs. CMC?
 - Can move 2nd feed to Edmonton? volume scans cross network twice?
 - use sarracenia methods both ways: dd_subscribe with Fingerprint winnonwing
 - How many vm´s/SPC one or two?


The conservative plan:
 - use same as today. FTP bothways for SPC´s,
 - FTP in for CMC, fingerprint winnowing outbound.
 - single vm with failover.
 - URP people might not like the variability...

in between plan:
 - use FTP in everywhere.
 - no shared drive two standalone vm´s.
 - use sarra outbound only, but everywhere.


Someone Other Than Michel Feed Sundew->DD
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All of the feeds for dd that currently use sundew as the *bootstrap* to create initial
data sources for the dd/ddi ´



Iterations
==========

These iterations were the plan last spring.  They turned out to be humourously inaccurate.
Trying the feature list above, rather than a schedule.  This is essentially historic 
But there isn´t a plan to replace it yet.  A new plan should come out of the feature work
done above.  For now, just stop reading here...

  - 1 iteration per month.

  - at least a .dpkg produced per iteration.

  - run stuff once per iteration on windows to see it vaguely works.
    (don't package it, just try it out.)
    if it doesn't work on windows, note the problem, that's all.
    until we get to packaging...

  - Design work needs to run one iteration ahead.
    features of iteration 3 need to be firmed up in iteration 2.

  - at the beginning of the month, the initial focus documents are agreed.
    through the month, they evolve.

  - at the end of the month, features corresponding to the focus documents 
    have been implemented, and the focus documents updated to reflect them.

  - at end of each phase, revise plan.txt



Iteration 0 
-----------

focus: Outline.txt, the glossy design.vsd

initial versions of all the focus documents, and plan.txt



Iteration 1: Block-oriented Transfers and Logs: June
----------------------------------------------------

focus: deltas.txt, logmessages.txt, dd_post_sample.txt

   dd_post, dd_sara, and dd_subscribe 

   validate that AMQP over SSL works, because it will all need to be there.

   implements v01.notice, and v01.log
   maintains compatibility with v00 (so subscribe can read v00.)
   
   - does blockwise checksums.

   - does just enough validation to do the YMD/<source> thing.

   - dd_post should not do validation (so easier to test psychotic settings
      like 1 byte blocks.)

   post to a switch, sara build a site, dd_subscribe pulls from it.
	             logs build                      logs pull

   - use a single exchange (no source exchanges etc...)
   - logs just go to log exchange.

HW: whatever is lying around.

... meanwhile in GPSC...
    someone is building ssh servers in science.gc.ca for interactive...
    some nodes for sftp & bbcp ... these will just use



Iteration 2: Directory Watch: July
----------------------------------

   focus: cluster.txt
	- because then we need to get hw implemented next iteration.


   watch a directory, and post what is there (flat)
	- using inotify (kernel feature), or perhaps inotifywait (as a wrapper process.)
	- only needs to work for a flat directory at first.

   deferred: windows version of dd_watch (no inotify available.)
	question, if this is built as inotifywait calling dd_post (or something like that.)
	then there is an inotify-win.  just introduces a dependency... but makes it easy.


   base user-facing delivery function done.

   do speedos (see monitoring.txt)

   figure out whether we need a dd_log, or if dd_subscribe is enough.
    
   testing, testing, testing...

HW: whatever is lying around.



Iteration 3:  Security/Authentication, Transition Strategy:  August
-------------------------------------------------------------------

   focus: validation.txt, accounts.txt, 

   - now start using the exchanges correctly.

   - LDAP realms are ready.
	design is done.
	user mirroring.

  add the source_<user> exchanges.
   log2source routing thing.

  v01.permit.
		set
		get

   move all the of amqp traffic to SSL.
   validation of same 

   create .htaccess files using sara and subscribe
	- re-create them each day


 understand the situation with new PX, old PX, px-inter.
 need to pick a strategy that minimizes future work.
 determine how Sundew and Sarracenia work together.

 somebody add windows directory polling.

HW:  initial config... in ec.gc.ca  or science.gc.ca ?

    ddsr1.cmc.ec.gc.ca ... these could be in science.gc.ca ?
    ddsr2.cmc.ec.gc.ca ... why not?

    use existing ddi and dd.beta... eventually dd


Iteration 4: Management: September
----------------------------------

focus: configuration.txt, monitoring.txt, scope.txt, packaging.txt

add operator monitoring (read-only at first)
	- nagios based on speedos?

add configuration settings / management.

	analysts operators can stop/start ingest,
	set things in discard.

	set bandwidth-quotas per source


implement scopes/distribution

helpdesk...
Figure out how to get users created (UVL? something else?)



Iteration 5: Operations for Science.gc.ca.: October
---------------------------------------------------


	all the science ones should be AMQP/SSL.

Analyst training.

Security scanning...
	... hmm...

HW:
  add:  
    ddsr1.science.gc.ca
    ddsr2.science.gc.ca

    di1.science.gc.ca
    di2.science.gc.ca

    dd1.collab.science.gc.ca
    dd2.collab.science.gc.ca
	

    say for URP, the chain could be nurp->ddsr.ec-><push>->ddsr.science.gc.ca
		->di1.science.gc.ca, <push> dd1.science.gc.ca

    do logs make it back from science to urp ?	yes it just shovels from it's own echange
    on ddsr to it's own and it keeps going back to urp. cool.



Iteration 6: Packaging & Acquisition from outside: November
-----------------------------------------------------------

So far it's all sources that are inside, and we are pushing internal or to outside.
what about accepting data from outside?

Are they just ordinary sources?

Can we make it really easy to build a ddsr node. for other people to deploy.
so it is easy for others to adopt.   Recipe for a standlone single node config.


Figure out packaging?
	
start making other packages?
	redhat/centos?
	windows?

	do we make it 'pip' compatible?
		so on windows they install python, then pip pulls in deps?


End of Phase 1
--------------

     Success criteria:
	operating di.science.gc.ca cluster.
	operating dd.science.gc.ca cluster.
	operating ddsr.science.gc.ca cluster?

	operating ddi.edm.ec.gc.ca cluster
	operating dd*.* in ec, with 'new' model available.
	transition begun.

	fully NAGIOS's. no other monitoring needed (I hope.)

     November to March...
	clean up from phase 1.
        move transition forward.


Phase 2:  (Next FY)
-------------------
     
     - migration of systems.

     - performance tuning/accelleration.
       see if there is some obvious 'go faster' stuff.
       do we want to support bbcp, or is per block threading better anyways?
       setsockopts/buffers, etc... probably a whole year there.
       but need some deployments to see issues, and address pain points,
       rather than guessing.

     - migrate from AMQP/s to https websockets (every broker runs a gateway.)
       to eliminate firewalling issue. 
       focus document: webification.txt
       all the AMQP functionality used in phase1 remains unchanged.
       the only change is that the client programs might use a websocket:
       to initiate their AMQP connections tunnelled through ws:
       this will remove the need to permit AMQP protocol connections,
       making firewall stuff easier.
       if we do ws:, then it would web socket over SSL, and we no longer
       need AMQP/S,
       Kazaa provides this, but it's commercial... free one might not be 
       jwebsocket.org looks promising...
       hard (ie. hardcode proxy to localhost.)

     - GUI'ish enablement ?
	   TBD.



