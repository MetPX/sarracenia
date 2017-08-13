
=============================
Background Reading for Design
=============================



General References
------------------

Distributed Computing is about a multiple computers (or nodes) participating to provide
a service.  They fundamentally are nodes on networks without any shared storage.
A foundational reference is: CAP theorem -- http://en.wikipedia.org/wiki/CAP_theorem
basically:

    * Consistency: all nodes provide the same answers to all questions.
    * Availability: at least one node will always answer any question.
    * Partition Tolerance: what answers you get when nodes cannot talk to each other. 

The CAP theorem says that these three properties battle one another and one cannot have perfect
implementations of all of them. This is similar to the engineering quip: Fast, Good, Cheap: Pick any two,
A good discussion is http://berb.github.io/diploma-thesis/original/061_challenge.html
    
Another very short, but very helpful reference is "Fallacies of Distributed Computing." by Peter L. Deutsch.
Essentially:

	* The network is reliable.
	* Latency is zero.
	* Bandwidth is infinite.
	* The network is secure.
	* Topology doesn't change.
	* There is one administrator.
	* Transport cost is zero.
	* The network is homogeneous.

provides motivation for loosest possible coupling, also for asynchronous operation.

High Availability solutions are generally based on https://en.wikipedia.org/wiki/Quorum_(distributed_computing)
The idea is that an application is written as a serial/single node application, and a magical layer implements
something to deal with the reality that systems are distributed for reliability reasons. 
 
It is a very attractive idea to software developers because then they just ignore all this stuff, and
say: Oracle will do it for me (RAC), or linux (dozens of solutions.) Those Quorum systems
are very complex in many different ways. There are Quorum protocols the communicate between nodes.

What they do in practice is combine all your nodes into a single large configuration with synchronization points
where everyone needs to agree. One can no longer test individual nodes and get any assurance of the behaviour 
of their composition, and it introduces failure modes that result from the Quorum protocols. The quorum 
protocols are essentially blackboxes and when they fail, one *discovers* how they work. So it essentially 
expands the problem space to be covered by deployment staff when things go wrong.
    
An alternative to using quorum protocols is state-machine replication. Nodes do the same thing
and so they get the same answers. There is no vote, no communication among nodes, because
they should just have come to the same conclusions.  This is better for deployments in practice 
because each node is participating individually, each node can be tested on it's own, and messages 
from other nodes can be sent to it to cover all of its possible behaviours, there is no magical other 
protocol and the various failure modes to cover. It is also easy to test, because you just run two 
nodes, and when they disagree, you have an application problem.  

For application scaling (getting a system to run over many nodes to increase performance), state-machine
replication is far better because as you add nodes, the votes just get more complicated (in terms of
algorithmic complexity and naturally, elapsed time.) 

The complexity for applications come from when nodes are far from one another, they may not get 
the same inputs in the same order, and so the application needs to understand how to account for
that.  The 100% certain answer is that one can't (this is a manifestation of the principles and CAP.)
Evaluating whether results are equivalent is the primary challenge introduced.

The debate often boils down to the application developers wanting to avoid consideration of distributed 
computing by getting a lower layer to take care of it, and the deployment people saying: ok we
can do that, but it has a high cost in deployment of those layers, and often in practice, the difficulty of
configuring and testing those layers introduces more failures than they avoid.  If the goal is high availability,
then these solutions are often not achieving it.

Sarracenia implements a sort of virtual shared storage, which is one way of minimizing what applications need
to do.  Applications communicate by passing files to one another.  For that to work, the application needs to 
be implement transactions on finite state machines to ensure the participating nodes have parallel state.  
The applications are simpler, Sarracenia itself is relatively simple, all the components compose in easily
understood ways.


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

    Why using a DB as a backing store makes little sense.  DB's are very popular, people want 
    to use them for many things, but sometimes they are a poor fit.  A message transfer system 
    is one such case::

	  https://www.rabbitmq.com/blog/2011/01/20/rabbitmq-backing-stores-databases-and-disks/


Cautionary Tale of Complexity
-----------------------------

The following article by a key AMQP guy who eventually forked off to 0MQ.
This history of AMQP is that version 0.8 of the standard came out, and it was small and simple, and many 
compatible implementations of it were produced, and it became a marketable technology, so than a whole
bunch of big players got into the game, and then started working on improving the standard.
This process resulted in AMQP 1.0, which is completely different from 0.8, from even a conceptual level.
Sarracenia uses rabbitmq which is fundamentally a 0.8 broker.  I don't know if that will ever change.

Pieter Hintjens is an early AMQP developer, who eventually gave up on it, and decided to do 0MQ.
The story he tells is a very compelling account, of a disease that often occurs in designs of distributed
systems.  People do not appreciate CAP and the fallacies, and they thing they can *solve* the problem.

reference: http://www.imatix.com/articles:whats-wrong-with-amqp/ 

 *AMQP's positioning as Enterprise Technology has made the Working Group tolerant of complexity that would not have survived one hour on the Internet. People would have said, "OMG? ROTFL!" and posted the proposals onto Slashdot where they would have been mocked six feet under. Instead they got incorporated into the official specifications and released as Gospel. As a form of subtle comedy ("we're not ready yet, so here is some light farce to entertain you"), it would have a certain style. As serious work and part of the historical record, it is a failure.*

 *Apart from the tolerance for shoddy work wrapped up and oversold as "extra value", Enterprise Technology sets the bar so high that no-one can jump it. "We must have 100% guaranteed reliability even if the server crashes", sounds fine but this single demand - repeatedly stressed and sold by some of the AMQP participants - has caused most of the AMQP slippage. In fact no vendor can guarantee 100% absolute reliability, not in messaging, not in any software, not in cars, food, computers, anywhere. And no-one needs it. As long as the probability of loss is low enough, that's fine. Or, put it like this: if it's cheaper to compensate a client for a lost message/exploding computer/late flight/failed brakes than to make the technology more reliable, stop making it more reliable. The better is the enemy of the good, and it's more costly too.*

 *Yet as far as AMQP is concerned, Enterprise Technology must be 100% reliable. This means making transactions that can properly survive a failover from a primary to backup server. This means the protocol must have mechanisms for switching sessions over from one server to another. This means we need to redefine the atomicity of every operation from queue creation to message transfer, as well as redefine what a session is. That means we need to treat everything as a message. Or perhaps the opposite. That means we need dozens of new data types, including multiple variants of that insufficiently complex concept called a "bit". Yes, finally we get to a 300-page specification. Now we have something suitable for the Enterprise!*

 *Well, no. What we have is a smelly mess looking like Godzilla's regurgitated breakfast. You can recognize pieces of Tokyo, but it's not a place you'd want to live in anymore. In communications, reliability comes mainly from making servers that don't crash. And this comes from making pieces that are simpler. And this comes from lowering the bar on the demands for perfection. Ironically, the ambitions of AMQP to be perfect have the opposite effect.*

Even very good people get this stuff wrong, and regardless of the amount of effort and expense thrown at the problem,
There is no perfect solution possible.  Often one is in the realm of diminishing returns, and the complexity imposes 
a cost of people not understanding what it does, what the failure modes are, and how to deal with them in practice.   
There is true value in simplicity.




Why not DDS?
------------

DDS:
	- http://portals.omg.org/dds/
	- #1 there are no free implementations, client or server.
	- #2 it is very complicated.  Many layers of standards to navigate.
		it comes from OMG, which brought us CORBA.  looks very RPC... complicated.
	- #3 it implements an API (means language bindings needed)  none easily available.
             it is streaming oriented, and point to point. does not enable topologies.
	- it is still very new and evolving, but should be watched.


