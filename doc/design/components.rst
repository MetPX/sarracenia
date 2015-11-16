
===========================
 Description of Components
===========================

in alphabetical order.

sr_get
------

same as sr_subscribe, but supporting sftp, as opposed to just http/s.
also supporting instances?


sr_ingest 
---------

::

 --broker amqp://<account>@<broker>/
		

 -  kind of local version of SARRA, just the RA part...
 -  subscribe to the xac_<account> exchange written by the user.
 -  read log messages there of the form v01.log.<account>.<account> 200
    which indicates a successful delivery of the file to this system.
 -  trigger pre-fetch and post-fetch verifications of the file.
    if it fails validation, then log error. done.

 -  assuming it is OK, move it to a system area?
    or something, it stays here? huh? user can delete?
 -  re-announce to downstream-broker


sr_log2cluster 
--------------

look at the xlog exchange, check the *cluster* header of each message (which
indicates where the corresponding product was injected.) Consult log2cluster.conf,
Send the log message to the indicated cluster.

sr_log2src 
----------

::

        --broker amqp://<swuser>@<broker>/

swuser is an admin user with rights to read xlog
authenticate to broker as swuser, read log messages on the xlog exchange 
of the form v01.log.<account>.<whatever>
copy them to xs_<account> exchange so the user can pick them up.
on the same broker... 

in some cases, <account> will not be a local account.  look up account
in a table (acc2src table) to identify which source to send the messages to.

dunno: run one for all accounts, or one per account?




sr_post 
-------

::

        args...   -b blocksize -w tag [basedir] <source-url> <destination-url>

destination url == --broker amqp://<source>@<broker>/<relativepath?>


sr_put 
------

like sr_sender but dispatches on this side....
for use when a firewall prevents sr_sara from retrieving data from
the source.  The source initiates multiple streams and distributes
slices among them. They upload each slice, and post as it finishes.

also support instances?
 

sr_sarra 
~-------

::

	--broker,--source-broker,--upstream-broker ? ??
	subscribe to a given exchange on a given broker for  sr.post messages.
	--prefetch-script <prescript>

	run prescript, based on the sr.post to see if it is OK to download.
	if not, log an error.
	if so, download it.

	--postfetch-script <postscript>

	run postscript against the contents of the file.  see if it passes
	those checks. if so.

	re-post to a destination exchange that refers to the local server.
	--repost-broker, --downstream-broker
	

sr_sender 
---------

:: 

        [--broker] [--downstream-broker=<url>] 
        --broker,--source-broker,--upstream-broker ? ??

        subscribe to a given exchange on a given broker for  sr.post messages.

        re-post to a destination exchange that refers to the local server.
        --repost-broker, --downstream-broker



dd/sr_subscribe 
---------------

::

        [-n|--no-download] [-d|--download-and-discard] [-l|--log-dir] config-file
        this command line is from v00 sr_subscribe... 

        --broker amqp://<account>@<broker>/

        will cause sr_subscribe to connect to <broker> and authenticate as <account>
        it will then subscribe to xac_<account> and look for v01.post.!<account> messages
        (to avoid loops.) 


sr_winnow 
---------

::

	scripted version of NURP reduction of multiple sources to one.
