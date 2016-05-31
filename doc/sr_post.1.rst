
=========
 SR_Post
=========

------------------------------------------------
Publish the Availability of a File to Subcribers
------------------------------------------------

:Manual section: 1 
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite


SYNOPSIS
========

**sr_post** [ *OPTIONS* ][ *-b|--broker broker* ][ *-u|--url url* ] [ *-p|--path ] path1 path2...pathN

DESCRIPTION
===========

**sr_post** posts the availability of a file by creating an announcement.
In contrast to most other sarracenia components that act as daemons,
sr_post is a one shot invocation which posts and exits.
Subscribers use `sr_subscribe <sr_subscribe.1.html>`_  
to consume announcements and download the file.  To make files available 
to subscribers, **sr_post** sends the announcements to an AMQP server, 
also called a broker.  Format of argument to the *broker* option:: 

       [amqp|amqps]://[user[:password]@]host[:port][/vhost]

The [*-u|--url url*] option specifies the location 
subscribers will download the file from.  There is usually one post per file.
Format of argument to the *url* option::

       [ftp|http|sftp]://[user[:password]@]host[:port]/
       or
       [ftp|http|sftp]://[user[:password]@]host[:port]/
       or
       file:

The [*-p|--path path1 path2 .. pathN*] option specifies the path of the files
to be announced. There is usually one post per file.
Format of argument to the *path* option::

       /absolute_path_to_the/filename
       or
       relative_path_to_the/filename

An example invocation of *sr_post*::

 sr_post -b amqp://broker.com -u sftp://stanley@mysftpserver.com/ -p /data/shared/products/foo 

By default, sr_post reads the file /data/shared/products/foo and calculates its checksum.
It then builds a post message, logs into broker.com as user 'guest' (default credentials)
and sends the post  to defaults vhost '/' and default exchange. The default exchange 
is the prefix *xs_* followed by the broker username, hence defaulting to 'xs_guest'.
A subscriber can download the file /data/shared/products/foo by authenticating as user stanley
on mysftpserver.com using the sftp protocol to broker.com assuming he has proper credentials.
The output of the command is as follows ::

 [INFO] Published xs_guest v02.post.data.shared.products.foo '20150813161959.854 sftp://stanley@mysftpserver.com/ /data/shared/products/foo' sum=d,82edc8eb735fd99598a1fe04541f558d parts=1,4574,1,0,0

In MetPX-Sarracenia, each post is published under a certain topic.
The log line starts with '[INFO]', followed by the **topic** of the
post. Topics in *AMQP* are fields separated by dot. The complete topic starts with
a topic_prefix (see option)  version *V02*, an action *post*,
followed by a subtopic (see option) here the default, the file path separated with dots
*data.shared.products.foo*

The second field in the log line is the message notice.  It consists of a time 
stamp *20150813161959.854*, and the source url of the file in the last 2 fields.

The rest of the information is stored in AMQP message headers, consisting of key=value pairs.
The *sum=d,82edc8eb735fd99598a1fe04541f558d* header gives file fingerprint (or checksum
) information.  Here, *d* means md5 checksum performed on the data, and *82edc8eb735fd99598a1fe04541f558d*
is the checksum value. The *parts=1,4574,1,0,0* state that the file is available in 1 part of 4574 bytes
(the filesize.)  The remaining *1,0,0* is not used for transfers of files with only one part.

Another example::

 sr_post -b amqp://broker.com -dr /data/web/public_data -u http://dd.weather.gc.ca/ -p bulletins/alphanumeric/SACN32_CWAO_123456

By default, sr_post reads the file /data/web/public_data/bulletins/alphanumeric/SACN32_CWAO_123456
(concatenating the document_root and relative path of the source url to obtain the local file path)
and calculates its checksum. It then builds a post message, logs into broker.com as user 'guest'
(default credentials) and sends the post to defaults vhost '/' and exchange 'xs_guest'

A subscriber can download the file http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 using http
without authentication on dd.weather.gc.ca.


ARGUMENTS AND OPTIONS
=====================

Please refer to the `sr_config(7) <sr_config.7.html>`_ manual page for a detailed description of 
common settings, and methods of specifying them.

**[-b|--broker <broker>]**

  the broker to which the post is sent.

**[--blocksize <value>]**

The value of the *blocksize*  is an integer that may be followed by  letter designator *[B|K|M|G|T]* meaning:
for Bytes, Kilobytes, Megabytes, Gigabytes, Terabytes respectively.  All theses references are powers of 2.
Files bigger than this value will get announced with *blocksize* sized parts.

By default, **sr_post** computes a reasonable blocksize that depends on the file'size.
The user can set a fixed *blocksize* if it is better for its products or if he wants to
take advantage of the **caching** mechanism.

**[-c|--config <configfile>]**

  A list of settings in a configuration file 

**[--caching]**

  When one is planning reposting directories, this option caches
  what was posted and will post only files (parts) that were new
  (or changed) when invoked again.  For caching purpose, 
  it needs to have a fixed blocksize. So **blocksize** needs to
  be declared.

**[-dr|--document_root <path>]**

  The *document_root* option supplies the directory path that,
  when combined (or found) in the given *path*, 
  gives the local absolute path to the data file to be posted.

**[-ex|--exchange <exchange>]**

  Sr_post publishes to an exchange named *xs_*"broker_username" by default.
  Use the *exchange* option to override that default.
  Note that the administrator must have created the exchange before one can post to it.

**[-f|--flow <string>]**

  An arbitrary label that allows the user to identify a specific flow.
  The flow string is sets in the amqp message header.  By default, there is no flow.

**[-h|-help|--help**

  Display program options.


**[-p|--path path1 path2 ... pathN]**

**sr_post** evaluates the filesystem paths from the **path** option 
and possibly the **document_root** if the option is used.

If a path defines a file this file is announced.

If a path defines a directory then all files in that directory are
announced... 

If this path defines a directory and the option **recursive** is true
then all files in that directory are posted and should **sr_post** finds
one (or more) directory(ies), it scans it(them) are posts announcements
until all the tree is scanned.

The AMQP announcements are made of the three fields, the announcement time,
the **url** option value and the resolved paths to which were withdrawn
the *document_root* present and needed.

**[-rec|--recursive <boolean>]**

The recursive default is False. When the **path** given (possibly combined with **document_root**)
describes one or several directories,  if **recursive** is True, the directory tree is scanned down and all subtree
files are posted.

**[--reset]**

  When one has used **--caching** this option will get rid of the
  cached informations.


**[-rn|--rename <path>]**

  With the *rename*  option, the user can suggest a destination path to its files. If the given
  path ends with '/' it suggests a directory path...  If it doesn't, the option specifies a file renaming.

**[-sub|--subtopic <key>]**

The subtopic default can be overwritten with the *subtopic* option.

**[-to|--to <destination>,<destination>,... ]** -- MANDATORY

  A comma-separated list of destination clusters to which the posted data should be sent.
  Ask pump administrators for a list of valid destinations.

  default: None.

.. note:: 
  FIXME: a good list of destination should be discoverable.


**[-tp|--topic_prefix <key>]**

  *Not usually used*
  By default, the topic is made of the default topic_prefix : version *V02*, an action *post*,
  followed by the default subtopic: the file path separated with dots (dot being the topic separator for amqp).
  You can overwrite the topic_prefix by setting this option.


**[-u|--url <url>]**

The **url** option sets the protocol, credentials, host and port under
which the product can be fetched.

The AMQP announcememet is made of the tree fields, the announcement time,
this **url** value and the given **path** to which was withdrawn the *document_root*
if necessary.

If the concatenation of the two last fields of the announcement that defines
what the subscribers will use to download the product. 


ADVANCED OPTIONS
================

**[-p|--parts <value>]**

The user can suggest how to download a file.  By default it suggests to download the entire file.
In this case, the amqp message header will have an entry parts with value '1,filesize_in_bytes'.
To suggest to download a file in blocksize of 10Mb, the user can specify *-p i,10M*. *i* stands for
"inplace" and means to put the part directly into the file.  *-p p,10M* suggests the same blocksize but to put the part
in a separate filepart. If the *blocksize* is bigger than the filesize, the program will fall back to the default.
There will be one post per suggested part.

The value of the *blocksize*  is an integer that may be followed by  letter designator *[B|K|M|G|T]* meaning:
for Bytes, Kilobytes, Megabytes, Gigabytes, Terabytes respectively.  All theses references are powers of 2.

When suggesting parts, the value put in the amqp message header varies.
For example if headers[parts] as value 'p,256,12,11,4' it stands for :
*p* suggesting part, a blocksize in bytes *256*,
the number of block of that size *12*, the remaining bytes *11*, 
and the current block *4*,

**[-sum|--sum <string>]**

All file posts include a checksum.  It is placed in the amqp message header will have as an
entry *sum* with default value 'd,md5_checksum_on_data'.
The *sum* option tell the program how to calculate the checksum.
It is a comma separated string.  Valid checksum flags are ::

    [0|n|d|c=<scriptname>]
    where 0 : no checksum... value in post is 0
          n : do checksum on filename
          d : do md5sum on file content

Then using a checksum script, it must be registered with the pumping network, so that consumers
of the postings have access to the algorithm.


DEVELOPER SPECIFIC OPTIONS
==========================

**[-debug|--debug]**

Active if *-debug|--debug* appears in the command line... or
*debug* is set to True in the configuration file used.

**[-r|--randomize]**

Active if *-r|--randomize* appears in the command line... or
*randomize* is set to True in the configuration file used.
If there are several posts because the file is posted
by block because the *blocksize* option was set, the block 
posts are randomized meaning that the will not be posted
ordered by block number.

**[-rr|--reconnect]**

Active if *-rc|--reconnect* appears in the command line... or
*reconnect* is set to True in the configuration file used.
*If there are several posts because the file is posted
by block because the *blocksize* option was set, there is a
reconnection to the broker everytime a post is to be sent.

ADMINISTRATOR SPECIFIC
======================

**[-queue_name]**

If a client wants a product to be reannounced,
the broker administrator can use *sr_post*  and publish
directly into the client's queue. The client could provide
his queue_name... or the administrator would find it on
the broker... From the log where the product was processed on
the broker, the administrator would find all the messages
properties. The administrator should pay attention on slight
differences between the logs properties and the *sr_post* arguments.
The logs would mention *from_cluster*  *to_clusters* and associated
values...  **sr_post** arguments would be *-cluster* and  *-to*
respectively. The administrator would execute **sr_post** providing
all the options setting everything found in the log plus the 
targetted queue_name  *-queue_name q_....*


SEE ALSO
========

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(7) <sr_post.7.html>`_ - the format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the http-only download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.



