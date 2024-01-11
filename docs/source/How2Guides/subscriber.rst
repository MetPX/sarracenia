
==================
 Subscriber Guide
==================

------------------------------------------------
Receiving Data from a MetPX-Sarracenia Data Pump
------------------------------------------------


Revision Record
---------------


:version: |release|
:date: |today|


Introduction
------------

A Sarracenia data pump is a web server with notifications
for subscribers to know, quickly, when new data has arrived.  
To find out what data is already available on a pump, 
view the tree with a web browser.  
For simple immediate needs, one can download data using the 
browser itself, or a standard tool such as wget.

The usual intent is to automatically download the data 
wanted to a directory on a subscriber
machine where other software can process it.  Please note:

- the tool is entirely command line driven (there is no GUI) More accurately, it is mostly configuration file driven.
  most of the *interface* involves using a text editor to modify configuration files.
- while written to be compatible with other environments, the focus is on Linux usage. 
- the tool can be used as either an end-user tool, or a system-wide transfer engine.
  This guide is focused on the end-user case.  
- All documentation of the package is available 
  at https://metpx.github.io/sarracenia

While Sarracenia can work with any web tree, or any URL 
that sources choose to post, there is a conventional layout, for example at:

   http://hpfx.collab.science.gc.ca

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
per source. A Source in Sarracenia is an account used to inject
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

The original Environment and Climate Change Canada data mart, is
one "source" in this sense, showing up on hpfx as WXO-DD, or the same
tree being available at the root of::

  https://dd.weather.gc.ca


once down to the viewing the content from a given source,
products are organized in a way defined by the source::


   Icon  Name                    Last modified      Size  Description
   [TXT] about_dd_apropos.txt    2021-05-17 13:23  1.0K  
   [DIR] air_quality/            2020-12-10 14:47    -   
   [DIR] alerts/                 2022-07-13 12:00    -   
   [DIR] analysis/               2022-07-13 13:17    -   
   [DIR] barometry/              2022-03-22 22:00    -   
   [DIR] bulletins/              2022-07-13 13:19    -   
   [DIR] citypage_weather/       2022-07-13 13:21    -   
   [DIR] climate/                2020-09-03 16:30    -   
   [DIR] doc/                    2022-09-28 20:00    -   
   [DIR] ensemble/               2022-07-13 13:34    -   
   [DIR] hydrometric/            2021-01-14 14:12    -   
   [DIR] marine_weather/         2020-12-15 14:51    -   
   [DIR] meteocode/              2022-07-13 14:01    -   
   [DIR] model_gdsps/            2021-12-01 21:41    -   
   [DIR] model_gdwps/            2021-12-01 16:50    -   

Directories below that level are related to the date being sought.


One can run sr3 to download selected products from Data pumps like these.
The configuration files are a few lines of configuration, and sr3
includes some examples.


To list the available configurations with *sr3 list* ::

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

AMIS, the Canadian AES (Atmospheric Environment Service) Meteorological Information Service, was a satellite 
broadcast system for weather data in the 1980's. It is a continuous stream of text messages (originally at 4800 bps!) 
and each message is limited to 14000 bytes. The service was transitioned to an internet streaming feed in the early 2000's,
and the streaming version is still fed to those interested in air and maritime navigation across the country.

One can download a continuous feed of such traditional weather bulletins from the original datamart using the subscribe/dd_amis.conf 
configuration example::

    $ sr3 add subscribe/dd_amis.conf
    add: 2021-01-26 01:13:54,047 [INFO] sarracenia.sr add copying: /usr/lib/python3/dist-packages/sarracenia/examples/subscribe/dd_amis.conf to /home/peter/.config/sr3/subscribe/dd_amis.conf 

Now files in `.config/` can be used directly::
 
    $ sr3 list
    User Configurations: (from: /home/peter/.config/sr3 )
    subscribe/dd_amis.conf           admin.conf                       credentials.conf                 default.conf                     
    logs are in: /home/peter/.cache/sr3/log


To view a configuration, give it to `sr3 list` as an argument:: 

    $ sr3 list subscribe/dd_amis.conf
    # this is a feed of wmo bulletin (a set called AMIS in the old times)
    
    broker amqps://dd.weather.gc.ca/
    
    # instances: number of downloading processes to run at once.  defaults to 1. Not enough for this case
    instances 5
    
    # expire, in operational use, should be longer than longest expected interruption
    expire 10m
    
    subtopic bulletins.alphanumeric.#
    
    directory /tmp/dd_amis
    accept .*

Then it can be run interactively *sr3 foreground subscribe/dd_amis* or as a service
with *sr3 start subscribe/dd_amis*  in both cases, files will be downloaded from
dd.weather.gc.ca into the local machine's /tmp/dd_amis directory.

more:

* `CLI Introduction (Jupyter Notebook) <../Tutorials/1_CLI_introduction.html>`_
* `Setup a Remote Subscriber <../Tutorials/Setup_a_remote_subscriber.html>`_
* `Options in the configuration file <../Reference/sr3_options.7.rst>`_

Server Side Resources Allocated for Subscribers
-----------------------------------------------

Every configuration results in corresponding resources being declared on the broker,
whose lifetime is controlled by the *expire* setting. The default *expire* is set
to 300 seconds to avoid cluttering up servers with small experiments.  Set *expire*
the the value that makes the most sense for your application (long enough to cover
outages you may experience.) In a configuration file, something like::

  expire 3h

might be appropriate. When changing *subtopic* or *queue* settings, or when one 
expects to not use a configuration for an extended period of time, it is best to::

  sr3 cleanup subscribe/swob.conf

which will de-allocate the queue (and its bindings) on the server.

Why? Whenever a subscriber is started, a queue is created on the data pump, with 
the topic bindings set by the configuration file. If the subscriber is stopped, 
the queue keeps getting notification messages as defined by subtopic selection, and when the 
subscriber starts up again, the queued notification messages are forwarded to the client. 
So when the *subtopic* option is changed, since it is already defined on the 
server, one ends up adding a binding rather than replacing it.  For example,
if one has a subtopic that contains SATELLITE, and then stops the subscriber, 
edit the file and now the topic contains only RADAR, when the subscriber is 
restarted, not only will all the queued satellite files be sent to the consumer, 
but the RADAR is added to the bindings, rather than replacing them, so the 
subscriber will get both the SATELLITE and RADAR data even though the configuration 
no longer contains the former.

Also, if one is experimenting, and a queue is to be stopped for a very long 
time, it may accumulate a large number of notification messages. The total number of notification messages 
on a data pump has an effect on the pump performance for all users. It is therefore 
advisable to have the pump de-allocate resources when they will not be needed 
for an extended periods, or when experimenting with different settings.


Working with Multiple Configurations
-------------------------------------

Place all configuration files, with the .conf suffix, in a standard 
directory: ~/.config/sr3/subscribe/ For example, if there are two files in 
that directory: dd_amis.conf and hpfx_amis.conf, one could then run:: 

    fractal% sr3 start subscribe/dd_amis.conf
    starting:.( 5 ) Done

    fractal%

to start the CMC downloading configuration. One can use by
using the sr3 command to start/stop multiple configurations at once. 
The sr3 command will go through the default directories and start up 
all the configurations it finds::

    fractal% sr3 status
    status: 
    Component/Config                         State             Run  Miss   Exp Retry
    ----------------                         -----             ---  ----   --- -----
    subscribe/dd_amis                        stopped             0     0     0     0
    subscribe/hpfx_amis                      stopped             0     0     0     0
          total running configs:   0 ( processes: 0 missing: 0 stray: 0 )
    fractal% sr3 edit subscribe/hpfx_amis
    
    fractal% sr3 start
    starting:.( 10 ) Done
    
    fractal% sr3 status
    status: 
    Component/Config                         State             Run  Miss   Exp Retry
    ----------------                         -----             ---  ----   --- -----
    subscribe/dd_amis                        running             5     0     5     0
    subscribe/hpfx_amis                      running             5     0     5     0
          total running configs:   2 ( processes: 10 missing: 0 stray: 0 )
    fractal% 
    

will start up some sr3 processes as configured by CMC.conf and others 
to match hpfx_amis.conf. Sr3 stop will also do what you would expect. As will sr3 status.  
Note that there are 5 sr_subscribe processes start with the CMC 
configuration and 3 NWS ones. These are *instances* and share the same 
download queue. 

more:

* `Command line Guide <../Explanation/CommandLineGuide.html>`_
* `Sr3 Manual page <../Reference/sr3.1.html>`_


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

https://github.com/MetPX/sarracenia/blob/main/sarracenia/examples/subscribe/ddc_cap-xml.conf::

    broker amqps://dd.weather.gc.ca/
    topicPrefix v02.post

    #expiration du file d´attende sur le serveur. doit excèder la durée maximale 
    #     de panne qu´on veut tolérer sans perte. (1d un jour?)
    expire 10m
    subtopic alerts.cap.#

    mirror

    directory ${HOME}/datamartclone

https://github.com/MetPX/sarracenia/blob/main/sarracenia/examples/subscribe/ddc_normal.conf::

   broker amqps://dd.weather.gc.ca/
   topicPrefix v02.post

   subtopic #

   # reject hi priority data captured by other configuration.
   reject .*alerts/cap.*

   #expire, needs to be longer than the longest expected interruption in service.
   expire 10m

   mirror
   directory ${HOME}/datamartclone


Where you want the mirror of the data mart to start at $(HOME)/datamartclone (presumably there is a web
server configured do display that directory.) Likely, the *ddc_normal* configuration 
will experience a lot of queueing, as there is a lot of data to download. The *ddc_hipri.conf* is 
only subscribed to weather warnings in Common Alerting Protocol format, so there will be
little to no queueing for that data.




Refining Selection
------------------

.. warning:: 
  **FIXME**: Make a picture, with a: 

  - broker at one end, and the subtopic apply there.  
  - client at the other end, and the accept/reject apply there.

Pick *subtopics* ( which are applied on the broker with no notification message downloads ) to narrow
the number of notification messages that traverse the network to get to the sarracenia client processes.
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
  acceptUnmatched off

In the above example, ninjo-station catalog data is placed in the
catalog_common/in directory, rather than in the point data 
hierarchy used to store the data that matches the first three
accept clauses.  

.. Note::

  Note that .* in the subtopic directive, where
  it means ´match any one topic´ (ie. no period characters allowed in 
  topic names) has a different meaning than it does in an accept 
  clause, where it means match any string.
  
  Yes, this is confusing. No, it cannot be helped.  

more:

* `Downloading using the Command Line (Jupyter Notebook) <../Tutorials/1_CLI_introduction.html>`_


Data Loss
---------


Outage
~~~~~~

The *expire* determines how long the data pump will hold onto your queued subscription,
after a disconnection. The setting needs to be set longer than the longest outage your 
feed needs to survive without data loss.


Too slow, Queue Too Large
~~~~~~~~~~~~~~~~~~~~~~~~~ 

The performance of a feed
is important, as, serving the internet, a one client´s slow download affects all the other ones,
and a few slow clients can overwhelm a data pump.  Often there are server policies in place
to prevent mis-configured (i.e. too slow) subscriptions from resulting in very long queues.


When the queue becomes too long, the data pump may start discarding messages, and
the subscriber will perceive that as data loss.


To identify slow downloads, examine the lag in the download log. For example, create
a sample subscriber like so::

 fractal% sr3 list ie

 Sample Configurations: (from: /home/peter/Sarracenia/sr3/sarracenia/examples )
 cpump/cno_trouble_f00.inc        flow/amserver.conf               flow/poll.inc                    flow/post.inc                    flow/report.inc                  flow/sarra.inc                   
 flow/sender.inc                  flow/shovel.inc                  flow/subscribe.inc               flow/watch.inc                   flow/winnow.inc                  poll/airnow.conf                 
 poll/aws-nexrad.conf             poll/mail.conf                   poll/nasa-mls-nrt.conf           poll/noaa.conf                   poll/soapshc.conf                poll/usgs.conf                   
 post/WMO_mesh_post.conf          sarra/wmo_mesh.conf              sender/am_send.conf              sender/ec2collab.conf            sender/pitcher_push.conf         shovel/no_trouble_f00.inc        
 subscribe/aws-nexrad.conf        subscribe/dd_2mqtt.conf          subscribe/dd_all.conf            subscribe/dd_amis.conf           subscribe/dd_aqhi.conf           subscribe/dd_cacn_bulletins.conf 
 subscribe/dd_citypage.conf       subscribe/dd_cmml.conf           subscribe/dd_gdps.conf           subscribe/dd_radar.conf          subscribe/dd_rdps.conf           subscribe/dd_swob.conf           
 subscribe/ddc_cap-xml.conf       subscribe/ddc_normal.conf        subscribe/downloademail.conf     subscribe/ec_ninjo-a.conf        subscribe/hpfxWIS2DownloadAll.conf subscribe/hpfx_amis.conf         
 subscribe/hpfx_citypage.conf     subscribe/local_sub.conf         subscribe/ping.conf              subscribe/pitcher_pull.conf      subscribe/sci2ec.conf            subscribe/subnoaa.conf           
 subscribe/subsoapshc.conf        subscribe/subusgs.conf           sender/am_send.conf              sender/ec2collab.conf            sender/pitcher_push.conf         watch/master.conf                
 watch/pitcher_client.conf        watch/pitcher_server.conf        watch/sci2ec.conf                
 fractal% 

pick one ane add it local configuration::

 fractal% sr3 add subscribe/hpfx_amis.conf
 missing state for subscribe/hpfx_amis
 add: 2022-12-07 12:39:15,513 3286889 [INFO] root add matched existing ['subscribe/hpfx_amis']
 2022-12-07 12:39:15,513 3286889 [ERROR] root add nothing specified to add
 fractal%

run it in foreground for a few seconds and stop it::

    fractal% sr3 foreground subscribe/hpfx_amis
    .2022-12-07 12:39:37,977 [INFO] 3286919 sarracenia.flow loadCallbacks flowCallback plugins to load: ['sarracenia.flowcb.gather.message.Message', 'sarracenia.flowcb.retry.Retry', 'sarracenia.flowcb.housekeeping.resources.Resources', 'log']
    2022-12-07 12:39:38,194 [INFO] 3286919 sarracenia.moth.amqp __getSetup queue declared q_anonymous_subscribe.hpfx_amis.67711727.37906289 (as: amqps://anonymous@hpfx.collab.science.gc.ca/) 
    2022-12-07 12:39:38,194 [INFO] 3286919 sarracenia.moth.amqp __getSetup binding q_anonymous_subscribe.hpfx_amis.67711727.37906289 with v02.post.*.WXO-DD.bulletins.alphanumeric.# to xpublic (as: amqps://anonymous@hpfx.collab.science.gc.ca/)
    2022-12-07 12:39:38,226 [INFO] 3286919 sarracenia.flowcb.log __init__ subscribe initialized with: {'post', 'on_housekeeping', 'after_accept', 'after_work', 'after_post'}
    2022-12-07 12:39:38,226 [INFO] 3286919 sarracenia.flow run callbacks loaded: ['sarracenia.flowcb.gather.message.Message', 'sarracenia.flowcb.retry.Retry', 'sarracenia.flowcb.housekeeping.resources.Resources', 'log']
    2022-12-07 12:39:38,226 [INFO] 3286919 sarracenia.flow run pid: 3286919 subscribe/hpfx_amis instance: 0
    2022-12-07 12:39:38,241 [INFO] 3286919 sarracenia.flow run now active on vip None
    2022-12-07 12:39:42,564 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 2.20 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/SR/KWAL/17/SRWA20_KWAL_071739___7440 
    2022-12-07 12:39:42,564 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 3.17 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/SR/KWAL/17/SRMN70_KWAL_071739___39755 
    2022-12-07 12:39:42,564 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 2.17 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/SR/KWAL/17/SRCN40_KWAL_071739___132 
    2022-12-07 12:39:42,564 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 2.17 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/SR/KWAL/17/SRMN20_KWAL_071739___19368 
    2022-12-07 12:39:42,564 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 1.19 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/SX/KWAL/17/SXAK50_KWAL_071739___15077 
    2022-12-07 12:39:42,957 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/SRWA20_KWAL_071739___7440 
    2022-12-07 12:39:42,957 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/SRMN70_KWAL_071739___39755 
    2022-12-07 12:39:42,957 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/SRCN40_KWAL_071739___132 
    2022-12-07 12:39:42,957 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/SRMN20_KWAL_071739___19368 
    fractal% sr3 foreground subscribe/hpfx_amis
    .2022-12-07 12:39:37,977 [INFO] 3286919 sarracenia.flow loadCallbacks flowCallback plugins to load: ['sarracenia.flowcb.gather.message.Message', 'sarracenia.flowcb.retry.Retry', 'sarracenia.flowcb.housekeeping.resources.Resources', 'log']
    2022-12-07 12:39:38,194 [INFO] 3286919 sarracenia.moth.amqp __getSetup queue declared q_anonymous_subscribe.hpfx_amis.67711727.37906289 (as: amqps://anonymous@hpfx.collab.science.gc.ca/) 
    2022-12-07 12:39:38,194 [INFO] 3286919 sarracenia.moth.amqp __getSetup binding q_anonymous_subscribe.hpfx_amis.67711727.37906289 with v02.post.*.WXO-DD.bulletins.alphanumeric.# to xpublic (as: amqps://anonymous@hpfx.collab.science.gc.ca/)
    2022-12-07 12:39:38,226 [INFO] 3286919 sarracenia.flowcb.log __init__ subscribe initialized with: {'post', 'on_housekeeping', 'after_accept', 'after_work', 'after_post'}
    2022-12-07 12:39:38,226 [INFO] 3286919 sarracenia.flow run callbacks loaded: ['sarracenia.flowcb.gather.message.Message', 'sarracenia.flowcb.retry.Retry', 'sarracenia.flowcb.housekeeping.resources.Resources', 'log']
    2022-12-07 12:39:38,226 [INFO] 3286919 sarracenia.flow run pid: 3286919 subscribe/hpfx_amis instance: 0
    2022-12-07 12:39:38,241 [INFO] 3286919 sarracenia.flow run now active on vip None
    2022-12-07 12:39:42,564 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 2.20 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/SR/KWAL/17/SRWA20_KWAL_071739___7440 
    2022-12-07 12:39:42,564 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 3.17 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/SR/KWAL/17/SRMN70_KWAL_071739___39755 
    2022-12-07 12:39:42,564 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 2.17 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/SR/KWAL/17/SRCN40_KWAL_071739___132 
    2022-12-07 12:39:42,564 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 2.17 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/SR/KWAL/17/SRMN20_KWAL_071739___19368 
    2022-12-07 12:39:42,564 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 1.19 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/SX/KWAL/17/SXAK50_KWAL_071739___15077 
    2022-12-07 12:39:42,957 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/SRWA20_KWAL_071739___7440 
    2022-12-07 12:39:42,957 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/SRMN70_KWAL_071739___39755 
    2022-12-07 12:39:42,957 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/SRCN40_KWAL_071739___132 
    2022-12-07 12:39:42,957 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/SRMN20_KWAL_071739___19368 
    2022-12-07 12:39:42,957 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/SXAK50_KWAL_071739___15077 
    2022-12-07 12:39:42,957 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/SXAK50_KWAL_071739___15077 
    2022-12-07 12:39:43,227 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 0.71 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/SR/KWAL/17/SRCN40_KWAL_071739___40860 
    2022-12-07 12:39:43,227 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 0.71 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/SA/KNKA/17/SAAK41_KNKA_071739___36105 
    2022-12-07 12:39:43,227 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 0.71 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/SR/KWAL/17/SRCN40_KWAL_071739___19641 
    2022-12-07 12:39:43,457 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/SRCN40_KWAL_071739___40860 
    2022-12-07 12:39:43,457 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/SAAK41_KNKA_071739___36105 
    2022-12-07 12:39:43,457 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/SRCN40_KWAL_071739___19641 
    2022-12-07 12:39:43,924 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 0.40 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/SR/KWAL/17/SRCN40_KWAL_071739___44806 
    2022-12-07 12:39:43,924 [INFO] 3286919 sarracenia.flowcb.log after_accept accepted: (lag: 0.40 ) https://hpfx.collab.science.gc.ca /20221207/WXO-DD/bulletins/alphanumeric/20221207/UA/CWAO/17/UANT01_CWAO_071739___24012 
    2022-12-07 12:39:44,098 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/SRCN40_KWAL_071739___44806 
    2022-12-07 12:39:44,098 [INFO] 3286919 sarracenia.flowcb.log after_work downloaded ok: /tmp/hpfx_amis/UANT01_CWAO_071739___24012 

The **lag:** numbers reported in the foreground display indicate how old the data is (in seconds, based on the time it was added to the network
by the source. If you see that lag grow unreasonably, your subscription has a performance problem.


Performance
-----------


There are many aspects of Performance that we won't go into here.

more:

Minimizing the time after a file has been delivered, and before it is picked up by the next hop:

* `Knowing when to pick up a file <../Explanation/DetectFileReady.html>`_ 
* `Knowing when a file is delivered <../Explanation/FileCompletion.html>`_ 

Getting file changes noticed rapidly, filtering frequent file re-writes, scheduling copies:

* `Case Study: HPC Mirroring <../Explanation/History/HPC_Mirroring_Use_Case.html>`_
* C implementation: `sr3_cpost <../Reference/sr3_post.1.rst>`_ `sr3_cpump <../Reference/sr3_cpump.1.rst>`_
  used mostly when python isn't easy to get working.

The most common desire when performance is raised is speed up their downloads.
the steps are as follows:


Optimize File Selection per Process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Often users specif # as their subtopic, meaning the accept/rejects do all the work. In many cases, users are only interested in a small fraction of the files being published.  For best performance, **Make *subtopic* as specific as possible** to have minimize sending notification messages that are send by the broker and arrive on the subscriber only to be rejected. (use *log_reject* option to find such products.)

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
  the number of notification messages prefetched.) It can improve performance over long 
  distances or in high notification message rates within an data centre.

* If you control the origin of a product stream, and the consumers will want a
  very large proportion of the products announced, and the products are small
  (a few K at most), then consider combining use of v03 with inlining for 
  optimal transfer of small files.  Note, if you have a wide variety of users
  who all want different data sets, inlining can be counter-productive. This
  will also result in larger notification messages and mean much higher load on the broker.
  It may optimize a few specific cases, while slowing the broker down overall.


Use Instances
~~~~~~~~~~~~~

Once you have optimized what a single subscriber can do, if it is not fast enough, 
then use the *instances* option to have more processes participate in the 
processing.  Having 10 or 20 instances is not a problem at all.  The maximum 
number of instances that will increase performance will plateau at some point
that varies depending on latency to broker, how fast the instances are at processing
each file, the prefetch in use, etc...  One has to experiment.

Examining instance logs, if they seem to be waiting for notification messages for a long time,
not actually doing any transfer, then one might have reached queue saturation.
This often happens at around 40 to 75 instances. Rabbitmq manages a single queue
with a single CPU, and there is a limit to how many notification messages a queue can process
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

In order to properly suppress duplicate file notification messages in data streams 
that need multiple instances, one uses winnowing with *post_exchangeSplit*.
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

more:

* `Duplicate Suppression <../Explanation/DuplicateSuppression.rst>`_
 
Plugins
-------

Default file processing is often fine, but there are also pre-built customizations that
can be used to change processing done by components. The list of pre-built plugins is
in a 'plugins' directory wherever the package is installed (viewable with *sr_subscribe list*)
sample output::

   $ sr3 list help
   blacklab% sr3 list help
   Valid things to list: examples,eg,ie flow_callback,flowcb,fcb v2plugins,v2p

   $ sr3 list fcb
      
      
   Provided callback classes: ( /home/peter/Sarracenia/sr3/sarracenia ) 
   flowcb/accept/delete.py          flowcb/accept/downloadbaseurl.py 
   flowcb/accept/hourtree.py        flowcb/accept/httptohttps.py     
   flowcb/accept/longflow.py        flowcb/accept/posthourtree.py    
   flowcb/accept/postoverride.py    flowcb/accept/printlag.py        
   flowcb/accept/rename4jicc.py     flowcb/accept/renamedmf.py       
   flowcb/accept/renamewhatfn.py    flowcb/accept/save.py            
   flowcb/accept/speedo.py          flowcb/accept/sundewpxroute.py   
   flowcb/accept/testretry.py       flowcb/accept/toclusters.py      
   flowcb/accept/tohttp.py          flowcb/accept/tolocal.py         
   flowcb/accept/tolocalfile.py     flowcb/accept/wmotypesuffix.py   
   flowcb/filter/deleteflowfiles.py flowcb/filter/fdelay.py          
   flowcb/filter/pclean_f90.py      flowcb/filter/pclean_f92.py      
   flowcb/filter/wmo2msc.py         flowcb/gather/file.py            
   flowcb/gather/message.py         flowcb/housekeeping/hk_police_queues.py 
   flowcb/housekeeping/resources.py flowcb/line_log.py               
   flowcb/log.py                    flowcb/mdelaylatest.py           
   flowcb/nodupe/data.py            flowcb/nodupe/name.py            
   flowcb/pclean.py                 flowcb/poll/airnow.py            
   flowcb/poll/mail.py              flowcb/poll/nasa_mls_nrt.py      
   flowcb/poll/nexrad.py            flowcb/poll/noaa_hydrometric.py  
   flowcb/poll/usgs.py              flowcb/post/message.py           
   flowcb/retry.py                  flowcb/sample.py                 
   flowcb/script.py                 flowcb/send/email.py             
   flowcb/shiftdir2baseurl.py       flowcb/v2wrapper.py              
   flowcb/wistree.py                flowcb/work/delete.py            
   flowcb/work/rxpipe.py            
   $ 

One can browse built-in plugins via the `FlowCallback Reference <../Reference/flowcb.html>`_
Plugins are written in python, and users can create their own and place them in ~/.config/sr3/plugins,
or anywhere in the PYTHONPATH (available for *import* )

Another way view documentation and source code of any plugin, the directory containing 
them is listed on the first line of the *list* directive above, and the rest of the path 
to the plugin is in the listing, so::

   vi /home/peter/Sarracenia/sr3/sarracenia/flowcb/nodupe/name.py

will start the vi editor to view the source of the plugin in question, which
also contains its documentation. Another way to view documentation, in addition 
to the above, is the standard pythonic way::

    fractal% python3
    Python 3.10.6 (main, Nov  2 2022, 18:53:38) [GCC 11.3.0] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import sarracenia.flowcb.run
    >>> help(sarracenia.flowcb.run)

Of importing the class in question, and then invoking python help() on the class.


Plugins can be included in flow configurations by adding 'flow_callback' lines like::

   callback work.rxpipe

which appends the given callback to the list of callbacks to be invoked.
There is also::

   callback_prepend work.rxpipe

which will prepend this callback to the list, so that is is called before the
non prepended ones. 


To recap:

* To view the plugins currently available on the system  *sr3 list fcb*
* To view the contents of a plugin, browse the `FlowCallback Reference <../Reference/flowcb.html>`_ use,
  or use a text editor, or import in a python interpreter, and use python help()
* Plugins can have option settings, just like built-in ones. They are described 
  in each plugin's documentation.
* To set them, place the options in the configuration file before the plugin call itself
* To make your own plugins, start with `Writing Flow Callbacks <FlowCallbacks.rst>`_, and
  put them in ~/.config/sr3/plugins, or anythere in your python environment's search path.

more:

* `Sarracenia General Concepts <../Explanation/Concepts.html>`_
* `using callbacks from command line (Jupyter Notebook) <../Tutorials/2_CLI_with_flowcb_demo.html>`_

Even more:
* `Sarracenia Programming Guide <../Explanation/SarraPluginDev.html>`_
* `Writing Flow Callbacks <FlowCallbacks.rst>`_  



file_rxpipe
-----------

The file_rxpipe plugin that writes the names of files downloaded to a named pipe. 
Setting this up required two lines in an flow configuration file::

$ mknod /home/peter/test/.rxpipe p
$ sr3 edit subscribe/swob 

  broker amqps://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#

  rxpipe_name /home/peter/test/.rxpipe

  callback work.rxpipe

  directory /tmp
  mirror True
  accept .*
  # rxpipe is a builtin after_work plugin which writes the name of the file received to
  # a pipe named '.rxpipe' in the current working directory.


With rxpipe, every time a file transfer has completed and is ready for 
post-processing, its name is written to the linux pipe (named .rxpipe.) 

.. NOTE::
   In the case where a large number of subscribe instances are working
   On the same configuration, there is slight probability that notifications
   may corrupt one another in the named pipe.  

   **FIXME** We should probably verify whether this probability is negligeable or not.
   



Anti-Virus Scanning
-------------------

Another example of easy use of a plugin is to achieve anti-virus scanning.
Assuming that ClamAV-daemon is installed, as well as the python3-pyclamd
package, then one can add the following to a subscriber
configuration file::

  broker amqps://dd.weather.gc.ca
  topicPredix v02.post
  batch 1
  callback clamav
  subtopic observations.swob-ml.#
  accept .*

So that each file downloaded is AV scanned. Sample run::

    $ sr3 foreground subscribe//dd_swob.conf 

    blacklab% sr3 foreground subscribe/dd_swob
    2022-03-12 18:47:18,137 [INFO] 29823 sarracenia.flow loadCallbacks plugins to load: ['sarracenia.flowcb.gather.message.Message', 'sarracenia.flowcb.retry.Retry', 'sarracenia.flowcb.housekeeping.resources.Resources', 'sarracenia.flowcb.clamav.Clamav', 'sarracenia.flowcb.log.Log']
    clam_scan on_part plugin initialized
    2022-03-12 18:47:22,865 [INFO] 29823 sarracenia.flowcb.log __init__ subscribe initialized with: {'after_work', 'on_housekeeping', 'after_accept'}
    2022-03-12 18:47:22,866 [INFO] 29823 sarracenia.flow run options:
    _Config__admin=amqp://bunnymaster:Easter1@localhost/ None True True False False None None, _Config__broker=amqps://anonymous:anonymous@dd.weather.gc.ca/ None True True False False None None,
    _Config__post_broker=None, accel_threshold=0, acceptSizeWrong=False, acceptUnmatched=False, action='foreground', attempts=3, auto_delete=False, baseDir=None, baseUrl_relPath=False, batch=100, bind=True,
    bindings=[('xpublic', ['v02', 'post'], ['observations.swob-ml.#'])], bufsize=1048576, bytes_per_second=None, bytes_ps=0, cfg_run_dir='/home/peter/.cache/sr3/subscribe/dd_swob', config='dd_swob',
    configurations=['subscribe/dd_swob'], currentDir=None, dangerWillRobinson=False, debug=False, declare=True, declared_exchanges=['xpublic', 'xcvan01'],
   .
   .
   .
    022-03-12 18:47:22,867 [INFO] 29823 sarracenia.flow run pid: 29823 subscribe/dd_swob instance: 0
    2022-03-12 18:47:30,019 [INFO] 29823 sarracenia.flowcb.log after_accept accepted: (lag: 140.22 ) https://dd4.weather.gc.ca /observations/swob-ml/20220312/COGI/2022-03-12-2344-COGI-AUTO-minute-swob.xml 
   .
   .
   .  # good entries...

    22-03-12 19:00:55,347 [INFO] 30992 sarracenia.flowcb.clamav after_work scanning: /tmp/dd_swob/2022-03-12-2347-CVPX-AUTO-minute-swob.xml
    2022-03-12 19:00:55,353 [INFO] 30992 sarracenia.flowcb.clamav avscan_hit part_clamav_scan took 0.00579023 seconds, no viruses in /tmp/dd_swob/2022-03-12-2347-CVPX-AUTO-minute-swob.xml
    2022-03-12 19:00:55,385 [INFO] 30992 sarracenia.flowcb.log after_accept accepted: (lag: 695.46 ) https://dd4.weather.gc.ca /observations/swob-ml/20220312/COTR/2022-03-12-2348-COTR-AUTO-minute-swob.xml 
    2022-03-12 19:00:55,571 [INFO] 30992 sarracenia.flowcb.clamav after_work scanning: /tmp/dd_swob/2022-03-12-2348-COTR-AUTO-minute-swob.xml
    2022-03-12 19:00:55,596 [INFO] 30992 sarracenia.flowcb.clamav avscan_hit part_clamav_scan took 0.0243611 seconds, no viruses in /tmp/dd_swob/2022-03-12-2348-COTR-AUTO-minute-swob.xml
    2022-03-12 19:00:55,637 [INFO] 30992 sarracenia.flowcb.log after_accept accepted: (lag: 695.71 ) https://dd4.weather.gc.ca /observations/swob-ml/20220312/CWGD/2022-03-12-2348-CWGD-AUTO-minute-swob.xml 
    2022-03-12 19:00:55,844 [INFO] 30992 sarracenia.flowcb.clamav after_work scanning: /tmp/dd_swob/2022-03-12-2348-CWGD-AUTO-minute-swob.xml
  
    .
    .
    . # bad entries.

    2022-03-12 18:50:13,809 [INFO] 30070 sarracenia.flowcb.log after_work downloaded ok: /tmp/dd_swob/2022-03-12-2343-CWJX-AUTO-minute-swob.xml 
    2022-03-12 18:50:13,930 [INFO] 30070 sarracenia.flowcb.log after_accept accepted: (lag: 360.72 ) https://dd4.weather.gc.ca /observations/swob-ml/20220312/CAJT/2022-03-12-2343-CAJT-AUTO-minute-swob.xml 
    2022-03-12 18:50:14,104 [INFO] 30070 sarracenia.flowcb.clamav after_work scanning: /tmp/dd_swob/2022-03-12-2343-CAJT-AUTO-minute-swob.xml
    2022-03-12 18:50:14,105 [ERROR] 30070 sarracenia.flowcb.clamav avscan_hit part_clamav_scan took 0.0003829 not forwarding, virus detected in /tmp/dd_swob/2022-03-12-2343-CAJT-AUTO-minute-swob.xml

    .
    . # every heartbeat interval, a little summary:
    .
    2022-03-12 19:00:55,115 [INFO] 30992 sarracenia.flowcb.clamav on_housekeeping files scanned 121, hits: 5


Logging and Debugging
---------------------

As sr3 components usually run as a daemon (unless invoked in *foreground* mode)
one normally examines its log file to find out how processing is going.  When only
a single instance is running, one can view the log of the running process like so::

   sr3 log subscribe/*myconfig*

FIXME: not implemented properly. normally use "foreground" command instead.

Where *myconfig* is the name of the running configuration. Log files
are placed as per the XDG Open Directory Specification. There will be a log file
for each *instance* (download process) of an flow process running the myflow configuration::

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
   print a log message when *rejecting* notification messages (choosing not to download the corresponding files)

   The rejection messages also indicate the reason for the rejection.

At the end of the day (at midnight), these logs are rotated automatically by
the components, and the old log gets a date suffix. The directory in which
the logs and metrics are stored can be overridden by the **log** option, the 
number of rotated logs to keep are set by the **logRotate** parameter. The 
oldest log file is deleted when the maximum number of logs and metrics has been 
reached and this continues for each rotation. An interval takes a duration of 
the interval and it may takes a time unit suffix, such as 'd\|D' for days, 'h\|H' 
for hours, or 'm\|M' for minutes. If no unit is provided logs will rotate at midnight.
Here are some settings for log file management:

- log <dir> ( default: ~/.cache/sarra/log ) (on Linux)
   The directory to store log files in.

- logMetrics ( default: True ) 
   whether to accumulate multiple metrics files at all.

- statehost <False|True> ( default: False )
   In large data centres, the home directory can be shared among thousands of
   nodes. Statehost adds the node name after the cache directory to make it
   unique to each node. So each node has it's own statefiles and logs.
   example, on a node named goofy,  ~/.cache/sarra/log/ becomes ~/.cache/sarra/goofy/log.

- logRotateCount <max_logs> ( default: 5 , alias: lr_backupCount)
   Maximum number of logs archived.

- logRotateInterval <duration>[<time_unit>] ( default: 1, alias: lr_interval)
   The duration of the interval with an optional time unit (ie 5m, 2h, 3d)

- permLog ( default: 0600 )
   The permission bits to set on log files.



flowcb/log.py Debug Tuning
~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to application-options, there is a flowcb that is used by default for logging, which
has additional options:

- logMessageDump  (default: off) boolean flag
  If set, all fields of a notification message are printed, at each event, rather than just a url/path reference.

- logEvents ( default after_accept,after_work,on_housekeeping )
   emit standard log messages at the given points in message processing.
   other values: on_start, on_stop, post, gather, ... etc...

etc... One can also modify the provided plugins, or write new ones to completely change the logging.

more:

* `Log module <../Reference/flowcb.html#module-sarracenia.flowcb.log>`_


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
Sometimes during interoperability testing, one must see the raw notification messages, before decoding by moth classes::

    messageDebugDump

Either or both of these options will make very large logs, and are best used judiciously.

more:

* `Moth API <../api-documentation.html#module-sarracenia.moth>`_

  
Housekeeping Metrics
--------------------
  
  
Flow Callbacks can implement a on_housekeeping entry point.  This entry point is usually
an opportunity for callbacks to print metrics periodically.  The builtin log and
resource monitoring callbacks, for example, give lines in the log like so::

    2022-03-12 19:00:55,114 [INFO] 30992 sarracenia.flowcb.housekeeping.resources on_housekeeping Current Memory cpu_times: user=1.97 system=0.3
    2022-03-12 19:00:55,115 [INFO] 30992 sarracenia.flowcb.housekeeping.resources on_housekeeping Memory threshold set to: 161.2 MiB
    2022-03-12 19:00:55,115 [INFO] 30992 sarracenia.flowcb.housekeeping.resources on_housekeeping Current Memory usage: 53.7 MiB / 161.2 MiB = 33.33%
    2022-03-12 19:00:55,115 [INFO] 30992 sarracenia.flowcb.clamav on_housekeeping files scanned 121, hits: 0 
    2022-03-12 19:00:55,115 [INFO] 30992 sarracenia.flowcb.log housekeeping_stats messages received: 242, accepted: 121, rejected: 121  rate:    50%
    2022-03-12 19:00:55,115 [INFO] 30992 sarracenia.flowcb.log housekeeping_stats files transferred: 0 bytes: 0 Bytes rate: 0 Bytes/sec
    2022-03-12 19:00:55,115 [INFO] 30992 sarracenia.flowcb.log housekeeping_stats lag: average: 778.91, maximum: 931.06 
  
more:

* `Housekeeping callbacks <../Reference/flowcb.html#module-sarracenia.flowcb.housekeeping>`_
  
  
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

more:

* `Duplicate Suppression <../Explanation/DuplicateSuppression.rst>`_


Web Proxies
-----------

The best method of working with web proxies is to put the following
in the default.conf::

   declare env HTTP_PROXY http://yourproxy.com
   declare env HTTPS_PROXY http://yourproxy.com

Putting in default.conf ensures that all subscribers will use
the proxy, not just a single configuration. 


API Level Access
----------------

Sarracenia version 3 also offers python modules that can be called
from existing python applications.

* `Flow API to replace CLI usage <../Tutorials/3_api_flow_demo.html>`_

The flow API brings in all the option placement and parsing from
Sarracenia, it is a pythonic way of starting up a flow from python itself.

Or one may not want to use the Sarracenia configuration scheme, 
perhaps one just wants to use the message protocol support, for 
that: 

* Subscribing using the (much less complex) Moth API (Jupyter Notebook) `<../Tutorials/4_api_moth_sub_demo.ipynb>`_
* Posting from python code with Moth (Jupyter Notebook) `<../Tutorials/5_api_moth_post_demo.ipynb>`_



More Information
----------------


* The `sr3(1) <../Reference/sr3.1.html>`_ is the definitive source of reference
  information for configuration options. For additional information,
* the main web site: `Sarracenia Documentation <https://metpx.github.io/sarracenia>`_

