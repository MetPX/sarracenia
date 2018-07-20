
==============
 Data Sources
==============

---------------------------------------------------
Injecting Data into a MetPX-Sarracenia Pump Network
---------------------------------------------------

.. warning::
  **FIXME**: Missing sections are highlighted by **FIXME**. 
  Not really ready for use, too much missing for now.

.. contents::

.. note::
  **FIXME**: known missing elements: good discussion of checksum choice.
  Caveat about file update strategies. Use case of a file that is constantly updated,
  rather than issuing new files.)

Revision Record
---------------

:version: @Version@
:date: @Date@


A Sarracenia data pump is a web (or sftp) server with notifications for subscribers
to know, quickly, when new data has arrived. To find out what data is already available
on a pump, view the tree with a web browser. For simple immediate needs, one can
download data using the browser itself, or a standard tool such as wget.
The usual intent is for sr_subscribe to automatically download the data
wanted to a directory on a subscriber machine where other software
can process it. Note that this manual uses subscriptions to test
data injection, so the subscriber guide should likely be read before
this one.

Regardless of how it is done, injecting data means telling the pump where the data
is so that it can be forwarded to and/or by the pump. This can be done by either
using the active and explicit sr_post command, or just using sr_watch on a directory.
Where there are large numbers of files, and/or tight timeliness constraints, invocation
of sr_post directly by the producer of the file is optimal, as sr_watch may provide
disappointing performance. Another explicit, but low frequency approach is the
sr_poll command, which allows one to query remote systems to pull data
into the network efficiently.

While sr_watch is written as an optimal directory watching system, there simply is no
quick way to watch large (say, more than 100,000 files) directory trees. On
dd.weather.gc.ca, as an example, there are 60 million files in about a million
directories. To walk that directory tree once takes several hours. To find new files,
the best temporal resolution is every few (say 3) hours. So on average a notification
will occur 1.5 hours after the file has showed up. Using I_NOTIFY (on Linux), it still
takes several hours to start up, because it needs to do an initial file tree walk to
set up all the watches. After that it will be instant, but if there are too many
files (and 60 million is very likely too many) it will just crash and refuse to work.
These are inherent limitations of watching directories, no matter how it is done.
If it is really neccessary to do this, there is hope.  Please 
consult `Quickly Announcing Very Large Trees On Linux`_

With sr_post, the program that puts the file anywhere in the arbitrarily deep tree[1]_ tells
the pump (which will tell subscribers) exactly where to look. There are no system limits
to worry about. That’s how dd.weather.gc.ca works, and notifications are sub-second, with
60 million files on the disk. It is much more efficient, in general, to do direct
notifications rather than pass by the indirection of the file system, but in small
and simple cases, it makes little practical difference.

In the simplest case, the pump takes data from your account, wherever you have it,
providing you give it permission. We describe that case first.

.. [1] While the file tree itself has no limits in depth or number, the ability to
   filter based on *topics* is limited by AMQP to 255 characters. So the *subtopic*
   configuration item is limited to somewhat less than that. There isn't a fixed
   limit because topics are utf8 encoded which is variable length. Note that the
   *subtopic* directive is meant to provide coarse classification,  and
   use of *accept/reject* is meant for more detailed work.   *accept/reject* clauses
   do not rely on AMQP headers, using path names stored in the body of the
   message, and so are not affected by this limit.


SFTP Injection
--------------

Using the sr_post(1) command directly is the most straightforward way to inject data
into the pump network. To use sr_post, you have to know:

- the name of the local broker: ( say: ddsr.cmc.ec.gc.ca )
- your authentication info for that broker ( say: user=rnd : password=rndpw )
- your own server name (say: grumpy.cmc.ec.gc.ca )
- your own user name on your server (say: peter)

Assume the goal is for the pump to access peter's account via SFTP. Then you need
to take the pump's public key, and place it in peter's .ssh/authorized_keys.
On the server you are using (*grumpy*), one needs to do something like this::

  cat pump.pub >>~peter/.ssh/authorized_keys

This will enable the pump to access peter's account on grumpy using his private key.
So assuming one is logged in to peter's account on grumpy, one can store the broker
credentials safely::

  echo 'amqps://rnd:rndpw@ddsr.cmc.ec.gc.ca' >> ~/.config/sarra/credentials.conf:

.. Note::
  Passwords are always stored in the credentials.conf file.

So now the command line for sr_post is just the url for ddsr to retrieve the
file on grumpy::

  sr_post -post_broker amqp://guest:guest@localhost/ -post_base_dir /var/www/posts/ \
  -post_base_url http://localhost:81/frog.dna

  2016-01-20 14:53:49,014 [INFO] Output AMQP  broker(localhost) user(guest) vhost(/)
  2016-01-20 14:53:49,019 [INFO] message published :
  2016-01-20 14:53:49,019 [INFO] exchange xs_guest topic v02.post.frog.dna
  2016-01-20 14:53:49,019 [INFO] notice   20160120145349.19 http://localhost:81/ frog.dna
  2016-01-20 14:53:49,020 [INFO] headers  parts=1,16,1,0,0 sum=d,d108dcff28200e8d26d15d1b3dfeac1c to_clusters=localhost

There is a sr_subscribe to subscribe to all ``*.dna`` posts the subscribe log said. Here is the config file::

  broker amqp://guest:guest@localhost
  directory /var/www/subscribed
  subtopic #
  accept .*dna*

and here is the related output from the subscribe log file::

  2016-01-20 14:53:49,418 [INFO] Received notice  20160120145349.19 http://grumpy:80/ 20160120/guest/frog.dna
  2016-01-20 14:53:49,419 [INFO] downloading/copying into /var/www/subscribed/frog.dna
  2016-01-20 14:53:49,420 [INFO] Downloads: http://grumpy:80/20160120/guest/frog.dna  into /var/www/subscribed/frog.dna 0-16
  2016-01-20 14:53:49,424 [INFO] 201 Downloaded : v02.report.20160120.guest.frog.dna 20160120145349.19 http://grumpy:80/ 20160120/guest/frog.dna 201 sarra-server-trusty guest 0.404653 parts=1,16,1,0,0 sum=d,d108dcff28200e8d26d15d1b3dfeac1c from_cluster=test_cluster source=guest to_clusters=test_cluster rename=/var/www/subscribed/frog.dna message=Downloaded

Or alternatively, here is the log from an sr_sarra instance::

  2016-01-20 14:53:49,376 [INFO] Received v02.post.frog.dna '20160120145349.19 http://grumpy:81/ frog.dna' parts=1,16,1,0,0 sum=d,d108dcff28200e8d26d15d1b3dfeac1c to_cluster=ddsr.cmc.ec.gc.ca
  2016-01-20 14:53:49,377 [INFO] downloading/copying into /var/www/test/20160120/guest/frog.dna
  2016-01-20 14:53:49,377 [INFO] Downloads: http://grumpy:81/frog.dna  into /var/www/test/20160120/guest/frog.dna 0-16
  2016-01-20 14:53:49,380 [INFO] 201 Downloaded : v02.report.frog.dna 20160120145349.19 http://grumpy:81/ frog.dna 201 sarra-server-trusty guest 0.360282 parts=1,16,1,0,0 sum=d,d108dcff28200e8d26d15d1b3dfeac1c from_cluster=test_cluster source=guest to_clusters=test_cluster message=Downloaded
  2016-01-20 14:53:49,381 [INFO] message published :
  2016-01-20 14:53:49,381 [INFO] exchange xpublic topic v02.post.20160120.guest.frog.dna
  2016-01-20 14:53:49,381 [INFO] notice   20160120145349.19 http://grumpy:80/ 20160120/guest/frog.dna
  @

The command asks ddsr to retrieve the treefrog/frog.dna file by logging
in to grumpy as peter (using the pump's private key) to retrieve it, and posting it
on the pump, for forwarding to the other pump destinations.

Similar to sr_subscribe, one can also place configuration files in an sr_post specific directory::

  blacklab% sr_post edit dissem.conf

  post_broker amqps://rnd@ddsr.cmc.ec.gc.ca/
  post_base_url sftp://peter@grumpy

and then::

  sr_post -c dissem -url treefrog/frog.dna

If there are different varieties of posting used, configurations can be saved for each one.

.. warning::
   **FIXME**: Need to do a real example. this made up stuff isn´t sufficiently helpful.

   **FIXME**: sr_post does not accept config files right now, says the man page.  True/False?

   sr_post command lines can be a lot simpler if it did.

sr_post typically returns immediately as its only job is to advise the pump of the availability
of files. The files are not transferred when sr_post returns, so one should not delete files
after posting without being sure the pump actually picked them up.

.. NOTE::

  sftp is perhaps the simplest for the user to implement and understand, but it is also
  the most costly in terms of CPU on the server.  All of the work of data transfer is
  done at the python application level when sftp acquisition is done, which isn't great.

  A lower CPU version would be for the client to send somehow (sftp?) and then just
  tell where the file is on the pump (basically the sr_sender2 version).

Note that this example used sftp, but if the file is available on a local web site,
then http would work, or if the data pump and the source server share a file system,
then even a file url could work.


HTTP Injection
--------------

If we take a similar case, but in this case there is some http accessible space,
the steps are the same or even simpler if no authentication is required for the pump
to acquire the data. One needs to install a web server of some kind.

Assume a configuration that shows all files under /var/www as folders, running under
the www-data users. Data posted in such directories must be readable to the www-data
user, to allow the web server to read it. The server running the web server
is called *blacklab*, and the user on the server is *peter* running as peter on blacklab,
a directory is created under /var/www/project/outgoing, writable by peter,
which results in a configuration like so::

  sr_watch edit project.conf 

  broker amqp://feeder@localhost/
  url http://blacklab/
  post_base_dir /var/www/project/outgoing


Then a watch is started::

  sr_watch start project 

.. warning::
  **FIXME**: real example.

  **FIXME**: sr_watch was supposed to take configuration files, but might not have
   been modified to that effect yet.

While sr_watch is running, any time a file is created in the *document_root* directory,
it will be announced to the pump (on localhost, ie. the server blacklab itself).::

 cp frog.dna  /var/www/project/outgoing

.. warning::
  **FIXME**: real example.

This triggers a post to the pump. Any subscribers will then be able to download
the file.

.. warning::
   **FIXME**. too much broken for now to really run this easily...
   so creating real demo is deferred.


Polling External Sources
------------------------

Some sources are inherently remote, and we are unable to interest or affect them.
One can configure sr_poll to pull in data from external sources, typically web sites.
The sr_poll command typically runs as a singleton that tracks what is new at a source tree
and creates source messages for the pump network to process.

External servers, especially web servers often have different ways of posting their
product listings, so custom processing of the list is often needed. That is why sr_poll
has the do_poll setting, meaning that use of a plugin script is virtually required
to use it.

.. note::
   see the poll_script included in the package plugins directory for an example.
   **FIXME**: 


Report Messages
---------------

If the sr_post worked, that means the pump accepted to take a look at your file.
To find out where your data goes to afterward, one needs to examine source
log messages. It is also important to note that the initial pump, or any other pump
downstream, may refuse to forward your data for various reasons, that will only
be reported to the source in these report messages.


To view source report messages, the sr_report command is just a version of sr_subscribe, with the
same options where they make sense. If the configuration file (~/.config/sarra/default.conf)
is set up, then all that is needed is::

  sr_report

To view report messages indicating what has happenned to the items inserted into the
network from the same pump using that account (rnd, in the example). One can trigger
arbitrary post processing of report messages by using on_message plugin.

.. warning::
   **FIXME**: need some examples.



Large Files
-----------

Larger files are not sent as a single block. They are sent in parts, and each
part is fingerprinted, so that when files are updated, unchanged portions are
not sent again. There is a default threshold built into the sr\_ commands, above
which partitioned announcements will be done by default. This threshold can
be adjusted to taste using the *part_threshold* option.

Different pumps along the route may have different maximum part sizes. To
traverse a given path, the part must be no larger than the threshold setting
of all the intervening pumps. A pump will send the source an error log
message if it refuses to forward a file.

As each part is announced, so there is a corresponding report message for
each part.  This allows senders to monitor progress of delivery of large
files.

Reliability and Checksums
-------------------------

Every piece of data injected into the pumping network needs to have a unique fingerprint (or checksum).
Data will flow if it is new, and determining if the data is new is based on the fingerprint.
To get reliability in a sarracenia network, multiple independent sources are provisioned.
Each source announces their products, and if they have the same name and fingerprint, then
the products are considered the same.

The sr_winnow component of sarracenia looks at incoming announcements and notes which products
are received (by file name and checksum). If a product is new, it is forwarded on to other components
for processing. If a product is a duplicate, then the announcement is not forwarded further.
Similarly, when sr_subscribe or sr_sarra components receive an announcement for a product that is already
present on the local system, they will examine the fingerprint and not download the data unless it is different.
Checksum methods need to be known across a network, as downstream components will re-apply them.

Different fingerprinting algorithms are appropriate for different types of data, so
the algorithm to apply needs to be chosen by the data source, and not imposed by the network.
Normally, the 'd' algorithm is used, which applies the well-known Message-Digest 5 (md5sum)
algorithm to the data in the file.

When there is one origin for data, this algorithm works well. For high availability,
production chains will operate in parallel, preferably with no communication between
them.  Items produced by independent chains may naturally have different processing
time and log stamps and serial numbers applied, so the same data processed through
different chains will not be identical at the binary level.   For products produced
by different production chains to be accepted as equivalent, they need to have
the same fingerprint.

One solution for that case is, if the two processing chains will produce data with
the same name, to checksum based on the file name instead of the data, this is called 'n'.
In many cases, the names themselves are production chain dependent, so a custom
algorithm is needed. If a custom algorithm is chosen, it needs to be published on
the network::

 http://dd.cmc.ec.gc.ca/config/msc-radar/sums/

    u.py

So downstream clients can obtain and apply the same algorithm to compare announcements
from multiple sources.

.. warning::
   **FIXME**: science fiction again:  no such config directories exist yet. no means to update them.
   search path for checksum algos?  built-in,system-wide,per-source?

   Also, if each source defines their own algorithm, then they need to pick the same one
   (with the same name) in order to have a match.

   **FIXME**: verify that fingerprint verification includes matching the algorithm as well as value.

   **FIXME**:  not needed at the beginning, but likely at some point.
   in the mean time, we just talk to people and include their algorithms in the package.

.. NOTE::

  Fingerprint methods that are based on the name, rather than the actual data,
  will cause the entire file to be re-sent when they are updated.


User Headers
------------

What if there is some piece of metadata that a data source has chosen for some reason not to
include in the filename hierarchy? How can data consumers know that information without having
to download the file in order to determine that it is uninteresting. An example would be
weather warnings. The file names might include weather warnings for an entire country.  If consumers
are only interested in downloading warnings that are local to them, then, a data source could
use the on_post hook in order to add additional headers to the message.

.. note::
  With great flexibility comes great potential for harm. The path names should include as much information
  as possible as sarracenia is built to optimize routing using them.  Additional meta-data should be used
  to supplement, rather than replace, the built-in routing.

To add headers to messages being posted, one can use header option. In a configuration
file, add the following statements::

  header CAP_province=Ontario
  header CAP_area-desc=Uxbridge%20-%20Beaverton%20-%20Northern%20Durham%20Region
  header CAP_polygon=43.9984,-79.2175 43.9988,-79.219 44.2212,-79.3158 44.4664,-79.2343 44.5121,-79.1451 44.5135,-79.1415 44.5136,-79.1411 44.5137,-79.1407 44.5138,-79.14 44.5169,-79.0917 44.517,-79.0879 44.5169,-79.0823 44.218,-78.7659 44.0832,-78.7047 43.9984,-79.2175

So that when a file advertisement is posted, it will include the headers with the given values.
This example is artificial in that it statically assigns the header values which is appropriate 
to simple cases. For this specific case, it is likely more appropriate to implement a specialized 
on_post plugin for Common Alerting Protocol files to extract the above header information and 
place it in the message headers for each alert.




Efficiency Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~

It is not recommended to put overly complex logic in the plugin scripts, as they execute synchronously with
post and receive operations. Note that the use of built-in facilities of AMQP (headers) is done to
explicitly be as efficient as possible. As an extreme example, including encoded XML into messages
will not affect performance slightly, it will slow processing by orders of magnitude. One will not
be able to compensate for with multiple instances, as the penalty is simply too large to overcome.

Consider, for example, Common Alerting Protocol (CAP) messages for weather alerts.  These alerts routinely
exceed 100 KBytes in size, wheras a sarracenia message is on the order of 200 bytes.  The sarracenia messages
go to many more recipients than the alert: anyone considering downloading an alert, as oppposed to just the ones
the subscriber is actually interested in, and this metadata will also be included in the report messages,
and so replicated in many additional locations where the data itself will not be present.

Including all the information that is in the CAP would mean just in terms of pure transport 500 times
more capacity used for a single message.  When there are many millions of messages to transfer, this adds up.
Only the minimal information required by the subscriber to make the decision to download or not should be
added to the message.  It should also be noted that in addition to the above, there is typically a 10x to
100x cpu and memory penalty parsing an XML data structure compared to plain text representation, which
will affect the processing rate.


============================================
Quickly Announcing Very Large Trees On Linux
============================================

To mirror very large trees (millions of files) in real time, it takes too long for tools like rsync 
or find to traverse and generate lists of files to copy. On Linux, one can intercept calls for
file operations using the well known shim library technique. This technique provides virtually
real-time announcements of files regardless of the size of the tree, with minimal overhead as
this technique imposes much less load than tree traversal mechanisms, and makes use of the
C implementation of Sarracenia, which uses very little memory or processor resources.

To use this technique, one needs to have the C implementation of Sarracenia installed. The Libsrshim
library is part of that package, and the environment needs to be configured to intercept calls
to the C library like so::

    export SR_POST_CONFIG=somepost.conf
    export LD_PRELOAD=libsrshim.so.1.0.0

Where *somepost.conf* is a valid configuration that can be tested with sr_post to manually post a file.
Any process invoked from a shell with these settings will have all calls to routines like close(2)
intercepted by libsrshim. Libsrshim will check if the file is being written, and then apply the
somepost configuration (accept/reject clauses) and post the file if it is appropriate.
Example::

    blacklab% more pyiotest
    f=open("hoho", "w+" )
    f.write("hello")
    f.close()
    blacklab% 
    
    blacklab% more test2.sh
    
    echo "called with: $* "
    if [ ! "${LD_PRELOAD}" ]; then
       export SR_POST_CONFIG=`pwd`/test_post.conf
       export LD_PRELOAD=`pwd`/libsrshim.so.1.0.0
       exec $0
       #the exec here makes the LD_PRELOAD affect this shell, as well as sub-processes.
    fi
    
    set -x
    
    echo "FIXME: exec above fixes ... builtin i/o like redirection not being posted!"
    bash -c 'echo "hoho" >>~/test/hoho'
    
    /usr/bin/python2.7 pyiotest
    cp libsrshim.c ~/test/hoho_my_darling.txt
    
    blacklab% 
    
    lacklab% ./test2.sh
    called with:  
    called with:  
    +++ echo 'FIXME: exec above fixes ... builtin i/o like redirection not being posted!'
    FIXME: exec above fixes ... builtin i/o like redirection not being posted!
    +++ bash -c 'echo "hoho" >>~/test/hoho'
    2017-10-21 20:20:44,092 [INFO] sr_post settings: action=foreground log_level=1 follow_symlinks=no sleep=0 heartbeat=300 cache=0 cache_file=off
    2017-10-21 20:20:44,092 [DEBUG] setting to_cluster: localhost
    2017-10-21 20:20:44,092 [DEBUG] post_broker: amqp://tsource:<pw>@localhost:5672
    2017-10-21 20:20:44,094 [DEBUG] connected to post broker amqp://tsource@localhost:5672/#xs_tsource_cpost_watch
    2017-10-21 20:20:44,095 [DEBUG] isMatchingPattern: /home/peter/test/hoho matched mask: accept .*
    2017-10-21 20:20:44,096 [DEBUG] connected to post broker amqp://tsource@localhost:5672/#xs_tsource_cpost_watch
    2017-10-21 20:20:44,096 [DEBUG] sr_post file2message called with: /home/peter/test/hoho sb=0x7ffef2aae2f0 islnk=0, isdir=0, isreg=1
    2017-10-21 20:20:44,096 [INFO] published: 20171021202044.096 sftp://peter@localhost /home/peter/test/hoho topic=v02.post.home.peter.test sum=s,a0bcb70b771de1f614c724a86169288ee9dc749a6c0bbb9dd0f863c2b66531d21b65b81bd3d3ec4e345c2fea59032a1b4f3fe52317da3bf075374f7b699b10aa source=tsource to_clusters=localhost from_cluster=localhost mtime=20171021202002.304 atime=20171021202002.308 mode=0644 parts=1,2,1,0,0
    +++ /usr/bin/python2.7 pyiotest
    2017-10-21 20:20:44,105 [INFO] sr_post settings: action=foreground log_level=1 follow_symlinks=no sleep=0 heartbeat=300 cache=0 cache_file=off
    2017-10-21 20:20:44,105 [DEBUG] setting to_cluster: localhost
    2017-10-21 20:20:44,105 [DEBUG] post_broker: amqp://tsource:<pw>@localhost:5672
    2017-10-21 20:20:44,107 [DEBUG] connected to post broker amqp://tsource@localhost:5672/#xs_tsource_cpost_watch
    2017-10-21 20:20:44,107 [DEBUG] isMatchingPattern: /home/peter/src/sarracenia/c/hoho matched mask: accept .*
    2017-10-21 20:20:44,108 [DEBUG] connected to post broker amqp://tsource@localhost:5672/#xs_tsource_cpost_watch
    2017-10-21 20:20:44,108 [DEBUG] sr_post file2message called with: /home/peter/src/sarracenia/c/hoho sb=0x7ffeb02838b0 islnk=0, isdir=0, isreg=1
    2017-10-21 20:20:44,108 [INFO] published: 20171021202044.108 sftp://peter@localhost /c/hoho topic=v02.post.c sum=s,9b71d224bd62f3785d96d46ad3ea3d73319bfbc2890caadae2dff72519673ca72323c3d99ba5c11d7c7acc6e14b8c5da0c4663475c2e5c3adef46f73bcdec043 source=tsource to_clusters=localhost from_cluster=localhost mtime=20171021202044.101 atime=20171021202002.320 mode=0644 parts=1,5,1,0,0
    +++ cp libsrshim.c /home/peter/test/hoho_my_darling.txt
    2017-10-21 20:20:44,112 [INFO] sr_post settings: action=foreground log_level=1 follow_symlinks=no sleep=0 heartbeat=300 cache=0 cache_file=off
    2017-10-21 20:20:44,112 [DEBUG] setting to_cluster: localhost
    2017-10-21 20:20:44,112 [DEBUG] post_broker: amqp://tsource:<pw>@localhost:5672
    2017-10-21 20:20:44,114 [DEBUG] connected to post broker amqp://tsource@localhost:5672/#xs_tsource_cpost_watch
    2017-10-21 20:20:44,114 [DEBUG] isMatchingPattern: /home/peter/test/hoho_my_darling.txt matched mask: accept .*
    2017-10-21 20:20:44,115 [DEBUG] connected to post broker amqp://tsource@localhost:5672/#xs_tsource_cpost_watch
    2017-10-21 20:20:44,115 [DEBUG] sr_post file2message called with: /home/peter/test/hoho_my_darling.txt sb=0x7ffc8250d950 islnk=0, isdir=0, isreg=1
    2017-10-21 20:20:44,116 [INFO] published: 20171021202044.115 sftp://peter@localhost /home/peter/test/hoho_my_darling.txt topic=v02.post.home.peter.test sum=s,f5595a47339197c9e03e7b3c374d4f13e53e819b44f7f47b67bf1112e4bd6e01f2af2122e85eda5da633469dbfb0eaf2367314c32736ae8aa7819743f1772935 source=tsource to_clusters=localhost from_cluster=localhost mtime=20171021202044.109 atime=20171021202002.328 mode=0644 parts=1,15117,1,0,0
    blacklab% 
    


Note::
   file re-direction of i/o resulting from shell builtins (no process spawn) in the shell where 
   the environment variables are first set WILL NOT BE POSTED. only sub-shells are affected::

      # will not be posted...
      echo "hoho" >kk.conf

      # fill be posted.
      bash -c 'echo "hoho" >kk.conf' 
  
   This is a limitation of the technique, as the dynamic library load order is resolved on 
   process startup, and cannot be modified afterward. One work-around::

     if [ ! "${LD_PRELOAD}" ]; then
       export SR_POST_CONFIG=`pwd`/test_post.conf
       export LD_PRELOAD=`pwd`/libsrshim.so.1.0.0
       exec $*
     fi

  Which will activate the shim library for the calling environment by restarting it.
  This particular code may have impact on command line options and may not be directly applicable.


As an example, we have a tree of 22 million files that is written continuously day and night.
We need to copy that tree to a second file system as quickly as possible, with an aspirational
maximum copy time being about five minutes.
