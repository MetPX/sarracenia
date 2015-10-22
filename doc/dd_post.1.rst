
=========
 DD_Post
=========

------------------------------------------------
Publish the Availability of a File to Subcribers
------------------------------------------------

:Manual section: 1 
:Date: Aug 2015
:Version: 0.0.1
:Manual group: MetPx Sarracenia Suite


SYNOPSIS
========

**dd_post** [ *-u|--url url* ] [ *-b|--broker broker* ]...[ *OPTIONS* ]

DESCRIPTION
===========

**dd_post** posts the availability of a file by creating an announcment.
Subscribers use `dd_subscribe <dd_subscribe.1.html>`_ to consume the announcement and 
download the file.  To make files available to subscribers, **dd_post** sends 
the announcements to an AMQP server, also called a broker.  Format of argument 
to the *broker* option:: 

       [amqp|amqps]://[user[:password]@]host[:port][/vhost]

The [*-u|--url url*] option specifies the location 
from which subscribers will download the file.  There is usually one post per file.
Format of argument to the *url* option::

       [ftp|http|sftp]://[user[:password]@]host[:port]//absolute_path_to_the/filename
       or
       [ftp|http|sftp]://[user[:password]@]host[:port]/relative_path_to_the/filename
       or
       file://absolute_path_to_the/filename

The double-slash at the beginning of the path marks it as absolute, whereas a single
slash is relative to a *document_root* provided as another option.
An example invocation of *dd_post*::

 dd_post -u sftp://stanley@mysftpserver.com//data/shared/products/foo -b amqp://broker.com

By default, dd_post reads the file /data/shared/products/foo and calculates its checksum.
It then builds a post message, logs into broker.com as user 'guest' (default credentials)
and sends the post  to defaults vhost '/' and default exchange 'amq.topic'.
A subscriber can download the file /data/shared/products/foo by authenticating as user stanley
on mysftpserver.com using the sftp protocol to broker.com assuming he has proper credentials.
The output of the command is as follows ::

 [INFO] v02.post.data.shared.products.foo  '20150813161959.854 sftp://stanley@mysftpserver.com/ /data/shared/products/foo'
              source=guest sum=d,82edc8eb735fd99598a1fe04541f558d parts=1,4574,1,0,0

In MetPX-Sarracenia, each post is published under a certain topic.
The log line starts with '[INFO]', followed by the **topic** of the
post. Topics in *AMQP* are fields separated by dot. The complete topic starts with
a topic_prefix (see option)  version *V02*, an action *post*,
followed by a subtopic (see option) here the default, the file path separated with dots
*data.shared.products.foo*

.. NOTE::
  FIXME: the topic does not contain the user?  Should it contain the source user? some docs say yes.

The second field in the log line is the message notice.  It consists of a time 
stamp *20150813161959.854*, and the source url of the file in the last 2 fields.

the rest of the information comes message headers, consisting of key-value pairs.
the first header should is *source=guest* indicating the user used to authenticate to the broker.
The *sum=d,82edc8eb735fd99598a1fe04541f558d* header gives file fingerprint (or checksum
) information.  Here, *d* means md5 checksum performed on the data, and *82edc8eb735fd99598a1fe04541f558d*
is the checksum value. The *parts=1,4574,1,0,0* state that the file is available in 1 part of 4574 bytes
(the filesize.)  The remaining *1,0,0* is not used for transfers of files with only one part.

Another example::

 dd_post -dr /data/web/public_data -u http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 -b amqp://broker.com

By default, dd_post reads the file /data/web/public_data/bulletins/alphanumeric/SACN32_CWAO_123456
(concatenating the document_root and relative path of the source url to obtain the local file path)
and calculates its checksum. It then builds a post message, logs into broker.com as user 'guest'
(default credentials) and sends the post to defaults vhost '/' and exchange 'amq.topic'

A subscriber can download the file http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 using http
without authentication on dd.weather.gc.ca.

.. NOTE::
  FIXME: the amq.topic ... is this correct? xpublic? validate.


ARGUMENTS AND OPTIONS
=====================

**[-b|--broker <broker>]**

  the broker to which the post is sent.

**[-c|--config <configfile>]**

  Any command line arguments has a corresponding long version starting with '--'.
  For example *-u* has the long form *--url*. You can also specify
  this option in a configuration file shall you need it. To do so, you simply
  use the long form without the '--', and put its value separated by a space.
  In a configuration file the right syntax to set the url is :

**url <url>** 

  The *config* option is no exception... and if used the content of this
  other specified file will have its options processed.

**[-dr|--document_root <path>]**

  The *document_root* option supplies the directory path that,
  when combined with the relative one from *url*, 
  gives the local absolute path to the data file to be posted.

**[-ex|--exchange <exchange>]**

  By default, the exchange used is amq.topic. This exchange is provided on broker
  for general usage. It can be overwritten with this *exchange* option

.. NOTE::
   FIXME: default is wrong?  figure out how often used?

**[-f|--flow <string>]**

  An arbitrary label that allows the user to identify a specific flow.
  The flow string is sets in the amqp message header.  By default, there is no flow.

**[-h|-help|--help**

  Display program options.

**[-rn|--rename <path>]**

  With the *rename*  option, the user can suggest a destination path to its files. If the given
  path ends with '/' it suggests a directory path...  If it doesn't, the option specifies a file renaming.

**[-tp|--topic_prefix <key>]**

  *Not usually used*
  By default, the topic is made of the default topic_prefix : version *V02*, an action *post*,
  followed by the default subtopic: the file path separated with dots (dot being the topic separator for amqp).
  You can overwrite the topic_prefix by setting this option.

**[-sub|--subtopic <key>]**

The subtopic default can be overwritten with the *subtopic* option.

**[-u|--url <url>]**

*url* is the actual download url to be
used by the subscribers.

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

Then using a checksum script, it must be registered with the switch, so that consumers
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

`dd_log(7) <dd_log.7.html>`_ - the format of log messages.

`dd_post(7) <dd_post.7.html>`_ - the format of announcement messages.

`dd_sara(1) <dd_sara.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`dd_subscribe(1) <dd_subscribe.1.html>`_ - the http-only download client.

`dd_watch(1) <dd_watch.1.html>`_ - the directory watching daemon.



