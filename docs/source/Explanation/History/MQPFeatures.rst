
AMQP for Sarracenia
===================

AMQP Feature Selection
----------------------

AMQP is a universal message passing protocol with many different
options to support many different messaging patterns.  MetPX-sarracenia specifies and uses a
small subset of AMQP patterns. An important element of Sarracenia development was to
select from the many possibilities a small subset of methods are general and
easily understood, in order to maximize potential for interoperability.

Analogy FTP
~~~~~~~~~~~

Specifying the use of a protocol alone may be insufficient to provide enough information for
data exchange and interoperability.  For example when exchanging data via FTP, a number of choices
need to be made above and beyond the protocol.

        - authenticated or anonymous use?
        - how to signal that a file transfer has completed (permission bits? suffix? prefix?)
        - naming convention
        - text or binary transfer

Agreed conventions above and beyond simply FTP (IETF RFC 959) are needed.  Similar to the use
of FTP alone as a transfer protocol is insufficient to specify a complete data transfer
procedure, use of AMQP, without more information, is incomplete. The intent of the conventions
layered on top of AMQP is to be a minimum amount to achieve meaningful data exchange.

AMQP: not 1.0, but 0.8 or 0.9
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

AMQP 1.0 standardizes the on-the-wire protocol, but removed all broker standardization.
As the use of brokers is key to Sarracenia´s use of, was a fundamental element of earlier standards,
and as the 1.0 standard is relatively controversial, this protocol assumes a pre 1.0 standard broker,
as is provided by many free brokers, such as rabbitmq and Apache QPid, often referred to as 0.8,
but 0.9 and post 0.9 brokers could inter-operate well.

Named Exchanges and Queues
~~~~~~~~~~~~~~~~~~~~~~~~~~

In AMQP prior to 1.0, many different actors can define communication parameters, such as exchanges
to publish to, queues where messages accumulate, and bindings between the two. Applications
and users declare and user their exchanges, queues, and bindings. All of this was dropped
in the move to 1.0 making topic based exchanges, an important underpinning of pub/sub patterns
much more difficult.

in AMQP 0.9, one subscriber can declare a queue, and then multiple processes (given the right
permissions and the queue name) can consume from the same queue. That requires being able
to name the queue. In another protocol, such as MQTT, one cannot name the queue, and so
this processing pattern is not supported.

The mapping convention describte in a Topic_ section, allows MQTT to establish separate
hierarchies which provides a fixed distribution among the workers, but not exactly the
self-balancing shared queue that AMQP provides.


.. NOTE::

  In RabbitMQ (the initial broker used), permissions are assigned using regular expressions. So
  a permission model where AMQP users can define and use *their* exchanges and queues
  is enforced by a naming convention easily mapped to regular expressions (all such
  resources include the username near the beginning). Exchanges begin with: xs_<user>_.
  Queue names begin with: q_<user>_.  

Topic-based Exchanges
~~~~~~~~~~~~~~~~~~~~~

Topic-based exchanges are used exclusively. AMQP supports many other types of exchanges,
but sr_post have the topic sent in order to support server side filtering by using topic
based filtering. At AMQP 1.0, topic-based exchanges (indeed all exchanges, are no
longer defined.) Server-side filtering allows for much fewer topic hierarchies to be used,
and for much more efficient subsciptions.

In Sarracenia, topics are chosen to mirror the path of the files being announced, allowing
straight-forward server-side filtering, to be augmented by client-side filtering on
message reception.

The root of the topic tree is the version of the message payload.  This allows single brokers
to easily support multiple versions of the protocol at the same time during transitions.  *v02*,
created in 2015, is the third iteration of the protocol and existing servers routinely support previous
versions simultaneously in this way.  The second sub-topic defines the type of message.
At the time of writing:  v02.post is the topic prefix for current post messages.

Little Data 
~~~~~~~~~~~

The AMQP messages contain announcements, no actual file data. AMQP is optimized for and assumes
small messages. Keeping the messages small allows for maximum message throughtput and permits
clients to use priority mechanisms based on transfer of data, rather than the announcements.
Accomodating large messages would create many practical complications, and inevitably require
the definition of a maximum file size to be included in the message itself, resulting in
complexity to cover multiple cases.

Sr3_post is intended for use with arbitrarily large files, via segmentation and multi-streaming.
Blocks of large files are announced independently and blocks can follow different paths
between initial pump and final delivery. The protocol is unidirectional, in that there
is no dialogue between publisher and subscriber. Each post is a stand-alone item that
is one message in a stream, which on receipt may be spread over a number of nodes.

However, it is likely that, for small files over high latency links, it is
more efficient to include the body of the files in the messages themselve,
rather than forcing a separate retrieval phase.  The relative advantage depends on:

* relative coarseness of server side filtering means some filtering is done on
  the client side.  Any data embedded for messages discarded on the client-side
  are waste.

* Sarracenia establishes long-lived connections for some protocols, such as SFTP,
  so the relative overhead for a retrieval may not be long.

* One will achieve a higher messaging rate without data being embedded, and if the
  messages are distributed to a number of workers, it is possible that the resulting
  message rate is higher without embedded data (because of faster distribution for
  parallel download) than the savings from embedding.

* the lower the latency of the connection, the lesser the performance advantage
  of embedding, and the more it becomes a limiting factor on high performance
  transfers.

Further work is needed to better clarify when it makes sense to embed content
in messages. For now, the *content* header is included to allow such experiments
to occur.



Other Parameters
~~~~~~~~~~~~~~~~

AMQP has many other settings, and reliability for a particular use case
is assured by making the right choices.

* persistence (have queues survive broker restarts, default to true),

* expiry (how long a queue should exist when no-one is consuming from it.  Default: a few
  minutes for development, but can set much longer for production)

* message_ttl (the life-span of queued messages. Messages that are too old will not
  be delivered: default is forever.)

* Pre-fetch is an AMQP tunable to determine how many messages a client will
  retrieve from a broker at once, optimizing streaming. (default: 25)

These are used in declarations of queues and exchanges to provide appropriate
message processing.  This is not an exhaustive list.

