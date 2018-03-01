

Transfer from EC to Science
---------------------------

    Overview:

	user Earnest is at EC-Burlington site on the Econet (which is fairly flat.).
	he is in the cloudmechanics group (made up example)
	wants to transfer a file to the high performance computing science.gc.ca 
	
    AMQP layer:
	So Earnest fires up sr-post on server svrEC-Burlington...  
			broker target: amqp://uearnest@svrsftp.science.gc.ca/
				which means he posts on the xac_earnest exchange.

	now... science.gc.ca cannot initiate a connection to svrEC-Burlington (no inbound to EC)
        so to send it, one must do::

	    sr-sender,   
		subscribed to xac_earnest... and then sending the files
		posting the log to xac_earnest as well.
				
   Data Layer:
	local auth on server in EC using EC credentials and permissions.

	sftp -> sftp.sciencec.gc.ca ... posting to the normal science domain.


   log layer:
        log messages posted to xac_earnest... copied to system-wide xlog.   sr-src2log  ?

   1. Storage Distribution
        The storage is on the two end servers, and is normal user space no server specific storage.

   2. Server s/w Distribution.
        the user would have sr-sarracenia available to run the sr_post, and sr_sender binaries.
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

	do sr-post they authenticate to the sftp´s rabbitmq server.
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
	If you fire up n-sr_senders, they will initiate n connections to sftp. the lb´s with
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

