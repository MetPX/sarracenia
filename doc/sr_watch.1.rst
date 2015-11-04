==========
 DD_Watch 
==========

-----------------------------------------------------------
watch a directory and post messages when files in it change
-----------------------------------------------------------

:Manual section: 1 
:Date: Aug 2015
:Version: 0.0.1
:Manual group: MetPX-Sarracenia

SYNOPSIS
========

**dd_watch** [ *-u|--url url* ] [ *-b|--broker broker_url* ]...[ *OPTIONS* ]

DESCRIPTION
===========

Watches a directory and publishes posts when files in the directory change
(are added, modified, or deleted.) Its arguments are very similar to  `dd_post <dd_post.1.html>`_.
In the MetPX-Sarracenia suite, the main goal is to post the availability and readiness
of one's files. Subscribers use  *dd_subscribe*  to consume the post and download the files.

Posts are sent to an AMQP server, also called a broker, specified with the option [ *-b|--broker broker_url* ]. 
Format of argument to the *broker* option:: 

       [amqp|amqps]://[user[:password]@]host[:port][/vhost]

The [*-u|--url url*] option specifies the location from which subscribers 
will download the file.  There is usually one post per file.
If the URL specifies a directory, *dd_watches* create a posts for any time
a file in that directory that is created, modified or deleted. 
If the *url* specifies a file,  *dd_watch*  watches that only that file.

format of argument to the *url* option::

       [ftp|http|sftp]://[user[:password]@]host[:port]//absolute_path_to/what_to_watch
       or
       [ftp|http|sftp]://[user[:password]@]host[:port]/relative_path_to/what_to_watch
       or
       file://absolute_path_to/what_to_watch

The double-slash at the beginning of the path marks it as absolute, whereas a single
slash is relative to a *document_root* provided as another option.

An example of an excution of  *dd_watch*  checking a file::

 dd_watch -s sftp://stanley@mysftpserver.com//data/shared/products/foo -pb amqp://broker.com

Here,  *dd_watch*  checks events on the file /data/shared/products/foo.
Default events settings reports if the file the file is modified or deleted.
When the file gets modified,  *dd_watch*  reads the file /data/shared/products/foo
and calculates its checksum.  It then builds a post message, logs into broker.com as user 'guest' (default credentials)
and sends the post to defaults vhost '/' and exchange 'amq.topic' (default exchange)

A subscriber can download the file /data/shared/products/foo  by logging as user stanley
on mysftpserver.com using the sftp protocol to  broker.com assuming he has proper credentials.

The output of the command is as follows ::

 [INFO] v02.post.data.shared.products.foo '20150813161959.854 sftp://stanley@mysftpserver.com/ /data/shared/products/foo'
       source=guest parts=1,256,1,0,0 sum=d,fc473c7a2801babbd3818260f50859de event=IN_CLOSE_WRITE

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
is the checksum value.  The  *event=IN_CLOSE_WRITE*  means, in our case, that the file was modified.

.. NOTE::
   FIXME: reference to event... remove?

Another example watching a file::

 dd_watch -dr /data/web/public_data -s http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 -pb amqp://broker.com

By default, dd_watch checks the file /data/web/public_data/bulletins/alphanumeric/SACN32_CWAO_123456
(concatenating the document_root and relative path of the source url to obtain the local file path).
If the file changes, it calculates its checksum. It then builds a post message, logs into broker.com as user 'guest'
(default credentials) and sends the post to defaults vhost '/' and exchange 'sx_guest' (default exchange)

A subscriber can download the file http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 using http
without authentication on dd.weather.gc.ca.

An example checking a directory::

 dd_watch -dr /data/web/public_data -s http://dd.weather.gc.ca/bulletins/alphanumeric -pb amqp://broker.com

Here, dd_watch checks for file creation(modification) in /data/web/public_data/bulletins/alphanumeric
(concatenating the document_root and relative path of the source url to obtain the directory path).
If the file SACN32_CWAO_123456 is being created in that directory, dd_watch calculates its checksum.
It then builds a post message, logs into broker.com as user 'guest' 
(default credentials) and sends the post to exchange 'amq.topic' (default exchange)

A subscriber can download the created/modified file http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 using http
without authentication on dd.weather.gc.ca.

ARGUMENTS AND OPTIONS
=====================


**[-b|--broker <broker>]**
       *broker*  is the broker to connect to to send the post.

**[-c|--config <configfile>]**

Any command line arguments has a corresponding long version starting with '--'.
For example  *-u*  has the long form  *--url* . You can also specify
this option in a configuration file shall you need it. To do so, you simply
use the long form without the '--', and put its value separated by a space.
In a configuration file the right syntax to set the url is :

**url <url>**

The  *config*  option is no exception... and if used the content of this
other specified file will have its options processed.


**[-dr|--document_root <path>]**

The  *document_root*  option supplies the directory path that,
when combined with the relative one from  *source url* , 
gives the local absolute path to the data file to be posted.
.fi

**[-e|--events <exchange>]**

By default, the events for dd_watch are IN_CLOSE_WRITE|IN_DELETE.
If you want to consider only one of these simply use the  *events*  option
and set it to IN_CLOSE_WRITE for creation/modification or  IN_DELETE for deletion.

.. NOTE:: 
    FIXME: events listing default is wrong... now have links and renames also by default.
    Do we want to just remove the **events** option and let dd_watch worry which events needed?

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

**[-tp|--topic_prefix <key>]**

By default, the topic is made of the default topic_prefix : version  *V02* , an action  *post* ,
followed by the default subtopic: the file path separated with dots (dot being the topic separator for amqp).
You can overwrite the topic_prefix by setting this option.

**[-sub|--subtopic <key>]**

The subtopic default can be overwritten with the  *subtopic*  option.

**[-u|--url <url>]**

The *url*  is the download url to be used by the subscribers.

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
   FIXME:  likely the dd_post/dd_watch default values for parts should change.
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

FILES IGNORED
=============

In order to avoid alerting for partially written (usually temporary) files, *dd_watch* does not post
events for changes to files with certain names:

 - files whose names begin with a dot **.**
 - files whose names end in .tmp

.. NOTE::
   FIXME: is this right?  need better does it ignore part files? should it?

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

`dd_get(1) <dd_get.1.html>`_ - the multi-protocol download client.

`dd_log(7) <dd_log.7.html>`_ - the format of log messages.

`dd_log2source(1) <dd_log2source.7.html>`_ - copy log messages from the switch log bus to upstream destination.

`dd_sara(1) <dd_sara.1.html>`_ - Subscribe and Re-advertise: A combined downstream an daisy-chain posting client.

`dd_post(1) <dd_post.1.html>`_ - post announcemensts of specific files.

`dd_post(7) <dd_post.7.html>`_ - The format of announcement messages.

`dd_sara(1) <dd_sara.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`dd_subscribe(1) <dd_subscribe.1.html>`_ - the http-only download client.


