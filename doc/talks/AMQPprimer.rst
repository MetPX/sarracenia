
==============================
 AMQP - Primer for Sarracenia
==============================

Scope
-----

- AMQP is a vast and interesting topic in it's own right.
  Not trying to explain that here.
- Introduce Only Concepts needed to user Sarracenia.
- More information: metpx.sourceforge.net/#AMQP
- Google AMQP, rabbitmq.


Advanced Message Queueing Protocol
----------------------------------

- Open International standard from financial world.
- seeing good adoption in monitoring and integration for HPC
    - Intel HPC stack
    - https://wiki.openstack.org/wiki/Heat/Vision
    - used behind the scenes, not user visible.

- this is because it is:
   - low latency
   - encourages asynchronous operations.
   - language/protocol/vendor neutral.
   - very reliable.


Concepts
--------

- an AMQP Server is called a Broker.
 
- There are many different broker software implementations, we use rabbitmq. 
  Not trying to be rabbitmq specific, but management functions differ between implementations.

- In sarracenia, we run a web server (apache), sftp server (openssh), and amqp broker (rabbitmq)
  on the same user-facing address.  

- In Sarracenia, we expose AMQP so that users can consult internet resources 


- queues are usually taken care of transparently, but you need to know
   - To send a message, create a queue, send the message to the queue.
   - A Consumer/subscriber also creates a queue to receive messages.

- An exchange is a matchmaker between producer and consumer queues.
   - A message arrives through a producer queue.
   - message goes to the exchange, is anyone interested in this message?
   - message is routed to interested consumer queues, or dropped if there aren't any.

- Multiple processes can share a queue, they just take turns adding or removing messages from it.
   - This is used heavily for sr_sara and sr_subcribe multiple instances.

- Queues can be 'durable', so even if your subscription process dies, if you come back in a reasonable
  time and you use the same queue, you will not have missed any messages.

- How to Decide if Someone is Interested.
  - For Sarracenia, we use (AMQP standard) Topic based Exchanges.
  - Subscribers indicate what topics they are interested in, and the filtering occurs server/broker side.
  - Topics are just keywords separated by a dot. wildcards: # matches anything, * matches one word.
  - We create the topic hierarcy from the path name.
  - topic prefix?  We start the topic tree with fixed fields:
	- v02 the version/format of sarracenia messages.
 	- post ... the message type, this is an announcement of a file (or part of a file) being available.  


Review:
------

One connects to an AMQP broker and creates a queue.  A publisher sends messages to it's queue,
a consumer reads messages from their queue.  Publisher and Consumers queue are linked together by 
exchanges.  Sarracenia uses topic exchanges to allow consumers to allow server side filtering.
The topic tree is based on the file tree you can browse if you visit the corresponding web server.



