==========
 MIGRATION
==========

-------------------------------------------
Sundew sender migration to sarracenia (PXATX)
-------------------------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite

.. contents::

DESCRIPTION
===========

This document was written right after my presentation of August 8th.
It will basically be a summary of what was said for the sundew sender
migration part of it.

The scripts used in the presentation use routing tables, sender 
configuration, logs and a dump of sarra database of products.

I used a similar setup with similar tools on my desktop. All of this,
is to be taken as a suggestion or a startup. I have heavily used some
of it during the conversion of sundew pull to sarra poll-sarra pairs.

Most if the time for pxatx senders, I would only use pxsender_2_sarra.sh.
It converts sundew-sender to a sarra-sender in a dummy fashion... no extra.
From the converted config, I would simply add the migrated polled products
I had just migrated and drop the rest of the sundew sender config.

The sender tools where an entire day of products is presented as messages
to the sarra sender migrated I used 3 times... I simply coded that while
I tried to migrate sundew-sender as part of my migration project.
As porting sundew-sender to sarra showed to be a much greater task than
I expected, I simply drop the idea. And did not use these tools anymore.

Peter wanted me to present my work. The goal is to engage his troup
in the project of migrating the sundew-sender to sarra.

All of these facts must be considered when using the presented tools.
I am not saying THEY ARE the tools to use in order to properly conduct
I am not saying the are reliable enough to be used blindly.
For myself, they would certainly be my starting point, should I be part
of that project.

So you the reader are part of that project now I guess if you read this.
I propose the tools as a start for your own migration. Use them as 
tips, basis, ideas, or tools... make of them what you want...  and
good luck for your journey in this big sundew-sender conversion 
project.

SETUP
=====

Historically, after having poke the several clusters (sundew and sarra)
with tools on data-lb-ops1 (under users px and sarra)... it was so 
annoying that I decided one day to get all the information available
on all the clusters and work from my desktop. I am convinced that it
strikes you as simpler than doing "srl grep" or "pxl grep" in all clusters.
So my tools would work on a local copy of the needed files.

In order to use the scripts provided as is, as a start, you would need
to install the same setup as I was using when developping/using them.
Of course, this is not mandatory, and should you prefer other setups,
you can do so and modify the scripts accordingly... or write you own...

So my setup was::

     mkdir ~/convert

     # and in this directory you place

     ~/convert
     │
     ├── tools
     │   ├── compare.sh
     │   ├── do_this_pull.sh
     │   ├── do_this_sender.sh
     │   ├── pull_2_pollsarra.sh
     │   ├── pxsender_2_sarra.sh
     │   ├── sr_sender_one_day.sh
     │   └── sundew_routing_2_sarra_subtopic.py
     │
     ├── plugins
     │   ├── msg_from_file.py
     │   └── pxSender_log.py
     │
     ├── config
     │   │
     │   ├── pxatx
     │   │   └── etc
     │   │       ├── rx
     │   │       ├── fx
     │   │       ├── scripts
     │   │       ├── trx
     │   │       ├── tx
     │   │       └── ...
     │   │
     │   ├── sundew
     │   │   └── etc
     │   │       ├── rx
     │   │       ├── fx
     │   │       ├── scripts
     │   │       ├── trx
     │   │       ├── tx
     │   │       └── ...
     │   │
     │   └── sarra
     │           ├── cpost
     │           ├── plugins
     │           ├── poll
     │           ├── post
     │           ├── sarra
     │           ├── sender
     │           ├── shovel
     │           └── watch
     │
     ├── log 
     │   │
     │   ├── pxatx
     │   │   └── ...
     │   │
     │   ├── sr_pxatx
     │   │   └── ...
     │   │
     │   ├── ddsr (sarra)
     │   │   ├── px2-ops
     │   │   ├── px3-ops
     │   │   ├── px4-ops
     │   │   ├── px5-ops
     │   │   ├── px6-ops
     │   │   ├── px7-ops
     │   │   └── px8-ops
     │   │
     │   └── sundew
     │       ├── px2-ops
     │       ├── px3-ops
     │       ├── px4-ops
     │       ├── px5-ops
     │       ├── px6-ops
     │       ├── px7-ops
     │       └── px8-ops
     │
     │
     └── data
         └── ddsr.20190804  (sarra /apps/sarra/public_data/20190804 *)


The files found in the tools directory can be taken from the
sarracenia depot on github under ~/sarracania/tools. (If not in the master
they would be found in branch issue199)

For files found in the plugins directory directory can be taken from the 
sarracenia depot on github under ~/sarracania/sarra/plugins. (If not in the
master they would be found in branch issue199)

The config directory is just a straight copy of all the configs 
for each of the clusters... and here **sr_pxatx** means the sarra portion
of pxatx.

For the logs and the data, one would think to have a whole day and so
I would always aim at getting all of "yesterday".  

So one can go on each node and scp "yesterday's log" where the setup is
installed under the proper representing directory.

The creation of data file (ddsr.20190804) was done as follow::

     ssh sarra@data-lb-ops1 '. ./.bash_profile; cd ~/master/saa; srl "cd /apps/sarra/public_data; find 20190804 -type f"' >> ddsr.20190804


On the server where you would to the migration, you need sarracenia of course.
The fact that px1-ops was off the sarra cluster was an opportunity since it
provides the same environment as the targetted cluster. If one such node is
not available when you a migration to a cluster (in fact I would be tempted
to say any migration of any kinds) ... I recommand you to have such a node
available.

SUNDEW SENDER CONVERSION PROCESS
================================

I cannot say for sure that all my tools get everything straight.
Should you find better ways or modifications to do, dont hesitate.

For now, should you use them out of the box, here is how I would
proceed with the them.

Under ~/convert, create your own working/migrating directory... ex.::

    mkdir SENDERS
    cd    SENDERS

Select one config that you would like to start working with.
(Perhaps to start, the senders with the smallest number of delivery
would be a good start... dont do them all, keep some for the other
team member to sharp their teeth too).

To get ready, make sure that the plugins under ~/convert/plugins are
sarra-wise available::
 
     cp ~/convert/plugins/* ~/.config/sarra/plugins

And perhaps adjust the path to be able to call the tools easily::
 
     export PATH=.~/convert/tools:$PATH

Ok now, convert that sender... Here I suppose as in the presentation
that it is accessdepot-iml.conf for simplicity (or remainder)::

     # convert the sender place infos in directory ACCESSDEPOT_IML
     # The script will show an estimated of time to finish
     # that can be hours depending on the routing tables and sender configs

     do_this_sender.sh accessdepot-iml

     # access the resulting directory and have a look at the info
     # gathered by the script

     cd ACCESSDEPOT_IML
     vi INFO_accessdepot-iml

     # make sure the credential were extracted, ready for sarra
     ls credentials
     cat credentials

     # go check/edit/modify the configs and includes
     cd sender
     vi accessdepot-iml.conf

     # You think your sarra config/includes for this sender is ok
     # give it a try, run a whole day
     # *** CATCH in script sr_sender_one_day.sh
     # *** it appends to your sender config lines like
     # *** msg_file /local/home/sarra/convert/data/ddsr.20190804
     # *** THIS IS DATA DEPENDANT AND NEEDS TO BE TAKEN INTO ACCOUNT

     sr_sender_one_day.sh sender/accessdepot-iml.conf

     # check it out if this sender is done...
     # It will stop when all products of the data file are processed

     tail -f ~/.cache/sarra/log/sr_accessdepot-iml_01.log

     # When done compare the logs of the sundew sender
     # the sender's log have to be of the same date as the data product file

     compare.sh accessdepot-iml

     # IF the compare says the exact same number of products
     # and there are no product to be rejected or missing 
     # the sender is ready. 

     # If not... (and that is probably in most cases)
     # If there are no missing product... only some to be
     # rejected, would try restricting your accept/reject
     # and  you would loop doing the following until resolution
     #
     # 1- Fix the sender again
     # 2- Run through a whole day again
     # 3- check when finished
     # 4- compare
     #
     # a looping sequence like this :

     vi sender/accessdepot-iml.conf
     sr_sender_one_day.sh sender/accessdepot-iml.conf
     tail -f ~/.cache/sarra/log/sr_sender_accessdepot-iml_01.log
     compare.sh accessdepot-iml

     # missing products are more problematic
     # needs further investigation and perhaps
     # the addition of processes, or products to sarra
     

This was done, as is, in today's presentation. I cannot say it enough...
as I mentionned, I have not done many of these sundew senders conversions
by gaving it a day of products... The few I did were enough to leave
sundew-senders migration alone and focus on pxatx-sundew. I would certainly
start from there should I be you. But again, this is a personal choice...
Your ideas and methods being as good as mine.

When using tools, one can trigger them on say 5 sender configs and
have more work ahead. The experience gathered during these 5 migrations
can be ported into the tools hoping to get better results for the next 5
and so on. So always have 5 in the oven. It is important to run batches
since some may take hours to be processed. 

If no change is done to the sarra db layout and products, the files in
the setup are accurate enought to pursue the migration.

On the opposite, changes to the sarra db layout and product additions,
removals or whatever changes, requieres the files "sarra db for yesterday"
and "sundew logs for yesterday"  to be updated... Or else, the results from
the tools will not represent the current state of things.

Have fun   :-)


