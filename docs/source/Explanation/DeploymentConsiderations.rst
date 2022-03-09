Deployment Considerations
=========================

Sarracenia data pumps are often placed in network designs near demarcation points, to provide
an application level demarcation point to allow for security scanning and to limit visibility
into different zones.  Pumps may either have all services incorporated on a single server,
or commonly the main broker is on a dedicated node, and the nodes that do the data transfer
are called *Transport Engines.*  In high performance deployments, each transport engine
may have a local broker to deal with local transfers and transformations. 

Transport Engines
-----------------

Transport engines are the data servers queried by subscribers, by the end users, or other pumps.
The subscribers read the notices and fetch the corresponding data, using the indicated protocol.
The software to serve the data can be either SFTP or HTTP (or HTTPS.) For specifics of
configuring the servers for use, please consult the documentation of the servers themselves.
Also note that additional protocols can be enabled through the use of do\_ plugins, as
described in the Programming Guide.


IPv6
~~~~

A sample pump was implemented on a small VPS with IPv6 enabled. A client
from far away connected to the rabbitmq broker using IPv6, and the 
subscription to the apache httpd worked without issues. *It just works*. There
is no difference between IPv4 and IPv6 for sarra tools, which are agnostic of
IP addresses.

On the other hand, one is expected to use hostnames, since use of IP addresses
will break certificate use for securing the transport layer (TLS, aka SSL) No
testing of IP addresses in URLs (in either IP version) has been done.



Designs
-------

There are many different arrangements in which sarracenia can be used. 

Dataless
  where one runs just sarracenia on top of a broker with no local transfer engines.
  This is used, for example to run sr_winnow on a site to provide redundant data sources.

Standalone
  the most obvious one, run the entire stack on a single server, openssh and a web server
  as well the broker and sarra itself. Makes a complete data pump, but without any redundancy.

Switching/Routing
  Where, in order to achieve high performance, a cluster of standalone nodes are placed behind
  a load balancer. The load balancer algorithm is just round-robin, with no attempt to associate
  a given source with a given node. This has the effect of pumping different parts of large files
  through different nodes. So one will see parts of files announced by such pump, to be
  re-assembled by subscribers.

Data Dissemination
  Where in order to serve a large number of clients, multiple identical servers, each with a complete
  mirror of data

FIXME:
  ok, opened big mouth, now need to work through the examples.


Dataless or S=0
~~~~~~~~~~~~~~~

A configuration which includes only the AMQP broker. This configuration can be used when users
have access to disk space on both ends and only need a mediator. This is the configuration
of sftp.science.gc.ca, where the HPC disk space provides the storage so that the pump does
not need any, or pumps deployed to provide redundant HA to remote data centres.

.. note::

  FIXME: sample configuration of shovels, and sr_winnow (with output to xpublic) to allow
  subscribers in the SPC to obtain data from either edm or dor.

Note that while a configuration can be dataless, it can still make use of rabbitmq
clustering for high availability requirements (see rabbitmq clustering below.)


Winnowed Dataless 
~~~~~~~~~~~~~~~~~

Another example of a dataless pump would be to provide product selection from two upstream
sources using sr_winnow. The sr_winnow is fed by shovels from upstream sources, and
the local clients just connect to this local pump. sr_winnow takes
care of only presenting the products from the first server to make
them available. One would configure sr_winnow to output to the xpublic exchange
on the pump.

Local subscribers just point at the output of sr_winnow on the local pump. This
is how feeds are implemented in the Storm prediction centres of ECCC, where they
may download data from whichever national hub produces data first.


Dataless With Sr_poll
~~~~~~~~~~~~~~~~~~~~~

The sr_poll program can verify if products on a remote server are ready or modified.
For each of the product, it emits an announcement on the local pump. One could use
sr_subscribe anywhere, listen to announcements and get the products (provided the
credentials to access it)


Standalone
~~~~~~~~~~

In a standalone configuration, there is only one node in the configuration. It runs all components
and shares none with any other nodes. That means the Broker and data services such as sftp and
apache are on the one node.

One appropriate usage would be a small non-24x7 data acquisition setup, to take responsibility of data
queuing and transmission away from the instrument. It is restarted when the opportunity arises.
It is just a matter of installing and configuring all a data flow engine, a broker, and the package
itself on a single server. The *ddi* systems are generally configured this way.



Switching/Routing
~~~~~~~~~~~~~~~~~

In a switching/routing configuration, there is a pair of machines running a 
single broker for a pool of transfer engines. So each transfer engine's view of
the file space is local, but the queues are global to the pump.  

Note: On such clusters, all nodes that run a component with the
same config file created by default have an identical **queue_name**. Targetting the
same broker, it forces the queue to be shared. If it should be avoided,
the user can just overwrite the default **queue_name** inserting **${HOSTNAME}**.
Each node will have its own queue, only shared by the node instances.
ex.: queue_name q_${BROKER_USER}.${PROGRAM}.${CONFIG}.${HOSTNAME} )

Often there is internal traffic of data acquired before it is finally published.
As a means of scaling, often transfer engines will also have brokers to handle
local traffic, and only publish final products to the main broker.  This is how
*ddsr* systems are generally configured.


Security Considerations
-----------------------

This section is meant to provide insight to those who need to perform a security review
of the application prior to implementation.

Client
~~~~~~

All credentials used by the application are stored
in the ~/.config/sarra/credentials.conf file, and that file is forced to 600 permissions.


Server/Broker
~~~~~~~~~~~~~

Authentication used by transport engines is independent of that used for the brokers. A security
assessment of rabbitmq brokers and the various transfer engines in use is needed to evaluate
the overall security of a given deployment.


The most secure method of transport is the use of SFTP with keys rather than passwords. Secure
storage of sftp keys is covered in documentation of various SSH or SFTP clients. The credentials
file just points to those key files.

For Sarracenia itself, password authentication is used to communicate with the AMQP broker,
so implementation of encrypted socket transport (SSL/TLS) on all broker traffic is strongly
recommended.

Sarracenia users are actually users defined on rabbitmq brokers.
Each user Alice, on a broker to which she has access:

 - can create and publish to any exchange that starts with xs_Alice\_
 - has an exchange xr_Alice, where she reads her report messages.
 - can configure (read from and acknowledge) queues named qs_Alice\_.* to bind to exchanges
 - Alice can create and destroy her own queues and exchanges, but no-one else's.
 - Alice can only post data that she is publishing (it will refer back to her)
 - Alice can also read (or subscribe to) any exchange whose name ends in *public*.
 - Alice can thus create an exchange others can subscribe to with the following name:  xs_Alice_public

Alice cannot create any exchanges or other queues not shown above.

Rabbitmq provides the granularity of security to restrict the names of
objects, but not their types. Thus, given the ability to create a queue named q_Alice,
a malicious Alice could create an exchange named q_Alice_xspecial, and then configure
queues to bind to it, and establish a separate usage of the broker unrelated to sarracenia.

To prevent such misuse, sr_audit is a component that is invoked regularly looking
for mis-use, and cleaning it up.


Input Validation
~~~~~~~~~~~~~~~~

Users such as Alice post their messages to their own exchange (xs_Alice). Processes which read from
user exchanges have a responsibility for validation. The process that reads xs_Alice (likely an sr_sarra)
will overwrite any *source* or *cluster* heading written into the message with the correct values for
the current cluster, and the user which posted the message.

The checksum algorithm used must also be validated. The algorithm must be known. Similarly, if
there is a malformed header of some kind, it should be rejected immediately. Only well-formed messages
should be forwarded for further processing.

In the case of sr_sarra, the checksum is re-calculated when downloading the data, it
ensures it matches the message. If they do not match, an error report message is published.
If the *recompute_checksum* option is True, the newly calculated checksum is put into the message.
Depending on the level of confidence between a pair of pumps, the level of validation may be
relaxed to improve performance.

Another difference with inter-pump connections, is that a pump necessarily acts as an agent for all the
users on the remote pumps and any other pumps the pump is forwarding for. In that case, the validation
constraints are a little different:

- source doesn´t matter. (feeders can represent other users, so do not overwrite.)
- ensure cluster is not local cluster (as that indicates either a loop or misuse.)

If the message fails the non-local cluster test, it should be rejected, and logged (FIME: published ... hmm... clarify)

.. NOTE::
 FIXME:
   - if the source is not good, and the cluster is not good... cannot report back. so just log locally?


Privileged System Access
~~~~~~~~~~~~~~~~~~~~~~~~

Ordinary (sources, and subscribers) users operate sarra within their own permissions on the system,
like an scp command. The pump administrator account also runs under a normal linux user account and,
given requires privileges only on the AMQP broker, but nothing on the underlying operating system.
It is convenient to grant the pump administrator sudo privileges for the rabbitmqctl command.

There may be a single task which must operate with privileges: cleaning up the database, which is an easily
auditable script that must be run on a regular basis. If all acquisition is done via sarra, then all of
the files will belong to the pump administrator, and privileged access is not required for this either.



Glossary
--------

Sarracenia documentation uses a number of words in a particular way.
This glossary should make it easier to understand the rest of the documentation.


Source
  Someone who wants to ship data to someone else. They do that by advertising a 
  trees of files that are copied from the starting point to one or more pumps
  in the network. The advertisement sources produced tell others exactly where 
  and how to download the files, and Sources have to say where they want the 
  data to go to.

  Sources use programs like `sr_post.1 <../Reference/sr3.1.rst#post>`_, 
  `sr_watch.1 <../Reference/sr3.1.rst#watch>`_, and `sr_poll(1) <../Reference/sr3.1.rst#poll>`_ to create 
  their advertisements.


Subscribers
  are those who examine advertisements about files that are available, and 
  download the files they are interested in.

  Subscribers use `sr_subscribe(1) <../Reference/sr3.1.rst#subscribe>`_


Post, Notice, Notification, Advertisement, Announcement
  These are AMQP messages build by sr_post, sr_poll, or sr_watch to let users
  know that a particular file is ready. The format of these AMQP messages is 
  described by the `sr_post(7) <../Reference/sr3.1.rst#post>`_ manual page. All of these 
  words are used interchangeably. Advertisements at each step preserve the
  original source of the posting, so that report messages can be routed back 
  to the source.


Report messages
  These are AMQP messages (in `sr_post(7) <../Reference/sr3.1.rst#post>`_ format, with _report_ 
  field included) built by consumers of messages, to indicate what a given pump 
  or subscriber decided to do with a message. They conceptually flow in the 
  opposite direction of notifications in a network, to get back to the source.


Pump or broker
  A pump is a host running Sarracenia, a rabbitmq AMQP server (called a *broker*
  in AMQP parlance) The pump has administrative users and manage the AMQP broker
  as a dedicated resource.  Some sort of transport engine, like an apache 
  server, or an openssh server, is used to support file transfers. SFTP, and 
  HTTP/HTTPS are the protocols which are fully supported by sarracenia. Pumps
  copy files from somewhere, and write them locally. They then re-advertise the
  local copy to its neighbouring pumps, and end user subscribers, they can 
  obtain the data from this pump.

.. Note::
  For end users, a pump and a broker is the same thing for all practical 
  purposes. When pump administrators configure multi-host clusters, however, a 
  broker might be running on two hosts, and the same broker could be used by 
  many transport engines. The entire cluster would be considered a pump. So the
  two words are not always the same.


Dataless Pumps
  There are some pumps that have no transport engine, they just mediate 
  transfers for other servers, by making messages available to clients and
  servers in their network area.


Dataless Transfers
  Sometimes transfers through pumps are done without using local space on the pump.


Pumping Network
  A number of interconnects servers running the sarracenia stack. Each stack 
  determines how it routes items to the next hop, so the entire size or extent
  of the network may not be known to those who put data into it.


Network Maps
  Each pump should provide a network map to advise users of the known destination
  that they should advertise to send to. *FIXME* undefined so far.
