==========
 SR_Watch 
==========

-----------------------------------------------------------
watch a directory and post messages when files in it change
-----------------------------------------------------------

:Manual section: 1 
:Date: @Date@
:Version: @Version@
:Manual group: MetPX-Sarracenia

SYNOPSIS
========

**sr_watch** [ *-u|--url url* ] [ *-b|--broker broker_url* ]...[ *-p|--path* ] path] [reload|restart|start|status|stop]

DESCRIPTION
===========

Watches a directory and publishes posts when files in the directory change
(are added, modified, or deleted.) Its arguments are very similar to  `sr_post <sr_post.1.html>`_.
In the MetPX-Sarracenia suite, the main goal is to post the availability and readiness
of one's files. Subscribers use  *sr_subscribe*  to consume the post and download the files.

Posts are sent to an AMQP server, also called a broker, specified with the option [ *-b|--broker broker_url* ]. 

CREDENTIAL OPTIONS
------------------

The broker option sets all the credential information to connect to the  **RabbitMQ** server

- **broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqp://anonymous:anonymous@dd.weather.gc.ca/ ) 

All sr\_ tools store all sensitive authentication info in the credentials.conf file.
Passwords for SFTP, AMQP, and HTTP accounts are stored in URL´s there, as well as other pointers
to thins such as private keys, or FTP modes.

For more details, see: `sr_config(7) credentials <sr_config.7.html/#credentials>`_

Mandatory Settings
------------------

The [*-u|--url url*] option specifies the protocol, credentials, host and port to which subscribers 
will connect to get the file. 

format of argument to the *url* option::

       [ftp|http|sftp]://[user[:password]@]host[:port]/
       or
       [ftp|http|sftp]://[user[:password]@]host[:port]/
       or
       file:


The [*-p|--path path*] option tells *sr_watch* what to look for.
If the *path* specifies a directory, *sr_watches* create a posts for any time
a file in that directory that is created, modified or deleted. 
If the *path* specifies a file,  *sr_watch*  watches that only that file.
In the announcement, it is specified with the *path* of the product.
There is usually one post per file.


An example of an excution of  *sr_watch*  checking a file::

 sr_watch -s sftp://stanley@mysftpserver.com/ -p /data/shared/products/foo -b amqp://broker.com start

Here,  *sr_watch*  checks events on the file /data/shared/products/foo.
Default events settings reports if the file the file is modified or deleted.
When the file gets modified,  *sr_watch*  reads the file /data/shared/products/foo
and calculates its checksum.  It then builds a post message, logs into broker.com as user 'guest' (default credentials)
and sends the post to defaults vhost '/' and exchange 'xs_stanley' (default exchange)

A subscriber can download the file /data/shared/products/foo  by logging as user stanley
on mysftpserver.com using the sftp protocol to  broker.com assuming he has proper credentials.

The output of the command is as follows ::

 [INFO] v02.post.data.shared.products.foo '20150813161959.854 sftp://stanley@mysftpserver.com/ /data/shared/products/foo'
       source=guest parts=1,256,1,0,0 sum=d,fc473c7a2801babbd3818260f50859de 

In MetPX-Sarracenia, each post is published under a certain topic.
After the '[INFO]' the next information gives the \fBtopic*  of the
post. Topics in  *AMQP*  are fields separated by dot. In MetPX-Sarracenia 
it is made of a  *topic_prefix*  by default : version  *V02* , an action  *post* ,
followed by the  *subtopic*  by default : the file path separated with dots, here, *data.shared.products.foo* 

After the topic hierarchy comes the body of the notification.  It consists of a time  *20150813161959.854* , 
and the source url of the file in the last 2 fields.

The remaining line gives informations that are placed in the amqp message header.
Here it consists of  *source=guest* , which is the amqp user,  *parts=1,256,0,0,1* ,
which suggest to download the file in 1 part of 256 bytes (the actual filesize), trailing 1,0,0
gives the number of block, the remaining in bytes and the current 
block.  *sum=d,fc473c7a2801babbd3818260f50859de*  mentions checksum information,
here,  *d*  means md5 checksum performed on the data, and  *fc473c7a2801babbd3818260f50859de* 
is the checksum value.  When the event on a file is a deletion, sum=R,0  R stands for remove.

Another example watching a file::

 sr_watch -dr /data/web/public_data -s http://dd.weather.gc.ca/ -p bulletins/alphanumeric/SACN32_CWAO_123456 -b amqp://broker.com start

By default, sr_watch checks the file /data/web/public_data/bulletins/alphanumeric/SACN32_CWAO_123456
(concatenating the document_root and relative path of the source url to obtain the local file path).
If the file changes, it calculates its checksum. It then builds a post message, logs into broker.com as user 'guest'
(default credentials) and sends the post to defaults vhost '/' and exchange 'sx_guest' (default exchange)

A subscriber can download the file http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 using http
without authentication on dd.weather.gc.ca.

An example checking a directory::

 sr_watch -dr /data/web/public_data -s http://dd.weather.gc.ca/ -p bulletins/alphanumeric -b amqp://broker.com start

Here, sr_watch checks for file creation(modification) in /data/web/public_data/bulletins/alphanumeric
(concatenating the document_root and relative path of the source url to obtain the directory path).
If the file SACN32_CWAO_123456 is being created in that directory, sr_watch calculates its checksum.
It then builds a post message, logs into broker.com as user 'guest' 
(default credentials) and sends the post to exchange 'amq.topic' (default exchange)

A subscriber can download the created/modified file http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 using http
without authentication on dd.weather.gc.ca.

ARGUMENTS AND OPTIONS
=====================

Please refer to the `sr_config(7) <sr_config.7.html>`_ manual page for a detailed description of
common settings, and methods of specifying them.

**[-b|--broker <broker>]**
       *broker*  is the broker to connect to to send the post.

**[-c|--config <configfile>]**
       A file filled with options.

**[-dr|--document_root <path>]**

The  *document_root*  option supplies the directory path that,
when combined with the relative one from  *source url* , 
gives the local absolute path to the data file to be posted.
.fi

**[-e|--events <event|event|...>]**

A list of event types to monitor separated by a 'pipe symbol'.
Available events:  create, delete, follow, link, modify, poll
Default: default is all of them, except poll

The *create*, *modify*, and *delete* events reflect what is expected: a file being created, modified, or deleted.
The *follow* and *link* attributes are less obvious, and affect how symbolic links are processed.
If *link* is set, symbolic links will be posted as links so that consumers can choose 
how to process them. if it is not set, then no link events will ever be posted.

The *follow* keyword causes symbolic links to be traversed.  if *follow* is set
and the destination of a symbolic link is a file, then that destination file should be posted as well as the link.
If the destination of the symbolic link is a directory, then the directory should be added to those being
monitored by sr_watch.   If *follow* is false, then no action related to the destination of the symbolic link is taken.

By Default, sr_watch selects a (OS dependent) optimal method to watch a directory.   For large trees,
the optimal method can be manyfold (10x or even 100x) faster to recognize when a file has been modified.
In some cases, however, platform optimal methods do not work (such as with some network shares, or distributed file systems), so one must use a slower but more reliable and portable polling method.  The *poll* keyword causes sr_watch to select the polling method in spite of the availability of a normally better one.

.. note::
   move or rename events are treated as modify events

**[-ex|--exchange <exchange>]**

By default, the exchange used is amq.topic. This exchange is provided on broker
for general usage. It can be overwritten with this  *exchange*  option

**[-f|--flow <string>]**

The *flow* is an arbitrary label that allows the user to identify a specific flow.
The flow string is sets in the amqp message header.  By default there is no flow.

**[-h|-help|--help]**

Display program options.

**[-l <logpath>]**

Set a file where all the logs will be written.
Logfile will rotate at 'midnight' and kept for an history of 5 files.


**[-rn|--rename <path>]**

With the  *rename*   option, the user can
suggest a destination path for its files. If the given
path ends with '/' it suggests a directory path... 
If it doesn't, the option specifies a file renaming.


**[-to|--to <destination>,<destination>,... ]** -- MANDATORY

  A comma-separated list of destination clusters to which the posted data should be sent.
  Ask pump administrators for a list of valid destinations.

  default: None.

.. note:: 
  FIXME: a good list of destination should be discoverable.


**[-tp|--topic_prefix <key>]**

By default, the topic is made of the default topic_prefix : version  *V02* , an action  *post* ,
followed by the default subtopic: the file path separated with dots (dot being the topic separator for amqp).
You can overwrite the topic_prefix by setting this option.

**[-rec|--recursive <boolean>]**

The recursive default is False. When the **url** given (possibly combined with **document_root**)
describes a directory,  if **recursive** is True, the directory tree is scanned down and all subtree
files are watched.


**[-sub|--subtopic <key>]**

The subtopic default can be overwritten with the  *subtopic*  option.


**[-p|--path path]**

**sr_post** evaluates the filesystem path from the **path** option 
and possibly the **document_root** if the option is used.

If a path defines a file this file is watched.

If a path defines a directory then all files in that directory are
watched... 

If this path defines a directory and the option **recursice** is true
then all files in that directory are watched and should **sr_watch** finds
one (or more) directory(ies), it watches it(them) recursively
until all the tree is scanned.

The AMQP announcements are made of the tree fields, the announcement time,
the **url** option value and the resolved paths to which were withdrawn
the *document_root* present and needed.

**[-u|--url <url>]**

The **url** option sets the protocol, credentials, host and port under
which the product can be fetched.

The AMQP announcememet is made of the tree fields, the announcement time,
this **url** value and the given **path** to which was withdrawn the *document_root*
if necessary.

If the concatenation of the two last fields of the announcement that defines
what the subscribers will use to download the product. 


FIXME :  Daluma :  **cache** **blocksize** **reset**   how will Daluma
         deals/uses these to have an sr_watch that uses caching... etc.


**[--parts <value>]**

the value should be one of::

   0 - autocompute an appropriate partitioning strategy (default)
   1 - always send files in a single part.
   p,<sz> - used a fixed partition size (example size: 1M )

Files can be announced as multiple parts.  Each part has a separate checksum.
The parts and their checksums are stored in the cache. Partitions can traverse
the network separately, and in paralllel.  When files change, transfers are
optimized by only sending parts which have changed.

The autocomputation algorithm determines a blocksize that encourages a reasonable number of parts
for files of various sizes.  As the file size varies, the automatic computation will give different
results.  this will result in resending information which has not changed as partitions of a different
size will have different sums, and therefore be tagged as different.  In cases where large files are
being appended to, it make sense to specify a fixed partition size so that the blocks in the cache
will be the same blocks as those generated when the file is larger, and so avoid re-transmission.
So use of 'p,10M' would make sense in that case.

In cases where a custom downloader is used which does not understand partitioning, it is necessary
to avoid having the file split into parts, so one would specify '1' to force all files to be send
as a single part.

The value of the *blocksize*  is an integer that may be followed by  letter designator *[B|K|M|G|T]* meaning:
for Bytes, Kilobytes, Megabytes, Gigabytes, Terabytes respectively.  All theses references are powers of 2.


**[-sum|--sum <string>]**

All file posts include a checksum.  It is placed in the amqp message header will have as an
entry *sum* with default value 'd,md5_checksum_on_data'.
The *sum* option tell the program how to calculate the checksum.
It is a comma separated string.  Valid checksum flags are ::

    [0|n|d|c=<scriptname>]
    where 0 : no checksum... value in post is a random integer
          n : do checksum on filename
          d : do md5sum on file content (default)

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

**[-real|--realpath <boolean>]**  EXPERIMENTAL

The realpath option resolves paths given to their canonical ones, eliminating any indirection via symlinks.
The behaviour improves the ability of sr_watch to monitor trees, but the trees may have completely different paths than the arguments given. This option also enforces traversing of symbolic links.   This is implemented to preserve the behaviour of an earlier iteration of sr_watch, but it is not clear if it required or useful.  Feedback welcome.

**[-rr|--reconnect]**

Active if *-rc|--reconnect* appears in the command line... or
*reconnect* is set to True in the configuration file used.
*If there are several posts because the file is posted
by block because the *blocksize* option was set, there is a
reconnection to the broker everytime a post is to be sent.


CAVEATS
=======

In order to avoid alerting for partially written (usually temporary) files, *sr_watch* does not post
events for changes to files with certain names:

 - files whose names begin with a dot **.**
 - files whose names end in .tmp

.. NOTE::
   FIXME: is this right?  need better does it ignore part files? should it?

Another file operation which is not currently optimally managed is file renaming. When a file is renamed
within a directory tree, sarracenia will simply announce it under the new name, and does not communicate
that already transferred data has simply changed name.  Subscribers who have transferred the data under the 
old name will transfer it again under the new name, with no relation being made with the old file.

SEE ALSO
========

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - the format of announcement messages.

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_report(1) <sr_report.1.html>`_ - process report messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the http-only download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.


