=============================
 General Sarracenia Concepts
=============================

This document describes abstractions underlying Sarracenia. 
It isn't clear how directly applicable this information is to normal usage, 
but it seems this information should be available *somewhere*.

.. contents::

Introduction
------------

Sarracenia pumps form a network. The network uses mqp brokers as a transfer
manager which sends advertisements in one direction and report messages in the
opposite direction. Administrators configure the paths that data flows through
at each pump, as each broker acts independently, managing transfers from
transfer engines it can reach, with no knowledge of the overall network. The
locations of pump and the directions of traffic flow are chosen to work with
permitted flows. Ideally, no firewall exceptions are needed.

Sarracenia does no data transport. It is a management layer to co-ordinate
the use of transport layers. So to get a running pump, actual transport mechanisms
need to be set up as well. The two mechanisms currently supported are web
servers and SFTP. In the simplest case, all of the components are on the
same server, but there is no need for that. The broker could be on a
different server from both ends of a given hop of a data transfer.

The best way for data transfers to occur is to avoid polling. It is more
efficient if writers can be coaxed into emitting appropriate sr_post messages.
Similarly, when delivering, it is ideal if the receivers use sr_subscribe, and
an on_file plugin to trigger their further processing, so that the file is 
handed to them without polling. This is the most efficient way of working, but
it is understood that not all software can be made co-operative. Tools to poll
in order to start transport flows are sr_poll, and sr_watch.

Generally speaking, Linux is the main deployment target, and the only platform on which
server configurations are deployed. Other platforms are used as client end points.
This isn´t a limitation, it is just what is used and tested. Implementations of
the pump on Windows should work, they just are not tested.


The Flow Algorithm
~~~~~~~~~~~~~~~~~~

All of the components (post, subscribe, sarra, sender, shovel, watch, winnow)
share substantial code and differ only in default settings. The Flow
algorithm is:

* Gather a list of messages
* Filter them with accept/reject clauses
* Work on the accepted messages.
* Post the work accomplished for the next flow.

in more detail:

.. table:: **Table 1: The Algorithm for All Components**
 :align: center

 +----------+-------------------------------------------------------------+
 |          |                                                             |
 |  PHASE   |                 DESCRIPTION                                 |
 |          |                                                             |
 +----------+-------------------------------------------------------------+
 | *gather* | Get information about an initial list of files              |
 |          |                                                             |
 |          | from: a queue, a directory, a polling script.               |
 |          | output: worklist.incoming populated with messages.          |
 |          |                                                             |
 |          | Each message is a python dictionary.                        |
 +----------+-------------------------------------------------------------+
 | *Filter* | Reduce the list of files to act on.                         |
 |          |                                                             |
 |          | Apply accept/reject clauses                                 |
 |          |                                                             |
 |          | after_accept callbacks                                      |
 |          | move messages from worklist.incoming to worklist.rejected.  |
 |          | ones to run: flowcb/nodupe.py (runs duplicate suppresion.)  |
 |          |                                                             |
 +----------+-------------------------------------------------------------+
 | *work*   | process the message by downloading or sending               |
 |          |                                                             |
 |          | run transfer (download or send.)                            |
 |          |                                                             |
 |          | run after_work                                              |
 +----------+-------------------------------------------------------------+
 | *post*   | Post announcement of file downloads/sent to post_broker     |
 |          | or otherwise dispose of task (to file, or retry... or)      |
 +----------+-------------------------------------------------------------+

The main components of the python implementation of Sarracenia all implement the same 
algorithm described above. The algorithm has various points where custom processing
can be inserted flowCallbacks, or deriving classes from flow, integrity, or transfer
classes.

The components just have different default settings:

.. table:: **Table 2: How Each Component Uses the Flow Algorithm**
 :align: center

 +------------------------+--------------------------+
 | Component              | Use of the algorithm     |
 +------------------------+--------------------------+
 +------------------------+--------------------------+
 | *sr_subscribe*         | Gather=gather.message    |
 |                        |                          |
 |   Download file from a | Filter                   |
 |   pump.                |                          |
 |                        | Work=Download            |
 |   default mirror=False |                          |
 |   All others it is True| post=optional            |
 +------------------------+--------------------------+
 | *sr_sarra*             | Gather=gather.message    |
 |                        |                          |
 |   Used on pumps.       |                          |
 |   Download file from a | Filter                   |
 |   pump to another pump |                          |
 |   Post the file from   |                          |
 |   the new pump so that |                          |
 |   subscribers to       | Work=Download            |
 |   this pump can        |                          |
 |   download in turn.    | post=post                |
 |                        |                          |
 +------------------------+--------------------------+
 | *sr_poll*              | Gather                   |
 |                        | if has_vip: poll         |
 |                        |                          |
 |   Find files on other  | Filter                   |
 |   servers to post to   |                          |
 |   a pump.              | if has_vip:              |
 |                        |     Work=nil             |
 |   has_vip*             |                          |
 |                        |     Post=yes             |
 |                        |     Message?, File?      |
 +------------------------+--------------------------+
 | *sr_shovel*            | Gather=gather.message    |
 |                        |                          |
 |   Move posts or        | Filter (shovel cache=off)|
 |   reports around.      |                          |
 |                        | Work=nil                 |
 |                        |                          |
 |                        | Post=yes                 |
 +------------------------+--------------------------+
 | *sr_winnow*            | Gather=gather.message    |
 |                        |                          |
 |   Move posts or        | Filter (shovel cache=off)|
 |   reports around.      |                          |
 |                        | Work=nil                 |
 |   suppress duplicates  |                          |
 |                        | Post=yes                 |
 +------------------------+--------------------------+
 | *sr_post/watch*        | Gather=gather.file       |
 |                        |                          |
 |   Find file on a       | Filter                   |
 |   local server to      |                          |
 |   post                 | Work=nil                 |
 |                        |                          |
 |                        | Post=yes                 |
 |                        |   Message?, File?        |
 +------------------------+--------------------------+
 | *sr_sender*            | Gather=gather.message    |
 |                        |                          |
 |   Send files from a    | Filter                   |
 |   pump. If remote is   |                          |
 |   also a pump, post    | Do=sendfile              |
 |   the sent file there. |                          |
 |                        | Outlet=optional          |
 +------------------------+--------------------------+

Components are easily composed using AMQP brokers, which create elegant networks
of communicating sequential processes (in the `Hoare <http://dl.acm.org/citation.cfm?doid=359576.359585>`_ sense).

Multiple processes: Instances, Singletons and VIP
-------------------------------------------------

The flow algorithm isn't confined to a single process. Many processes can run
the same flow configuration. For the sarra, sender, shovel and subscribe, components,
one sets the *instance* setting to the number of processes to run and 
consume from the configured *queue* that they share.

The poll, post, and watch components, by contrast, are limited to a single process
on any given server. In the table above, there is a note about *has_vip*. When 
there are multiple servers participating in a configuration, the vip directive
can be used to have the servers co-operate to provide a single service (where
only one server is active at a time.) For most components, The vip directive in
a configuration file defines a virtual ip address that a server must have 
actively on it for that component to be active. If Sarracenia detects that the
interface is not present on the server, then the component will run in passive
mode.

For almost all components, passive mode means that no processing will occur.
it will just passively check once in a while if it has obtained the vip, and
if not, will stand by indefinitely.

The exception to this is poll, which works differently. in poll, when you
do not have the vip the following algorithmic loop will continue:

* gather
* filter
* after_accept

The poll's gather and fileter being alive and kicking even in passive mode, 
allows it to subscribe to the exchange it is posting to and update it's cache
of files posted from the messages, so that if it ever does become active, its
state is current.



Mapping AMQP Concepts to Sarracenia
-----------------------------------

It is helpful to understand a bit about AMQP to work with Sarracenia. 
AMQP is a vast and interesting topic in its own right. No attempt is
made to explain all of it here. This section just provides a little context, and introduces
only background concepts needed to understand and/or use Sarracenia. For more information
on AMQP itself, a set of links is maintained at the 
`Metpx web site <sarra.rst#amqp>`_ 

.. image:: Concepts/AMQP4Sarra.svg
    :scale: 50%
    :align: center

An AMQP Server is called a Broker. *Broker* is sometimes used to refer to the software,
other times server running the broker software (same confusion as *web server*.) In the
above diagram, AMQP vocabulary is in Orange, and Sarracenia terms are in blue. There are
many different broker software implementations. We use rabbitmq. We are not trying to
be rabbitmq specific, but management functions differ between implementations.

*Queues* are usually taken care of transparently, but you need to know
   - A consumer/subscriber creates a queue to receive messages.
   - Consumer queues are *bound* to exchanges (AMQP-speak)
   - MQTT equivalent: *client-id*

An *exchange* is a matchmaker between *publisher* and *consumer queues*.
   - A message arrives from a publisher.
   - message goes to the exchange, is anyone interested in this message?
   - in a *topic based exchange*, the message topic provides the *exchange key*.
   - interested: compare message key to the bindings of *consumer queues*.
   - message is routed to interested *consumer queues*, or dropped if there aren't any.
   - concept does not exist in MQTT, used as root of the topic hierarchy.

Multiple processes can share a *queue*, they just take turns removing messages from it.
   - This is used heavily for sr_sarra and sr_subcribe multiple instances.
   - Same concept is available as *shared subscriptions* in MQTT.

How to Decide if Someone is Interested.
   - For Sarracenia, we use (AMQP standard) *topic based exchanges*.
   - Subscribers indicate what topics they are interested in, and the filtering occurs server/broker side.
   - Topics are just keywords separated by a dot. Wildcards: # matches anything, * matches one word.
   - We create the topic hierarchy from the path name (mapping to AMQP syntax)
   - Resolution & syntax of server filtering is set by AMQP. (. separator, # and * wildcards)
   - Server side filtering is coarse, messages can be further filtered after download using regexp on the actual paths (the reject/accept directives.)



AMQP v09 (Rabbitmq) Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MetPX-Sarracenia is only a light wrapper/coating around Message Queueing Protocols.
For those who are familiary with the underlying protocols, These are the mappings:

  - A MetPX-Sarracenia data pump is a python AMQP application that uses a (rabbitmq)
    broker to co-ordinate SFTP and HTTP client data transfers, and accompanies a
    web server (apache) and sftp server (openssh), often on the same user-facing address.

  - A MetPX-Sarracenia data pump can also work with rabbitmq replaced by an MQTT broker
    such as mosquitto.org (but some administrivia must be handled manually.

  - Wherever reasonable, we use their terminology and syntax.
    If someone knows AMQP, they understand. If not, they can research.

    - Users configure a *broker*, instead of a pump.
    - by convention, the default vhost '/' is always used (did not feel the need to use other vhosts yet)
    - users explicitly can pick their *queue* names (this ia a client-id in MQTT.)
    - users set *subtopic*,
    - topics with dot separator are minimally transformed, rather than encoded.
    - queue is set to *durable* so that messages are not lost across broker restarts.
    - we use *message headers* (AMQP-speak for key-value pairs) rather than encoding in JSON or some other payload format.
    - *expire* how long to keep an idle queue or exchange around. 

  - reduce complexity through conventions.
     - use only one type of exchanges (Topic), take care of bindings.
     - naming conventions for exchanges and queues.
        - exchanges start with x.
          - xs_Weather - the exchange for the source (mqp user) named Weather to post messages
          - xpublic -- exchange used for most subscribers.
        - queues start with q\_

MQTT (version =5) Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~

MQTT is actually a better match to Sarracenia than AMQP, as it is entirely
based on hierarchical topics, while topics are only one among a variety of 
choices for routing methods in AMQP.

  - in MQTT, topic separator is / instead of .
  - the MQTT topic wildcard *#* is the same as in AMQP (match rest of topic)
  - the MQTT topic wildcard *+* is the same as the AMQP *\** (match one topic.)
  - an AMQP "Exchange" is mapped to the root of the MQTT topic tree, 
  - an AMQP "queue" is represented in MQTT by  *client-id* and a *shared subscription*
    Note: Shared subscriptions are only present in MQTTv5. So Sarracenia can only easily

    * AMQP: A queue named *queuename* is bount to an exchange xpublic with key: v03.observations ...  
    * MQTT subscription: topic $shared/*queuename*/xpublic/v03/observations ...  

  - connections are clean_sesssion=0 normally, to recover messages when a connection is broken.
  - MQTT QoS==1 is used to assure messages are sent at least once, and avoid overhead
    of ensuring only once.
  - AMQP *prefetch* mapped to MQTT *receiveMaximum*
  - *expire* has same meaning in MQTT as in AMQP.

MQTT v3 lacks shared subscriptions, and the recovery logic is quite different.
Sarracenia only supports v5.


Flow Through Pumps
------------------

.. image:: Concepts/e-ddsr-components.jpg
    :scale: 100%
    :align: center



A description of the conventional flow of messages through exchanges on a pump:

- subscribers usually bind to the xpublic exchange to get the main data feed.
  This is the default in sr_subscribe.

- A user named Alice will have two exchanges:

  - xs_Alice the exhange where Alice posts her file notifications and report messages.(via many tools)
  - xr_Alice the exchange where Alice reads her report messages from (via sr_report)

- usually sr_sarra will read from xs_alice, retrieve the data corresponding to Alice´s *post*
  message, and make it available on the pump, by re-announcing it on the xpublic exchange.

- sr_winnow may pull from xs_alice instead, but follows the same pattern as sr_sarra.

- usually, sr_audit --users will cause rr_alice2xreport shovel configurations to 
  read xs_alice and copy the report messages onto the private xreport exchange.

- Admins can point sr_report at the xreport exchange to get system-wide monitoring.
  Alice will not have permission to do that, she can only look at xl_Alice, which should have
  the report messages pertinent to her.

- rr_xreport2source shovel configurations auto-generated by sr_audit look at messages for the 
  local Alice user in xreport, and sends them to xl_Alice.

The purpose of these conventions is to encourage a reasonably secure means of operating.
If a message is taken from xs_Alice, then the process doing the reading is responsible for
ensuring that it is tagged as coming from Alice on this cluster. This prevents certain
types of ´spoofing´ as messages can only be posted by proper owners.


Users and Roles
---------------

Usernames for pump authentication are significant in that they are visible to all.
They are used in the directory path on public trees, as well as to authenticate to the broker.
They need to be understandable. They are often wider scope than a person...
perhaps call them 'Accounts'. It can be elegant to configure the same usernames
for use in transport engines.

All Account names should be unique, but nothing will avoid clashes when sources originate from
different pump networks, and clients at different destinations. In practice, name clashes are
addressed by routing to avoid two different sources' with the same name having their
data offerings combined on a single tree. On the other hand, name clashes are not always an error.
Use of a common source account name on different clusters may be used to implement folders that
are shared between the two accounts with the same name.

Pump users are defined with the *declare* option. Each option starts with the *declare*
keyword, followed by the specified role, and lastly the user name which has that role.
Role can be one of:

subscriber
  A subscriber is user that can only subscribe to data and report messages. Not permitted to inject data.
  Each subscriber gets an xs_<user> named exchange on the pump, where if a user is named *Acme*,
  the corresponding exchange will be *xs_Acme*. This exchange is where an sr_subscribe
  process will send its report messages.

  By convention/default, the *anonymous* user is created on all pumps to permit subscription without
  a specific account.

source
  A user permitted to subscribe or originate data. A source does not necessarily represent
  one person or type of data, but rather an organization responsible for the data produced.
  So if an organization gathers and makes available ten kinds of data with a single contact
  email or phone number for questions about the data and it's availability, then all of
  those collection activities might use a single 'source' account.

  Each source gets a xs_<user> exchange for injection of data posts, and, 
  similar to a subscriber, to send report messages about processing and receipt
  of data. Each source is able to view all of the messages for data it has 
  injected, but the location where all of these messages are available varies
  according to administrator configuration of report routing. A source may 
  inject data on pumpA, but may subscribe to reports on a different pump. The
  reports corresponding to the data the source injected are written in 
  exchange xl_<user>.

  When data is first injected, the path is modified by sarracenia to prepend a 
  fixed upper part of the directory tree. The first level directory is the day
  of ingest into the network in YYYYMMDD format. The second level directory is
  the source name. So for a user Alice, injecting data on May 4th, 2016, the
  root of the directory tree is:  20160504/Alice. Note that all pumps are 
  expected to run in the UTC timezone (widely, but inaccurately, referred to
  as GMT.)

  There are daily directories because there is a system-wide life-time for data, it is deleted
  after a standard number of days, data is just deleted from the root.

  Since all clients will see the directories, and therefore client configurations will include them.
  It would be wise to consider the account name public, and relatively static.

  Sources determine who can access their data, by specifying which cluster to send the data to.

feeder
  a user permitted to subscribe or originate data, but understood to represent a pump.
  This local pump user would be used to, run processes like sarra, report routing shovels, etc...


admin
  a user permitted to manage the local pump.
  It is the real rabbitmq-server administrator.
  The administrator runs sr_audit to create/delete
  exchanges, users, or clean unused queues... etc.

Example of a complete valid admin.conf, for a host named *blacklab* ::

  cluster blacklab
  admin amqps://hbic@blacklab/
  feeder  amqps://feeder@blacklab/
  declare source goldenlab
  declare subscriber anonymous

A corresponding credentials.conf would look like::

  amqps://hbic:hbicpw@blacklab/
  amqps://feeder:feederpw@blacklab/
  amqps://goldenlab:puppypw@blacklab/
  amqps://anonymous:anonymous@blacklab/


