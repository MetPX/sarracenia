
==================
 Subscriber Guide
==================

------------------------------------------------
Receiving Data from a MetPX-Sarracenia Data Pump
------------------------------------------------

Status: Pre-Draft

.. note::
  Pardon the dust, This package is alpha, not ready for general use yet. Please Stay Tuned!
  **FIXME**: Missing sections are highlighted by **FIXME**.  What is here should be accurate!

.. contents::

Introduction
------------

A Sarracenia data pump is a web server with notifications
for subscribers to know, quickly, when new data has arrived.  
To find out what data is already available on a pump, 
view the tree with a web browser.  
For simple immediate needs, one can download data using the 
browser itself, or a standard tool such as wget.
The usual intent is for sr_subscribe to automatically 
download the data wanted to a directory on a subscriber
machine where other software can process it.  Please note:

- the tool is entirely command line driven (there is no GUI) More accurately, it is mostly config file driven.
  most of the *interface* involves using a text editor to modify configuration files.
- while written to be compatible with other environments, 
  the focus is on Linux usage. 
- the tool can be used as either an end-user tool, or a system-wide transfer engine.
  This guide is focused on the end-user case.  
- More detailed reference material is available at the 
  traditional sr_subscribe(1) man page,
- All documentation of the package is available 
  at http://metpx.sf.net

While Sarracenia can work with any web tree, or any URL 
that sources choose to post, there is a conventional layout.
A data pump's web server will just expose web accessible folders
and the root of the tree is the date, in YYYYMMDD format.
These dates do not represent anything about the data other than 
when it was put into the pumping network, and since Sarracenia 
always uses Universal Co-ordinated Time, the dates might not correspond
the current date/time in the location of the subscriber::

  Index of /

  Icon  Name                    Last modified      Size  Description
  [PARENTDIR] Parent Directory                             -   
  [DIR] 20151105/               2015-11-27 06:44    -   
  [DIR] 20151106/               2015-11-27 06:44    -   
  [DIR] 20151107/               2015-11-27 06:44    -   
  [DIR] 20151108/               2015-11-27 06:44    -   
  [DIR] 20151109/               2015-11-27 06:44    -   
  [DIR] 20151110/               2015-11-27 06:44    -  

A variable number of days are stored on each data pump, for those
with an emphasis on real-time reliable delivery, the number of days
will be shorter.  For other pumps, where long term outages need
to be tolerated, more days will be kept. 
Under the first level of date trees, there is a directory
per source.  A Source in Sarracenia is an account used to inject
data into the pump network.  Data can cross many pumps on it´s
way to the visible one::

  Index of /20151110
  
  Icon  Name                    Last modified      Size  Description
  [PARENTDIR] Parent Directory                             -   
  [DIR] UNIDATA-UCAR/           2015-11-27 06:44    -   
  [DIR] NOAAPORT/               2015-11-27 06:44    -   
  [DIR] MSC-CMC/                2015-11-27 06:44    -   
  [DIR] UKMET-RMDCN/            2015-11-27 06:44    -   
  [DIR] UKMET-Internet/         2015-11-27 06:44    -   
  [DIR] NWS-OPSNET/             2015-11-27 06:44    -  
  
The data under each of these directories was obtained from the named
source. In these examples, it is actually injected by DataInterchange
staff, and the names are chosen to represent the origin of the data.

A First Example
---------------

The tree described above is the conventional one found on most data pumps, 
but the original data pump, dd.weather.gc.ca, pre-dates the convention.
Regardless of the tree, one can browse it to find the data of interest. 
On dd.weather.gc.ca one can browse to http://dd.weather.gc.ca/observations/swob-ml/
to find the tree of all the weather observations in SWOB format
recently issued by any Environment Canada forecast office.
A configuration to obtain these files will look like so::

  blacklab% cat >../dd_swob.conf <<EOT

  broker amqp://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#
  accept .*
  # write all SWOBS into the current working directory.
  EOT

On the first line, *broker* indicates where to connect to get the
stream of notifications. The term *broker* is taken from AMQP (http://www.amqp.org), 
which is the protocol used to transfer the notifications.
The notifications that will be received all have *topics* that correspond 
to their URL. The notifications are sent by AMQP topic-based exchanges, 
which are hierarchical and use '.' as a separator, so we need to translate
the path hierarchy to a topic hierarchy.  Basically wherever there was a path 
separator ( ´/´ on most operating systems, or ´\´ on Windows ) on the path 
on the web server, to build the topic of a notification, the separator is 
replaced by a period ( ´.´ ), as in AMQP period is the hierarchical 
separator character. The top of the topic tree is used by sr_sarracenia,
so usually users only deal with sub-topics, two levels down from the root.

By default, the sub-topic is ´#´ which is a wildcard that matches and and all 
subtopics. The other wildcard usable in the subtopic option is ´*´ which matches 
anything between two periods (a single level of the topic hierarchy.)  The
subtopic option tells the broker what notifications are of interest to a 
subscriber.

Let´s start up a subscriber (assume the config file was called dd_swob.conf::

  blacklab% sr_subscribe ../dd_swob.conf start
  2015-12-03 06:53:35,268 [INFO] user_config = 0 ../dd_swob.conf
  2015-12-03 06:53:35,269 [INFO] instances 1 
  2015-12-03 06:53:35,270 [INFO] sr subscribe dd swob 0001 started

The subscriber then runs in the background. To keep most of sr_subscribe´s
working files out of the way, they it is stored elsewhere. example:
Once sr_subscribe is started with the given config file,
the following files are created::

  blacklab% ls -al ~/.cache/sarra/
  total 20
  drwxrwxr-x  2 peter peter 4096 Dec  3 06:53 .
  drwxrwxr-x 11 peter peter 4096 Dec  3 06:16 ..
  -rw-rw-rw-  1 peter peter  623 Dec  3 06:53 sr_subscribe_dd_swob_0001.log
  -rw-rw-rw-  1 peter peter    4 Dec  3 06:53 .sr_subscribe_dd_swob_0001.pid
  -rw-rw-rw-  1 peter peter    1 Dec  3 06:53 .sr_subscribe_dd_swob.state
  blacklab% 

.. NOTE::
   Directory is platform and configuration dependent. 
   use a file manager to navigate somewhere like:

   on Windows:  C:\\\\Users\\\\peter\\AppData\\\\Local\\\\science.gc.ca\\sarra

   on Mac:      /Users/peter/Library/Caches/sarra

Each process started will have a pid file and a log file indicating it´s progress.
As each matching observation is posted on dd.weather.gc.ca, a notification will be
posted on the AMQP broker there.  If we take a look at the swob file created, it 
immediately gives an indication of whether it succeeded in connecting to the broker::

  blacklab% tail ~/.cache/sarra/sr_subscribe_dd_swob_0001.log
  
  2015-12-03 06:53:35,635 [INFO] Binding queue q_anonymous.21096474.62787751 with key v02.post.observations.swob-ml.# to exchange xpublic on broker amqp://anonymous@dd.weather.gc.ca/
  2015-12-03 17:32:01,834 [INFO] user_config = 1 ../dd_swob.conf
  2015-12-03 17:32:01,835 [INFO] sr_subscribe start
  2015-12-03 17:32:01,835 [INFO] sr_subscribe run
  2015-12-03 17:32:01,835 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2015-12-03 17:32:01,835 [INFO] AMQP  input :    exchange(xpublic) topic(v02.post.observations.swob-ml.#)
  2015-12-03 17:32:01,835 [INFO] AMQP  output:    exchange(xs_anonymous) topic(v02.log.#)
  
  2015-12-03 17:32:08,191 [INFO] Binding queue q_anonymous.21096474.62787751 with key v02.post.observations.swob-ml.# to exchange xpublic on broker amqp://anonymous@dd.weather.gc.ca/
  blacklab% 
  
The sr_subscribe will get the notification and download the file into the 
current working directory. Only one download process is started, by default.  
If higher performance is needed, then the *instance* option can be set 
to a higher number, and that number of sr_subscribers will share
the work of downloading, each with their own log file (0002,0003, etc...)
As the start up is normal, that means the authentication information was good.
Passwords are stored in the ~/.config/sarra/credentials.conf file.
The format is just a complete url on each line.  Example for above would be::
  
  amqp://anonymous:anonymous@dd.weather.gc.ca/

The password is located after the :, and before the @ in the URL as is standard
practice.  This credentials.conf file should be private (linux octal permissions: 0600).  
Also, if a .conf file is placed in the ~/.config/sarra/subscribe directory, then 
sr_subscribe will find it without having to give the full path.


.. note::
   Directory where configuration is stored is platform and (on Windows)
   configuration dependent. Reasonable places they might be:

   on Windows:  C:\\\\Users\\\\peter\\AppData\\\\Local\\\\science.gc.ca\\sarra

A normal download looks like this::

  2015-12-03 17:32:15,031 [INFO] Received topic   v02.post.observations.swob-ml.20151203.CMED
  2015-12-03 17:32:15,031 [INFO] Received notice  20151203223214.699 http://dd2.weather.gc.ca/ \
         observations/swob-ml/20151203/CMED/2015-12-03-2200-CMED-AUTO-swob.xml
  2015-12-03 17:32:15,031 [INFO] Received headers {'filename': '2015-12-03-2200-CMED-AUTO-swob.xml', 'parts': '1,3738,1,0,0', \
        'sum': 'd,157a9e98406e38a8252eaadf68c0ed60', 'source': 'metpx', 'to_clusters': 'DD,DDI.CMC,DDI.ED M', 'from_cluster': 'DD'}
  2015-12-03 17:32:15,031 [INFO] downloading/copying into ./2015-12-03-2200-CMED-AUTO-swob.xml 

Giving all the information contained in the notification.  Here is a failure::

  2015-12-03 17:32:30,715 [INFO] Downloads: http://dd2.weather.gc.ca/observations/swob-ml/20151203/CXFB/2015-12-03-2200-CXFB-AUTO-swob.xml  into ./2015-12-03-2200-CXFB-AUTO-swob.xml 0-6791
  2015-12-03 17:32:30,786 [ERROR] Download failed http://dd2.weather.gc.ca/observations/swob-ml/20151203/CXFB/2015-12-03-2200-CXFB-AUTO-swob.xml
  2015-12-03 17:32:30,787 [ERROR] Server couldn't fulfill the request. Error code: 404, Not Found

Note that this message is not always a failure, as sr_subscribe retries a few times before giving up.
In any event, after a few minutes, Here is what the current directory looks like::

  blacklab% ls -al | tail
  -rw-rw-rw-  1 peter peter   7875 Dec  3 17:36 2015-12-03-2236-CL3D-AUTO-minute-swob.xml
  -rw-rw-rw-  1 peter peter   7868 Dec  3 17:37 2015-12-03-2236-CL3G-AUTO-minute-swob.xml
  -rw-rw-rw-  1 peter peter   7022 Dec  3 17:37 2015-12-03-2236-CTRY-AUTO-minute-swob.xml
  -rw-rw-rw-  1 peter peter   6876 Dec  3 17:37 2015-12-03-2236-CYPY-AUTO-swob.xml
  -rw-rw-rw-  1 peter peter   6574 Dec  3 17:36 2015-12-03-2236-CYZP-AUTO-swob.xml
  -rw-rw-rw-  1 peter peter   7871 Dec  3 17:37 2015-12-03-2237-CL3D-AUTO-minute-swob.xml
  -rw-rw-rw-  1 peter peter   7873 Dec  3 17:37 2015-12-03-2237-CL3G-AUTO-minute-swob.xml
  -rw-rw-rw-  1 peter peter   7037 Dec  3 17:37 2015-12-03-2237-CTBF-AUTO-minute-swob.xml
  -rw-rw-rw-  1 peter peter   7022 Dec  3 17:37 2015-12-03-2237-CTRY-AUTO-minute-swob.xml
  -rw-rw-rw-  1 peter peter 122140 Dec  3 17:38 sr_subscribe_dd_swob_0001.log
  blacklab% 


Working with Multiple Configurations
-------------------------------------

A small digression:

normally one just specifies the full path to the configuration file for sr_subscribe.
When running downloads from multiple sources, or to different destinations, one can place 
all the subscription configuration files, with the .conf suffix, in a standard 
directory: ~/.config/sarra/subscribe/

Imagine there are two files in that directory:  CMC.conf and NWS.conf.
One could then run:: 

  peter@idefix:~/test$ sr_subscribe CMC.conf start
  2016-01-14 18:13:01,414 [INFO] installing script validate_content.py 
  2016-01-14 18:13:01,416 [INFO] installing script validate_content.py 
  2016-01-14 18:13:01,416 [INFO] sr_subscribe CMC 0001 starting
  2016-01-14 18:13:01,418 [INFO] sr_subscribe CMC 0002 starting
  2016-01-14 18:13:01,419 [INFO] sr_subscribe CMC 0003 starting
  2016-01-14 18:13:01,421 [INFO] sr_subscribe CMC 0004 starting
  2016-01-14 18:13:01,423 [INFO] sr_subscribe CMC 0005 starting
  2016-01-14 18:13:01,427 [INFO] sr_subscribe CMC 0006 starting
  peter@idefix:~/test$ 

from anywhere, and the configuration in the directory would be invoked.  Also, one can use by using 
the sr command to start/stop multiple configurations at once.  The sr command will go through the 
default directories and start up all the configurations it finds::

  peter@idefix:~/test$ sr_subscribe CMC.conf start
  2016-01-14 18:13:01,414 [INFO] installing script validate_content.py 
  2016-01-14 18:13:01,416 [INFO] installing script validate_content.py 
  2016-01-14 18:13:01,416 [INFO] sr_subscribe CMC 0001 starting
  2016-01-14 18:13:01,418 [INFO] sr_subscribe CMC 0002 starting
  2016-01-14 18:13:01,419 [INFO] sr_subscribe CMC 0003 starting
  2016-01-14 18:13:01,421 [INFO] sr_subscribe CMC 0004 starting
  2016-01-14 18:13:01,423 [INFO] sr_subscribe CMC 0005 starting
  2016-01-14 18:13:01,416 [INFO] sr_subscribe NWS 0001 starting
  2016-01-14 18:13:01,416 [INFO] sr_subscribe NWS 0002 starting
  2016-01-14 18:13:01,416 [INFO] sr_subscribe NWS 0003 starting
  peter@idefix:~/test$ 

will start up some sr_subscribe processes as configured by CMC.conf and others to match NWS.conf.
sr stop will also do what you would expect.  As will sr status.  Back to file reception:



Refining Selection
------------------

.. note:: 
  **FIXME**: Make a picture, with a 
  - broker at one end, and the subtopic apply there.
  - client at the other end, and the accept/reject apply there.

The *accept* option applies on the sr_subscriber processes themselves,
providing regular expression based filtering of the notifications which are transferred.  
In contrast to operating on the topic (a transformed version of the path), *accept* operates 
on the actual path (well, URL), indicating what files within the notification stream 
received should actually be downloaded.  Look in the *Downloads* line of the log file 
for examples of this transformed path.

.. Note:: Brief Introduction to Regular Expressions

  Regular expressions are a very powerful way of expressing pattern matches. 
  They provide extreme flexibility, but in these examples we will only use a
  very trivial subset: The . is a wildcard matching any single character. If it
  is followed by an occurrence count, it indicates how many letters will match
  the pattern. the * (asterisk) character, means any number of occurrences.
  so:

  - .* means any sequence of characters of any length. In other words, match anything.
  - cap.* means any sequence of characters that starts with cap.
  - .*CAP.* means any sequence of characters with CAP somewhere in it.
  - .*cap means any sequence of characters that ends with CAP.

  Please consult various internet resources for more information on the full
  variety of matching possible with regular expressions:

  - https://en.wikipedia.org/wiki/Regular_expression
  - http://www.regular-expressions.info/ 

This is a different language than what is used in the subtopics, because the simpler language
in the subtopic directives comes from the AMQP specification.  We are not able to provide
full


back to sample configuration files:

Note the following::

  blacklab% cat >../dd_swob.conf <<EOT

  broker amqp://anonymous@dd.weather.gc.ca
  accept .*/observations/swob-ml/.*

  #write all SWOBS into the current working directory
  #BAD: THIS IS NOT AS GOOD AS THE PREVIOUS EXAMPLE .
  #     NO subtopic MEANS EXCESSIVE NOTIFICATIONS processed.
  EOT

This configuration, from the subscriber point of view, will likely deliver
the same data as the previous example. However, the default subtopic being 
a wildcard means that the server will transfer all notifications for the 
server (likely millions of them) that will be discarded by the subscriber 
process applying the accept clause.  It will consume a lot more CPU and 
bandwidth on both server and client.  One should choose appropriate subtopics 
to minimize the notifications that will be transferred only to be discarded.
The *accept* (and *reject*) patterns is used to further refine *subtopic* rather 
than replace it.

By default, the files downloaded will be placed in the current working
directory when sr_subscribe was started.  This can be overridden using
the *directory* option

If downloading a directory tree, and the intent is to mirror the tree, 
then the option mirror should be set::

  blacklab% cat >../dd_swob.conf <<EOT

  broker amqp://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#
  directory /tmp
  mirror True
  accept .*
  #
  # instead of writing to current working directory, write to /tmp.
  # in /tmp. Mirror: create a hierarchy like the one on the source server.
  EOT

One can also intersperse *directory* and *accept/reject* directives to build
an arbitrarily different hierarchy from what was on the source data pump.
The configuration file is read from top to bottom, so then sr_subscribe
finds a ''directory'' option setting, only the ''accept'' clauses after
it will cause files to be placed relative to that directory::

  blacklab% cat >../ddi_ninjo_part1.conf <<EOT

  broker amqp://ddi.cmc.ec.gc.ca/
  subtopic ec.ops.*.*.ninjo-a.#

  directory /tmp/apps/ninjo/import/point/reports/in
  accept .*ABFS_1.0.*
  accept .*AQHI_1.0.*
  accept .*AMDAR_1.0.*

  directory /tmp/apps/ninjo/import/point/catalog_common/in
  accept .*ninjo-station-catalogue.*

  directory /tmp/apps/ninjo/import/point/scit_sac/in
  accept .*~~SAC,SAC_MAXR.*

  directory /tmp/apps/ninjo/import/point/scit_tracker/in
  accept .*~~TRACKER,TRACK_MAXR.*

  EOT

In the above example, ninjo-station catalog data is placed in the
catalog_common/in directory, rather than in the point data 
hierarchy used to store the data that matches the first three
accept clauses.  

.. Note::

  Note that .* in the subtopic directive, where
  it means ´match any one topic´ (ie. no period characters allowed in 
  topic names) has a different meaning than it does in an accept 
  clause, where it means match any string.
  
  Yes, this is confusing.  No, it cannot be helped.  

  Why: The syntax of wildcarding in AMQP (which defines suptopic syntax) is 
  set by the international standard, and there are no other systems that 
  use it.  Regular expressions are a well known pattern matching language 
  with widespread support.


Basic File Reception
--------------------

So local files are being created in the account, how does one trigger processing?
The following examples assume linux reception and a bash shell, but can be 
readily understood and applied to other environments.

If mirror is false, then a simple way would be to have a process that watches
the current directory and give the file names which arrive to some other program.
This can be done via either a traditional ´ls´ loop::

  while true; do
     ls | grep -v  "*.tmp" | do_something
     sleep 5
  done

This will poll the directory every five seconds and feed file names to ''do_something'',
excluding temporary files.  Temporary files are used to store file
fragments until a complete file is received, so it is important to avoid processing 
them until the complete file is received.  Sometimes existing software already scans 
directories, and has fixed ideas about the files it will ingest and/or ignore.
The *inflight* option allows one to set the name of the temporary files during transfer
to conform to other software´s expectations.  the default setting is '.tmp' so
that temporary files have that suffix.

Setting *inflight* to ´.´ will cause the temporary files to begin a dot, the tradition
for making hidden files on linux.  Setting *inflight* to something other than that, 
such as 'inflight .temp´ will cause the name of the temporary files to be suffixed with ´.temp´
When a file is completely received, it will be renamed, removing the *inflight* 
.temp suffix.  Another possibility is to use *tempdir* dir option.  When software 
is particularly stubborn about ingesting anything it sees::

 tempdir ../temp

Setting the tempdir option to a tree outside the actual destination dir will cause 
the file to be assembled elsewhere and only renamed into the destination directory 
once it is complete.


The 'ls' method works especially well if ''do_something'' erases the file after it 
is processed, so that the 'ls' command is only ever processing a small directory 
tree, and every file that shows up is *new*.

For a hierarchy of file (when mirror is true), ls itself is a bit unwieldy.  Perhaps 
the following is better::

  while true; do
     find . -print | grep -v "*.tmp" | do_something
     sleep 5
  done

There is also the complexity that *do_something* might not delete files.  In that case,  
one needs to filter out the files which have already been processed.  Perhaps rather than 
listing all the files in a directory one wants only to be notified of the files which have 
changed since the last poll::
  
  while true; do
     touch .last_poll
     sleep 5
     find . -newer .last_poll -print | grep -v sr_*.log | grep -v ".*/.sr_.*" | do_something
  done

All of these methods have in common that one walks a file hierarchy every so often, polling
each directory by reading it's entirety to find new entries.  There is a natural maximum rate 
one can poll a directory tree, and there is good deal of overhead to walking trees, especially 
when they are large and deep.  To avoid polling, one can use the inotifywait command::

  inotifywait -r `pwd` | grep -v sr_*.log | grep -v ".*/.sr_.*" | do_something 

On a truly local file system, inotifywait is a lot more efficient than polling methods, 
but the efficiency of inotify might not be all that different from polling on remote
directories (where, in some cases it is actually implemented by polling under the covers.)
There is also a limit to the number of things that can be watched this way on a system as a whole
and the process of scanning a large directory tree to start up an inotifywait can be quite
significant.

Regardless of the method used, the principle behind Basic File Reception is that sr_subscribe
writes the file to a directory, and an independent process does i/o to find the new file.
It is worth noting that it would be more efficient, in terms of cpu and i/o of the system,  
if sr_subscribe would directly inform the processing software that the file has arrived.



Better File Reception
---------------------

Ideally, rather than using the file system, sr_subscribe indicates when each file is ready:: 

  blacklab% cat >../dd_swob.conf <<EOT

  broker amqp://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#

  file_rxpipe_name /home/peter/test/.rxpipe
  on_file file_rxpipe
  directory /tmp
  mirror True
  accept .*
  # rxpipe is a builtin on_file script which writes the name of the file received to
  # a pipe named '.rxpipe' in the current working directory.
  EOT

With the *on_file* option, one can specify a processing option such as rxpipe.  With rxpipe, 
every time a file transfer has completed and is ready for post-processing, its name is written 
to the linux pipe (named .rxpipe) in the current working directory.  So the code for post-processing 
becomes::

  do_something <.rxpipe

No filtering out of working files by the user is required, and ingestion of partial files is
completely avoided.   

.. NOTE::
   In the case where a large number of sr_subscribe instances are working
   On the same configuration, there is slight probability that notifications
   may corrupt one another in the named pipe.  
   We should probably verify whether this probability is negligeable or not.
   **FIXME**



Partial File Updates
--------------------

When files are large, they are divided into parts.  Each part is transferred
separately by sr_sarracenia.  So when a large file is updated, new part
notifications (posts) are created.  sr_subscribe will check if the file on 
disk matches the new part by checksumming the local data and comparing
that to the post.  If they do not match, then the new part of the file
will be downloaded.


Redundant File Reception
------------------------

In environments where high reliability is required, multiple servers
are often configured to provide services. The Sarracenia approach to
high availability is ´Active-Active´ in that all sources are online
and producing data in parallel.  Each source publishes data,
and consumers obtain it from the first source that makes it availble,
using checksums to determine whether the given datum has been obtained
or not.

This filtering requires implementation of a local dataless pump with 
sr_winnow.  See the Administrator Guide for more information.

