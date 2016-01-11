
Status: Pre-Draft3

===================
Implementation Plan
===================


Overview
========


focus documents go through status:

  - successive drafts are numbered: draft1...N. 
  - pre-draft1  - document being create/modified, not ready for review.
  - draft1 - document ready for review.
  - approved-draft1 - document reviewed and approved.


Revision Record
---------------

 - Draft1 approved in June 2015
 - Draft2 circulated in prior to November 4th internal meeting.


.. contents::

Design Principles
-----------------

- The pumping software knows as little as possible about the data being transferred.
  no data parsing should be necessary for the software.  The only data parsed is
  what is defined in the sr_post(7) and sr_log(7) manual pages, and the various 
  configuration files.

- Minimize the need for nudging by administrators of data in flight. It is 
  best if the source can define where they want the data to go.

- if the client did not get a log message that something happenned, it might as well
  not have happenned.  Client specific logging is a critical element of the application.


Critical Features for Initial Release
-------------------------------------

Trying to figure out when we will be ''done'' for a first release.
After First Release, can roll it out properly.  For now, just rolling things out
to minimal number of systems to have test beds.  It is important for the initial 
release to have sufficient maturity to be usable.  Usable means it would pass 
various hurdles, such as acceptable security, coverage of use cases, etc...

  1. ( *Done* ) **post messages updated**

     Assigned to: Michel Grenier

     The message format to support new features must be implemented.
     (progressed through v01, and v02 designs.) 
 
     criteria:  sr_* tools produce and process v02 messages as described by 
     sr_post.7 man page. 
 
  2. ( *Done* ) **multi-part segmentation/re-assembly** 

     Assigned to: Michel Grenier

     There must be no limitation on maximum file size that can traverse the network.
     Eliminating file size restrictions is accomplished by sending parts of the
     file through the network at a time, so that no intervenining pump is required
     to store the entire file.
 
     On Long-haul links, a single connection suffers greatly from round-trip latency.
     for high performance transfers, a simple speedup is to send the data as multiple
     streams.  segmentation/reassembly enables this easy-win speed up over longhaul links.
 
     criteria: implementation of parts header in sr_post(7), successful transfer
     of multi-part files across a single hop.
 
  3. ( *Waiting* ) **multi-part completion triggering.**

     Assigned to: Michel Grenier

     When a file is segmented (because it is large), the pieces may arrive in arbitrary order.
     Data users need to know when all of the pieces have arrived, so that they can start their
     processing.  Not clear how to do that yet.  Addressing other features while thinking
     about this.
 
     criteria: trigger a post-reception script after the last block is processed
     when a files blocks have not been delivered sequentially.
 
 
  4. ( *Done* ) **log message creation.**

     Assigned to: Michel Grenier

     It isn't enough to deliver data to clients.  Sources must know which clients received
     which data.  Delivery logs are information that data sources are very interested in
     and needs to be granularly deliverable (ie. if Alice injects a product, she can know
     where her data went, but she cannot see where products inserted by Bob went.) 
     current system logs are binary (can see all or none) which makes logs difficult to share.
     Instead of relying on traditional log files, the records of delivery are a flow
     of individual messages which can be granularly routed.
 
     criteria: log messages created, read with sr_subscribe.
 
 
  5. ( *Done* ) **user-centric multi-pump log message routing.**

     Assigned to: Michel Grenier

     Using the same mechanisms as the announcements (AMQP messages) but conceptually 
     in the opposite direction (flowing from consumers back to sources.)
     This is accomplished by ensuring that log messages for consumption are sent
     back throught the pumping network to get to where the source can view them.

     criteria:  log message inserted at one pump is routed correctly to a source
     which inserted the relevant post into another pump.
 
  6. ( *Done* ) **source data routing (over multiple pumps).**

     Assigned to: Michel Grenier

     Currently, routing through multiple pumps is done manually by admins.
     Admins manually configure each intervening pump for each data set's routing needs.
     
     A user cannot specify the pumps to which data should be sent.
     Giving users that capability is a design goal of the project.
     Need a relatively simple model for the data sources to specify the distribution
     of their data.  This is to be addressed after log message routing.
 
  7. ( *Done* ) **multi-user support.**

     Assigned to: Michel Grenier

     In previous iterations, all product insertion was trusted (done by administrators)
     In this version, sources are distinct from adminsitrators, and so a lower
     level of familiarity with the system is expected, greater simplicity is needed,
     and input sanitation is necessary.
 
     Criteria:
     A user should be prevented from inserting (log or post) messages that appear to 
     come from another user.  A user should be able to read their own log messages, 
     but not those of others.
 
 
  8. ( *Done* ) **Triggering**

     Assigned to: Michel Grenier

     After a product is received, users must be able to configure scripts to
     trigger their procesing activities.
      
     criteria: sr_subscribe called with a scipt that does a tail on the file received.
     so you can see that the complete file is there before it runs. or run a checksum
     or something.
 
  9. ( *Done* ) **Automated Linux Builds & Packaging**

     Assigned to: Khosrow Ebrahimpour

     It should not be separate work to produce packages to/from pypi and for debian/ubuntu. 
     to make packages.  Need to offload packaging to someone else, and have it automated
     so that the process is trivially simple, and so that others have packages they 
     can use the packages built.
 
     Criteria: daily snapshot dpkg files produced if commits are done during the 24 hours. 
     pypi automatically updated from sf.net ? use pypi/stdeb to produce .deb ?  It should
     install documentation and examples also in standard locations.
 
  
 10. ( *Waiting* ) **Manual sr_subscribe windows package**

     Assigned to: Stéphane Charlebois

     A build environment with several windows vm's to build and test sr_subscribe packages.
     require an .msi package containing a nuitka compiled binary.
     a documented in a guide for building a sr_subscribe package manually.
	
     
 11. ( *Waiting* ) **User Initiated HTTPS Private Transfers: Alice to Bob**

     Assigned to: ??

     In Contrast to weather data which is mostly public, in NRC, it would appear that
     most data transfers of interest are relatively private.  Just providing unrestricted
     access to data on a web server will not sufficient.
 
     Need to provide the data injector (source) with the ability to restrict which
     users can download data on remote clusters.

     Likely requires implementation of adm messages to configure htpasswd on directories.

     Pending Dependencies: Multi-User Support, Source Data Routing.

     Criteria:  
     sr\_?? command issued on one pump, triggers htpasswd restriction
     on another pump.
     Alice is on SwitchA, Bob has access to SwitchC, data goes from A to C via SwitchB.
     Eve running sr_sub on SwitchB should not be able to intercept.

 12. ( *Waiting* ) **Admin Guide/Functions**

     Assigned to: ??

     Need to document all the steps in setting up a pump in whatever cluster configurations
     are deemed appropriate (standalone first, then perhaps ddsr, and others.)
     Perhaps easier to build simple commands, than complicated documentation.
     tradeoffs.
     
     Pending Dependencies: Alice to Bob, Multi-User Support, Source Data Routing, Automated Linux Builds

     Criteria:
     doc tested by someone using it to configure a standalone pump, from vanilla linux server.
     Documented method to add a user, add an interpump connection, start up all the plumbing 
     processes.  How to configure SARRA to read from sx_user and post.  How to configure 
     pre-fetch (message), and post-fetch (file) validation. 

 12. ( *Waiting* ) **User Guide/Functions?**

     Assigned to: ??

     Walk through some use cases, to show how to apply the tool to a variety of problems
     at hand.  Perhaps just beef up the use cases?  Perhaps some demos?

     Criteria:
        someone manages to set up a file transfer using only the guides.
        Example...

 13. ( *Done* ) **End-User Operating Mode**

     Assigned to: Michel Grenier

     Should be easy to use in a way where no cron jobs or other accessories are required, 
     just set the config files and go.  One user just invokes it, like rsync or scp.

 14. ( *Waiting* ) **Service Provider Operating Mode**

     Assigned to: ??

     Ability to start up the configuration of a whole series of components together.
     Stop them together. like what was done for Sundew, cups, nqs, etc...
     put all the logs in a common place, the configs in one place, start up ten different
     configurations together...

     Depends on: Config File Paths.

 15. ( *Waiting* ) **Bandwidth Limiting**

     Assigned to: ??

     Need to be able to avoid saturating long links by limiting bandwidth usage.
     This needs to work over multiple nodes in DDSR, or SEP topologies.
     Suspect best path is to throttle message posting out of pre-validation?


 16. ( *Done* ) **Config File Paths**

     Assigned to: Michel Grenier

     Not baked yet.

     ~/.config/sarra/  ... default.conf, and credentials

 17. ( *Done* ) **Credential Store**

     Assigned to: Michel Grenier

     This one is only in ~/.conf/sarra/credentials.conf
     Have a file format where passwords, and pointers to other credentials (keys) 
     are stored, so that tools just refer to user@cluster, and look them up here.
     Otherwise credentials end up on command-line, which is bad.
     just a full URL + priv_key=

 18. ( *InProgress* ) **Apache Access Control**

     Assigned to: Khosrow Ebrahimpour

     have permissions (htaccess files in apache) so that
     control to folders is implemented as sara writes the file.
     creation of admin messages to control the content of the htaccess files.
     this feature does not require setting passwords or directory integration,
     just creations and modification of htaccess files.

     perhaps in two steps:  1st under admin control.  2nd: define v02.adm messages
     so that sources can set their own access control.


Release Blockers
~~~~~~~~~~~~~~~~

The list of things that are currently blocking graduation to the next quality
standard.  If we are in Alpha, then the list of issues prevents graduation to
beta, if in beta, then to release:

- ~/.conf/sarra/credentials.conf -- permissions.
  should force credentials to 600.

- sr_sender1 does not exist.

- sr_sender2 does not exist.

- sr_winnow does not exist.

- Cannot run as a pump (currently only start individual components.)
  need functioning equivalent to sundew´s: px start 

- User guide docs do not exist.

- Admin Guide not complete.

- sr_police (a scheduled watch dog to make sure all is cool) does not exist.

- when to trigger on_file when files are multi-part.
  Inplace True

  - An old version of the file is already on the server.
  - A newer version is coming in…  same size.
  - send its announcement parts randomly.
  - Since they all fit in… they are all downloaded in place.
  - Since it is random the last part can be amoung the first one to be inserted.
  - Calling the on_part is obvious.
  - don’t have a clue when it is finished and when to call the final on_file…   

  Could write a state file writing the parts inserted and when complete, 
  remove this file and invoke on_file.  But there is a race condition when 
  multiple instances want to update the state file.
 
- locking in sr_subscribe (as in dd_subscribe) except call it: 'inflight'
 

Known Bugs
----------

-- Multi-processing on windows... 
   only works as long as instance=1
-- remove is not propagated among switches.
-- new connection for every transfer (have connections persist.)

-- when receive a post for an older version of a file, what you download will not match
   the post. it generates a bogus checksum mismatch error.
  
   possible fix:
     -- add file modification time to the v02 messages.
        date/time encoding will be interesting, perhaps same as log message?
     -- if the file exists, and the v02 announcement is older than the file, then squawk 
        info ´posting older than file already received´)
     -- when we download, run os.utime (both windows and linux!) to set the modification time
        of the file, using the LastModificationTime HTTP header, + equivalent with SFTP.
     -- when a file is downloaded, compare the mtime of the file to that in the header
        with the one stored in the v02 announcement.
     -- if the v02 announcement is older than the file, then squawk 
        info ´downloaded data newer than posted´
        


Parking Lot For Initial Release
-------------------------------

Items which can be deferred past initial deployment. Items which are *Waiting* will need
to be initiated as quickly as possible after initial release.  They were only deferred to limit
scope and accellerate initial version.  *Deferred* issues have no
specific time line.

(offset numbering to keep separate from initial ones.)

 50. ( *Waiting* ) Nagios integration, via speedos?
     If we get the thing running, once there are users, this becomes important, but
     for initial release, not clear that this is critical.

 51. ( *Waiting* ) **Automated Windows client builds & packaging**
     It is very much expected that a number of uses will want to obtain data from windows
     laptops or servers.  the sr_subscribe command is the minimum tool needed to
     do that effectively.

     Configuring python as a dependency is rather complicated on windows.
     Simplified sr_subscribe client (http-only) can be compiled using nuitka and then rolled
     into an MSI.  Need to put in place an automated process to build those.
    
     Criteria:  sr_subscribe package for windows built automatically (daily?) 

 52. ( *Waiting* ) **Redhat Linux Packaging**
     Add to the automated build something that builds rpm packages for centos/redhat/scil.

 53. ( *Deferred* ) **Websocket Gateway**
     Using Kazaa or some other technology to make connections possible from web sockets.
     This would remove the need for a separate protocol (AMQP, usually port 5672) as all
     the control traffic would occur over a web connection.  One could implement
     clients directly in a browser.

 54. ( *Deferred* ) **GUI for sr_subscribe configuration**
     Graphical user interface to create configuration files might be handy for end users.
     Not clear how useful/important this is.  
   
 55. ( *Waiting* ) **web config file inclusion**
     Ideally, sources could provide configuration snippets for their data types that could
     be on the pumps, and directly referenced on the web sites by config files.
     So sources could move directories around, and just publish updated configurations to
     reflect the change.
     
 56. ( *Waiting* ) **ability to change password**
     This might be tough...

 57. ( *Waiting* ) **Directory Integration**

     Need to be able to use ActiveDirectory as the source for user info.
     Not sure if this means being able to use Kerberos or not.
     This is important to several NRC use cases, may be skewered if not present.

Known Gaps
~~~~~~~~~~

Things we need to keep in mind... solutions are perhaps not fully determined yet.
These items will graduate to features at some point.


101. ( *Critical?* ) If a firewall prevents SARA from pulling data from an sr_post,
     there is no simple sr_* ish way to send the data to a pump.  *sr_put* is 
     conceived as a program that uses instances to start up a bunch of streams
     and round-robins sending to the pump... on the pump, normal SARRA picks it up.
     This component has a working title: sr_sender2

102. ( *Critical* ) Not clear how file receipt/ingest works.
     users need to write to a private area, scanning/validation happens, then it
     gets moved to a ´public´ tree. can we do that with links?

103. ( *interesting* ) link support.
     sr_winnow that takes care of links.
     When a product arrives and it is already known, if the path is the
     same, then just drop it by not copying anywhere.  If the path is
     different (defining *different* is a discussion), then perhaps
     create a ´LINK´ post, so that rather than downloading, downstream
     consumers can link.
  
     What happens if a downstream consumer has accept/reject that made it not
     download the original? hmm... likely want to download it now...
     if it was downloaded, then just link, do not download.

     hard links or symbolic... concerns:
    
     - reduces to a single file system. 
     - windows portability
     - makes it easier for clients to transition (multiple posts of products)
     - perhaps an option setting True/False?
          
104. ( *important* ) lack of .adm. messages
     likely Khosrow will hit this first.  many needs, not explored yet
     role of source vs. pump admin permissions.

     - setting quotas?
     - setting access permissions.

105. ( *Important* ) Quota Measurement/Enforcement.
     Whenever Sarra writes to a tree, the space needs to be counted towards
     a quota... clearly counts for a source, but also perhaps the from_cluster?
     so have a quota that combines source@from_cluster ? but defaults to just
     the cluster if source quota not assigned.

     whenever a write will cause a quota to be exceeded, sara write should fail.
     and message returned.

106. ( *Important* ) Failure Recover Strategy.

     need to explore understand better how to deal with various issues.
     When to discard vs. queue, sample issues:

     - disk quota exceeded, just drop the message ( permanent, need to re-post to fix. )
     - bandwidth exceeded, leave it on the queue and sleep.   (send it later?)

107. ( *Important* ) file writing without closing.
     Currently, sr_watch only triggers posting of a file when it is closed (after
     writing has completed.) if a very large file is sequentially written over 
     a number of hours, it will only trigger transfer at the end, losing all 
     the time to transfer the older parts of the file.  One could sr_post the
     file at intervals, and the identical parts would get suppressed, but the
     new ones would be transferred.  Perhaps perk this up once an hour? 
     part of sr_watch, or not?


Critical Deployment Elements
----------------------------

The initial release does not just need to be ready, it needs to be deployed.  Deployment and 
development are linked, in that we do not encounter difficulties unless something is deployed, 
and we do not achieve business deliverables unless we deploy.  So there is an iterative loop, 
and we expect to upgrade frequently since the package is so young.

To upgrade frequently, we need to reduce the friction to producing upgrades.


sftp.science.gc.ca Server
~~~~~~~~~~~~~~~~~~~~~~~~~

*Assigned to:* Michel Grenier (Jun Hu3)

An S=0 (data-less) pumping service. The pumping nodes access the site-wide file systems
available to science.gc.ca. So authentication is what is on the systems.
likely characteristics:

 - bunny style clustered single broker instance shared among sftp1 and sftp2.
 - ssh configured to not accept passwords.  Key-files mandatory.
 - keys can be put in place by logging into interactive nodes.
 - privacy is OK, because it is from user to user space on each side,
 - only the messages might be intercepted?

Initial Delivery: January 2016

sftp.science.gc.ca Windows Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Assigned to:* Stéphane Charlebois 

In order for NRC clients to be able to use the sr_* tools, they need
access to a client. Need to assess methods of providing it. and
create at least an package.  This could develop from initially
being just instructions on a few options (how to install Python3, 
MS-vis studio 2012, and then the python deps) to an MSI.

Initial Delivery: End January 2016, likely at monthly intervals afterward.


ddi.cmc.ec.gc.ca
~~~~~~~~~~~~~~~~

*Assigned to:*  Michel Grenier (Jun Hu?)

The Dorval ddi (Data Distribution - Internal) needs to be compatible with the existing
public dd (Data Distribution, aka Data Mart) but also provide a model from which copies
to Edmonton are made.  The model for edmonton is under the ´sources/´ directory.

The root directory of ddi.cmc.ec.gc.ca
 - Demonstrates Independent DD Topology.
 - Demonstrates cross-feed DD Topology.
 - Provides source for Fingerprint Winnowing for Storm Prediction Centres

Initial Delivery: Done. Maintenance/usage continues


ddi.edm.ec.gc.ca
~~~~~~~~~~~~~~~~

*Assigned to:*  Michel Grenier (Jun Hu?)

The the two ddi's are Michel's testbeds, he needs them as part of 
dog fooding.  Anne-Marie needs them to do the new DMS feeds.

The Edmonton version of ddi is the test bed for the ´next´ layout of data.

 - Demonstrates Independent DD Topology. 
 - Demonstrates cross-feed DD Topology.
 - Provides source for Fingerprint Winnowing for Storm Prediction Centres

Initial Delivery: Done. Maintenance/usage continues


Convert URP to sr_post ? 
~~~~~~~~~~~~~~~~~~~~~~~~

*Assigned to:*  Wayne McNaughton ( Murray Rennie )

This a good dog-fooding exercise?  The URP people are asking about this.
We need to figure out if/when data feed methods will change.
This is about outputs from URP (how products are shipped out.)
For how URP acquires data, see next point.

A result of this should be *sr_winnow* and conventions around how
the multi-source reliability feeds are dealt with.  

The urps share username (say urp), and they both post to
xs_urp. sr_winnow maintains a table of path and checksums it has 
already seen.  When it sees a new checksum it enters it 
and the corresponding path into the table, and posts it
to the xwinnow exchange.   A Normal sr_sarra processes the xwinnow
exchange normally (treated as a multi-user pump, so no source check.)

Initial Delivery:  March 31st 2016 


Questions/Comments:  

- Peter is thinking that we don´t want three copies of everything
  on each site (a1, a2, and a), but just one (a).  If the sources
  a really different, you want multiples, but if they are identical, 
  no.

- should we just put a broker on each URP cluster, have a shovel
  from xpublic on each urp to xs_urp on a pump, and the
  processing is unchanged after that.  Someone wants access
  to urp1 output just connects to either cluster directly.
  is that pointless? 


how to talk about this stuff... over distance...



Figure our URP 2.9.2 Data Feed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Assigned to:*  Wayne McNaughton 

URP people are asking questions about data feeds.  SPC´s using FTP today, inbound
and outbound.  NURP is using FTP inbound, but fingerprint winnowing and a prototype
version of posting via Sundew scripting.   What is reasonable in the time available?

The ambitious plan:
 - Measure the difference in arrival time, SPC vs. CMC?
 - Can move 2nd feed to Edmonton? volume scans cross network twice?
 - use sarracenia methods both ways: sr_subscribe with Fingerprint winnonwing
 - How many vm´s per SPC one or two?


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

*Assigned to:*  Michel Grenier ( Jun Hu )

All of the feeds for dd that currently use sundew as the *bootstrap* to create initial
data sources for the dd/ddi.


The Queue of Small Changes
--------------------------

List of small things, to not forget...

- change default queue: cmc.xxx -> q_user.xxxx
  change sr_subscribe code and man page.
- adjust access controls: https://www.rabbitmq.com/access-control.html
  to ensure no ordinary users can declare or delete exchanges. only admin users.
- sr_sarra move 'recompute_chksum' to Developer options
- sr_sarra man page says default exchange is amq.topic. hmm.. that is wrong.
- force permissions to 600 on credentials.conf
- sr_police to flag weird stuff
  exchanges that do not start with x (and ar not built-in.)
  queues that do not start with q\_
  perhaps delete them? or just report?
  or figure out how to set rabbitmq permissions to prevent misuse.
- adjust apache indexing to put date directories in descending order. - Khosrow.
  access pattern is that most people want the latest data, so makes little sense
  to have nearly everyone read the entire directory.
- self-test to use config.
  really cool that there are now TEST options for some of the modules.
  But the test modules hard code the broker and other settings, so
  cannot be used elsewhere.
  TEST modules should use a configuration module:
  ~/.config/sarra/<component>/test.conf
  so that self-test can work anywhere.
- Looks like mirror True makes the directory tree, but does not place files in it. 




Windows Worries
~~~~~~~~~~~~~~~

minor: Windows doesn´t work (ie. fully.) perhaps not an issue for initial release.

- tasks... fork/exec, createProcess, multiprocessing issue.

- hard links ?   
  createhardlink call exists on windows now.

- cron ?   	   
  modern windows has schtasks and can be done from Scheduled Tasks control panel.
  Just need setup for the windows tool.

- file permissions  
  how to make sure credentials.conf is private on multi-user systems.
  




Deferred Deployment Elements
----------------------------

This functionality will not be present initially, but needs to figure into later plans.




sr_box
~~~~~~

Essentially DropBox functionality, provided over the sarracenia pumping infrastructure.
This is a wrapper around the the components built in earlier iterations to provide
dropbox emulation.

- sr_subscribe reproduces remote writes
- sr_watch posts local writes (while ignoring sr_subscribe ones)
- something (to do the writes to the pump from local.) probably just fire off a sr_sender.
  or will pump have sr_sarra lying around, so no need? what about firewalls?
- default pump (sftp.science.gc.ca ?)
- encfs provides privacy layer (dropbox is default private, dd is default public)

There is little to no code to implement this functionality, but a lot of configuration.
Need to make it plug & play before offering it.

Would be interesting to do a shared folder this way.  need to do some renaming (source)
hmm... interesting though.


sr_share
~~~~~~~~

Like sr_box, except different people use the same amqp username so that there are
different people writing to the same share (amqp user with same name exists on different
shares.) not sure if this is any different from sr_box.



Pull Distribution
~~~~~~~~~~~~~~~~~

If someone specifies ANY as to_clusters, does that mean we need to push that data to all
pumps?  Is there a bit-torrent-style demand element to propagation?  what if announcements
we processed by creating ''symbolic links'' on the next element of the chain, so that the
copy does not actually happen until someone actually asks for it?



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

For the first iteration, things were completed pretty much on time.
This is all done.

focus: deltas.txt, logmessages.txt, sr_post_sample.txt

   sr_post, sr_sarra, and sr_subscribe 

   validate that AMQP over SSL works, because it will all need to be there.

   implements v01.notice, and v01.log
   maintains compatibility with v00 (so subscribe can read v00.)
   
   - does blockwise checksums.

   - does just enough validation to do the YMD/<source> thing.

   - sr_post should not do validation (so easier to test psychotic settings
      like 1 byte blocks.)

   post to a pump, sarra build a site, sr_subscribe pulls from it.
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
    *This is still not done*
    Have a look at clusters.rst

watch a directory, and post what is there (flat)
  - using inotify (kernel feature), or perhaps inotifywait (as a wrapper process.)
  - only needs to work for a flat directory at first.
    *done on time for flat tree, but configs were hard-coded*

  deferred: windows version of sr_watch (no inotify available.)
	question, if this is built as inotifywait calling sr_post (or something like that.)
	then there is an inotify-win.  just introduces a dependency... but makes it easy.
        *nope, not done.*

   base user-facing delivery function done.
   *nope*

   do speedos (see monitoring.txt)
   *nope*

   figure out whether we need a sr_log, or if sr_subscribe is enough.
   *yes, we need sr_log, there is one, but it isn´t quite right yet*
    
   testing, testing, testing...

HW: whatever is lying around.



Iteration 3:  Security/Authentication, Transition Strategy:  August
-------------------------------------------------------------------

   *this is about where we are now... figuring out accounts and auth.*

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

   create .htaccess files using sarra and subscribe
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



