
=========
 SR_post 
=========

-------------------------------------------
Sarracenia v02 Post Message Format/Protocol
-------------------------------------------

:Manual section: 7
:Date: @Date@
:Version: @Version@
:Manual group: MetPX-Sarracenia

.. contents::

SYNOPSIS
--------

The format of file change announcements for sr_post.  

An sr_post message consists of four parts: **AMQP TOPIC, First Line, Rest of Message, AMQP HEADERS.**

**AMQP Topic:** *<version>.post.{<dir>.}*

::

           <version> = "v02" the version of the protocol or format.
           "post" = the type of message within the protocol.
           <dir> = a sub-directory leading to the file (perhaps many directories deep)
           <filename> = the name of the file on the server.

**AMQP Headers:** *<series of key-value pairs>*

::
           "parts" = size and partitioning information.
           "sum" = checksum algorithm and value.

**Body:** *<first line> = <date stamp> <base_url> <relpath> <newline>*


::

          <date stamp> - YYYYMMDDHHMMSS.ss - UTC date/timestamp.
          <base_url>   - root of the url to download.
          <relpath>    - relative path can be catenated to <base_url>

<*rest of body is reserved for future use*>


DESCRIPTION
-----------

Sources create messages in the *sr_post* format to announce file changes. Subscribers 
read the post to decide whether a download of the content being announced is warranted.  This 
manual page completely describes the format of those messages.  The messages are payloads 
for an Advanced Message Queuing Protocol (AMQP) message bus, but file data transport 
is separate, using more common protocols such as SFTP, HTTP, HTTPS, or FTP (or other?).
Files are transported as pure byte streams, no metadata beyond the file contents is 
transported (permission bits, extended attributes, etc...). Permissions of files 
on the destination system are upto the receiver to decide.

With this method, AMQP messages provide a 'control plane' for data transfers.  While each post message 
is essentially point to point, data pumps can be transitively linked together to make arbitrary 
networks.  Each posting is consumed by the next hop in the chain. Each hop re-advertises 
(creates a new post for) the data for later hops.  The posts flow in the same direction as the 
data.  If consumers permit it, report messages (see sr_report(7)) also flow through the control path, 
but in the opposite direction, allowing sources to know the entire disposition of their 
files through a network.  

The minimal layer over raw AMQP provides more complete file transfer functionality:

Source Filtering (use of `AMQP TOPIC`_ exchanges)
   The messages make use of *topic exchanges* from AMQP, where topics are hierarchies
   meant to represent subjects of interest to a consumer.  A consumer may upload the 
   selection criteria to the broker so that only a small subset of postings
   are forwarded to the client.  When there are many users interested in only small subsets
   of data, the savings in traffic are large.

Fingerprint Winnowing (use of the sum_ header)
   Each product has a checksum and size intended to identify it uniquely, referred to as
   a *fingerprint*.  If two files have the same fingerprint, they are considered
   equivalent.  In cases where multiple sources of equivalent data are available but 
   downstream consumers would prefer to receive single announcements
   of files, intermediate processes may elect to publish notifications of the first 
   product with a given fingerprint, and ignore subsequent ones. 
   Propagating only the first occurrence of a datum received downstream, based on
   its fingerprint, is termed: *Fingerprint Winnowing*.

   *Fingerprint Winnowing* is the basis for a robust strategy for high availability:  setting up
   multiple sources for the same data, consumers accept announcements from all of them, but only
   forwarding the first one received downstream.  In normal operation, one source may be faster 
   than the others, and so the other sources' files are usually 'winnowed'. When one source
   disappears, the other sources' data is automatically selected, as the fingerprints
   are now *fresh* and used, until a faster source becomes available.

   The advantage of this method for high availability is that no A/B decision is required.
   The time to *switchover* is zero.  Other strategies are subject to considerable delays
   in making the decision to switchover, and pathologies one could summarize as flapping,
   and/or deadlocks.  

   *Fingerprint Winnowing* also permits *mesh-like*, or *any to any* networks, where one simply 
   interconnects a node with others, and messages propagate.  Their specific path through the 
   network is not defined, but each participant will download each new datum from the first
   node that makes it available to them.  Keeping the messages small and separate from data 
   is optimal for this usage.
 
Partitioning (use of the parts_ Header)
   Any store on a forward data pumping network that transports entire files limits the maximum
   file size to the minimum available on any intervening node. To avoid defining a maximum 
   file size, a segmentation standard is specified, allowing intervening nodes to hold
   only segments of the file, and forward them as they are received, rather than being
   forced to hold the entire file.

   Partitioning also permits multiple streams to transfer portions of the file in parallel. 
   Multiple streams can provide an effective optimization over long links.

   

AMQP TOPIC
----------

In topic based AMQP exchanges, every message has a topic header.  AMQP defines the '.' character 
as a hierarchical separator (like '\' in a Windows path name, or '/' on linux) there is also a
pair of wildcards defined by the standard:  '*' matches a single topic, '#' matches the rest of 
the topic string. To allow for changes in the message body in the future, topic trees begin with 
the version number of the protocol.   

AMQP allows server side topic filtering using wildcards.  Subscribers specify topics of 
interest (which correspond to directories on the server), allowing them to pare down the 
number of notifications sent from server to client.  

The root of the topic tree is the version specifier: "v02".  Next comes the message type specifier.  
These two fields define the protocol that is in use for the rest of the message.
The message type for post messages is "post".  After the fixed topic prefix, 
the remaining sub-topics are the path elements of the file on the web server.  
For example, if a file is placed on http://www.example.com/a/b/c/d/foo.txt, 
then the complete topic of the message will be:  *v02.post.a.b.c.d*
AMQP fields are limited to 255 characters, and the characters in the field are utf8 
encoded, so actual length limit may be less than that. 



THE FIRST LINE 
--------------

The first line of a message contains all mandatory elements of an announcement.
There are a series of white space separated fields:

*<date stamp>*: the date the posting was emitted.  Format: YYYYMMDDHHMMSS. *<decimalseconds>*

 Note: The datestamp is always in the UTC timezone.

*<base_url>* -- the base URL used to retrieve the data.

The URL consumers will use to download the data.  Example of a complete URL::

 sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRPDS_HiRes_000.gif

*<relativepath>*  the variable part of the URL, usually appended to *base_url*.


*<newline>* signals the end of the first line of the message and is denoted by a single line feed character.


THE REST OF MESSAGE
-------------------

Use of only the first line of the AMQP payload is currently defined.  
The rest of the payload body is reserved for future use.


AMQP HEADERS 
------------

In addition to the first line of the message containing all mandatory fields, optional 
elements are stored in AMQP headers (utf8 encoded key-value pairs limited to 255 bytes in length), included 
in messages when appropriate. 

**from_cluster=<cluster_name>**
   The from_cluster defines the name of the source cluster where the data was introduced into the network.
   It is used to return the logs back to the cluster whenever its products are used.

**link=<value of symbolic link>**
   When file to transfer is a symbolic link, the 'link' header is created to contain its value.

.. _parts:

**parts=<method>,<bsz>,<blktot>,<brem>,<bno>**

 A header indicating the method and partitioning settings applied to the file.
 Partitioning is used to send a single file as a collection of segments, rather than as
 a single entity.  Partitioning is used to accelerate transfers of large data sets by using
 multiple streams, and/or to reduce storage use for extremely large files.

 When transferring partitioned files, each partition is advertised and potentially transported
 independently across a data pumping network.

 *<method>*
 
 Indicates what partitioning method, if any, was used in transmission. 

 +-----------+---------------------------------------------------------------------+
 |   Method  | Description                                                         |
 +-----------+---------------------------------------------------------------------+
 |    p      | File is partitioned, individual part files are created.             |
 +-----------+---------------------------------------------------------------------+
 |    i      | File is partitioned, but blocks are read from a single file,        |
 |           | rather than parts.                                                  |
 +-----------+---------------------------------------------------------------------+
 |    1      | File is in a single part (no partitioning).                         |
 +-----------+---------------------------------------------------------------------+

 - analogous to rsync options: --inplace, --partial,

 *<blocksize in bytes>: bsz*

 The number of bytes in a block.  When using method 1, the size of the block is the size of the file.  
 Remaining fields only useful for partitioned files.	

 *<blocks in total>: blktot*
 the integer total number of blocks in the file (last block may be partial)

 *<remainder>: brem*
 normally 0, on the last block, remaining bytes in the file
 to transfer.

        -- if (fzb=1 and brem=0)
               then bsz=fsz in bytes in bytes.
               -- entire files replaced.
               -- this is the same as rsync's --whole-file mode.

 *<block#>: bno*
 0 origin, the block number covered by this posting.

**rename=<relpath>** 

If different from relpath, this value replaces relpath as the suggested location 
to write the file to.

**oldname=<path>**
**newname=<path>**

 when a file is renamed at the source, to send it to subscribers, two posts 
 result: one message is announced with the new name as the base_url, 
 and the oldname header set to the previous file name.
 Another message is sent with the old name as the src path, and the *newname* 
 as a header.  This ensures that *accept/reject* clauses are correctly
 interpreted, as a *rename* may result in a download if the former name
 matches a *reject*  clause, or a file removal if the new name
 matches a *reject* clause.

 Hard links are also handled as an ordinary post of the file with a *oldname*
 header set.

**source=<sourceid>**
 a character field indicating the source of the data injected into the network.
 should be unique within a data pumping network.  It's usually the same as the
 account used to authenticate to the broker.

.. _sum:

**sum=<method>,<value>**

 The sum is a signature computed to allow receivers to determine 
 if they have already downloaded the partition from elsewhere.

 *<method>* - character field indicating the checksum algorithm used.

 +-----------+---------------------------------------------------------------------+
 |   Method  | Description                                                         |
 +-----------+---------------------------------------------------------------------+
 |     0     | No checksums (unconditional copy.) Skips reading file (faster)      |
 +-----------+---------------------------------------------------------------------+
 |     a     | Application defined sum (which cannot be calculated, must be stored)|
 +-----------+---------------------------------------------------------------------+
 |     d     | Checksum the entire data (MD-5 as per IETF RFC 1321)                |
 +-----------+---------------------------------------------------------------------+
 |     L     | Linked: SHA512 sum of link value                                    |
 +-----------+---------------------------------------------------------------------+
 |     n     | Checksum the file name (MD-5 as per IETF RFC 1321)                  |
 +-----------+---------------------------------------------------------------------+
 |     R     | Removed: SHA512 of file name.                                       |
 +-----------+---------------------------------------------------------------------+
 |     s     | Checksum the entire data (SHA512 as per IETF RFC 6234)              |
 +-----------+---------------------------------------------------------------------+
 |     z     | Checksum on download, with algorithm as argument                    |
 |           | Example:  z,d means download, applying d checksum, and advertise    |
 |           | with that calculated checksum when propagating further.             |
 +-----------+---------------------------------------------------------------------+
 |  *<name>* | Checksum with some other algorithm, named *<name>*                  |
 |           | *<name>* should be *registered* in the data pumping network.        |
 |           | Registered means that all downstream subscribers can obtain the     |
 |           | algorithm to validate the checksum.                                 |
 +-----------+---------------------------------------------------------------------+


*<value>* The value is computed by applying the given method to the partition being transferred.
  for algorithms for which no value makes sense, a random integer is generated to support
  checksum based load balancing.


**to_clusters=<cluster_name1,cluster_name2,...>**
 The to_clusters defines a list of destination clusters where the data should go into the network.
 Each name should be unique within all exchanging rabbitmq clusters. It is used to do the transit
 of the products and their notices through the exchanging clusters.

*optional headers follow*

for the file mirroring use case, additional files will be present:

**atime,mtime,mode**

  man 2 stat - the linux/unix standard file metadata:
  access time, modification time, and permission (mode bits)
  the times are in the same decimal date format as the date stamp field.
  the permission string is four characters intended to be interpreted as
  traditional octal linux/unix permissions.

Headers which are unknown to a given client should be forwarded without modification.


EXAMPLE
-------

:: 

 Topic: v02.post.NRDPS.GIF.NRDPS_HiRes_000.gif
 first line: 201506011357.345 sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRDPS_HiRes_000.gif NRDPS/GIF/  
 Headers: parts=p,457,1,0,0 sum=d,<md5sum> source=ec_cmc

        - v02 - version of protocol
        - post - indicates the type of message
        - version and type together determine format of following topics and the message body.

        - blocksize is 457  (== file size)
        - block count is 1
        - remainder is 0.
        - block number is 0.
        - d - checksum was calculated on the body of the file.
        - complete source URL specified (does not end in '/')
        - relative path specified for

        pull from:
                sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRDPS_HiRes_000.gif

        complete relative download path:
                NRDPS/GIF/NRDPS_HiRes_000.gif

                -- takes file name from base_url.
                -- may be modified by validation process.


Another example
---------------

The post resulting from the following sr_watch command, noticing creation of the file 'foo'::

 sr_watch -s sftp://stanley@mysftpserver.com//data/shared/products/foo -pb amqp://broker.com

Here, *sr_watch* checks if the file /data/shared/products/foo is modified.
When it happens, *sr_watch*  reads the file /data/shared/products/foo and calculates its checksum.
It then builds a post message, logs into broker.com as user 'guest' (default credentials)
and sends the post to defaults vhost '/' and exchange 'sx_guest' (default exchange).

A subscriber can download the file /data/shared/products/foo  by logging in as user stanley
on mysftpserver.com using the sftp protocol to  broker.com assuming he has proper credentials.

The output of the command is as follows ::

  Topic: v02.post.20150813.data.shared.products.foo
  1st line of body: 20150813161959.854 sftp://stanley@mysftpserver.com/ /data/shared/products/foo
  Headers: parts=1,256,1,0,0 sum=d,25d231ec0ae3c569ba27ab7a74dd72ce source=guest

Posts are published on AMQP topic exchanges, meaning every message has a topic header.
The body consists of a time *20150813161959.854*, followed by the two parts of the retrieval URL.
The headers follow with first the *parts*, a size in bytes *256*,
the number of block of that size *1*, the remaining bytes *0*, the
current block *0*, a flag *d* meaning the md5 checksum is
performed on the data, and the checksum *25d231ec0ae3c569ba27ab7a74dd72ce*.


MetPX-Sarracenia
----------------

The MetPX project ( https://github.com/MetPX ) has a sub-project called Sarracenia which is intended
as a testbed and reference implementation for this protocol.  This implementation is licensed
using the General Public License (Gnu GPL v2), and is thus free to use, and can be used to
confirm interoperability with any other implementations that may arise.   While Sarracenia
itself is expected to be very usable in a variety of contexts, there is no intent for it
to implement any features not described by this documentation.  

This Manual page is intended to completely specify the format of messages and their 
intended meaning so that other producers and consumers of messages can be implemented.


AMQP Feature Selection
----------------------

AMQP is a universal message passing protocol with many different 
options to support many different messaging patterns.  MetPX-sarracenia specifies and uses a 
small subset of AMQP patterns.  An important element of sarracenia development was to 
select from the many possibilities a small subset of methods are general and easily understood, 
in order to maximize potential for interoperability.

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
procedure, use of AMQP, without more information, is incomplete.   The intent of the conventions
layered on top of AMQP is to be a minimum amount to achieve meaningful data exchange.

AMQP: not 1.0, but 0.8 or 0.9
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

AMQP 1.0 standardizes the on-the-wire protocol, but leaves out many features of broker interaction.   
As the use of brokers is key to sarracenia´s use of, was a fundamental element of earlier standards, 
and as the 1.0 standard is relatively controversial, this protocol assumes a pre 1.0 standard broker, 
as is provided by many free brokers, such as rabbitmq, often referred to as 0.8, but 0.9 and post
0.9 brokers are also likely to inter-operate well.

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

No data 
~~~~~~~

The AMQP messages contain announcements, no actual file data. AMQP is optimized for and assumes 
small messages. Keeping the messages small allows for maximum message throughtput and permits
clients to use priority mechanisms based on transfer of data, rather than the announcements.
Accomodating large messages would create many practical complications, and inevitably require 
the definition of a maximum file size to be included in the message itself, resulting in
complexity to cover multiple cases. 

Sr_post is intended for use with arbitrarily large files, via segmentation and multi-streaming.
Blocks of large files are announced independently and blocks can follow different paths
between initial pump and final delivery. The protocol is unidirectional, in that there 
is no dialogue between publisher and subscriber. Each post is a stand-alone item that 
is one message in a stream, which on receipt may be spread over a number of nodes. 

Other Parameters
~~~~~~~~~~~~~~~~

There are other parameters, such as persistence (have queues survive broker restarts, default to true),
expiry (how long a queue should exist when no-one is consuming from it.  Default: a few 
minutes for development, but can set much longer for production) message_ttl (the life-span of queued
messages. messages that are too old, will not be delivered. default is forever.)
Pre-fetch is an AMQP tunable to determine how many messages a client will retrieve from
a broker at once, optimizing streaming.




Applicable Standards
--------------------

* Sarracenia relies on `AMQP pre 1.0 <https://www.rabbitmq.com/resources/specs/amqp0-9-1.pdf>`_  as the
  1.0 standard eliminated concepts: broker, exchange, queue, and binding.  The 1.0 feature set is below the 
  minimum needed to support Sarracenia's pub-sub architecture.

* All messages are expected to use the UNICODE character set (ISO 10646), 
  represented by UTF-8 encoding (IETF RFC 3629).

* URL encoding, as per IETF RFC 1738, is used to escape unsafe characters where appropriate.


FURTHER READING
---------------

https://github.com/MetPX - home page of metpx-sarracenia

http://rabbitmq.net - home page of the AMQP broker used to develop Sarracenia.


SEE ALSO
--------

`sr_postv3(7) <sr_postv3.7.rst>`_ - experimental next version of sr_post messages.

`sr_report(7) <sr_report.7.rst>`_ - the format of report messages.

`sr_pulse(7) <sr_pulse.7.rst>`_ - the format of pulse messages.

`sr_report(1) <sr_report.1.rst>`_ - process report messages.

`sr_post(1) <sr_post.1.rst>`_ - post announcemensts of specific files.

`sr_sarra(8) <sr_sarra.8.rst>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - the download client.

`sr_watch(1) <sr_watch.1.rst>`_ - the directory watching daemon.

tree `dd_subscribe(1) <dd_subscribe.1.rst>`_ - the http-only download client.
