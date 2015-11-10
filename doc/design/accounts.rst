
Status: Pre-Draft

==========
 Accounts
==========

usernames for switch authentication are significant in that they are visible to all. 
They are used in the directory path on public trees, as well as to authenticate to the broker.
They need to be understandable.  they are often wider scope than a person... 
perhaps call them 'Accounts'.  they turn up as usernames in AMQP and HTTP.

All Account names should be unique, but nothing will avoid clashes when sources are on 
different origins, and clients at different destinations.  Just a matter of seeing name
clashes in practice and fixing them.

So an Account is allocated for
------------------------------

 - Each Source. (Alice)
   each source gets a source_<sourcename> exchange ... source_Alice. 
   on the posting switch (and the logging switch if different.)

   each source has a single ingest scope/context, where they can inject messages, or get logs.
   (same source cannot inject on ddsr, and ddi directly, as will not know where the logs 
   should go, for example, or control messages... hmm.)
   their directories get disseminated as YYYYMMDD/Alice/...
   They get daily directories because we impose system-wide life-time for data, it is deleted
   after a standard number of days (and we don't need to use 'find') just delete from the root.

   Since the clients will see the directories, and therefore client configurations will include them.
   it would be wise to consider the account name public, and relatively static.

   Sources determine who can access their data.
   two aspects:
   - distribution scope ( what servers to post to )
   - authorization (which clients on the servers should access it.)
   - see below sections for each.
   

 - Each Client (Bob)

    Client gets permission to access files (http level)
    Client gets permission to post log messages to log exchange 
    on the server that is sending them announcements.
    only exists in AMQP on the end broker.
    they authenticate to broker to get messages.

    also in apache at end server.
    All sources will see the client name in their logs.

    I'm starting to wonder if a client isn't just a source with a 0 b/w allocation.

    so instead of having a general exchange on the outside,
    every client gets their own, just like a source, and there is a 
    validator/shovel that puts it in the general log queue.

    If they decide to start posting, it ''just works.''

    they specify scope also?  say on dd we say their scope is 0 bytes (cannot post to our public site) but they can post to science (and it will get pulled in.)... 

    inside switches are subscribed to the source_dd exchange, and 
    they pull it in from the DMZ.  n chunks at a time.

    can clients issue re-xmit requests?
 
    v01.request.<source>.retransmit.....
	I can't understand when this would happen...
 	but it's interesting.
	is it a different type, or just a logentry
    
    

 - Each Layer between Source and Client (ddsr,ddi,dd)   

    so each hop generates a log message, assigned to the layers.

    internal hops can be removed from stats easily.
    only exists in AMQP on the relevant brokers (not needed in HTTP)

    ssc_ddsr
    ssc_ddi
    ssc_dd

    Is each layer a scope?... distribution?



Is Speedo a source? ... 
-----------------------

	creates no data, only messages.
	ssc_mon user?

Do we use the same authentication for SFTP?
	create an SFTP server using the same account?


Does Monitoring need an account?
--------------------------------


To store the accounts, do we create a sub-domain for ldap 
( dd.science.gc.ca, dd.collab.science.gc.ca) and put them in there?
just allocate locally?   hmm... dunno.


these are data interchange accounts (separate from interactive ones, 
per org, rather than per person.)



Distribution/Scope:
-------------------
	


Authorization:
--------------

	when sarra picks up permit messages, it needs to route them to 
	a separate exchange, that only specific users will be able to see,
	rather than a public one.

	source emits a message.
	v01.permit.set.<source>.<topic>.<subtopic>...   
	body of message is the list of permitted users.

	create an htaccess file with the users in it, but because of the date rollover,
	every day the directories are re-created, so it is not enough to
	create the htaccess once.  You need to remember the directory hierarchy
	and subscribe or sarra's mkdir needs to recreate the .htaccess before
	writing any files there.

	if the file is empty, then remove the .htaccess file.

	reply:

	v01.log.<source>.<scope>.permit.set...  
           which reports a succeed or fail status of the operation.

	v01.cfg.perm.get.<source>.<scope?>.<topic>.<subtopic>...

	v01.log.cfg.permit.get
		body contains the list of users.

	body of message is the list of permitted users.


Do we do user groups
--------------------

	user reps (users who can admin for groups of users.)

	Data Interchange....
	

AMQP has Vhosts
---------------

	Does this bring us anything?
	exchanges etc... all live in vhosts.
	could declare a separate vhost and put everything in there.
	currently using '/' (default) probably fine, but should review.


Authentication Methods
----------------------

	- DMS uses signatures... should we be doing that?
	- each user signs each message?
	- then no LDAP, have to manage all the keys.


	- limited to using username/password because rabbitmq can only bind to LDAP.
	- need to use methods supported by LDAP.
