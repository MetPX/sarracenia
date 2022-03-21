========
Sr3_Post
========

---------------------------------
Publish the Availability of Files
---------------------------------

:Manual section: 1 
:Date: |today|
:Version: |release|
:Manual group: MetPx Sarracenia Suite

SYNOPSIS
========

**sr3_post|sr3_cpost** [ *OPTIONS* ][ *-pb|--post_broker broker* ][ *-pbu|--post_base_url url[,url]...** ] 
[ *-p|--path ] path1 path2...pathN* ]

( also **libsrshim.so** )

DESCRIPTION
===========

**sr3_post** posts the availability of a file by creating an announcement.
In contrast to most other sarracenia components that act as daemons,
sr3_post is a one shot invocation which posts and exits.
To make files 
available to subscribers, **sr3_post** sends the announcements 
to an AMQP server, also called a broker.  

This manual page is primarily concerned with the python implementation,
but there is also an implementation in C, which works nearly identically.
Differences:

 - plugins are not supported in the C implementation.
 - C implementation uses POSIX regular expressions, python3 grammar is slightly different.
 - when the *sleep* option ( used only in the C implementation) is set to > 0,
   it transforms sr_cpost into a daemon that works like the *watch* component
   of `sr3(1) <sr3.1.html>`_.  

Mandatory Settings
------------------

The *post_base_url url,url,...* option specifies the location 
subscribers will download the file from.  There is usually one post per file.
Format of argument to the *post_base_url* option::

       [ftp|http|sftp]://[user[:password]@]host[:port]/
       or
       file:

When several urls are given as a comma separated list to *post_base_url*, the
url´s provided are used round-robin style, to provide a coarse form of load balancing.

The [*-p|--path path1 path2 .. pathN*] option specifies the path of the files
to be announced. There is usually one post per file.
Format of argument to the *path* option::

       /absolute_path_to_the/filename
       or
       relative_path_to_the/filename

The *-pipe* option can be specified to have sr_post read path names from standard 
input as well.


An example invocation of *sr3_post*::

 sr3_post --post_broker amqp://broker.com --post_baseUrl sftp://stanley@mysftpserver.com/ --path /data/shared/products/foo 

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
a topicPrefix (see option), version *V02*, an action *post*,
followed by a subtopic (see option) here the default, the file path separated with dots
*data.shared.products.foo*.

The second field in the log line is the message notice.  It consists of a time 
stamp *20150813161959.854*, and the source URL of the file in the last 2 fields.

The rest of the information is stored in AMQP message headers, consisting of key=value pairs.
The *sum=d,82edc8eb735fd99598a1fe04541f558d* header gives file fingerprint (or checksum
) information.  Here, *d* means md5 checksum performed on the data, and *82edc8eb735fd99598a1fe04541f558d*
is the checksum value. The *parts=1,4574,1,0,0* state that the file is available in 1 part of 4574 bytes
(the filesize.)  The remaining *1,0,0* is not used for transfers of files with only one part.

Another example::

 sr3_post --post_broker mqtt://broker.com --post_baseDir /data/web/public_data --postBaseUrl http://dd.weather.gc.ca/ --path bulletins/alphanumeric/SACN32_CWAO_123456

By default, sr_post reads the file /data/web/public_data/bulletins/alphanumeric/SACN32_CWAO_123456
(concatenating the post_base_dir and relative path of the source url to obtain the local file path)
and calculates its checksum. It then builds a post message, logs into broker.com as user 'guest'
(default credentials) and sends the post to defaults vhost '/' and exchange 'xs_guest', resulting
in publication to the MQTT broker under the topic: *xs_guest/v03/bulletins/alphanumeric/SACN32_CWAO_123456*

A subscriber can download the file http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 using http
without authentication on dd.weather.gc.ca.


ARGUMENTS AND OPTIONS
=====================

Please refer to the `sr3_options(7) <sr3_options(7)>`_ manual page for a detailed description of 
all settings, and methods of specifying them.

path path1 path2 ... pathN
--------------------------

  **sr3_post** evaluates the filesystem paths from the **path** option 
  and possibly the **baseDir** if the option is used.

  If a path defines a file, this file is announced.

  If a path defines a directory, then all files in that directory are
  announced... 

post_broker <broker>
--------------------

  the broker to which the post is sent.

post_baseDir <path>
-------------------

  The *base_dir* option supplies the directory path that,
  when combined (or found) in the given *path*, 
  gives the local absolute path to the data file to be posted.
  The document root part of the local path will be removed from the posted announcement.
  For sftp URLs: it can be appropriate to specify a path relative to a user account.
  Example of that usage would be:  -dr ~user  -post_base_url sftp:user@host  
  For file URLs: base_dir is usually not appropriate.  To post an absolute path, 
  omit the -dr setting, and just specify the complete path as an argument.

post_exchange <exchange>
------------------------

  Sr_post publishes to an exchange named *xs_*"broker_username" by default.
  Use the *post_exchange* option to override that default.

-h|--help
---------

  Display program options.

blocksize <value>
-----------------

**Not currently useful, will re-instate post v3**

This option controls the partitioning strategy used to post files.
The value should be one of::

     0 - autocompute an appropriate partitioning strategy (default)
     1 - always send entire files in a single part.
     <blocksize> - used a fixed partition size (example size: 1M )

Files can be announced as multiple parts.  Each part has a separate checksum.
The parts and their checksums are stored in the cache. Partitions can traverse
the network separately, and in parallel.  When files change, transfers are
optimized by only sending parts which have changed.  
  
The value of the *blocksize*  is an integer that may be followed by  letter designator *[B|K|M|G|T]* meaning:
for Bytes, Kilobytes, Megabytes, Gigabytes, Terabytes respectively.  All these references are powers of 2.
Files bigger than this value will get announced with *blocksize* sized parts.
  
The autocomputation algorithm determines a blocksize that encourages a reasonable number of parts
for files of various sizes.  As the file size varies, the automatic computation will give different
results.  This will result in resending information which has not changed as partitions of a different 
size will have different sums, and therefore be tagged as different.  
  
By default, **sr_post** computes a reasonable blocksize that depends on the file size.
The user can set a fixed *blocksize* if it is better for its products or if he wants to
take advantage of the **cache** mechanism.  In cases where large files are being appended to, for example,
it make sense to specify a fixed partition size so that the blocks in the cache will be the 
same blocks as those generated when the file is larger, and so avoid re-transmission.  So use 
of '10M' would make sense in that case.  
  
In cases where a custom downloader is used which does not understand partitioning, it is necessary
to avoid having the file split into parts, so one would specify '1' to force all files to be sent
as a single part.

post_baseUrl <url>
------------------

The **url** option sets the protocol, credentials, host and port under
which the product can be fetched.

The AMQP announcememet is made of the three fields, the announcement time,
this **url** value and the given **path** to which was withdrawn from the *base_dir*
if necessary.

The concatenation of the two last fields of the announcement defines
what the subscribers will use to download the product. 

reset
-----

When one has used **--suppress_duplicates|--cache**, this option empties the cache.


rename <path>
-------------

With the *rename*  option, the user can suggest a destination path to its files. If the given
path ends with '/' it suggests a directory path...  If it doesn't, the option specifies a file renaming.

*sr_post*, and *sr_watch* use a file based model based on a process and a disk cache,
whose design is single threaded. The shim library is typically used by many processes
at once, and would have resource contention and/or corruption issues with the cache.
The shim library therefore has a purely memory-based cache, tunable with 
the following shim\_ options. 


shim_defer_posting_to_exit EXPERIMENTAL
--------------------------------------- 

  Postpones file posting until the process exits.
  In cases where the same file is repeatedly opened and appended to, this
  setting can avoid redundant posts.  (default: False)

shim_post_minterval *interval* EXPERIMENTAL
-------------------------------------------

  If a file is opened for writing and closed multiple times within the interval,
  it will only be posted once. When a file is written to many times, particularly 
  in a shell script, it makes for many posts, and shell script affects performance.  
  subscribers will not be able to make copies quickly enough in any event, so
  there is little benefit, in say, 100 posts of the same file in the same second.
  It is wise set an upper limit on the frequency of posting a given file. (default: 5s)
  Note: if a file is still open, or has been closed after its previous post, then
  during process exit processing it will be posted again, even if the interval
  is not respected, in order to provide the most accurate final post.


shim_skip_parent_open_files EXPERIMENTAL
----------------------------------------
 
  The shim_skip_ppid_open_files option means that a process checks
  whether the parent process has the same file open, and does not
  post if that is the case. (default: True)


sleep *time*
------------

  **This option is only available in the c implementation (sr_cpost)**

  When the option is set, it transforms cpost into a sr_watch, with *sleep* being the time to wait between 
  generating events.  When files are written frequently, it is counter productive to produce a post for 
  every change, as it can produce a continuous stream of changes where the transfers cannot be done quickly 
  enough to keep up.  In such circumstances, one can group all changes made to a file
  in *sleep* time, and produce a single post.

  NOTE::
      in sr_cpost, when combined with force_polling (see `sr_watch(1) <sr3.1.rst#watch>`_ ) the sleep 
      interval should not be less than about five seconds, as it may miss posting some files.

   

subtopic <key>
--------------

  The subtopic default can be overwritten with the *subtopic* option.


nodupe_ttl on|off|999
---------------------

  Avoid posting duplicates by comparing each file to those seen during the
  *suppress_duplicates* interval. When posting directories, will cause
  *sr_post* post only files (or parts of files) that were new when invoked again. 
 
  Over time, the number of files in the cache can grow too large, and so it is cleaned out of
  old entries. The default lifetime of a cache entry is five minutes (300 seconds). This
  lifetime can be overridden with a time interval as argument ( the 999 above ).

  If duplicate suppression is in use,  one should ensure that a fixed **blocksize** is
  used ( set to a value other than 0 ) as otherwise blocksize will vary as files grow,
  and much duplicate data transfer will result.

integrity <method>[,<value>]
----------------------------

All file posts include a checksum. The *sum* option specifies how to calculate the it.
It is a comma separated string. Valid Integrity methods are ::

         cod,x      - Calculate On Download applying x
         sha512     - do SHA512 on file content  (default)
         md5        - do md5sum on file content
         md5name    - do md5sum checksum on filename 
         random     - invent a random value for each post.
         arbitrary  - apply the literal fixed value.


.. Note::

  The checksums are stored in extended file attributes (or Alternate Data Streams on Windows). 
  This is necessary for the *arbitrary* method to work, since we have no means of calculating it.


topicPrefix <key>
-----------------

  *Not usually used*
  By default, the topic is made of the default topicPrefix : version *V03*
  followed by the default subtopic: the file path separated with dots (dot being the topic separator for amqp).
  You can overwrite the topicPrefix by setting this option.

header <name>=<value>
---------------------

  Add a <name> header with the given value to advertisements. Used to pass strings as metadata.


SHIM LIBRARY USAGE
==================

Rather than invoking a sr_post to post each file to publish, one can have processes automatically
post the files they right by having them use a shim library intercepting certain file i/o calls to libc 
and the kernel. To activate the shim library, in the shell environment add::

  export SR_POST_CONFIG=shimpost.conf
  export LD_PRELOAD="libsrshim.so.1"

where *shimpost.conf* is an sr_cpost configuration file in
the ~/.config/sarra/post/ directory. An sr_cpost configuration file is the same
as an sr_post one, except that plugins are not supported.  With the shim
library in place, whenever a file is written, the *accept/reject* clauses of
the shimpost.conf file are consulted, and if accepted, the file is posted just
as it would be by sr_post. If using with ssh, where one wants files which are
scp'd to be posted, one needs to include the activation in the .bashrc and pass 
it the configuration to use::

  expoert LC_SRSHIM=shimpost.conf

Then in the ~/.bashrc on the server running the remote command::

  if [ "$LC_SRSHIM" ]; then
      export SR_POST_CONFIG=$LC_SRSHIM
      export LD_PRELOAD="libsrshim.so.1"
  fi
       
SSH will only pass environment variables that start with LC\_ (locale) so to get it 
passed with minimal effort, we use that prefix.

Shim Usage Tips
---------------

This method of notification does require some user environment setup.
The user environment needs to the LD_PRELOAD environment variable set
prior to launch of the process. Complications that remain as we have
been testing for two years since the shim library was first implemented:

* if we want to notice files created by remote scp processes (which create non-login shells)
  then the environment hook must be in .bashrc. and using an environment
  variable that starts with *LC_* to have ssh transmit the configuration value without 
  having to modify sshd configuration in typical linux distributions. 
  ( full discussion: https://github.com/MetPX/sarrac/issues/66 )

* code that has certain weaknesses, such as in FORTRAN a lack of IMPLICIT NONE
  https://github.com/MetPX/sarracenia/issues/69 may crash when the shim library
  is introduced. The correction needed in those cases has so far been to correct
  the application, and not the library.
  ( also: https://github.com/MetPX/sarrac/issues/12 )

* codes using the *exec* call ot `tcl/tk <www.tcl.tk>`_, by default considers any
  output to file descriptor 2 (standard error) as an error condition.  
  these messages can be labelled as INFO, or WARNING priority, but it will 
  cause the tcl caller to indicate a fatal error has occurred.  Adding 
  *-ignorestderr*  to invocations of *exec* avoids such unwarranted aborts.

* Complex shell scripts can experience an inordinate performance impact.
  Since *high performance shell scripts* is an oxymoron, the best solution,
  performance-wise is to re-write the scripts in a more efficient scripting
  language such as python  ( https://github.com/MetPX/sarrac/issues/15 )

* Code bases that move large file hierarchies (e.g. *mv tree_with_thousands_of_files new_tree* )
  will see a much higher cost for this operation, as it is implemented as
  a renaming of each file in the tree, rather than a single operation on the root.
  This is currently considered necessary because the accept/reject pattern matching
  may result in a very different tree on the destination, rather than just the
  same tree mirrored. See `Rename Processing`_ below for details.

* *export SR_SHIMDEBUG=1* will get your more output than you want. use with care.

Rename Processing
-----------------

It should be noted that file renaming is not as simple in the mirroring case as in the underlying
operating system. While the operation is a single atomic one in an operating system, when
using notifications, there are accept/reject cases that create four possible effects.

+---------------+---------------------------+
|               |    old name is:           |
+---------------+--------------+------------+
|               |  *Accepted*  | *Rejected* |
| New name is:  |              |            |
+---------------+--------------+------------+
|  *Accepted*   |   rename     |   copy     |
+---------------+--------------+------------+
|  *Rejected*   |   remove     |   nothing  |
+---------------+--------------+------------+

When a file is moved, two notifications are created:

*  One notification has the new name in the *relpath*, while containing and *oldname* 
   field pointing at the old name.  This will trigger activities in the top half of
   the table, either a rename, using the oldname field, or a copy if it is not present
   at the destination.

*  A second notification with the oldname in *relpath* which will be accepted
   again, but this time it has the *newname* field, and process the remove action.

While the renaming of a directory at the root of a large tree is a cheap atomic operation
in Linux/Unix, mirroring that operation requires creating a rename posting for each file
in the tree, and thus is far more expensive.


ENVIRONMENT VARIABLES
=====================

In the C implementation (sr_cpost), if the SR_CONFIG_EXAMPLES variable is set, then the *add* directive can be used
to copy examples into the user's directory for use and/or customization.

An entry in the ~/.config/sarra/default.conf (created via sr_subscribe edit default.conf )
could be used to set the variable::

  declare env SR_CONFIG_EXAMPLES=/usr/lib/python3/dist-packages/sarra/examples

the value should be available from the output of a list command from the python
implementation.



SEE ALSO
========

`sr3(1) <sr3.1.html>`_ - Sarracenia main command line interface.

`sr3_post(1) <sr3_post.1.html>`_ - post file announcements (python implementation.)

`sr3_cpost(1) <sr3_cpost.1.html>`_ - post file announcemensts (C implementation.)

`sr3_cpump(1) <sr3_cpump.1.html>`_ - C implementation of the shovel component. (copy messages)

**Formats:**

`sr3_credentials(7) <sr3_credentials.7.html>`_ - Convert logfile lines to .save Format for reload/resend.

`sr3_options(7) <sr_options.7.html>`_ - the configuration options

`sr3_post(7) <sr_post.7.html>`_ - the format of announcements.

**Home Page:**

`https://metpx.github.io/sarracenia <https://metpx.github.io/sarracenia>`_ - Sarracenia: a real-time pub/sub data sharing management toolkit




