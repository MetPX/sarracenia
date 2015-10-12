

Corp2NRCviaHPC
--------------

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

