
=============================
Background Reading for Design
=============================



General References
------------------

	CAP theorem -- http://en.wikipedia.org/wiki/CAP_theorem

	basically:
		- Consistency, Availability, Partition Tolerance:  Pick any two.

		illustrates some issues in distributed designs.
	

	Fallacies of Distributed Computing. --  Peter L. Deutsch
		a good dose of realism.  

			The network is reliable.
			Latency is zero.
			Bandwidth is infinite.
			The network is secure.
			Topology doesn't change.
			There is one administrator.
			Transport cost is zero.
			The network is homogeneous.

      provides motivation for loosest possible coupling, also for async
	in sarracenia, messages are sent.



HPC oriented practical advice
-----------------------------

  - http://moo.nac.uci.edu/~hjm/HOWTO_move_data.html

  - http://connect.ed-diamond.com/GNU-Linux-Magazine/GLMF-164/Parallelisez-vos-transferts-de-fichiers

  - http://fileutils.io

  - review of jlafon.io/parallel-file-treewalk*.html
    partitions the entire file to assigne to n processors.  also has to pick n.
    it takes a partitioning approach, so that scheduling is a problem.
    if you take opportunistic queueing, assuming availability of a broker, then the problem 
    is completely different.  The broker is too slow for use in real HPC parallel codes,
    but if you just make a work queue that is shared, you have the problem of serializing access
    to the queue, but partitioning goes away.  if we assume we are i/o bound (most of the time
    spent reading/writing data to network or disk.) then synchronization penalty for queue 
    access is perhaps not significant.

    On the other hand... libcircle, and the implementation of distributed termination
    might be helpful to us, in figuring out when transfers are finished.
    but we probably do not need something that elaborate.

    The sarra approach still makes sense (wide area transfers... lower speeds, not local focus)


Scaling RabbitMQ
----------------

    http://spring.io/blog/2011/04/01/routing-topologies-for-performance-and-scalability-with-rabbitmq/

    http://www.slideshare.net/gavinmroy/scaling-rabbitmq-to-11

    interesting bits:
        https://www.rabbitmq.com/community-plugins.html

    rabbitmq_delayed_message_exchange




about AMQP
----------

	http://blogs.digitar.com/jjww/2009/01/rabbits-and-warrens/ - from 2009
		introduction to amqp, with a slant towards rabbitmq and python

        http://www.imatix.com/articles:whats-wrong-with-amqp/ - one view of why AMQP 1.0 
	  will never be adopted. (10 years old now.)  we continue to use 0-9-1 which is
          the last simple yet fully featured standard.

        why using a DB as a backing store makes little sense.
          DB's are very popular, people want to use them for many things, but sometimes
	  they are a poor fit.  A message transfer system is one such case.
	  https://www.rabbitmq.com/blog/2011/01/20/rabbitmq-backing-stores-databases-and-disks/


Why not DDS?
------------

	- http://portals.omg.org/dds/
	- #1 there are no free implementations, client or server.
	- #2 it is very complicated.  Many layers of standards to navigate.
		it comes from OMG, which brought us CORBA.  looks very RPC... complicated.
	- #3 it implements an API (means language bindings needed)  none easily available.
             it is streaming oriented, and point to point. does not enable topologies.
	- it is still very new and evolving, but should be watched.


