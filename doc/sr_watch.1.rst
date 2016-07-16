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

**sr_watch** [ *-u|--url url* ] [ *-b|--broker broker_url* ]...[ *-p|--path ] path] [reload|restart|start|status|stop]

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

All sr_ tools store all sensitive authentication info is stored in the credentials file.
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

**[-e|--events <exchange>]**

FIXME  :  Daluma is making changes HERE.
By default, the events for sr_watch are IN_CLOSE_WRITE|IN_DELETE.
If you want to consider only one of these simply use the  *events*  option
and set it to IN_CLOSE_WRITE for creation/modification or  IN_DELETE for deletion.

.. NOTE:: 
    FIXME: events listing default is wrong... now have links and renames also by default.
    Do we want to just remove the **events** option and let sr_watch worry which events needed?

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


FIXME :  Daluma :  **caching** **blocksize** **reset**   how will Daluma
         deals/uses these to have an sr_watch that uses caching... etc.


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

SEE ALSO
========

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.html>`_ - the format of log messages.

`sr_post(7) <sr_post.7.html>`_ - the format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the http-only download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.



ZZZ

ADVANCED OPTIONS
================

**[-p|--parts <value>]**

Select how to announce changes to a file.
The default is to create a single announcment for
the entire file.  In this case, the amqp message header will have an
entry parts with value '1,filesize_in_bytes'.

For large files, when an update occurs, a large amount of the file 
may be unchanged, so announcing blocks gives the subscriber to option
to download only the parts of the file that have changed.
Also, by announcing parts of the file separately, they can be downloaded
in parallel.

To post announcements of a file with a blocksize of 10Mb,
the user can specify  *-p i,10M* .  *i*  stands for
"inplace" and means write the parts directly into the file.
* -p p,10M*  suggests the same blocksize but to put the part
in a separate filepart. If the  *blocksize*  is bigger than
the filesize, the program will fall back to the default.
There will be one post per suggested part.

The value of the  *blocksize*   is an integer that may be
followed by  [ *B|K|M|G|T* ] which stands for  *B* ytes
, *K* ilobytes,  *M* egabytes,  *G* igabytes,  *T* erabytes.
All theses references are powers of 2 (except for Bytes).

When suggesting parts, the value put in the amqp message header varies.
For example if headers[parts] as value 'p,256,12,11,4' it stands 
for : *p*  suggesting part, a blocksize in bytes  *256* ,
the number of block of that size  *12* , the remaining bytes  *11* ,
and the current block  *4* ,

.. NOTE::
   FIXME:  likely the sr_post/sr_watch default values for parts should change.
   There should be a threshold, so that above a certain file size, parts is used by default.
   I think picking a threshold like 50M is likely a good size. It should avoid the
   *Capybara effect*  and making it the default intelligent means that users 
   do not have to be aware of this setting for it to work at reasonable performance.
   Do not know whether i or p is an issue.

**[-sum|--sum <string>]**

All file posts include a checksum.  It is placed in the amqp message header will have as an
entry  *sum*  with default value 'd,md5_checksum_on_data'.  The  *sum*  option tells the 
subscriber how to calculate the checksum.  It is a comma separated string.
Valid checksum flags are ::

    [0|n|d|c=<scriptname>]
    where 0 : no checksum... value in post is 0
          n : do checksum on filename
          d : do md5sum on file content

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



DEVELOPER SPECIFIC OPTIONS
==========================

**[-debug|--debug]**

Active if  *-debug|--debug*  appears in the command line... or *debug*  is 
set to True in the configuration file used.

**[-r|--randomize]**

Active if  *-r|--randomize*  appears in the command line... or *randomize*  
is set to True in the configuration file used.
If there are several posts because the file is posted
by block because the  *blocksize*  option was set, the block 
posts are randomized meaning that the will not be posted
ordered by block number.

**[-rr|--reconnect]**

Active if  *-rc|--reconnect*  appears in the command line... or *reconnect*  is 
set to True in the configuration file used.  If there are several posts because 
the file is posted by block because the  *blocksize*  option was set, there is a
reconnection to the broker every time a post is to be sent.

SEE ALSO
========

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.html>`_ - the format of log messages.

`sr_report2source(1) <sr_report2source.7.html>`_ - copy log messages from the pump log bus to upstream destination.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe and Re-advertise: A combined downstream an daisy-chain posting client.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the http-only download client.


