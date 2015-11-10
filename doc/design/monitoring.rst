
Status: Pre-Draft

======================
Notes about Monitoring
======================

Questions: 
	is sr_log just sr_subscribe, or is it different?

likely do not need federation, just ''shovel'' rabbitmq_shovel_management

If a message error occurs, such that a downstream system is unable to process a message,
then the log message needs to propagate that back to the source.

Sources need to see the log messages for their sources.
Admin and monitoring needs to see all the messages. 

sr_log just dumps log messages (might be just sr_subscribe -n.)

-- the CFS runs a subscribe to pull the logs in in real-time, no cron required 
   (but queue if it goes down?)

-- for each known source, a log exchange is created (log_goes)

-- logs come through the brokers in the common log exchange (log) but most people cannot read that,
   only admin access.

-- process on log broker looks at mesages and routes them to per source log exchanges. ?
   source exchange permissions decide who can read those messages.

   new component:  sr_log2source
	-- looks at the topic, and just copies the message from the general log to the per 
	   source log.
	

sr_log use cases:

-- by sources to see the consumption of their products.
	-- sr_subscribe 
		logs in as <source> and binds to the exchange named log_<source>  
		each exchange is only readable by <source> and admin users.

FIXME: difference between sr_log and sr_sub!
	sr_log, when catenating, should inclued topic, where sr_subscribe will not.? 
		for speedos vs. logs.... hmm...


FIXME: defined speedos

-- to feed into "speedometers"
	web site? or app, taps into log feed.
	sr_speedo... looks at the flows generates stats each <interval> seconds.  interval is configurable.

	format: 
		<datetime> <goodcount> <errorcount> <goodbytecount> <badbytecount?> <bytes/interval> <files/interval> <interval>

	v01.speedo.client.<client> (ends)
		gives a rate of 200's and 4xx/s per second. 
	v01.speedo.source.<source> (ends)
		gives a rate of 200's and 4xx/s per second. 
	
	posted to 'log', and log_<source> exchanges. (perhaps two sr_speedos running, one per exch.)

	likely the 'all' one will have an interval of 1. but most sources much longer, like 60.
	v01.speedo.client.all <overall stats>
	v01.speedo.sources.all <overall stats>



-- by netops to feed into nagios.
	probably enought to subscribe to speedos....
	alert for all clients whose speeds are 0.

	when needed, they can likely do (command line)

	sr_log <pattern>
		<source> or <client>

	which does a sr_subscribe with an include of the given string.
		analysts could also do that.


	would accumulate statistics per source and per client:
		-- counters...
		-- t ... thresholds per client and per source ::

		   td - deadline for no deliverie in td time.
		   tminr - minimum rate of message ack to be considered 'up', no ack from client in t seconds... signal?
			

		-- perhaps nagios checks every minute, and just reports how many clients' t's are 
		   exceeded and lists them.

		-- builds an expectation of rate per client... 
			-- usually runs x products per minute.  if it varies too far for a given amount of time, alert.

		-- this will not see if a particular thingum from a client is stuck, only entire client.
		--  yeah, tough.
			


-- by analysts, either on a real-time log capture host, or on the CFS
       to get traceability just grep the logs... using either...
		source id, file name, flow id, client id, ... 

	sr_log <source> thing above is fun also.


-- by the CFS to capture significant logs directly .. so
	reducing requirement for periodic bulk transfers.?
	do we use this for real-time logs? not sure, CFS would need to be more up.


-- when a node fails... sr_watchdog? 
       if sr_sarra emitted a log when it started a transfer, and another when it finished.
       then sr_watchdog could be subscribed to them and know what products were in flight
       on every node at any time.



