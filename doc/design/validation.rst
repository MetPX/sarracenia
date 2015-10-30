
Status: Pre-Draft

This is a discussion about validation.  
It mentions many points, but the design to implement is in design.rst.

When a source posts an announcement, the switch must validate that it is proper,

examples of validation. 
	might not need them all, and there may be others, this just gives an idea.

---
prefetch:
This could be done, either as a distinct component or a pre-fetch script from dd_sara

	- if the source is stopped,
		waitloop.

	- check if the blocksize is reasonable (set system minimum and maximum.)
			reject.

	- else if no blocking used and the file is too big, then insist on a blocking.  
	   (ie. 1 TiB file, with no chunking?)
			reject.

	- validate distribution/scope list (header?)
		internet vs. escience (comma separated list) vs. warning?
		is scope is invalid: reject.

	- look at the file name.
		it sec may provide a list of extensions to ban.
		.exe, .zip, etc...
		reject.

	- compare against allocated bandwidth for this source,
		wait loop if exceeded.

	append source to permit messages.

	(inbound messages is ...
	v01.permit.set  --> outbound is v01.permit.set.<source>
	v01.permit.get  --> outbound is v01.permit.get.<source>

---

---
postfetch:

malware scan.
probably do a demontration configuration with clamAV.
run a virus scan or other tool against the block obtained.
if an alert is triggerred, refuse to re-announce.	

security guys worry: 
splitting files up means some malware split on boundary, so it gets missed.
Do you interchange last nth of one part, with first nth of next part
to trigger a boundary scan?  worst case n=2.

ugh:
now you need to associate each pair of parts... 
triger exchange between them... 

defer this ... 

problem:  what to do if something fails the scan?
 - discard?
 - log and wait for a 'force' from the source?
   aka quarantine...
 - consult a setting, that says 'let it go...'
   administrator can set 'do not scan' on per source basis.

 - can set file size threshold for scanning.


---


Scenarios:

why rate-limit:
	dd_post of a file that is 1 TiB.
	with 500MB chunks that will create 2000 block notifies.
	if validation does no rate limiting, then the 2000 blocks will get 
	fed into the queue in one go, and that transfer will take over.


Priorities: so far not present in design.
	want to send a weather warning then a 3 TB file is transferring with 20 threads.

	AMQP does have priorities, not there by default.

	the exchange that the validator writes to could be prioritized.
	there could be a number of priority mechanisms for dispatches.

	priority 0 is lowest (last picked).
	could assigne priorities as an inverse function of size (bigger files let smaller 
	ones through.)  not cler if use of amqp prio is the way to go..
	https://www.rabbitmq.com/priority.html -- hmm..
	
		Queues which have a max-length set will, as usual, drop messages from 
		the head of the queue to enforce the limit. This means that higher 
		priority messages might be dropped to make way for lower priority ones, 
		which might not be what you would expect.



why check scope/distribution?
	scopes:  science, internet, warnings?

	correspond to exchanges. where things get posted.
	most source cannot post 

	if we have a 'warnings' scope, then limit who can post to it.
	


why check blocksize:
	each notification is on the order of 100 bytes, so a block size smaller than
	that will cost a great deal of bandwidth in terms of messages going back and forth.
	want to keep the messages (announcements and logs) down to a small percentage of traffic.
	smallest reasonable 'blocksize' is 10KB (which gives 1% overhead.)

	if blocks are too big (1 TiB) then intermediate file systems have to store the entire file
	and may fill up.  limiting chunk size reduces the chances of that.


why check capacity:
	if the source has a disk allocation on the di server and it is exceeded, then 
	might be better to 'flow-control', stop the flow now, rather than have it pile up
	in the switches.



