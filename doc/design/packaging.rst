
status: Pre-Draft

Figure out packaging? 
---------------------

	- audit source to ensure full copyright headers applied.
	- the real command line interface.... uptil now was just working stuff.
	- what documentation should be available.
	- what packages should be built.


Goals
-----

Can we make it really easy to build a ddsr node for techies to deploy a server ?
so it is easy for others to adopt.   Recipe for a standlone single node config.

	- this would be linux only,
	- either a dpkg
	- a docker container?

Make it easy for mortals to install the client.
need self-contained windows install (an .exe) folks can download.
because many clients in various departments use windows as clients,
and many data sources may use windows also.


how to do languages & messaging
-------------------------------

need English & French 
just keep it in code, no natural language?
There's fabulous ones: http://en.wikipedia.org/wiki/List_of_HTTP_status_codes

metpx-sarracenia-server
	- depends: rabbitmq.
	- configuration sugar, to create a working/secure default to just start using.
	- sr_sara, and all the other components...
		log, and whatever.
		

metpx-sarracenia-client
	- sr_subscribe (dd_subscribe)  -
		should sr_subscribe accept it's config file on standard input?
	- sr_post
	- sr_watch
	- sr_send...


there might be a meta-client... one that invokes the others appropriately...
	sr_cp -broker amqp://mygroup@ddsr/ -threads 5  <operation>  <source> [<srcurl>] <dest>
		-broker says what the URL of the AMQP broker is.
		-threads says how many local instances to start.::

		<operation>

                post4pickup  -- sr_post, and the switch is expected to pull
                	-- requires <srcurl> to show URL remote will use to fetch.
                        fires off: just the sr_post -threads ignored.

                post2send    -- sr_post, then have local threads to send to sftp destination.
                        sftp destination is likely a 'source' for the switch, triggering further fwding ...
                        fires off: 1 sr_post and a 5 sr_sends, as appropriate.

                subscribe    -- sr_subscribe, but with n local instances.
                        fires off: 5 sr_sends, as appropriate.

                       fires off 5 sr_subscribes, or 
		
		
	
start making other packages?
	redhat/centos?
	windows?

	do we make it 'pip' compatible?
		so on windows they install python, then pip pulls in deps?


Dunno. We probably need to try a bunch out and see what sticks?


windows
~~~~~~~

Packaging for windows has particular issues because of a clash between the source 
distribution norm on open source, vs. the binary distribution norm on windows.   In 
python packages this bites because, PyCrypto has portions of it implemented in C, so standard installation means compiling that portion of the module, which creates a depdency on a C-compiler for every installation.  Given the lack of consistency in build environments on windows, one needs to obtain the build environment that matches what was used to build the python interpreter.  google search ´install pycrypto windows´ for more ample discussion.  

Lack of dependency management also bites, too much assembly required (install amqplib, paramiko, etc...)  this is all easily taken care of on linux, but beyond the ability of non-technical users on windows.


One way around it, use nuitka, to compile all depedendencies into a single binary package, put that in an MSI.

That does not solve the pycrypto compilation problem though.

One could modify paramiko to use a pure python implementation of pycrypto:

https://github.com/doegox/python-cryptoplus

compile that with nuitka.  to give a full package.


