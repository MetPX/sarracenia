
==================
 Subscriber Guide
==================

------------------------------------------------
Receiving Data from a MetPX-Sarracenia Data Pump
------------------------------------------------

[ `version française <fr/subscriber.rst>`_ ]


.. contents::

Revision Record
---------------


:version: @Version@
:date: @Date@


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
  at https://github.com/MetPX

While Sarracenia can work with any web tree, or any URL 
that sources choose to post, there is a conventional layout.
A data pump's web server will just expose web accessible folders
and the root of the tree is the date, in YYYYMMDD format.
These dates do not represent anything about the data other than 
when it was put into the pumping network, and since Sarracenia 
always uses Universal Co-ordinated Time, the dates might not correspond
the current date/time in the location of the subscriber::

  Index of /

  Name                    Last modified      Size  Description
  Parent Directory                             -   
  20151105/               2015-11-27 06:44    -   
  20151106/               2015-11-27 06:44    -   
  20151107/               2015-11-27 06:44    -   
  20151108/               2015-11-27 06:44    -   
  20151109/               2015-11-27 06:44    -   
  20151110/               2015-11-27 06:44    -  

A variable number of days are stored on each data pump, for those
with an emphasis on real-time reliable delivery, the number of days
will be shorter.  For other pumps, where long term outages need
to be tolerated, more days will be kept. 

Under the first level of date trees, there is a directory
per source.  A Source in Sarracenia is an account used to inject
data into the pump network.  Data can cross many pumps on its
way to the visible ones::

  Index of /20151110
  
  Name                    Last modified      Size  Description
  Parent Directory                             -   
  UNIDATA-UCAR/           2015-11-27 06:44    -   
  NOAAPORT/               2015-11-27 06:44    -   
  MSC-CMC/                2015-11-27 06:44    -   
  UKMET-RMDCN/            2015-11-27 06:44    -   
  UKMET-Internet/         2015-11-27 06:44    -   
  NWS-OPSNET/             2015-11-27 06:44    -  
  
The data under each of these directories was obtained from the named
source. In these examples, it is actually injected by DataInterchange
staff, and the names are chosen to represent the origin of the data.

To list the available configurations with *sr_subscribe list* ::

  $ sr3 list examples
    Sample Configurations: (from: /usr/lib/python3/dist-packages/sarracenia/examples )
    cpump/cno_trouble_f00.inc        poll/aws-nexrad.conf             poll/pollingest.conf             poll/pollnoaa.conf               poll/pollsoapshc.conf            
    poll/pollusgs.conf               poll/pulse.conf                  post/WMO_mesh_post.conf          sarra/wmo_mesh.conf              sender/ec2collab.conf            
    sender/pitcher_push.conf         shovel/no_trouble_f00.inc        subscribe/WMO_Sketch_2mqtt.conf  subscribe/WMO_Sketch_2v3.conf    subscribe/WMO_mesh_CMC.conf      
    subscribe/WMO_mesh_Peer.conf     subscribe/aws-nexrad.conf        subscribe/dd_2mqtt.conf          subscribe/dd_all.conf            subscribe/dd_amis.conf           
    subscribe/dd_aqhi.conf           subscribe/dd_cacn_bulletins.conf subscribe/dd_citypage.conf       subscribe/dd_cmml.conf           subscribe/dd_gdps.conf           
    subscribe/dd_ping.conf           subscribe/dd_radar.conf          subscribe/dd_rdps.conf           subscribe/dd_swob.conf           subscribe/ddc_cap-xml.conf       
    subscribe/ddc_normal.conf        subscribe/downloademail.conf     subscribe/ec_ninjo-a.conf        subscribe/hpfx_amis.conf         subscribe/local_sub.conf         
    subscribe/pitcher_pull.conf      subscribe/sci2ec.conf            subscribe/subnoaa.conf           subscribe/subsoapshc.conf        subscribe/subusgs.conf           
    sender/ec2collab.conf            sender/pitcher_push.conf         watch/master.conf                watch/pitcher_client.conf        watch/pitcher_server.conf        
    watch/sci2ec.conf


Each section of the listing shows the contents of the directory shown in parentheses.
To use an example as a starting point::

  $ sr3 add subscribe/dd_amis.conf
    add: 2021-01-26 01:13:54,047 [INFO] sarracenia.sr add copying: /usr/lib/python3/dist-packages/sarracenia/examples/subscribe/dd_amis.conf to /home/peter/.config/sr3/subscribe/dd_amis.conf 


Now files in `.config/` can be used directly::
 
  $ sr3 list
    User Configurations: (from: /home/peter/.config/sr3 )
    subscribe/dd_amis.conf           admin.conf                       credentials.conf                 default.conf                     
    logs are in: /home/peter/.cache/sr3/log


To view a configuration, give it to `sr_subscribe list` as an argument:: 

  $ sr3 list subscribe/dd_amis.conf
    # this is a feed of wmo bulletin (a set called AMIS in the old times)
    
    broker amqps://dd.weather.gc.ca/
    
    # instances: number of downloading processes to run at once.  defaults to 1. Not enough for this case
    instances 5
    
    # expire, in operational use, should be longer than longest expected interruption
    expire 10m
    
    subtopic bulletins.alphanumeric.#
    
    accept .*


To delete a configuration::

  $ sr3 remove subscribe/dd_amis
    2021-01-26 01:17:24,967 [INFO] root remove FIXME remove! ['subscribe/dd_amis']
    2021-01-26 01:17:24,967 [INFO] root remove removing /home/peter/.config/sr3/subscribe/dd_amis.conf 


Server Side Resources Allocated for Subscribers
-----------------------------------------------

Every configuration results in corresponding resources being declared on the broker.
When changing *subtopic* or *queue* settings, or when one expects to not use 
a configuration for an extended period of time, it is best to::

  sr3 cleanup subscribe/swob.conf

which will de-allocate the queue (and its bindings) on the server.

Why? Whenever a subscriber is started, a queue is created on the data pump, with 
the topic bindings set by the configuration file. If the subscriber is stopped, 
the queue keeps getting messages as defined by subtopic selection, and when the 
subscriber starts up again, the queued messages are forwarded to the client. 
So when the *subtopic* option is changed, since it is already defined on the 
server, one ends up adding a binding rather than replacing it.  For example,
if one has a subtopic that contains SATELLITE, and then stops the subscriber, 
edit the file and now the topic contains only RADAR, when the subscriber is 
restarted, not only will all the queued satellite files be sent to the consumer, 
but the RADAR is added to the bindings, rather than replacing them, so the 
subscriber will get both the SATELLITE and RADAR data even though the configuration 
no longer contains the former.

Also, if one is experimenting, and a queue is to be stopped for a very long 
time, it may accumulate a large number of messages. The total number of messages 
on a data pump has an effect on the pump performance for all users. It is therefore 
advisable to have the pump de-allocate resources when they will not be needed 
for an extended periods, or when experimenting with different settings.


Working with Multiple Configurations
-------------------------------------

Place all configuration files, with the .conf suffix, in a standard 
directory: ~/.config/sr3/subscribe/ For example, if there are two files in 
that directory: CMC.conf and NWS.conf, one could then run:: 

  peter@idefix:~/test$ sr3 start subscribe/CMC.conf 
  2016-01-14 18:13:01,414 [INFO] installing script validate_content.py 
  2016-01-14 18:13:01,416 [INFO] installing script validate_content.py 
  2016-01-14 18:13:01,416 [INFO] sr_subscribe CMC 0001 starting
  2016-01-14 18:13:01,418 [INFO] sr_subscribe CMC 0002 starting
  2016-01-14 18:13:01,419 [INFO] sr_subscribe CMC 0003 starting
  2016-01-14 18:13:01,421 [INFO] sr_subscribe CMC 0004 starting
  2016-01-14 18:13:01,423 [INFO] sr_subscribe CMC 0005 starting
  peter@idefix:~/test$ 

to start the CMC downloading configuration.  One can use by
using the sr command to start/stop multiple configurations at once. 
The sr command will go through the default directories and start up 
all the configurations it finds::

  peter@idefix:~/test$ sr3 start
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

will start up some sr3 processes as configured by CMC.conf and others 
to match NWS.conf. Sr3 stop will also do what you would expect. As will sr3 status.  
Note that there are 5 sr_subscribe processes start with the CMC 
configuration and 3 NWS ones. These are *instances* and share the same 
download queue. 


High Priority Delivery
----------------------

While the Sarracenia protocol does not provide explicit prioritization, the use
of multiple queues provides similar benefits. Each configuration results
in a queue declaration on the server side. Group products at like priority into
a queue by selecting them using a common configuration. The smaller the groupings,
the lower the delay of processing. While all queues are processed at the same priority,
data passes though shorter queues more quickly. One can summarize with:

  **Use Multiple Configurations to Prioritize**

To make the advice concrete, take the example of the Environment Canada data 
mart ( dd.weather.gc.ca ), which distributes gridded binaries, GOES satellite 
imagery, many thousands of city forecasts, observations, RADAR products, etc...  
For real-time weather, warnings and RADAR data are the highest priority. At certain 
times of the day, or in cases of backlogs, many hundreds of thousands of products 
can delay receipt of high priority products if only a single queue is used.  

To ensure prompt processing of data in this case, define one configuration to subscribe
to weather warnings (which are a very small number of products), a second for the RADARS
(a larger but still relatively small group), and a third (largest grouping) for all
the other data. Each configuration will use a separate queue. Warnings will be
processed the fastest, RADARS will queue up against each other and so experience some
more delay, and other products will share a single queue and be subject to more
delay in cases of backlog.

https://github.com/MetPX/sarracenia/blob/master/sarra/examples/subscribe/ddc_hipri.conf::

  broker amqps://dd.weather.gc.ca/
  mirror
  directory /data/web
  subtopic alerts.cap.#
  accept .*



https://github.com/MetPX/sarracenia/blob/master/sarra/examples/subscribe/ddc_normal.conf::

  broker amqps://dd.weather.gc.ca/
  subtopic #
  reject .*alerts/cap.*
  mirror
  directory /data/web
  accept .*


Where you want the mirror of the data mart to start at /data/web (presumably there is a web
server configured do display that directory.)  Likely, the *ddc_normal* configuration 
will experience a lot of queueing, as there is a lot of data to download.  The *ddc_hipri.conf* is 
only subscribed to weather warnings in Common Alerting Protocol format, so there will be
little to no queueing for that data.




Refining Selection
------------------

.. warning:: 
  **FIXME**: Make a picture, with a: 

  - broker at one end, and the subtopic apply there.  
  - client at the other end, and the accept/reject apply there.

Pick *subtopics* ( which are applied on the broker with no message downloads ) to narrow
the number of messages that traverse the network to get to the sarracenia client processes.
The *reject* and *accept* options are evaluated by the sr_subscriber processes themselves,
providing regular expression based filtering of the posts which are transferred.  
*accept* operates on the actual path (well, URL), indicating what files within the 
notification stream received should actually be downloaded. Look in the *Downloads* 
line of the log file for examples of this transformed path.

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
  - .*cap means any sequence of characters that ends with CAP.  In case where multiple portions of the string could match, the longest one is selected.
  - .*?cap same as above, but *non-greedy*, meaning the shortest match is chosen.

  Please consult various internet resources for more information on the full
  variety of matching possible with regular expressions:

  - https://docs.python.org/3/library/re.html
  - https://en.wikipedia.org/wiki/Regular_expression
  - http://www.regular-expressions.info/ 

back to sample configuration files:

Note the following::

$ sr3 edit subscribe/swob

  broker amqps://anonymous@dd.weather.gc.ca
  accept .*/observations/swob-ml/.*

  #write all SWOBS into the current working directory
  #BAD: THIS IS NOT AS GOOD AS THE PREVIOUS EXAMPLE
  #     NOT having a "subtopic" and filtering with "accept" MEANS EXCESSIVE NOTIFICATIONS are processed.

This configuration, from the subscriber point of view, will likely deliver
the same data as the previous example. However, the default subtopic being 
a wildcard means that the server will transfer all notifications for the 
server (likely millions of them) that will be discarded by the subscriber 
process applying the accept clause. It will consume a lot more CPU and 
bandwidth on both server and client. One should choose appropriate subtopics 
to minimize the notifications that will be transferred only to be discarded.
The *accept* (and *reject*) patterns is used to further refine *subtopic* rather 
than replace it.

By default, the files downloaded will be placed in the current working
directory when sr_subscribe was started. This can be overridden using
the *directory* option.

If downloading a directory tree, and the intent is to mirror the tree, 
then the option mirror should be set::

$ sr3 edit subscribe/swob

  broker amqps://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#
  directory /tmp
  mirror True
  accept .*
  #
  # instead of writing to current working directory, write to /tmp.
  # in /tmp. Mirror: create a hierarchy like the one on the source server.

One can also intersperse *directory* and *accept/reject* directives to build
an arbitrarily different hierarchy from what was on the source data pump.
The configuration file is read from top to bottom, so then sr_subscribe
finds a ''directory'' option setting, only the ''accept'' clauses after
it will cause files to be placed relative to that directory::

$ sr3 edit subscribe/ddi_ninjo_part1.conf 

  broker amqps://ddi.cmc.ec.gc.ca/
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


Performance
-----------

If transfers are going too slowly, the steps are as follows:


Optimize File Selection per Process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Often users specif # as their subtopic, meaning the accept/rejects do all the work. In many cases, users are only interested in a small fraction of the files being published.  For best performance, **Make *subtopic* as specific as possible** to have minimize sending messages that are send by the broker and arrive on the subscriber only to be rejected. (use *log_reject* option to find such products.)

* **Place *reject* statements as early as possible in the configuration**. As rejection saves processing of any later regex's in the configuration.

* **Have few accept/reject clauses**: because it involves a regular expression
  match, accept/reject clauses are expensive, but evaluating a complex
  regex is not much more expensive than a simple one, so it is better to have
  a few complicated ones than many simple ones.  Example::

          accept .*/SR/KWAL.*
          accept .*/SO/KWAL.*

  will run at rougly half the speed (or double the cpu overhead) compared to ::

         accept .*/S[OR]/KWAL.*

* **Use suppress_duplicates**.  In some cases, there is a risk of the same file
  being announced more than once.  Usually clients do not want redundant copies 
  of files transferred.  The *suppress_duplicates* option sets up a cache of 
  checksums of the files which have gone by, and prevents their being processed
  again. 
 
* If you are transferring small files, the built-in transfer processing is quite
  good, but **if there are large files** in the mix, then oflloading to a C 
  binary is going to go faster. **Use plugins such as accel_wget, accel_sftp, 
  accel_cp** (for local files.) These plugins have threshold settings so that
  the optimial python transer methods are still used for files smaller than the
  threshold.

* **increasing prefetch** can reduce the average latency (being amortised over
  the number of messages prefetched.) It can improve performance over long 
  distances or in high message rates within an data centre.

* If you control the origin of a product stream, and the consumers will want a
  very large proportion of the products announced, and the products are small
  (a few K at most), then consider combining use of v03 with inlining for 
  optimal transfer of small files.  Note, if you have a wide variety of users
  who all want different data sets, inlining can be counter-productive. This
  will also result in larger messages and mean much higher load on the broker.
  It may optimize a few specific cases, while slowing the broker down overall.


Use Instances
~~~~~~~~~~~~~

Once you have optimized what a single subscriber can do, if it is not fast enough, 
then use the *instances* option to have more processes participate in the 
processing.  Having 10 or 20 instances is not a problem at all.  The maximum 
number of instances that will increase performance will plateau at some point
that varies depending on latency to broker, how fast the instances are at processing
each file, the prefetch in use, etc...  One has to experiment.

Examining instance logs, if they seem to be waiting for messages for a long time,
not actually doing any transfer, then one might have reached queue saturation.
This often happens at around 40 to 75 instances. Rabbitmq manages a single queue
with a single CPU, and there is a limit to how many messages a queue can process
in a given unit of time.

If the queue becomes saturated, then we need to partition the subscriptions
into multiple configurations.  Each configuration will have a separate queue,
and the queues will get their own CPU's.  With such partitioning, we have gone
to a hundred or so instances and not seen saturation.  We don't know when we run
out of performance.

We haven't needed to scale the broker itself yet.


High Performance Duplicate Suppression
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One caveat to the use of *instances* is that *suppress_duplicates* is ineffective
as the different occurrences of the same file will not be received by the same 
instance, and so with n instances, roughly n-1/n duplicates will slip through. 

In order to properly suppress duplicate file announcements in data streams 
that need multiple instances, one uses winnowing with *post_exchange_split*.
This option sends data to multiple post exchanges based on the data checksum,
so that all duplicate files will be routed to the same winnow process.
Each winnow process runs the normal duplicate suppression used in single instances,
since all files with the same checksum end up with the same winnow, it works.
The winnow processes then post to the exchange used by the real processing 
pools.

Why is high performance duplicate suppresion a good thing? Because the 
availability model of Sarracenia is to have individual application stacks
blindly produce redudant copies of products. It requires no application
adjustment from single node to participating in a cluster.  Sarracenia
selects the first result we receive for forwarding. This avoids any sort 
of quorum protocol, a source if great complexity in high availability 
schemes, and by measuring based on output, minimizes the potential for
systems to appear up, when not actually being completely functional. The 
applications do not need to know that there is another stack producing the same
products, which simplifies them as well.

 
Plugins
-------

Default file processing is often fine, but there are also pre-built customizations that
can be used to change processing done by components. The list of pre-built plugins is
in a 'plugins' directory wherever the package is installed (viewable with *sr_subscribe list*)
sample output::

 $ sr_subscribe list
   
   packaged plugins: ( /usr/lib/python3/dist-packages/sarra/plugins ) 
            __pycache__     destfn_sample.py       download_cp.py       download_dd.py 
        download_scp.py     download_wget.py          file_age.py        file_check.py 
            file_log.py       file_rxpipe.py        file_total.py          hb_cache.py 
              hb_log.py         hb_memory.py          hb_pulse.py         html_page.py 
            line_log.py         line_mode.py         msg_2http.py        msg_2local.py 
      msg_2localfile.py     msg_auditflow.py     msg_by_source.py       msg_by_user.py 
           msg_delay.py        msg_delete.py      msg_download.py          msg_dump.py 
          msg_fdelay.py msg_filter_wmo2msc.py  msg_from_cluster.py     msg_hour_tree.py 
             msg_log.py     msg_print_lag.py   msg_rename4jicc.py    msg_rename_dmf.py 
   msg_rename_whatfn.py       msg_renamer.py msg_replace_new_dir.py          msg_save.py 
        msg_skip_old.py        msg_speedo.py msg_sundew_pxroute.py    msg_test_retry.py 
     msg_to_clusters.py         msg_total.py        part_check.py  part_clamav_scan.py 
          poll_pulse.py       poll_script.py    post_hour_tree.py          post_log.py 
      post_long_flow.py     post_override.py   post_rate_limit.py        post_total.py 
           watch_log.py 
   configuration examples: ( /usr/lib/python3/dist-packages/sarra/examples/subscribe ) 
               all.conf     all_but_cap.conf            amis.conf            aqhi.conf 
               cap.conf      cclean_f91.conf       cdnld_f21.conf       cfile_f44.conf 
          citypage.conf           clean.conf       clean_f90.conf            cmml.conf 
   cscn22_bulletins.conf         ftp_f70.conf            gdps.conf         ninjo-a.conf 
             q_f71.conf           radar.conf            rdps.conf            swob.conf 
             t_f30.conf      u_sftp_f60.conf 
   
   user plugins: ( /home/peter/.config/sr3/plugins ) 
           destfn_am.py         destfn_nz.py       msg_tarpush.py 
   
   general: ( /home/peter/.config/sr3 ) 
             admin.conf     credentials.conf         default.conf
   
   user configurations: ( /home/peter/.config/sr3/subscribe )
        cclean_f91.conf       cdnld_f21.conf       cfile_f44.conf       clean_f90.conf 
           ftp_f70.conf           q_f71.conf           t_f30.conf      u_sftp_f60.conf 
   
 $ 

For all plugins, the prefix indicates how the plugin is to be used: a file\_ plugin is
to be used with *on_file*, *Msg\_* plugins are to be used with on_message, etc...
When plugins have options, the options must be placed before the plugin declaration
in the configuration file. Example::

  msg_total_interval 5
  on_message msg_total

The *msg_total* plugin is invoked whenever a message is received, and the *msg_total_interval*
option, used by that plugin, has been set to 5. To learn more: *sr_subscribe list msg_total.py*

Plugins are all written in python, and users can create their own and place them in ~/.config/sr3/plugins. 
For information on creating new custom plugins, see The `Sarracenia Programming Guide <../Contribution/Development.rst>`_  


To recap:

* To view the plugins currently available on the system  *sr_subscribe list plugins*
* To view the contents of a plugin: *sr_subscribe list <plugin>*
* The beginning of the plugin describes its function and settings
* Plugins can have option settings, just like built-in ones
* To set them, place the options in the configuration file before the plugin call itself
* To make your own new plugin: *sr3 edit subscribe/<plugin>.py*


file_rxpipe
-----------

The file_rxpipe plugin for sr_subscribe makes all the instances write the names 
of files downloaded to a named pipe. Setting this up required two lines in 
an sr_subscribe configuration file::

$ sr3 edit subscribe/swob 

  broker amqps://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#

  file_rxpipe_name /home/peter/test/.rxpipe
  on_file file_rxpipe
  directory /tmp
  mirror True
  accept .*
  # rxpipe is a builtin on_file plugin which writes the name of the file received to
  # a pipe named '.rxpipe' in the current working directory.

With the *on_file* option, one can specify a processing option such as rxpipe.  
With rxpipe, every time a file transfer has completed and is ready for 
post-processing, its name is written to the linux pipe (named .rxpipe) in the 
current working directory.  

.. NOTE::
   In the case where a large number of sr_subscribe instances are working
   On the same configuration, there is slight probability that notifications
   may corrupt one another in the named pipe.  

   **FIXME** We should probably verify whether this probability is negligeable or not.
   



Anti-Virus Scanning
-------------------

Another example of easy use of a plugin is to achieve anti-virus scanning.
Assuming that ClamAV is installed, as well as the python3-pyclamd
package, then one can add the following to an sr_subscribe 
configuration file::

  broker amqps://dd.weather.gc.ca
  on_part part_clamav_scan.py
  subtopic observations.swob-ml.#
  accept .*

so that each file downloaded (or each part of the file if it is large),
is to be AV scanned. Sample run::

$ sr_subscribe --reset foreground ../dd_swob.conf 
  clam_scan on_part plugin initialized
  clam_scan on_part plugin initialized
  2016-05-07 18:01:15,007 [INFO] sr_subscribe start
  2016-05-07 18:01:15,007 [INFO] sr_subscribe run
  2016-05-07 18:01:15,007 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2016-05-07 18:01:15,137 [INFO] Binding queue q_anonymous.sr_subscribe.dd_swob.13118484.63321617 with key v02.post.observations.swob-ml.# from exchange xpublic on broker amqps://anonymous@dd.weather.gc.ca/
  2016-05-07 18:01:15,846 [INFO] Received notice  20160507220115.632 http://dd3.weather.gc.ca/ observations/swob-ml/20160507/CYYR/2016-05-07-2200-CYYR-MAN-swob.xml
  2016-05-07 18:01:15,911 [INFO] 201 Downloaded : v02.report.observations.swob-ml.20160507.CYYR 20160507220115.632 http://dd3.weather.gc.ca/ observations/swob-ml/20160507/CYYR/2016-05-07-2200-CYYR-MAN-swob.xml 201 blacklab anonymous 0.258438 parts=1,4349,1,0,0 sum=d,399e3d9119821a30d480eeee41fe7749 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=./2016-05-07-2200-CYYR-MAN-swob.xml message=Downloaded 
  2016-05-07 18:01:15,913 [INFO] part_clamav_scan took 0.00153089 seconds, no viruses in ./2016-05-07-2200-CYYR-MAN-swob.xml
  2016-05-07 18:01:17,544 [INFO] Received notice  20160507220117.437 http://dd3.weather.gc.ca/ observations/swob-ml/20160507/CVFS/2016-05-07-2200-CVFS-AUTO-swob.xml
  2016-05-07 18:01:17,607 [INFO] 201 Downloaded : v02.report.observations.swob-ml.20160507.CVFS 20160507220117.437 http://dd3.weather.gc.ca/ observations/swob-ml/20160507/CVFS/2016-05-07-2200-CVFS-AUTO-swob.xml 201 blacklab anonymous 0.151982 parts=1,7174,1,0,0 sum=d,a8b14bd2fa8923fcdb90494f3c5f34a8 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=./2016-05-07-2200-CVFS-AUTO-swob.xml message=Downloaded 
  

Logging and Debugging
---------------------

As sr3 components usually run as a daemon (unless invoked in *foreground* mode)
one normally examines its log file to find out how processing is going.  When only
a single instance is running, one can view the log of the running process like so::

   sr3 log subscribe/*myconfig*

FIXME: not implemented properly. normally use "foreground" command instead.

Where *myconfig* is the name of the running configuration. Log files
are placed as per the XDG Open Directory Specification. There will be a log file
for each *instance* (download process) of an sr_subscribe process running the myflow configuration::

   in linux: ~/.cache/sarra/log/sr_subscribe_myflow_01.log

One can override placement on linux by setting the XDG_CACHE_HOME environment variable, as
per: `XDG Open Directory Specification <https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.html>`_
Log files can be very large for high volume configurations, so the logging is very configurable.

To begin with, one can select the logging level throughout the entire application using
logLevel, and logReject:

- debug
   Setting option debug is identical to use  **logLevel debug**

- logLevel ( default: info )
   The level of logging as expressed by python's logging. Possible values are :  critical, error, info, warning, debug.

- log_reject <True|False> ( default: False )
   print a log message when *rejecting* messages (choosing not to download the corresponding files)

   The rejection messages also indicate the reason for the rejection.

At the end of the day (at midnight), these logs are rotated automatically by
the components, and the old log gets a date suffix. The directory in which
the logs are stored can be overridden by the **log** option, the number of
rotated logs to keep are set by the **logrotate** parameter. The oldest log
file is deleted when the maximum number of logs has been reach and this
continues for each rotation. An interval takes a duration of the interval and
it may takes a time unit suffix, such as 'd\|D' for days, 'h\|H' for hours,
or 'm\|M' for minutes. If no unit is provided logs will rotate at midnight.
Here are some settings for log file management:

- log <dir> ( default: ~/.cache/sarra/log ) (on Linux)
   The directory to store log files in.

- statehost <False|True> ( default: False )
   In large data centres, the home directory can be shared among thousands of
   nodes. Statehost adds the node name after the cache directory to make it
   unique to each node. So each node has it's own statefiles and logs.
   example, on a node named goofy,  ~/.cache/sarra/log/ becomes ~/.cache/sarra/goofy/log.

- logrotate <max_logs> ( default: 5 , alias: lr_backupCount)
   Maximum number of logs archived.

- logrotate_interval <duration>[<time_unit>] ( default: 1, alias: lr_interval)
   The duration of the interval with an optional time unit (ie 5m, 2h, 3d)

- permLog ( default: 0600 )
   The permission bits to set on log files.



flowcb/log.py Debug Tuning
~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to application-options, there is a flowcb that is used by default for logging, which
has additional options:

- logMessageDump  (default: off) boolean flag
  If set, all fields of a message are printed, at each event, rather than just a url/path reference.

- logEvents ( default after_accept,after_work,on_housekeeping )
   emit standard log messages at the given points in message processing.
   other values: on_start, on_stop, post, gather, ... etc...

etc... One can also modify the provided plugins, or write new ones to completely change the logging.


moth Debug Tuning
~~~~~~~~~~~~~~~~~

Turning on logLevel to debug on the entire application often results in inordinately large log files.
By default the Messages Organized into Topic Hierarchies (Moth) parent class for the messaging protocols,
ignores the application-wide debug option.  To enable debugging output from these classes, there
are additional settings.

One can explicitly set the debug option specifically for the messaging protocol class::

    set sarracenia.moth.amqp.AMQP.logLevel debug
    set sarracenia.moth.mqtt.MQTT.logLevel debug

will make the messaging layer very verbose.
Sometimes during interoperability testing, one must see the raw messages, before decoding by moth classes::

    messageDebugDump

Either or both of these options will make very large logs, and are best used judiciously.



  
Speedo Metrics
--------------
  
Activating the speedo plugin lets one understand how much bandwidth
and how many messages per second a given set of selection criteria
result in::
  
  broker amqps://dd.weather.gc.ca
  on_message msg_speedo
  subtopic observations.swob-ml.#
  accept .*

  
Gives lines in the log like so::

$ sr_subscribe --reset foreground ../dd_swob.conf 
  2016-05-07 18:05:52,097 [INFO] sr_subscribe start
  2016-05-07 18:05:52,097 [INFO] sr_subscribe run
  2016-05-07 18:05:52,097 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2016-05-07 18:05:52,231 [INFO] Binding queue q_anonymous.sr_subscribe.dd_swob.13118484.63321617 with key v02.post.observations.swob-ml.# from exchange xpublic on broker amqps://anonymous@dd.weather.gc.ca/
  2016-05-07 18:05:57,228 [INFO] speedo:   2 messages received:  0.39 msg/s, 2.6K bytes/s, lag: 0.26 s
  
  
  
Partial File Updates
--------------------

When files are large, they are divided into parts. Each part is transferred
separately by sr_sarracenia. So when a large file is updated, new part
notifications (posts) are created. sr_subscribe will check if the file on 
disk matches the new part by checksumming the local data and comparing
that to the post. If they do not match, then the new part of the file
will be downloaded.


Redundant File Reception
------------------------

In environments where high reliability is required, multiple servers
are often configured to provide services. The Sarracenia approach to
high availability is ´Active-Active´ in that all sources are online
and producing data in parallel. Each source publishes data,
and consumers obtain it from the first source that makes it available,
using checksums to determine whether the given datum has been obtained
or not.

This filtering requires implementation of a local dataless pump with 
sr_winnow. See the Administrator Guide for more information.

Web Proxies
-----------

The best method of working with web proxies is to put the following
in the default.conf::

   declare env HTTP_PROXY http://yourproxy.com
   declare env HTTPS_PROXY http://yourproxy.com

Putting in default.conf ensures that all subscribers will use
the proxy, not just a single configuration. 




More Information
----------------

The `sr_subscribe(1) <../Reference/sr3.1.rst#subscribe>`_ is the definitive source of reference
information for configuration options. For additional information,
consult: `Sarracenia Documentation <../Reference/sr3.1.rst#documentation>`_


