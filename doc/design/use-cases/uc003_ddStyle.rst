

Use Case 3: a web server where users can see the files sent (dd style)
----------------------------------------------------------------------

       data dissemination...

       likely:
          have multiple independent servers for op0hr service.
		- like current dd, requires broker per server.
          
          have a multiple servers with a cluster file system for op3hr service.
		- one broker for all servers.

	  have a single server with a shared or file system for opDay service
		- one broker on the server.

