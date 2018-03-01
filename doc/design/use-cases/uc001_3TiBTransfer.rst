

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
	

