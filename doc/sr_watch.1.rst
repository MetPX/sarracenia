==========
 SR_Watch 
==========

-----------------------------------------------------------
Watch a directory and post messages when files in it change
-----------------------------------------------------------

:Manual section: 1 
:Date: @Date@
:Version: @Version@
:Manual group: MetPX-Sarracenia

.. contents::


SYNOPSIS
========

**sr_watch** [ *-pbu|--post_base_url url* ] [ *-pb|--post_broker broker_url* ]...[ *-p|--path* ] [reload|restart|start|status|stop] [path]

DESCRIPTION
===========

Watches a directory and publishes posts when files in the directory change
( added, modified, or deleted). Its arguments are very similar to  `sr_post <sr_post.1.rst>`_.
In the MetPX-Sarracenia suite, the main goal is to post the availability and readiness
of one's files. Subscribers use  *sr_subscribe*  to consume the post and download the files.

Posts are sent to an AMQP server, also called a broker, specified with the option [ *-pb|--post_broker broker_url* ]. 

CREDENTIAL OPTIONS
------------------

The broker option sets all the credential information to connect to the  **RabbitMQ** server

- **post_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqps://anonymous:anonymous@dd.weather.gc.ca/ )

All sr\_ tools store all sensitive authentication info in the credentials.conf file.
Passwords for SFTP, AMQP, and HTTP accounts are stored in URLs there, as well as other pointers
to things such as private keys or FTP modes.

For more details, see: `sr_subscribe(1) credentials <sr_subscribe.1.html#credentials>`_

Mandatory Settings
------------------

The [*-post_base_url|--pbu|--url url*] option specifies the protocol, credentials, host and port to which subscribers 
will connect to get the file. 

Format of argument to the *url* option::

       [ftp|http|sftp]://[user[:password]@]host[:port]/
       or
       [ftp|http|sftp]://[user[:password]@]host[:port]/
       or
       file:


The [*-p|--path path*] option tells *sr_watch* what to look for.
If the *path* specifies a directory, *sr_watches* creates a post for any time
a file in that directory is created, modified or deleted. 
If the *path* specifies a file,  *sr_watch*  watches only that file.
In the announcement, it is specified with the *path* of the product.
There is usually one post per file.


An example of an execution of  *sr_watch*  checking a file::

 sr_watch -s sftp://stanley@mysftpserver.com/ -p /data/shared/products/foo -pb amqp://broker.com -action start

Here,  *sr_watch*  checks events on the file /data/shared/products/foo.
Default events settings reports if the file the file is modified or deleted.
When the file gets modified,  *sr_watch*  reads the file /data/shared/products/foo
and calculates its checksum.  It then builds a post message, logs into broker.com as user 'guest' (default credentials)
and sends the post to defaults vhost '/' and post_exchange 'xs_stanley' (default exchange)

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
which suggests to download the file in 1 part of 256 bytes (the actual filesize), trailing 1,0,0
gives the number of block, the remaining in bytes and the current 
block.  *sum=d,fc473c7a2801babbd3818260f50859de*  mentions checksum information,
here,  *d*  means md5 checksum performed on the data, and  *fc473c7a2801babbd3818260f50859de* 
is the checksum value.  When the event on a file is a deletion, sum=R,0  R stands for remove.

Another example watching a file::

 sr_watch -dr /data/web/public_data -s http://dd.weather.gc.ca/ -p bulletins/alphanumeric/SACN32_CWAO_123456 -pb amqp://broker.com -action start

By default, sr_watch checks the file /data/web/public_data/bulletins/alphanumeric/SACN32_CWAO_123456
(concatenating the base_dir and relative path of the source url to obtain the local file path).
If the file changes, it calculates its checksum. It then builds a post message, logs into broker.com as user 'guest'
(default credentials) and sends the post to defaults vhost '/' and post_exchange 'sx_guest' (default post_exchange)

A subscriber can download the file http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 using http
without authentication on dd.weather.gc.ca.

An example checking a directory::

 sr_watch -dr /data/web/public_data -pbu http://dd.weather.gc.ca/ -p bulletins/alphanumeric -pb amqp://broker.com -action start

Here, sr_watch checks for file creation(modification) in /data/web/public_data/bulletins/alphanumeric
(concatenating the base_dir and relative path of the source url to obtain the directory path).
If the file SACN32_CWAO_123456 is being created in that directory, sr_watch calculates its checksum.
It then builds a post message, logs into broker.com as user 'guest' 

A subscriber can download the created/modified file http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 using http
without authentication on dd.weather.gc.ca.

ARGUMENTS AND OPTIONS
=====================

Please refer to the `sr_subscribe(1) <sr_subscribe.1.rst>`_ manual page for a detailed description of
common settings, and methods of specifying them.

[--blocksize <value>]
---------------------

The value should be one of::

   0 - autocompute an appropriate partitioning strategy (default)
   1 - always send files in a single part.
   <sz> - used a fixed partition size (example size: 1M )

Files can be announced as multiple blocks (or parts). Each part has a separate checksum.
The parts and their checksums are stored in the cache. Partitions can traverse
the network separately, and in paralllel.  When files change, transfers are
optimized by only sending parts which have changed.

The autocomputation algorithm determines a blocksize that encourages a reasonable number of parts
for files of various sizes.  As the file size varies, the automatic computation will give different
results. This will result in resending information which has not changed as partitions of a different
size will have different sums.  Where large files are being appended to, it makes sense to specify a 
fixed partition size. 

In cases where a custom downloader is used that does not understand partitioning, it is necessary
to avoid having the file split into parts, so one would specify '1' to force all files to be sent
as a single part.

The value of the *blocksize*  is an integer that may be followed by  letter designator *[B|K|M|G|T]* meaning:
for Bytes, Kilobytes, Megabytes, Gigabytes, Terabytes respectively.  All these references are powers of 2.

[-pb|--post_broker <broker>]
----------------------------

       *broker*  is the broker to connect to to send the post.

[-c|--config <configfile>]
--------------------------

       A file filled with options.

[--delete <boolean>]
--------------------

In force_polling mode, assume that directories empty themselves, so that every file in each *path*
should be posted at every polling pass, instead of just new ones.  Use caching to ignore the ones
seen before.  In polling mode, the speed of recognition of files is limited to the speed at which
a tree can be traversed.  The scanning method needs to be chosen based on the performance sought.


[-pbd|--post_base_dir <path>]
-----------------------------

The  *base_dir*  option supplies the directory path that,
when combined with the relative one from  *source url* , 
gives the local absolute path to the data file to be posted.

[-e|--events <event|event|...>]
-------------------------------

A list of event types to monitor separated by a 'pipe symbol'.
Available events:  create, delete, link, modify

The *create*, *modify*, and *delete* events reflect what is expected: a file being created, modified, or deleted.
If *link* is set, symbolic links will be posted as links so that consumers can choose 
how to process them. If it is not set, then no symbolic link events will ever be posted.

.. note::
   move or rename events result in a special double post pattern, with one post as the old name
   and a field *newname* set, and a second post with the new name, and a field *oldname* set. 
   This allows subscribers to perform an actual rename, and avoid triggering a download when possible.

[-pe|--post_exchange <exchange>]
--------------------------------

  sr_watch publishes to an exchange named *xs_*"broker_username" by default.
  Use the *post_exchange* option to override that default.

[-fp|--force_polling <boolean>]
-------------------------------

By default, sr_watch selects an (OS dependent) optimal method to watch a 
directory. For large trees, the optimal method can be manyfold (10x or even 
100x) faster to recognize when a file has been modified. In some cases, 
however, platform optimal methods do not work (such as with some network 
shares, or distributed file systems), so one must use a slower but more
reliable and portable polling method.  The *force_polling* keyword causes
sr_watch to select the polling method in spite of the availability of a
normally better one.  KNOWN LIMITATION: When *force_polling* is set, 
the *sleep* setting should be at least 5 seconds. It is not currently clear
why.

NOTE::

  When directories are consumed by processes using the subscriber *delete* option, they stay empty, and
  every file should be reported on every pass.  When subscribers do not use *delete*, sr_watch needs to
  know which files are new.  It does so by noting the time of the beginning of the last polling pass.
  File are posted if their modification time is newer than that.  This will result in many multiple posts
  by sr_watch, which can be minimized with the use of cache.   One could even depend on the cache
  entirely and turn on the *delete* option, which will have sr_watch attempt to post the entire tree
  every time (ignoring mtime).

[-pos|--post_on_start]
----------------------

When starting sr_watch, one can either have the program post all the files in the directories watched
or not.


[-fs|--follow_symlinks <boolean>]
---------------------------------

The *follow_symlinks* option causes symbolic links to be traversed.  If *follow_symlinks* is set
and the destination of a symbolic link is a file, then that destination file should be posted as well as the link.
If the destination of the symbolic link is a directory, then the directory should be added to those being
monitored by sr_watch.   If *follow_symlinks* is false, then no action related to the destination of the symbolic 
link is taken.

[-header <name>=<value>]
------------------------

Add a <name> header with the given value to advertisements. Used to pass strings as metadata in the
advertisements to improve decision making for consumers.  Should be used sparingly. There are limits
on how many headers can be used, and minimizing the size of messages has important performance
impacts.

[-h|-help|--help]
-----------------

Display program options.

[-l <logpath>]
--------------

Set a file where all the logs will be written.
Logfile will rotate at 'midnight' and kept with a history of 5 files.

[-p|--path path]
----------------

**sr_post** evaluates the filesystem path from the **path** option 
and possibly the **post_base_dir** if the option is used.

If a path defines a file then this file is watched.

If a path defines a directory then all files in that directory are
watched... 

If this path defines a directory, all files in that directory are 
watched and should **sr_watch** find one (or more) directory(ies), it 
watches it(them) recursively until all the tree is scanned.

The AMQP announcements are made of the tree fields, the announcement time,
the **url** option value and the resolved paths to which were withdrawn
the *post_base_dir* present and needed.

[-real|--realpath <boolean>]
----------------------------

The realpath option resolves paths given to their canonical ones, eliminating 
any indirection via symlinks. The behaviour improves the ability of sr_watch to 
monitor trees, but the trees may have completely different paths than the arguments 
given. This option also enforces traversing of symbolic links. 

[-rn|--rename <path>]
---------------------

With the  *rename*   option, the user can
suggest a destination path for its files. If the given
path ends with '/' it suggests a directory path... 
If it doesn't, the option specifies a file renaming.

[-sub|--subtopic <key>]
-----------------------

The subtopic default can be overwritten with the  *subtopic*  option.

[--sleep <time> ]
-----------------

The time to wait between generating events.  When files are written frequently, it is counter productive
to produce a post for every change, as it can produce a continuous stream of changes where the transfers
cannot be done quickly enough to keep up.  In such circumstances, one can group all changes made to a file 
in *sleep* time, and produce a single post.


[-to|--to <destination>,<destination>,... ]
-------------------------------------------

  A comma-separated list of destination clusters to which the posted data should be sent.
  Ask pump administrators for a list of valid destinations.

  default: the hostname of the broker being posted to.

.. note:: 
  FIXME: a good list of destination should be discoverable.

[-tp|--topic_prefix <key>]
--------------------------

By default, the topic is made of the default topic_prefix : version  *V02* , an action  *post* ,
followed by the default subtopic: the file path separated with dots (dot being the topic separator for amqp).
You can overwrite the topic_prefix by setting this option.

[-pbu|--post_base_url <url>]
----------------------------

The **post_base_url** option sets the protocol, credentials, host and port under
which the product can be fetched.

The post body contains three fields: the announcement time,
this **post_base_url** value and the **path**, relative from *post_base_dir*, if necessary.

The concatenation of the two last fields of the post gives the complete URL 
subscribers use to download the file. 

[-sum|--sum <string>]
---------------------

All file posts include a checksum.  It is placed in the amqp message header will have as an
entry *sum* with default value 'd,md5_checksum_on_data'.
The *sum* option tell the program how to calculate the checksum.
It is a comma separated string.  Valid checksum flags are ::

    [0|n|d|s|N|z]
    where 0 : no checksum... value in post is a random integer (only for testing/debugging.)
          d : do md5sum on file content (default for now, compatibility)
          n : do md5sum checksum on filename
          p : do SHA512 checksum on filename and partstr [#]_
          s : do SHA512 on file content (default in future)
          z,a : calculate checksum value using algorithm a and assign after download.

Other checksum algorithms can be added. See Programming Guide.

.. [#] only implemented in C. ( see https://github.com/MetPX/sarracenia/issues/117 )

File Detection Strategies
-------------------------

The fundamental job of sr_watch is to notice when files are available to be transferred.
The appropriate strategy varies according to:

 - the **number of files in the tree** to be monitored, 
 - the **minimum time to notice changes** to files that is acceptable, and
 - the **size of each file** in the tree.  

**The easiest tree to monitor is the smallest one.** With a single directory to
watch where one is posting for an *sr_sarra* component, then use of the 
*delete* option will keep the number of files in directory at any one point
small and minimize the time to notice new ones. In such optimal conditions, 
noticing files in a hundredth of a second is reasonable to expect. Any method
will work well for such trees, but the sr_watch defaults (inotify) are usually
the lowest overhead.

sr_watch is sr_post with the added *sleep* option that will cause it to loop
over directories given as arguments.  sr_cpost is a C version that functions
identically, except it is faster and uses much less memory, at the cost of the
loss of plugin support.  With sr_watch (and sr_cpost) The default method of
noticing changes in directories uses OS specific mechanisms (on Linux: INOTIFY)
to recognize changes without having to scan the entire directory tree manually. 
Once primed, file changes are noticed instantaneously, but requires an 
initial walk across the tree, *a priming pass*.

For example, **assume a server can examine 1500 files/second**. If a **medium
sized tree is 30,000 files, then it will take 20 seconds for a priming pass**.
Using the fastest method available, one must assume that on startup for such a
directory tree it will take 20 seconds or so before it starts reliably posting
all files in the tree. After that initial scan, files are noticed with 
sub-second latency.  So a **sleep of 0.1 (check for file changes every tenth
of a second) is reasonable, as long as we accept the intial priming pass.**
If one selects **force_polling** option, then that 20 second delay is incurred
for each polling pass, plus the time to perform the posting itself. **For the
same tree, a *sleep* setting of 30 seconds would be the minimum to recommend.
Expect that files will be noticed about 1.5* the *sleep* settings on average.**
In this example, about when they are about 45 seconds. Some will be picked up
sooner, others later. Apart from special cases where the default method misses
files, it is much slower on medium sized trees than the default and should not
be used if timeliness is a concern.

In supercomputing clusters, distributed files systems are used, and the OS 
optimized methods for recognizing file modifications (INOTIFY on Linux) do not
cross node boundaries. To use sr_watch with the default strategy on a 
directory in a compute cluster, one usually must have an sr_watch process 
running on every node. If that is undesirable, then one can deploy it on a
single node with *force_polling* but the timing will be constrained by the
directory size.

As the tree being monitored grows in size, sr_watch's latency on startup grows,
and if polling is used the latency to notice file modifications will grow as
well. For example, with a tree with 1 million files, one should expect, at best,
a startup latency of 11 minutes. If using polling, then a reasonable expectation 
of the time it takes to notice new files would be in the 16 minute range. 

If the performance above is not sufficient, then one needs to consider the use
of the shim library instead of sr_watch. First, install the C version of 
Sarracenia, then set the environment for all processes writing files that
need to be posted to call it::

  export SR_POST_CONFIG=shimpost.conf
  export LD_PRELOAD="libsrshim.so.1"

where *shimpost.conf* is an sr_cpost configuration file in 
the ~/.config/sarra/post/ directory. An sr_cpost configuration file is the same
as an sr_post one, except that plugins are not supported.  With the shim
library in place, whenever a file is written, the *accept/reject* clauses of
the shimpost.conf file are consulted, and if accepted, the file is posted just
as it would be by sr_watch.

So far, the discussion has been about the time to notice a file has changed.
Another consideration is the time to post files once they have been noticed.
There are tradeoffs based on the checksum algorithm chosen. The most robust
choice is the default: *s* or SHA-512. When using the *s* sum method, the
entire file will be read in order to calculate it's checksum, which is
likely to determine the time to posting. The check sum will used by 
downstream consumers to determine whether the file being announced is new,
or one that has already been seen, and is really handy.

**For smaller files, checksum calculation time is negligible, but it is
generally true that bigger files take longer to post.** When **using the
shim library** method, the same process that wrote the file is the one
**calculating the checksum**, the likelihood of the file data being in a
locally accessible cache is quite high, so it **is as inexpensive as
possible**. It should also be noted that the sr_watch/sr_cpost **directory 
watching processes are single threaded, while when user jobs call sr_post, or
use the shim library, there can be as many processes posting files as there are
file writers.**

To shorten posting times, one can select *sum* algorithms that do not read
the entire file, such as *N* (SHA-512 of the file name only), but then one
loses the ability to differentiate between versions of the file.  

note ::
  should think about using N on the sr_watch, and having multi-instance shovels
  recalculate checksums so that part becomes easily parallellizable. Should be
  straightforward, but not yet explored as a result of use of shim library. FIXME.

A last consideration is that in many cases, other processes are writing files
to directories being monitored by sr_watch. Failing to properly set file 
completion protocols is a common source of intermittent and difficult to
diagnose file transfer issues. For reliable file transfers, it is critical
that both the writer and sr_watch agree on how to represent a file that
isn't complete.


File Detection Strategy Table
-----------------------------

+--------------------------------------------------------------------------------------------+
|                                                                                            |
|         File Detection Strategies (Order: Fastest to Slowest )                             |
|         Faster Methods Work for Larger Trees.                                              |
|                                                                                            |
+-------------+---------------------------------------+--------------------------------------+
| Method      | Description                           | Application                          |
+=============+=======================================+======================================+
|             |File delivery advertised by libsrshim  |Many user jobs which cannot be        |
|Implicit     | - requires C package.                 |modified to post explicitly.          |
|posting      | - export LD_PRELOAD=libsrshim.so.1    |                                      |
|using shim   | - must tune rejects as everything     | - multi-million file trees.          |
|library      |   might be posted.                    | - most efficient.                    |
|             | - works on any size file tree.        | - more complicated to setup.         |
|(LD_PRELOAD) | - very multi-threaded.                | - use where python3 not available.   |
|             | - I/O by writer (better localized)    | - no sr_watch needed.                |
|(in C)       | - very multi-threaded (user processes)| - no plugins.                        |
|             |                                       |                                      |
+-------------+---------------------------------------+--------------------------------------+
|             |File delivery advertised by            |User posts only when file is complete.|
|Explicit     |`sr_post(1) <sr_post.1.rst>`_          |                                      |
|posting by   |or other sr\_ components               |                                      |
|clients      |after file writing complete.           |                                      |
|             |                                       | - user has finest grain control.     |
|             | - poster builds checksums             | - usually best.                      |
|C: sr_cpost  | - fewer round trips (no renames)      | - if available, do not use sr_watch. |
|or           | - only a little slower than shim.     | - requires explicit posting by user  |
|Python:      | - no directory scanning.              |   scripts/jobs.                      |
|sr_post      | - many sr_posts can run at once.      |                                      |
+-------------+---------------------------------------+--------------------------------------+
|sr_cpost     |works like watch if sleep > 0          | - where python3 is hard to get.      |
|             |                                       | - where speed is critical.           |
|(in C)       | - faster than sr_watch                | - where plugins not needed.          |
|             | - uses less memory than sr_watch.     | - same issues with tree size         |
|             | - practical with a bit bigger trees.  |   as sr_watch, just a little later.  |
|             |                                       |   (see following methods)            |
+-------------+---------------------------------------+--------------------------------------+
|sr_watch with|Files transferred with a *.tmp* suffix.|Receiving from most other systems     |
|reject       |When complete, renamed without suffix. |(.tmp support built-in)               |
|.*\.tmp$     |Actual suffix is settable.             |Use to receive from Sundew.           |
|(suffix)     |                                       |                                      |
|             | - requires extra round trips for      |best choice for most trees on a       |
|             |   rename (a little slower)            |single server or workstation. Full    |
|             |                                       |plugin support.                       |
|  (default)  | - Assume 1500 limited to files/second |                                      |
|             | - Large trees mean long startup.      |works great with 10000 files          |
|(in Python)  | - each node in a cluster may need     |only a few seconds startup.           |
|             |   to run an instance                  |                                      |
|             | - each sr_watch single threaded.      |too slow for millions of files.       |
+-------------+---------------------------------------+--------------------------------------+
|sr_watch with|                                       |                                      |
|reject       |Use Linux convention to *hide* files.  |Sending to systems that               |
|^\\..*       |Prefix names with '.'                  |do not support suffix.                |
|(Prefix)     |that need that. (compatibility)        |                                      |
|             |same performance as previous method.   |                                      |
|             |                                       |                                      |
+-------------+---------------------------------------+--------------------------------------+
|sr_watch with|                                       |                                      |
|inflight     |Minimum age (modification time)        |Last choice, guarantees delay only if |
|number       |of the file before it is considered    |no other method works.                |
|(mtime)      |complete.                              |                                      |
|             |                                       |Receiving from uncooperative          |
|             | - Adds delay in every transfer.       |sources.                              |
|             | - Vulnerable to network failures.     |                                      |
|             | - Vulnerable to clock skew.           |(ok choice with PDS)                  |
|             |                                       |                                      |
|             |                                       |If a process is re-writing a file     |
|             |                                       |often, can use mtime to smooth out    |
|             |                                       |the i/o pattern, by slowing posts.    |
+-------------+---------------------------------------+--------------------------------------+
|force_polling|As per above 3, but uses plain old     |Only use when INOTIFY has some sort   |
|using reject |directory listings.                    |of issue, such as cluster file        |
|or mtime     |                                       |system in a supercomputer.            |
|methods above| - Large trees means slower to notice  |                                      |
|             |   new files                           |needed on NFS shares with multiple    |
|             | - should work anywhere.               |writing nodes.                        |
|             |                                       |                                      |
+-------------+---------------------------------------+--------------------------------------+




DEVELOPER SPECIFIC OPTIONS
==========================

[-debug|--debug]
----------------

Active if *-debug|--debug* appears in the command line... or
*debug* is set to True in the configuration file used.

[-r|--randomize]
----------------

Active if *-r|--randomize* appears in the command line... or
*randomize* is set to True in the configuration file used.
If there are several posts because the file is posted
by block (the *blocksize* option was set), the block 
posts are randomized meaning that they will not be posted
in order of block number.

[-rr|--reconnect]
-----------------

Active if *-rc|--reconnect* appears in the command line... or
*reconnect* is set to True in the configuration file used.
*If there are several posts because the file is posted
by block because the *blocksize* option was set, there is a
reconnection to the broker everytime a post is to be sent.

[--on_heartbeat]
----------------

Every *heartbeat* seconds, the *on_heartbeat* is invoked.  For periodic operations that happen relatively rarely, on the
scale of many minutes, usually. The argument is actually a duration, so it can be expressed in various time units:  5m (five minutes),  2h (two hours), days, or weeks. 

[--on_watch]
------------

Every *sleep* seconds, file system changes occurred are processed in a batch.  Prior to this processing,
the *on_watch* plugin is invoked.  It can be used to put a file in one of the watched directories... 
and have it published.  sleep is usually a much shorter interval than the heartbeat. It is also a 
duration, and so can be expressed in the same units as well.


CAVEATS
=======

Temporary Files
---------------

In order to avoid alerting for partially written (usually temporary) files, *sr_watch* does not post
events for changes to files with certain names:

 - files whose names begin with a dot **.**
 - files whose names end in .tmp

.. NOTE::
   FIXME: is this right?  need better does it ignore part files? should it?

Inotify Instance
----------------

Many linux systems have limits on how many directories can be watched that are set quite low, to minimize
kernel memory usage.  If you see a message like so::

    raise OSError("inotify instance limit reached")
    OSError: inotify instance limit reached

In that case, use administrative privileges to set *sysctl fs.inotify.max_user_instance=<enough>* to a number 
that is big enough.  More kernel memory will be allocated for this, no other effects of changing this setting are known.



SEE ALSO
========

`sr_post(1) <sr_post.1.rst>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.rst>`_ - the format of announcement messages.

`sr_report(7) <sr_report.7.rst>`_ - the format of report messages.

`sr_report(1) <sr_report.1.rst>`_ - process report messages.

`sr_sarra(8) <sr_sarra.8.rst>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - The download client (main manual page.)
