
==================
 Subscriber Guide
==================



------------------------------------------------
Receiving Data from a MetPX-Sarracenia Data Pump
------------------------------------------------

.. contents::


Introduction
------------

A Sarracenia data pump is a web server with a notification
system for subscribers to know, quickly, when new
data has arrived.  To find out what data is available 
on a pump, just view the tree with a web browser.  For 
small immediate needs one can download data using the 
browser itself, or any standard downloader such as wget,
but that is not really the intended use.  

In general, one configures sr_subscribe to automatically 
download the data you want, to a directory
where other software can process it.  Please note that
the tool is entirely command line driven (there is no GUI)
and that, while written to be compatible with other 
environments, the focus is on Linux usage in programmatic 
settings.

While Sarracenia can work with any web tree, or any URL 
that sources want to post, there is a conventional layout.
A data pump's web server will just expose web accessible folders
and the root of the tree is the date, in YYYYMMDD format.

These dates do not represent anything about the data other than 
when it was put into the pumping network, and since Sarracenia 
always uses Universal Co-ordinated Time, the dates might not correspond
the current date/time in the location of the subscriber.

Under the first level of date trees, there is a directory
per source.  A Source in Sarracenia is an account used to inject
data into the pump network.  Data can cross many pumps on it´s
way to the visible one.  The tree described above is the conventional 
one found on most data pumps, but the original data pump, 
dd.weather.gc.ca, pre-dates the convention.

FIXME: insert standard tree image.

Please note that this is an introduction to obtaining data
from MetPX-Sarracenia data pumps. More detailed reference material
is available at the traditional sr_subscribe(1) man page,
and the other documentation of the package at http://metpx.sf.net_

A First Example
---------------

Regardless of the tree, one can browse the directory tree to find the
data of interest. on dd.weather.gc.ca one can browse to

http://dd.weather.gc.ca/observations/swob-ml/

And find the tree of all the weather observations in SWOB format
recently issued by any Environment Canada 
forecast office.

A configuration to obtain these files will look like so::

  blacklab% cat >../dd_swob.conf <<EOT

  broker amqp://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#
  accept .*
  # write all SWOBS into the current working directory.
  EOT

The first line *broker* indicates where to connect to get the
stream of notifications.   The term *broker* is taken from AMQP, which
is the protocol used to transfer the notifications.

The notifications that will be received all have *topics* that correspond 
to their URL.   The notifications are sent by AMQP topic-based exchanges.
Basically wherever there was a path separator ( ´/´ on most operating systems, 
or ´\´ on Windows ) on the path on the web server, to build the topic of
a notification, the separator is replaced by a period ( ´.´ ), as in AMQP
period is the hierarchical separator character.

By default, the sub-topic is ´#´ which is a wildcard that matches all (any?) 
subtopic.  The other wildcard usable in the subtopic option is ´*´ which matches 
anything between two periods (a single level of the topic hierarchy.)  The
subtopic option tells the broker what notifications are of interest to a 
subscriber.

Let´s start up a subscriber (assume the config file was called dd_swob.conf::

  blacklab% sr_subscribe ../dd_swob.conf start
  2015-12-03 06:53:35,268 [INFO] user_config = 0 ../dd_swob.conf
  2015-12-03 06:53:35,269 [INFO] instances 1 
  2015-12-03 06:53:35,270 [INFO] sr subscribe dd swob 0001 started

The subscriber then runs in the background. If we look in the current working
directory, the following files are created::

  blacklab% ls -al
  total 20
  drwxrwxr-x  2 peter peter 4096 Dec  3 06:53 .
  drwxrwxr-x 11 peter peter 4096 Dec  3 06:16 ..
  -rw-rw-rw-  1 peter peter  623 Dec  3 06:53 sr_subscribe_dd_swob_0001.log
  -rw-rw-rw-  1 peter peter    4 Dec  3 06:53 .sr_subscribe_dd_swob_0001.pid
  -rw-rw-rw-  1 peter peter    1 Dec  3 06:53 .sr_subscribe_dd_swob.state
  blacklab% 

.. NOTE::
  FIXME:
  These files may be created under ~/.cache/sarra instead of in the current directory, not sure?
  once q_ fixed, show example of file downloaded.

Each process started will have a pid file and a log file indicating it´s progress.
As each matching observation is posted on dd.weather.gc.ca, a notification will be
posted on the AMQP broker there.  

If we take a look at the swob file created, it immediately gives an indication
of whether it succeeded in connecting to the broker::

  blacklab% tail sr_subscribe_dd_swob_0001.log
  
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
the work of downloading, each with their own log file.

As the start up is normal, that means the authentication information was good.
Passwords are stored in the ~/.config/sarra/credentials.conf file.
The format is just a complete url on each line.  Example for above would be::
  
  amqp://anonymous:anonymous@dd.weather.gc.ca/

the password being placed after the :, and before the @ in the URL as is standard
practice.  This file should be private (0600).  

.. note::
   FIXME: we should probably disable inclusion of passwords on the command line.
   it is just asking for issues.  safer to store in credentials.conf one method is better than two?

A normal download looks like this::

  2015-12-03 17:32:15,031 [INFO] Received topic   v02.post.observations.swob-ml.20151203.CMED
  2015-12-03 17:32:15,031 [INFO] Received notice  20151203223214.699 http://dd2.weather.gc.ca/ \
         observations/swob-ml/20151203/CMED/2015-12-03-2200-CMED-AUTO-swob.xml
  2015-12-03 17:32:15,031 [INFO] Received headers {'filename': '2015-12-03-2200-CMED-AUTO-swob.xml', 'parts': '1,3738,1,0,0', \
        'sum': 'd,157a9e98406e38a8252eaadf68c0ed60', 'source': 'metpx', 'to_clusters': 'DD,DDI.CMC,DDI.ED M', 'from_cluster': 'DD'}
  2015-12-03 17:32:15,031 [INFO] downloading/copying into ./2015-12-03-2200-CMED-AUTO-swob.xml 

Giving all the information contained in the notification. 
Here is a failure::

  2015-12-03 17:32:30,715 [INFO] Downloads: http://dd2.weather.gc.ca/observations/swob-ml/20151203/CXFB/2015-12-03-2200-CXFB-AUTO-swob.xml  into ./2015-12-03-2200-CXFB-AUTO-swob.xml 0-6791
  2015-12-03 17:32:30,786 [ERROR] Download failed http://dd2.weather.gc.ca/observations/swob-ml/20151203/CXFB/2015-12-03-2200-CXFB-AUTO-swob.xml
  2015-12-03 17:32:30,787 [ERROR] Server couldn't fulfill the request. Error code: 404, Not Found

after a few minutes, Here is what the current directory looks like::

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


Refining Selection
------------------

The *accept* option applies on the sr_subscriber processes themselves,
providing regular expression based filtering of the notifications which are
transferred.  In contrast to operating on the topic (a transformed version 
of the path), *accept* operates on the actual path (well, URL), indicating 
what files within the notification stream received should actually be 
downloaded.

Note the following::

  blacklab% cat >../dd_swob.conf <<EOT

  broker amqp://anonymous@dd.weather.gc.ca
  accept .*/observations/swob-ml/.*

  #write all SWOBS into the current working directory
  #BAD: THIS IS NOT AS GOOD AS THE PREVIOUS EXAMPLE .
  #     no subtopic means excessive notifications processed.
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

.. Note::
   FIXME: default mirror false?  I think that is wrong? not sure.

By default, the files downloaded will be placed in the current working
directory.   

If downloading a directory tree, and the intent is to mirror
the tree, then the option mirror should be set::

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

one can also intersperse *directory* and *accept/reject* directives to build
an arbitrarily different hierarchy.

FIXME: example of different hierarchy?


Basic File Reception
--------------------

So local files are being created in the account, how does one trigger processing?
The following examples assume linux reception and a bash shell, but can be 
readily understood and applied to other environments.

If mirror is false, then a simple way would be to have a process that watches
the current directory and give the file names which arrive to some other program.
This can be done via either a traditional ´ls´ loop::

  while true; do
     ls | grep -v  sr_*.log | do_something
     sleep 5
  done

This will poll the directory every five secondsa and feed file names to ''do_something'',
excluding any hidden files, or the sr_* logs.  Hidden files are used to store file
fragments until a complete file is received, so it is important to avoid processing 
them until the complete file is received.  Sometimes existing software already scans 
directories, and has fixed ideas about the files it will ingest and/or ignore.
The *lock* option allows one to set the name of the temporary files during transfer
to conform to other software´s expectations. 

Setting *lock* to ´.´ will cause the temporary files to begin a dot, the tradition
for making hidden files on linux.  Setting a lock to something other than that will
´say .temp´ will cause the name of the temporary files to be suffixed with ´.temp´
When a file is completely received, it will be renamed, removing the .temp suffix.
Another possibility is to use *tmpdir* dir option.  When software is particularly
stubborn about ingesting anything it sees::

 tempdir ../temp

setting the tempdir option to a tree outside the actual destination dir will cause 
the file to be assembled elsewhere and only renamed into the destination directory 
once it is complete.

The 'ls' method works especially well if ''do_something'' erases the file after it 
is processed, so that the 'ls' command is only ever processing a small directory 
tree, and every file that shows up is *new*.

For a hierarchy of file (when mirror is true), ls itself is a bit unwieldy.  Perhaps 
the following is better::

  while true; do
     find . -print | grep -v sr_*.log | grep -v ".*/.sr_.*" | do_something
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

All of these methods have in common that one walks a file hierarchy every so often.  So we
Poll each directory periodically.  There is a natural maximum rate one can poll a directory
tree, and there is good deal of overhead to walking trees, especially when they are large 
and deep.  To avoid polling, one can use the inotifywait command::

  inotifywait -r `pwd` | grep -v sr_*.log | grep -v ".*/.sr_.*" | do_something 

On a truly local file system, inotifywait is a lot more efficient than polling methods, 
but the efficiency of inotify might not be all that different from polling on remote
directories (where, in some cases it is actually implemented by polling under the covers.)
There is also a limit to the number of things that can be watched this way on a system as a whole
and the process of scanning a large directory tree to start up an inotifywait can be quite
significant.

Regardless of the method used, the principle behind Basic File Reception is that sr_subscribe
writes the file to a directory, and an independent process does i/o to find the new file.

It is wortth noting that it would be more efficient, in terms of cpu and i/o of the system,  
if sr_subscribe would directly inform the processing software that the file has arrived.


Better File Reception
---------------------

Ideally, rather than using the file system, sr_subscribe indicates when each file is ready:: 

  blacklab% cat >../dd_swob.conf <<EOT

  broker amqp://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#
  on_file rxpipe
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
   on the same configuration, there is slight probability that notifications
   may corrupt one another in the named pipe.  to be verified FIXME.


Advanced File Reception
-----------------------

While the *on_file* directive specifies the name of an action to perform on receipt
of a file, those actions are not fixed, but simply small scripts provided with the
package, and customizable by end users.  The rxpipe module is just an example 
provided with sarracenia::

  class RxPipe(object):
      import os,stat

      def __init__():

          # FIXME: check for existence if...
          self.rxpipe = os.mknod(".rxpipe", device=stat.S_IFIFO )
          # FIXME: set unbufferred ?

      def perform(self, ipath, logger ):
          self.rxpipe.write( ippath + "\n" )
          self.rxpipe.flush()
          return None

  rxpipe =RxPipe()

  self.on_file=rxpipe.perform

With this fragment of python, when sr_subscribe is first called, it ensures that
a pipe named .rxpipe is opened in the current working directory by executing
the __init__ function within the declared RxPipe python class.  Then, whenever
a file reception is completed, the assignment of *self.on_file* ensures that 
the rx.perform function is called.

FIXME: describe parameters.

The rxpipe.perform function just writes the name of the file dowloaded to
the named pipe.  The use of the named pipe renders data reception asynchronous
from data processing.   as shown in the previous example, one can then 
start a single task *do_something* which processes the list of files fed
as standard input to it, from a named pipe.  

In the examples above, file reception and processing are kept entirely separate.  If there
is a problem with processing, the file reception directories will fill up, potentially
growing to an unwieldy size and causing many practical difficulties.  

When a plugin such as on_file is used, the processing of each file downloaded is
run before proceeding to the next file.  

If the code in the on_file script is changed to do actual processing work, then
rather than being independent, the processing could provide back pressure to the 
data delivery mechanism.  If the processing gets stuck, then the sr_subscriber 
will stop downloading, and the queue will be on the server,
rather than creating a huge local directory on the client.

An additional point is that if the processing of files is invoked
in each instance, providing very easy parallel processing built 
into sr_subscribe.  


File Notification Without Downloading
-------------------------------------

If the data pump exists in a large shared environment, such as
a Supercomputing Centre with a site file system.  In that case,
the file might be available without downloading.  So just
obtaining the file notification and transforming it into a 
local file is sufficient::

  blacklab% cat >../dd_swob.conf <<EOT

  broker amqp://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#
  no_download
  document_root /data/web/dd_root
  on_message do_something

  accept .*
  # do_something will catenate document_root with the path in 
  # the notification to obtain the full local path.

.. note:: 
   FIXME:: --no_download exists, but not no_download, patch sr_config
   option is called notify_only, which seems a lot less obvious to me... ?


on_message is a scripting hook, exactly like on_file, that allows
specific processing to be done on receipt of a message.  A message will
usually correspond to a file, but for large files, there will be one
message per part. Checking the xxx...FIXME to find out which part 
you have.

.. note:: 
   FIXME: perhaps show a way of checking the parts header to 
   with an if statement in order to act on only the first part message
   for long files.


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

Approach 1
~~~~~~~~~~

The simplest approach to high availability is to configure a 
separate sr_subscribe for each source pump to write to the same
destination directories.  When one subscribe seeks to download data, 
it will look on local disk to see if is already there (as per the
partial file updates described above.) If the other subscribe has
already downloaded the file, then it will be there, and the other
subscribe will leave it alone.

This approach can lead to race conditions, where the two sr_subscribes
each check, that the file has not arrived, so they both start 
downloading.  This will have the effect of downloading ´raced´ files 
multiple times, while no file corruption should result from this,
it will cause the file to disappear after reception for a very short 
period (as one copy is replaced by another.)

FIXME: example of two sr_subscribes one pointing at edm, the other at CMC.

Approach 2
~~~~~~~~~~

To get around the race conditions, and avoid redundant downloading,
one would use sr_winnow2??? a process that would subscribe to both
upstreams and pick one, the same way sr_winnow works on a single
exchange.

FIXME:


Approach 3
~~~~~~~~~~

Force the user to install a local pump, run sr_winnow on the local pump.
This makes a lot of sense for SPC´s where otherwise every workstation
is doing this work independently.  They could aim at a local pump instead.

Approach 4
~~~~~~~~~~

sample config file::

  blacklab% cat >../dd_swob.conf <<EOT

  broker amqp://edm.ec.gc.ca,amqp://ddi.cmc.ec.gc.ca

  subtopic observations.swob-ml.#
  accept .*
  # do_something will catenate document_root with the path in 

Make broker a comman-separated list.  Have sr_subscribe connect to 
multiple upstreams.  since sr_subscribe already does not block, this 
is not a big deal?  could just check each subscription in turn.  All 
the other options (subtopic, accept/reject, directory) would be the same?

The change to sr_subscribe would be to add the same associative array
used in sr_winnow.  entries in the table would need to be aged out...

aging strategy:  once the file is written to disk, remove from table,
because it is on disk, so can always get it again... except... memory
is faster, why force recalculation if you don´t need to...

perhaps aging is better.  1 Associative array built per hour.
look in 1 array for the current hour, a second for the last hour.
when you get to a new hour, you throwout the oldest one (so it will
go to disk.)

what is the associative array for?  same as in sr_winnow:
	- indexed by checksum.
	- if it´s present, then we have already chosen to download it.
          so do not pass to download process.

This could be combined with approach 3 at SPC´s where instead of
doing HA with two local pumps, they just have two independent pumps,
sarra´d together (basically mini-ddi´s.)


Approach 5
~~~~~~~~~~

on_message action to do the same thing as Approach 4.  I think it is
such a common use case, that it should be built-in somehow... mind
you it could be a standard on_message script...  one we would provide
with sarracenia, but still need a change in sr_subscribe to connect to 
two upstreams.

That allows omission of the associative array etc... when not listening
to multiple upstreams.

