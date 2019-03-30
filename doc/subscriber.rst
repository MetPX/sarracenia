
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

When viewed in a git repository, use git to understand versioning.
This section is used when printing a document, where as part of
creation of a printable document the appropriate values will
be extracted from git.

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
data into the pump network.  Data can cross many pumps on its
way to the visible ones::

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

You should be able to list the available configurations with *sr_subscribe list* ::

  blacklab% sr_subscribe list plugins
  
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
  
  user plugins: ( /home/peter/.config/sarra/plugins ) 
          destfn_am.py         destfn_nz.py       msg_tarpush.py 
  
  blacklab% sr_subscribe list

  general: ( /home/peter/.config/sarra ) 
            admin.conf     credentials.conf         default.conf
  
  user configurations: ( /home/peter/.config/sarra/subscribe )
       cclean_f91.conf       cdnld_f21.conf       cfile_f44.conf       clean_f90.conf 
          ftp_f70.conf           q_f71.conf           t_f30.conf      u_sftp_f60.conf 
  
  blacklab% 


Each section of the listing shows the contents of the directory shown in parentheses.  One can
just edit the files in the directories directly, or modify them otherwise, as the list command is
only for convenience.  There are four sections:

 * system plugins:  python routines one can call from subscriber configuration. 
 * user plugins:    user written python routines of the same type.
 * general:  configuration files that are referenced by other configuration files.
 * user configurations: these are the ones set by the user and most often of interest.

To view a particular configuration, give sr_subscribe list the file as an argument:: 

    blacklab% sr_subscribe list msg_log.py

.. code:: python

    #!/usr/bin/python3
    
    """
      the default on_msg handler for sr_log.
      prints a simple notice.
    
    """
    
    class Msg_Log(object): 
    
        def __init__(self,parent):
            parent.logger.debug("msg_log initialized")
              
        def on_message(self,parent):
            msg = parent.msg
            parent.logger.info("msg_log received: %s %s%s topic=%s lag=%g %s" % \
               tuple( msg.notice.split()[0:3] + [ msg.topic, msg.get_elapse(), msg.hdrstr ] ) )
            return True
    
   
    msg_log = Msg_Log(self) # required: Make instance of class whose name is lower case version of class.
    
    self.on_message = msg_log.on_message  # assign self.on_message to corresponding function.
    
    blacklab% 



A First Example
---------------

The tree described above is the *conventional* one found on most data pumps, 
but the original data pump, dd.weather.gc.ca, pre-dates the convention.
Regardless of the tree, one can browse it to find the data of interest. 
On dd.weather.gc.ca one can browse to http://dd.weather.gc.ca/observations/swob-ml/
to find the tree of all the weather observations in SWOB format
recently issued by any Environment Canada forecast office.


First initialize the credentials storage file::

  blacklab% sr_subscribe edit credentials.conf

  amqps://anonymous:anonymous@dd.weather.gc.ca

The *edit* command just calls up the user's configured editor
on the file to be created in the right place.  To create
a configuration to obtain the swob files::

  blacklab% sr_subscribe edit swob.conf

  broker amqps://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#
  accept .*

  blacklab% 
  blacklab% sr_subscribe status swob
  2017-12-14 06:54:54,010 [INFO] sr_subscribe swob 0001 is stopped
  blacklab% 

NOTE:

  The above will write the files in the current working directory, and they will arrive quickly.
  It might be better to make a dedicated directory and use the *directory* option to place the files there.
  for example:  
  mkdir /tmp/swob_downloads
  *directory /tmp/swob_downloads*

On the first line, *broker* indicates where to connect to get the
stream of notifications. The term *broker* is taken from AMQP (http://www.amqp.org), 
which is the protocol used to transfer the notifications.
The notifications that will be received all have *topics* that correspond 
to their URL.  

Now start up a subscriber (assume the config file was called dd_swob.conf)::

  blacklab% sr_subscribe start dd_swob
  2015-12-03 06:53:35,268 [INFO] user_config = 0 ../dd_swob.conf
  2015-12-03 06:53:35,269 [INFO] instances 1 
  2015-12-03 06:53:35,270 [INFO] sr subscribe dd swob 0001 started

One can monitor activity with the *log* command::

  blacklab% sr_subscribe log dd_swob
  
  2015-12-03 06:53:35,635 [INFO] Binding queue q_anonymous.21096474.62787751 with key v02.post.observations.swob-ml.# to exchange xpublic on broker amqps://anonymous@dd.weather.gc.ca/
  2015-12-03 17:32:01,834 [INFO] user_config = 1 ../dd_swob.conf
  2015-12-03 17:32:01,835 [INFO] sr_subscribe start
  2015-12-03 17:32:01,835 [INFO] sr_subscribe run
  2015-12-03 17:32:01,835 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2015-12-03 17:32:01,835 [INFO] AMQP  input :    exchange(xpublic) topic(v02.post.observations.swob-ml.#)
  2015-12-03 17:32:01,835 [INFO] AMQP  output:    exchange(xs_anonymous) topic(v02.report.#)
  
  2015-12-03 17:32:08,191 [INFO] Binding queue q_anonymous.21096474.62787751 with key v02.post.observations.swob-ml.# to exchange xpublic on broker amqps://anonymous@dd.weather.gc.ca/
  blacklab% 
  
The sr_subscribe will get the notification and download the file into the 
current working directory. As the start up is normal, that means the 
authentication information was good. Passwords are stored in 
the ~/.config/sarra/credentials.conf file. The format is just a complete 
url on each line. An example of that would be::
  
  amqps://anonymous:anonymous@dd.weather.gc.ca/

The password is located after the :, and before the @ in the URL as is standard
practice. This credentials.conf file should be private (linux octal permissions: 0600).  
Also, if a .conf file is placed in the ~/.config/sarra/subscribe directory, then 
sr_subscribe will find it without having to give the full path.

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

Note that this message is not always a failure, as sr_subscribe retries 
a few times before giving up. In any event, after a few minutes, here is what 
the current directory looks like::

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


Server Side Resources Allocated for Subscribers
-----------------------------------------------

Every configuration results in corresponding resources being declared on the broker.
When changing *subtopic* or *queue* settings, or when one expects to not use 
a configuration for an extended period of time, it is best to::

  sr_subscribe cleanup swob.conf

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
directory: ~/.config/sarra/subscribe/ For example, if there are two files in 
that directory: CMC.conf and NWS.conf, one could then run:: 

  peter@idefix:~/test$ sr_subscribe start CMC.conf 
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

  peter@idefix:~/test$ sr start
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

will start up some sr_subscribe processes as configured by CMC.conf and others 
to match NWS.conf. Sr stop will also do what you would expect. As will sr status.  
Note that there are 5 sr_subscribe processes start with the CMC 
configuration and 3 NWS ones. These are *instances* and share the same 
download queue. 


High Priority Delivery
----------------------

While the Sarracenia protocol does not provide explicit prioritization, the use
of multiple queues provides similar benefits. Each configuration results
in a queue declaraton on the server side. Group products at like priority into
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

  blacklab% sr_subscribe edit swob

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

  blacklab% sr_subscribe edit swob

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

  blacklab% sr_subscribe edit ddi_ninjo_part1.conf 

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


Plugins
-------

Default file processing is often fine, but there are also pre-built customizations that
can be used to change processing done by components. The list of pre-built plugins is
in a 'plugins' directory wherever the package is installed (viewable with *sr_subscribe list*)
sample output::

   blacklab% sr_subscribe list
   
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
   
   user plugins: ( /home/peter/.config/sarra/plugins ) 
           destfn_am.py         destfn_nz.py       msg_tarpush.py 
   
   general: ( /home/peter/.config/sarra ) 
             admin.conf     credentials.conf         default.conf
   
   user configurations: ( /home/peter/.config/sarra/subscribe )
        cclean_f91.conf       cdnld_f21.conf       cfile_f44.conf       clean_f90.conf 
           ftp_f70.conf           q_f71.conf           t_f30.conf      u_sftp_f60.conf 
   
   blacklab% 

For all plugins, the prefix indicates how the plugin is to be used: a file\_ plugin is
to be used with *on_file*, *Msg\_* plugins are to be used with on_message, etc...
When plugins have options, the options must be placed before the plugin declaration
in the configuration file. Example::

  msg_total_interval 5
  on_message msg_total

The *msg_total* plugin is invoked whenever a message is received, and the *msg_total_interval*
option, used by that plugin, has been set to 5. To learn more: *sr_subscribe list msg_total.py*

Plugins are all written in python, and users can create their own and place them in ~/.config/sarra/plugins. 
For information on creating new custom plugins, see The `Sarracenia Programming Guide <Prog.rst>`_  


To recap:

* To view the plugins currently available on the system  *sr_subscribe list plugins*
* To view the contents of a plugin: *sr_subscribe list <plugin>*
* The beginning of the plugin describes its function and settings
* Plugins can have option settings, just like built-in ones
* To set them, place the options in the configuration file before the plugin call itself
* To make your own new plugin: *sr_subscribe edit <plugin>.py*


file_rxpipe
-----------

The file_rxpipe plugin for sr_subscribe makes all the instances write the names 
of files downloaded to a named pipe. Setting this up required two lines in 
an sr_subscribe configuration file::

  blacklab% sr_subscribe edit swob 

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

  blacklab% sr_subscribe --reset foreground ../dd_swob.conf 
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

  blacklab% sr_subscribe --reset foreground ../dd_swob.conf 
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

More Information
----------------

The `sr_subscribe(1) <sr_subscribe.1.rst>`_ is the definitive source of reference
information for configuration options. For additional information,
consult: `Sarracenia Documentation <sr_subscribe.1.rst#documentation>`_


