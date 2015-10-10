
===========================
 Description of Components
===========================

in alphabetical order.


dd_ingest 
---------

::

	--broker amqp://<account>@<broker>/
		

	-  kind of local version of SARA, just the RA part...
	-  subscribe to the xac_<account> exchange written by the user.
	-  read log messages there of the form v01.log.<account>.<account> 200
	   which indicates a successful delivery of the file to this system.
	-  trigger pre-fetch and post-fetch verifications of the file.
		if it fails validation, then log error. done.

	-  assuming it is OK, move it to a system area?
		or something, it stays here? huh? user can delete?
	-  re-announce to downstream-broker



dd_log2src 
----------

::

        --broker amqp://<swuser>@<broker>/

        authenticate to broker as swuser, read log messages on the xlog exchange 
        of the form v01.log.<account>.<whatever>
        copy them to xac_<account> exchange so the user can pick them up.
        on the same broker... 

        in some cases, <account> will not be a local account.  look up account
        in a table (acc2src table) to identify which source to send the messages to.

        dunno: run one for all accounts, or one per account?




dd_post 
-------

::

        args...   -b blocksize -w tag [basedir] <source-url> <destination-url>
	destination url == --broker amqp://<source>@<broker>/<relativepath?>




dd_sara 
-------

::

	--broker,--source-broker,--upstream-broker ? ??
	subscribe to a given exchange on a given broker for  dd.post messages.
	--prefetch-script <prescript>

	run prescript, based on the dd.post to see if it is OK to download.
	if not, log an error.
	if so, download it.

	--postfetch-script <postscript>

	run postscript against the contents of the file.  see if it passes
	those checks. if so.

	re-post to a destination exchange that refers to the local server.
	--repost-broker, --downstream-broker
	

dd_sender 
---------

:: 

        [--broker] [--downstream-broker=<url>] 
        --broker,--source-broker,--upstream-broker ? ??

        subscribe to a given exchange on a given broker for  dd.post messages.

        re-post to a destination exchange that refers to the local server.
        --repost-broker, --downstream-broker



dd_subscribe 
------------

::

        [-n|--no-download] [-d|--download-and-discard] [-l|--log-dir] config-file
        this command line is from v00 dd_subscribe... 

        --broker amqp://<account>@<broker>/

        will cause dd_subscribe to connect to <broker> and authenticate as <account>
        it will then subscribe to xac_<account> and look for v01.post.!<account> messages
        (to avoid loops.) 

