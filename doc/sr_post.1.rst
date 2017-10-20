
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

To consume announcements and download the file.  To make files available 
to subscribers, **sr_post** sends the announcements to an AMQP server, 
also called a broker.  


CREDENTIAL OPTIONS
------------------

The broker option sets all the credential information to connect to the  **RabbitMQ** server

- **broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqp://anonymous:anonymous@dd.weather.gc.ca/ ) 

All sr\_ tools store all sensitive authentication info in the credentials.conf file.
Passwords for SFTP, AMQP, and HTTP accounts are stored in URL´s there, as well as other pointers
to thins such as private keys, or FTP modes.

For more details, see: `sr_subscribe(7) credentials <sr_subscribe.7.html#credentials>`_


Mandatory Settings
------------------

The [*-u|--url url*] option specifies the location 
subscribers will download the file from.  There is usually one post per file.
Format of argument to the *url* option::

       [ftp|http|sftp]://[user[:password]@]host[:port]/
       or
       file:

The [*-p|--path path1 path2 .. pathN*] option specifies the path of the files
to be announced. There is usually one post per file.
Format of argument to the *path* option::

       /absolute_path_to_the/filename
       or
       relative_path_to_the/filename

the *-pipe* option can be specified to have sr_post read path names from standard 
input as well.



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

Please refer to the `sr_subscribe(7) <sr_subscribe.7.html>`_ manual page for a detailed description of 
common settings, and methods of specifying them.

**[-b|--broker <broker>]**

  the broker to which the post is sent.

**[-c|--config <configfile>]**

  A list of settings in a configuration file 

**[--cache]**

  When one is planning reposting directories, this option caches
  what was posted and will post only files (or parts of files) that were new
  when invoked again.   This is incompatible with the default *parts 0* strategy, one
  must specify an alternate strategy.

  If caching is in use,  **blocksize** should be set (to either 1 (announce entire file) 
  or a fixed blocksize.) as otherwise blocksize will vary as a function of file size.

**[-dr|--document_root <path>]**

  The *document_root* option supplies the directory path that,
  when combined (or found) in the given *path*, 
  gives the local absolute path to the data file to be posted.
  The document root part of the local path will be removed from the posted announcement.
  for sftp: url's it can be appropriate to specify a path relative to a user account.
  Example of that usage would be:  -dr ~user  -url sftp:user@host  
  for file: url's, document_root is usually not appropriate.  To post an absolute path, 
  omit the -dr setting, and just specify the complete path as an argument.
  

**[-ex|--exchange <exchange>]**

  Sr_post publishes to an exchange named *xs_*"broker_username" by default.
  Use the *exchange* option to override that default.
  Note that the administrator must have created the exchange before one can post to it.

**[-f|--flow <string>]**

  An arbitrary label that allows the user to identify a specific flow.
  The flow string is sets in the amqp message header.  By default, there is no flow.

**[-h|-help|--help**

  Display program options.

**[--blocksize <value>]**

This option controls the partitioning strategy used to post files.
the value should be one of::

   0 - autocompute an appropriate partitioning strategy (default)
   1 - always send entire files in a single part.
   <blocksize> - used a fixed partition size (example size: 1M )

Files can be announced as multiple parts.  Each part has a separate checksum.
The parts and their checksums are stored in the cache. Partitions can traverse
the network separately, and in paralllel.  When files change, transfers are
optimized by only sending parts which have changed.  

The value of the *blocksize*  is an integer that may be followed by  letter designator *[B|K|M|G|T]* meaning:
for Bytes, Kilobytes, Megabytes, Gigabytes, Terabytes respectively.  All theses references are powers of 2.
Files bigger than this value will get announced with *blocksize* sized parts.

The autocomputation algorithm determines a blocksize that encourages a reasonable number of parts
for files of various sizes.  As the file size varies, the automatic computation will give different
results.  this will result in resending information which has not changed as partitions of a different 
size will have different sums, and therefore be tagged as different.  

By default, **sr_post** computes a reasonable blocksize that depends on the file size.
The user can set a fixed *blocksize* if it is better for its products or if he wants to
take advantage of the **cache** mechanism.  In cases where large files are being appended to, for example,
it make sense to specify a fixed partition size so that the blocks in the cache will be the 
same blocks as those generated when the file is larger, and so avoid re-transmission.  So use 
of '10M' would make sense in that case.  

In cases where a custom downloader is used which does not understand partitioning, it is necessary
to avoid having the file split into parts, so one would specify '1' to force all files to be send
as a single part.

**[-p|--path path1 path2 ... pathN]**

**sr_post** evaluates the filesystem paths from the **path** option 
and possibly the **document_root** if the option is used.

If a path defines a file, this file is announced.

If a path defines a directory, then all files in that directory are
announced... 

If this path defines a directory and the option **recursive** is true,
then all files in that directory are posted. Should **sr_post** find
one (or more) directory(ies), it scans it(them) and posts announcements
until the entire tree is scanned.

The AMQP announcements are made of the three fields, the announcement time,
the **url** option value and the resolved paths to which were withdrawn from
the *document_root*, present and needed.

**[-pipe <boolean>]**

The pipe option is for sr_post to read the names of the files to post from standard input to read from
redirected files, or piped output of other commands. Default is False, accepting file names only on the command line.


**[-rec|--recursive <boolean>]**

The recursive default is False when the **path** given (possibly combined with **document_root**)
describes one or several directories.  If **recursive** is True, the directory tree is scanned down and all subtree
files are posted.

**[--reset]**

  When one has used **--cache** this option will get rid of the
  cached informations.


**[-rn|--rename <path>]**

  With the *rename*  option, the user can suggest a destination path to its files. If the given
  path ends with '/' it suggests a directory path...  If it doesn't, the option specifies a file renaming.

**[-sub|--subtopic <key>]**

The subtopic default can be overwritten with the *subtopic* option.

**[-to|--to <destination>,<destination>,... ]** 

  A comma-separated list of destination clusters to which the posted data should be sent.
  Ask pump administrators for a list of valid destinations.

  default: the hostname of the broker.

.. note:: 
  FIXME: a good list of destination should be discoverable.

**[-sum|--sum <string>]**

All file posts include a checksum.  The *sum* option specifies how to calculate the it.
It is a comma separated string.  Valid checksum flags are ::

    [0|n|d|c=<scriptname>]
    where 0 : no checksum... value in post is random integer (for load balancing purposes.)
          n : do checksum on filename
          d : do md5sum on file content (default... for compatibility with older releases.)
          s : do SHA512 on file content (future default)

Then using a checksum script, it must be registered with the pumping network, so that consumers
of the postings have access to the algorithm.


**[-tp|--topic_prefix <key>]**

  *Not usually used*
  By default, the topic is made of the default topic_prefix : version *V02*, an action *post*,
  followed by the default subtopic: the file path separated with dots (dot being the topic separator for amqp).
  You can overwrite the topic_prefix by setting this option.


**[-u|--url <url>]**

The **url** option sets the protocol, credentials, host and port under
which the product can be fetched.

The AMQP announcememet is made of the three fields, the announcement time,
this **url** value and the given **path** to which was withdrawn from the *document_root*
if necessary.

The concatenation of the two last fields of the announcement defines
what the subscribers will use to download the product. 

**[-header <name>=<value>]**

Add a <name> header with the given value to advertisements. Used to pass strings as metadata.




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
respectively. The administrator would execute **sr_post**, providing
all the options and setting everything found in the log plus the 
targetted queue_name  *-queue_name q_....*



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

**[-rc|--reconnect]**

Active if *-rc|--reconnect* appears in the command line... or
*reconnect* is set to True in the configuration file used.
*If there are several posts because the file is posted
by block because the *blocksize* option was set, there is a
reconnection to the broker everytime a post is to be sent.

**[--parts]**

The usual usage of the *blocksize* option is described above, which is what is usually used to set
the *parts* header in the messages produced, however there are a number of ways of using the parts flag 
that are not generally useful aside from within development.
In addition to the user oriented *blocksize* specifications listed before, any valid 'parts' header, as given in the 
parts header (e.g. 'i,1,150,0,0') .  One can also specify an alternate basic blocksize for the automatic 
algorithm by giving it after the '0', (eg. '0,5') will use 5 bytes (instead of 50M) as the basic block size, so one
can see how the algorithm works.





SEE ALSO
========

`sr_subscribe(7) <sr_subscribe.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_report(1) <sr_report.1.html>`_ - process report messages.

`sr_post(7) <sr_post.7.html>`_ - the format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the http-only download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.



