
=========================
File Detection Strategies
=========================


The fundamental job of watch is to notice when files are available to be transferred.
The appropriate strategy varies according to:

 - the **number of files in the tree** to be monitored,
 - the **minimum time to notice changes** to files that is acceptable, and
 - the **size of each file** in the tree.

**The easiest tree to monitor is the smallest one.** With a single directory to
watch where one is posting for an *sr_sarra* component, then use of the
*delete* option will keep the number of files in directory at any one point
small and minimize the time to notice new ones. In such optimal conditions,
noticing files in a hundredth of a second is reasonable to expect. Any method
will work well for such trees, but the watch defaults (inotify) are usually
the lowest overhead.

When the tree gets large, the decision can change based on a number of factors,
described in the following table. It describes the approaches which will be lowest
latency and highest throughput first, and works its way to the least efficient
options that insert the most delay per detection.


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
|             | - I/O by writer (better localized)    | - no watch needed.                   |
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
|(in C)       | - faster than watch                   | - where plugins not needed.          |
|             | - uses less memory than sr_watch.     | - same issues with tree size         |
|             | - practical with a bit bigger trees.  |   as sr_watch, just a little later.  |
|             |                                       |   (see following methods)            |
+-------------+---------------------------------------+--------------------------------------+
|sr_watch with|Files transferred with a *.tmp* suffix.|Receiving from most other systems     |
|reject       |When complete, renamed without suffix. |(.tmp support built-in)               |
|: \.*\\.tmp$ |Actual suffix is settable.             |Use to receive from Sundew.           |
|(suffix)     |                                       |                                      |
|             | - requires extra round trips for      |best choice for most trees on a       |
|             |   rename (a little slower)            |single server or workstation. Full    |
|             |                                       |plugin support.                       |
|  (default)  | - Assume 1500 limited to files/second |                                      |
|             | - Large trees mean long startup.      |works great with 10000 files          |
|(in Python)  | - each node in a cluster may need     |only a few seconds startup.           |
|             |   to run an instance                  |                                      |
|             | - each watch single threaded.         |too slow for millions of files.       |
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
|(mtime)      |complete. (aka: fileAgeMin)            |                                      |
|             |                                       |Receiving from uncooperative          |
|Alternate    | - Adds delay in every transfer.       |sources.                              |
|setting      | - Vulnerable to network failures.     |                                      |
|             | - Vulnerable to clock skew.           |(ok choice with PDS)                  |
|             |                                       |                                      |
|fileAgeMin   |                                       |If a process is re-writing a file     |
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


sr_watch is sr3_post with the added *sleep* option that will cause it to loop
over directories given as arguments.  sr3_cpost is a C version that functions
identically, except it is faster and uses much less memory, at the cost of the
loss of plugin support.  With a watch (and sr3_cpost), the default method of
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
cross node boundaries. To use watch with the default strategy on a
directory in a compute cluster, one usually must have a watch process
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
as an sr3_post one, except that plugins are not supported.  With the shim
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
  should think about using N on the watch, and having multi-instance shovels
  recalculate checksums so that part becomes easily parallellizable. Should be
  straightforward, but not yet explored as a result of use of shim library. FIXME.

A last consideration is that in many cases, other processes are writing files
to directories being monitored by sr_watch. Failing to properly set file
completion protocols is a common source of intermittent and difficult to
diagnose file transfer issues. For reliable file transfers, it is critical
that both the writer and watch agree on how to represent a file that
isn't complete.





SHIM LIBRARY USAGE
------------------

Rather than invoking a sr3_post to post each file to publish, one can have processes automatically
post the files they right by having them use a shim library intercepting certain file i/o calls to libc
and the kernel. To activate the shim library, in the shell environment add::

  export SR_POST_CONFIG=shimpost.conf
  export LD_PRELOAD="libsrshim.so.1"

where *shimpost.conf* is an sr_cpost configuration file in
the ~/.config/sarra/post/ directory. An sr_cpost configuration file is the same
as an sr3_post one, except that plugins are not supported.  With the shim
library in place, whenever a file is written, the *accept/reject* clauses of
the shimpost.conf file are consulted, and if accepted, the file is posted just
as it would be by sr3_post. If using with ssh, where one wants files which are
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


Shim Usage Notes
~~~~~~~~~~~~~~~~

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
  these notification messages can be labelled as INFO, or WARNING priority, but it will
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
  same tree mirrored. See below for details.

* *export SR_SHIMDEBUG=1* will get your more output than you want. use with care.


Rename Processing
~~~~~~~~~~~~~~~~~

It should be noted that file renaming is not as simple in the mirroring case as in the underlying
operating system. While the operation is a single atomic one in an operating system, when
using notifications, there are accept/reject cases that create four possible effects.

+---------------+---------------------------+
|               |    old name is:           |
+---------------+--------------+------------+
| New name is:  |  *Accepted*  | *Rejected* |
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


