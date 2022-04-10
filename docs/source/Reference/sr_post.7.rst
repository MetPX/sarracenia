
=========
 SR_post 
=========

-------------------------------------------
Sarracenia v03 Post Message Format/Protocol
-------------------------------------------

:Manual section: 7
:Date: |today|
:Version: |release|
:Manual group: MetPX-Sarracenia


STATUS: Stable/Default
----------------------

Sarracenia version 2 messages are the previous standard, used for terabytes
and millions of files per day of transfers. Version 3 is a proposal for a next
iteration of Sarracenia messages.

Most fields and their meaning is the same in version 3 as it was in version 2. 
Some fields are changing as the protocol is exposed to wider review than previously.

The change in payload protocol is targetted at simplifying future implementations
and enabling use by messaging protocols other than pre-1.0 AMQP.
See `v03 Changes <../Explanations/History/messages_v03.html>`_ for more details.

To generate messages in v03 format, use following setting::

  post_topicPrefix v03

To select messages to consume in that format::

  topicPrefix v03



SYNOPSIS
--------


Version 03 format of file change announcements for sr_post.  

An sr_post message consists of a topic, and the *BODY* 

**AMQP Topic:** *<version>.{<dir>.}*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

           <version> = "v03" the version of the protocol or format.
           "post" = the type of message within the protocol.
           <dir> = a sub-directory leading to the file (perhaps many directories deep)

**BODY:** *{ <headers> }* (JSON encoding.)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The headers are an array of name:value pairs::

  MANDATORY:

          "pubTime"       - YYYYMMDDTHHMMSS.ss - UTC date/timestamp.
          "baseUrl"       - root of the url to download.
          "relPath"       - relative path can be catenated to <base_url>
          "integrity"     - WMO version of v02 sum field, under development.
          {
             "method" : "md5" | "sha512" | "md5name" | "link" | "remove" | "cod" | "random" ,
             "value"  : "base64 encoded checksum value"
          }

  OPTIONAL:

          for GeoJSON compatibility:
          "type": "Feature"
          "geometry": RFC 7946 (geoJSON) compatible geographic specification.


          "size"          - the number of bytes being advertised.
          "blocks"        - if the file being advertised is partitioned, then:
          {
              "method"    : "inplace" | "partitioned" , - is the file already in parts?
              "size"      : "9999", - size of the blocks.
              "count"     : "9999", - number of blocks in the file.
              "remainder" : "9999", - the size of the last block.
              "number"    : "9999", - which block is this.
          }
          "rename"        - name to write file locally.
          "retPath"       - relative retrieval path can be catenated to <base_url> to override relPath
                            used for API cases.
          "topic"         - copy of topic from AMQP header (usually omitted)
          "source"        - the originating entity of the message. 
          "from_cluster"  - the originating cluster of a message.
          "to_clusters"   - a destination specification.
          "link"          - value of a symbolic link. (if sum starts with L)
          "atime"         - last access time of a file (optional)
          "mtime"         - last modification time of a file (optional)
          "mode"          - permission bits (optional)

          "content"       - for smaller files, the content may be embedded.
          {
              "encoding" : "utf-8" | "base64"  , 
              "value"    " "encoded file content"
          }

          For "v03.report" topic messages the following addtional
          headers will be present:
  
          "report" { "code": 999  - HTTP style response code. 
                     "message" :  - status report message documented in `Report Messages`_
                   }

          "type": "Feature"   - used for geoJSON compatibility.
          "geometry" : ... as per RFC7946  GoJSON compatibility.

          additional user defined name:value pairs are permitted.

NOTE:
     The **parts** header has not yet been reviewed by others. We started on the discussion of *size*,
     but there was no conclusion.


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
data.  If consumers permit it, report messages also flow through the control path, 
but in the opposite direction, allowing sources to know the entire disposition of their 
files through a network.  

The minimal layer over raw AMQP provides more complete file transfer functionality:

Source Filtering (use of TOPIC_ exchanges)
   The messages make use of *topic exchanges* from AMQP, where topics are hierarchies
   meant to represent subjects of interest to a consumer. A consumer may upload the 
   selection criteria to the broker so that only a small subset of postings
   are forwarded to the client.  When there are many users interested in only 
   small subsets of data, the savings in traffic are large.

Fingerprint Winnowing (use of the integrity_ header)
   Each product has an integrity fingerprint and size intended to identify it uniquely, 
   referred to as a *fingerprint*. If two files have the same fingerprint, they 
   are considered equivalent. In cases where multiple sources of equivalent data are 
   available but downstream consumers would prefer to receive single announcements
   of files, intermediate processes may elect to publish notifications of the first 
   product with a given fingerprint, and ignore subsequent ones. 
   Propagating only the first occurrence of a datum received downstream, based on
   its fingerprint, is termed: *Fingerprint Winnowing*.

   *Fingerprint Winnowing* is the basis for a robust strategy for high availability: setting up
   multiple sources for the same data, consumers accept announcements from all of them, but only
   forwarding the first one received downstream. In normal operation, one source may be faster 
   than the others, and so the other sources' files are usually 'winnowed'. When one source
   disappears, the other sources' data is automatically selected, as the fingerprints
   are now *fresh* and used, until a faster source becomes available.

   The advantage of this method for high availability is that no A/B decision is required.
   The time to *switchover* is zero. Other strategies are subject to considerable delays
   in making the decision to switchover, and pathologies one could summarize as flapping,
   and/or deadlocks.  

   *Fingerprint Winnowing* also permits *mesh-like*, or *any to any* networks, where one simply 
   interconnects a node with others, and messages propagate. Their specific path through the 
   network is not defined, but each participant will download each new datum from the first
   node that makes it available to them. Keeping the messages small and separate from data 
   is optimal for this usage.
 
Partitioning (use of the parts_ Header)
   In any store and forward data pumping network that transports entire files limits the maximum
   file size to the minimum available on any intervening node. To avoid defining a maximum 
   file size, a segmentation standard is specified, allowing intervening nodes to hold
   only segments of the file, and forward them as they are received, rather than being
   forced to hold the entire file.

   Partitioning also permits multiple streams to transfer portions of the file in parallel. 
   Multiple streams can provide an effective optimization over long links.

   

TOPIC
-----

In topic based AMQP exchanges, every message has a topic header. AMQP defines the '.' character 
as a hierarchical separator (like '\' in a windows path name, or '/' on linux) there is also a 
pair of wildcards defined by the standard:  '*' matches a single topic, '#' matches the rest of 
the topic string. To allow for changes in the message body in the future, topic trees begin with 
the version number of the protocol.   

AMQP allows server side topic filtering using wildcards. Subscribers specify topics of 
interest (which correspond to directories on the server), allowing them to pare down the 
number of notifications sent from server to client.  

The root of the topic tree is the version specifier: "v03".  Next comes the message type specifier.  
These two fields define the protocol that is in use for the rest of the message.
The message type for post messages is "post".  After the fixed topic prefix, 
the remaining sub-topics are the path elements of the file on the web server.  
For example, if a file is placed on http://www.example.com/a/b/c/d/foo.txt, 
then the complete topic of the message will be:  *v03.a.b.c.d*
AMQP fields are limited to 255 characters, and the characters in the field are utf8 
encoded, so actual length limit may be less than that. 

note::

  Sarracenia relies on brokers to interpret the topic header. Brokers interpret protocol
  specific headers *AMQP), and will not efficiently decode the payload to extract headers. 
  Therefore the topic header is stored in an AMQP header, rather than the payload to permit
  server-side filtering. To avoid sending the same information twice, this header is
  omitted from the JSON payload.

  Many client-side implementation will, once the message is loaded, set the *topic* header 
  in the in-memory structure, so it would be very unwise to to set the *topic* header
  in an application even though it isn't visible in the on-wire payload.


Mapping to MQTT
~~~~~~~~~~~~~~~

One goal of v03 format is to have a payload format that works with more than just AMQP.
Message Queing Telemetry Transport (MQTT v3.11) is an iso standard ( https://www.iso.org/standard/69466.html 
protocol that can easily support the same pub/sub messaging pattern, but a few details
differ, so a mapping is needed.

Firstly, the topic separate in MQTT is a forward slash (/), instead of the period (.) used in AMQP.

Second, with AMQP, one can establish separate topic hierarchies using *topic-based exchanges*. 
MQTT has no similar concept, there is simply one hierarchy, so when mapping, place the exchange
name at the root of the topic hierarchy to achieve the same effect::

  AMQP:   Exchange: <exchange name> 
             topic: v03.<directory>...

  MQTT:   topic: <exchange name>/v03/<directory>...



THE FIXED HEADERS
-----------------

The message is a single JSON encoded array, with a mandatory set of fields, while allowing
for use of arbitrary other fields.  Mandatory fields must be present in every message, and

 * "pubTime" : "*<date stamp>*" : the publication date the posting was emitted.  Format: YYYYMMDDTHHMMSS. *<decimalseconds>*

 Note: The datestamp is always in the UTC timezone.

 * "baseUrl" : "<*base_url*>" -- the base URL used to retrieve the data.

 * "relPath" : "<*relativepath*>" --  the variable part of the URL, usually appended to *baseUrl*.

The URL consumers will use to download the data. Example of a complete URL::

 sftp://afsiext@cmcdataserver/data/NRPDS/outputs/NRPDS_HiRes_000.gif


Additional fields:

**from_cluster=<cluster_name>**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   The from_cluster header defines the name of the source cluster where the 
   data was introduced into the network. It is used to return the logs back 
   to the cluster whenever its products are used.

**link=<value of symbolic link>**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   When file to transfer is a symbolic link, the 'link' header is created to 
   contain its value.

**size and blocks**
~~~~~~~~~~~~~~~~~~~
.. _parts:

::
     "size":<sz> , 
                  
     "blocks" : 
     { 
            "method": "inplace" or "partitioned", 
            "size": <bsz>,
            "count": <blktot>,
            "remainder": <brem>,
            "number": <bno>
     }

 A header indicating the method and parameters for partitioning applied for the file.
 Partitioning is used to send a single file as a collection of segments, rather than as
 a single entity.  Partitioning is used to accelerate transfers of large data sets by using
 multiple streams, and/or to reduce storage use for extremely large files.

 When transferring partitioned files, each partition is advertised and potentially transported
 independently across a data pumping network.

 *<method>*
 
 Indicates what partitioning method, if any, was used in transmission. 

 +-----------------+---------------------------------------------------------------------+
 |   Method        | Description                                                         |
 +-----------------+---------------------------------------------------------------------+
 | p - partitioned | File is partitioned, individual part files are created.             |
 +-----------------+---------------------------------------------------------------------+
 | i - inplace     | File is partitioned, but blocks are read from a single file,        |
 |                 | rather than parts.                                                  |
 +-----------------+---------------------------------------------------------------------+
 | 1 - <sizeonly>  | File is in a single part (no partitioning).                         |
 |                 | in v03, only *size* header will be present. *blocks* is omitted     |
 +-----------------+---------------------------------------------------------------------+

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
~~~~~~~~~~~~~~~~~~~~

 The relative path from the current directory in which to place the file.

**oldname=<path>** / **newname=<path>**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

**integrity**
~~~~~~~~~~~~~

The integrity field gives a checksum useful for identifying the contents
of a file::
 
 "integrity" : { "method" : <method>, "value": <value> } 
 
The integrity field is a signature computed to allow receivers to determine 
if they have already downloaded the product from elsewhere.

   *<method>* - string field indicating the checksum method used.

 +------------+---------------------------------------------------------------------+
 |  Method    | Description                                                         |
 +------------+---------------------------------------------------------------------+
 |  random    | No checksums (unconditional copy.) Skips reading file (faster)      |
 +------------+---------------------------------------------------------------------+
 |  arbitrary | arbitrary, application defined value which cannot be calculated     |
 +------------+---------------------------------------------------------------------+
 |  md5       | Checksum the entire data (MD-5 as per IETF RFC 1321)                |
 +------------+---------------------------------------------------------------------+
 |  link      | Linked: SHA512 sum of link value                                    |
 +------------+---------------------------------------------------------------------+
 |  md5name   | Checksum the file name (MD-5 as per IETF RFC 1321)                  |
 +------------+---------------------------------------------------------------------+
 |  remove    | Removed: SHA512 of file name.                                       |
 +------------+---------------------------------------------------------------------+
 |  sha512    | Checksum the entire data (SHA512 as per IETF RFC 6234)              |
 +------------+---------------------------------------------------------------------+
 |  cod       | Checksum on download, with algorithm as argument                    |
 |            | Example:  cod,sha512 means download, applying SHA512 checksum, and  |
 |            | advertise with that calculated checksum when propagating further.   |
 +------------+---------------------------------------------------------------------+
 | *<name>*   | Checksum with some other algorithm, named *<name>*                  |
 |            | *<name>* should be *registered* in the data pumping network.        |
 |            | Registered means that all downstream subscribers can obtain the     |
 |            | algorithm to validate the checksum.                                 |
 +------------+---------------------------------------------------------------------+

*<value>* The value is computed by applying the given method to the partition being transferred.
  for algorithms for which no value makes sense, a random integer is generated to support
  checksum based load balancing.



Report Messages
---------------

Some clients may return telemetry to the origin of downloaded data for troubleshooting
and statistical purposes. Such messages, have the *v03.report* topic, and have a *report*
header which is a JSON *object* with four fields:

 { "elapsedTime": <report_time>, "resultCode": <report_code>, "host": <report_host>, "user": <report_user>* }

 * *<report_code>*  result codes describe in the next session

 * *<report_time>*  time the report was generated.

 * *<report_host>*  hostname from which the retrieval was initiated.

 * *<report_user>*  broker username from which the retrieval was initiated.


Report messages should never include the *content* header (no file embedding in reports.)


Report_Code
~~~~~~~~~~~

The report code is a three digit status code, adopted from the HTTP protocol (w3.org/IETF RFC 2616)
encoded as text.  As per the RFC, any code returned should be interpreted as follows:

	* 2xx indicates successful completion,
	* 3xx indicates further action is required to complete the operation.
	* 4xx indicates a permanent error on the client prevented a successful operation.
	* 5xx indicates a problem on the server prevented successful operation.

.. NOTE::
   FIXME: need to validate whether our use of error codes co-incides with the general intent
   expressed above... does a 3xx mean we expect the client to do something? does 5xx mean
   that the failure was on the broker/server side?

The specific error codes returned, and their meanings are implementation-dependent.
For the sarracenia implementation, the following codes are defined:

+----------+--------------------------------------------------------------------------------------------+
|   Code   | Corresponding text and meaning for sarracenia implementation                               |
+==========+============================================================================================+
|   201    | Download successful. (variations: Downloaded, Inserted, Published, Copied, or Linked)      |
+----------+--------------------------------------------------------------------------------------------+
|   203    | Non-Authoritative Information: transformed during download.                                |
+----------+--------------------------------------------------------------------------------------------+
|   205    | Reset Content: truncated. File is shorter than originally expected (changed length         |
|          | during transfer) This only arises during multi-part transfers.                             |
+----------+--------------------------------------------------------------------------------------------+
|   205    | Reset Content: checksum recalculated on receipt.                                           |
+----------+--------------------------------------------------------------------------------------------+
|   304    | Not modified (Checksum validated, unchanged, so no download resulted.)                     |
+----------+--------------------------------------------------------------------------------------------+
|   307    | Insertion deferred (writing to temporary part file for the moment.)                        |
+----------+--------------------------------------------------------------------------------------------+
|   417    | Expectation Failed: invalid message (corrupt headers)                                      |
+----------+--------------------------------------------------------------------------------------------+
|   496    | failure: During send, other protocol failure.                                              |
+----------+--------------------------------------------------------------------------------------------+
|   497    | failure: During send, other protocol failure.                                              |
+----------+--------------------------------------------------------------------------------------------+
|   499    | Failure: Not Copied. SFTP/FTP/HTTP download problem                                        |
+----------+--------------------------------------------------------------------------------------------+
|   499    | Failure: Not Copied. SFTP/FTP/HTTP download problem                                        |
+----------+--------------------------------------------------------------------------------------------+
|   503    | Service unavailable. delete (File removal not currently supported.)                        |
+----------+--------------------------------------------------------------------------------------------+
|   503    | Unable to process: Service unavailable                                                     |
+----------+--------------------------------------------------------------------------------------------+
|   503    | Unsupported transport protocol specified in posting.                                       |
+----------+--------------------------------------------------------------------------------------------+
|   xxx    | Message and file validation status codes are script dependent                              |
+----------+--------------------------------------------------------------------------------------------+


Other Report Fields
~~~~~~~~~~~~~~~~~~~


*<report_message>* a string.





Optional Headers
----------------

for the file mirroring use case, additional headers will be present:

**atime,mtime,mode**
~~~~~~~~~~~~~~~~~~~~

  man 2 stat - the linux/unix standard file metadata:
  access time, modification time, and permission (mode bits)
  the times are in the same date format as the pubTime field.
  the permission string is four characters intended to be interpreted as
  traditional octal linux/unix permissions.


**Headers which are unknown to a given broker MUST be forwarded without modification.**

Sarracenia provides a mechanism for users to include arbitrary other headers in
messages, to amplify metadata for more detailed decision making about downloading data.
For example::

  "PRINTER" : "name_of_corporate_printer",

  "GeograpicBoundingBox" : 
   { 
           "top_left" : { "lat": 40.73, "lon": -74.1 } , 
           "bottom_right": { "lat": -40.01, "lon": -71.12 } 
   }

would permit the client to apply more elaborate and precise client side filtering,
and/or processing. Intervening implementation may know nothing about the header, 
but they should not be stripped, as some consumers may understand and process them.


EXAMPLE
-------

:: 

 AMQP TOPIC: v03.NRDPS.GIF
 MQTT TOPIC: exchange/v03/NRDPS/GIF/
 Body: { "pubTime": "201506011357.345", "baseUrl": "sftp://afsiext@cmcdataserver", "relPath": "/data/NRPDS/outputs/NRDPS_HiRes_000.gif",
    "rename": "NRDPS/GIF/", "parts":"p,457,1,0,0", "integrity" : { "method":"md5", "value":"<md5sum-base64>" }, "source": "ec_cmc" }

        - v03 - version of protocol
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

 sr_watch -pbu sftp://stanley@mysftpserver.com/ -path /data/shared/products/foo -pb amqp://broker.com

Here, *sr_watch* checks if the file /data/shared/products/foo is modified.
When it happens, *sr_watch*  reads the file /data/shared/products/foo and calculates its checksum.
It then builds a post message, logs into broker.com as user 'guest' (default credentials)
and sends the post to defaults vhost '/' and exchange 'sx_guest' (default exchange).

A subscriber can download the file /data/shared/products/foo  by logging in as user stanley
on mysftpserver.com using the sftp protocol to  broker.com assuming he has proper credentials.

The output of the command is as follows ::

  AMQP Topic: v03.20150813.data.shared.products
  MQTT Topic: <exchange>/v03/20150813/data/shared/products
  Body: { "pubTime":"20150813T161959.854", "baseUrl":"sftp://stanley@mysftpserver.com/", 
          "relPath": "/data/shared/products/foo", "parts":"1,256,1,0,0", 
          "sum": "d,25d231ec0ae3c569ba27ab7a74dd72ce", "source":"guest" } 

Posts are published on AMQP topic exchanges, meaning every message has a topic header.
The body consists of a time *20150813T161959.854*, followed by the two parts of the 
retrieval URL. The headers follow with first the *parts*, a size in bytes *256*,
the number of block of that size *1*, the remaining bytes *0*, the
current block *0*, a flag *d* meaning the md5 checksum is
performed on the data, and the checksum *25d231ec0ae3c569ba27ab7a74dd72ce*.


Optimization Possibilities
~~~~~~~~~~~~~~~~~~~~~~~~~~

optimization goal is for readabilty and ease of implementation, much more
than efficiency or performance. There are many optimizations to reduce
overheads of various sorts, all of which will increase implementation
complexity. examples: gzip the payload would save perhaps 50% size,
also grouping fixed headers together, ('body' header could contain
all fixed fields: "pubtime, baseurl, relpath, sum, parts", and another
field 'meta' could contain: atime, mtime, mode so there would be fewer
named fields and save perhaps 40 bytes of overhead per notice. But
all the changes increase complexity, make messages more involved to parse.



Standards
---------

 * Sarracenia relies on `AMQP pre 1.0 <https://www.rabbitmq.com/resources/specs/amqp0-9-1.pdf>`_  
   as the 1.0 standard eliminated concepts: broker, exchange, queue, and 
   binding.  The 1.0 feature set is below the minimum needed to support 
   Sarracenia's pub-sub architecture.

 * MQTT refers to `MQTT v5.0 <https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.pdf>`_ 
   and `MQTT v3.1.1 <http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html>`_,
   MQTT v5 has important extension: shared subscriptions (heavily used in Sarracenia.)
   so v5 is highly recommended. v3.1 support is only for legacy support reasons.

 * JSON is defined by `IETF RFC 7159 <https://www.rfc-editor.org/info/rfc7159>`_.
   JSON standard includes mandatory use of UNICODE character set (ISO 10646)
   JSON default character set is UTF-8, but allows multiple character 
   encodings (UTF-8, UTF-16, UTF-32), but also prohibits presence of 
   byte order markings (BOM.)

 * the same as Sarracenia v02, UTF-8 is mandatory. Sarracenia restricts JSON format 
   by requiring of UTF-8 encoding, (IETF RFC 3629) which does not need/use BOM.
   No other encoding is permitted.

 * URL encoding, as per IETF RFC 1738, is used to escape unsafe characters 
   where appropriate.


SEE ALSO
--------

`sr3(1) <sr3.1.html>`_ - Sarracenia main command line interface.

`sr3_post(1) <sr3_post.1.html>`_ - post file announcements (python implementation.)

`sr3_cpost(1) <sr3_cpost.1.html>`_ - post file announcemensts (C implementation.)

`sr3_cpump(1) <sr3_cpump.1.html>`_ - C implementation of the shovel component. (copy messages)

**Formats:**

`sr3_credentials(7) <sr3_credentials.7.html>`_ - Convert logfile lines to .save Format for reload/resend.

`sr3_options(7) <sr_options.7.html>`_ - the configuration options


**Home Page:**

`https://metpx.github.io/sarracenia <https://metpx.github.io/sarracenia>`_ - Sarracenia: a real-time pub/sub data sharing management toolkit


