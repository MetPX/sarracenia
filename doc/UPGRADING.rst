
---------------
 UPGRADE GUIDE
---------------

This file documents changes in behaviour to provide guidance to those upgrading 
from a previous version.  To upgrade across several versions, one needs to start
at the version after the one installed, and heed all notifications for interim
versions.  While configuration language stability is an important 
goal, on occasion changes cannot be avoided. This file does not document new 
features, but only changes that cause concern during upgrades.  The notices 
take the form:

**CHANGE**
   indicates where configurations files must be changed to get the same behviour as prior to release.

**ACTION** 
   Indicates a maintenance activity required as part of an upgrade process.

**BUG**
  indicates a bug serious to indicate that deployment of this version is not recommended.

*NOTICE*
  a behaviour change that will be noticeable during upgrade, but is no cause for concern.

*SHOULD*
  indicate recommended interventions that are recommended, but not mandatory. If prescribed activity is not done,
  the consequence is either a configuration line that has no effect (wasteful) or the application
  may generate messages.  
   
Installation Instructions
-------------------------

`Installation Guide <Install.html>`_



git origin/master branch
------------------------

*NOTICE*: added heartbeat_memory to default plugins, so components periodically restart when leaking.
*NOTICE*: fixed bug sr_post/sr_watch does not apply *events* option (posts all events regardless.)

2.17.12a1
---------

**BUG**: sr_post/sr_watch does not apply *events* option (posts all events regardless.)

*CHANGE*: accept_unmatch now always honoured. Formerly was set by presence/absence of
accept/reject clauses. Now, by default, a file with no accept/reject clauses will 
reject all files in subscribe and sender configurations, and accept all files in all 
other components (post, poll, sarra, shovel, winnow)  For Subscribe and sender 
configuration that have no accept and or reject clauses, one must add

*accept_unmatch*

to the end of the configuration file to have it behave the same as prior versions.


*NOTICE*: Generally fixes to recover when operations do not complete.  Pulse & timers.


2.17.11a3
---------

**BUG**: sr_post sometimes requires -p (-path) option before file names, where it didn't before.

*NOTICE*: fix for message bug in 11a2. 

*NOTICE*: now prefers amqplib (reverted from preference for pika in 11a1 and 2.) use_pika yes to force usage.

*NOTICE*: sr_watch/sr_post/sr_poll now merged, so sr_watch start will now post whole tree, rather than just differences.
Use of *suppress_duplicates* now encouraged with sr_watch.

*NOTICE*: no other changes...


2.17.11a2
---------

**BUGS**: ugly log message from syntax error in where:
Message: '%s does not have vip=%s, is sleeping'
Arguments: (('sr_winnow', '192.168.xx.yy'),)
shows up when using VIP. fills log with garbage.

*NOTICE*: bugfixes only. No changes needed vs. 11a1.


2.17.11a1
---------

**BUGS**: ugly log message from syntax error in where:
Message: '%s does not have vip=%s, is sleeping'
Arguments: (('sr_winnow', '192.168.xx.yy'),)
shows up when using VIP. fills log with garbage. 


*SHOULD*: change document_root -> base_dir (same for post_ variations.) The code still
understands the old values, but you will see a warning message advising you to change it.

*SHOULD*: change ${PDR} -> ${PBD} to mirror above change. There will be no visible
effect of this, but at some future release, PDR will be dropped.

*SHOULD*: URL option to post_base_url option.  will still understand old values, but 
warning will result.

*SHOULD*: use post_ versions in sr_post, so now it is post_base_url, post_base_dir, 
post_exchange Again, code still understands previous settings, but will warn.
  
*NOTICE*: now prefers to use pika library if available, but falls back to amqplib 
library available on older OS's.  amqplib will be deprecated over time.


2.17.10a3
---------

**BUGS**: switched to using pika for amqp library, which isn't available < ubuntu 16.04.
    do not install on systems where pika not available.

**CHANGE**: sr_sender now includes by default: on_message msg_2localfile, so that change
from previous versions @ 2.17.10 no longer required.

**ACTION**: must run sr_audit --reset --users foreground to correct permissions, since it was broken in previous release.  

Many issues resolved closer to usable.


2.17.10a2
---------

**BUGS**: Do not install this version. result of major refactor only used for deployment testing.

strip behaviour bug may be restored, that might solve the send issue.


2.17.10a1
---------

**BUGS**: Do not install this version. result of major refactor only used for deployment testing.
          many small issues, a bit numerous to list.

**CHANGE**:  All sr_sender configurations require plugin to read from local files. Please Add::

  on_message msg_2localfile
  
Failure to do so will result in *The file to send is not local* message, and send will fail.


**CHANGE**:  default *expire* setting was 10080 (in mins) which means expire after a week.  Now it is 5 minutes.
**It will also result data loss**, by dropping messages should the default be used in cases where the old value
was expected.  A disconnection of more than 5 minutes will cause the queue to be erased.  To configure what was previously 
the default behaviour, use setting::

       *expire 1W*

failure to do so, when connecting to configurations with older pumps versions  may result in warning messages about 
mismatched properties when starting up an existing client. 

**CHANGE**: expire and/or message_ttl settings now in seconds.  To get previous behaviour, append to the value m or M for minutes::

        old: *expire 240*      equivalent to new:  *expire 240M*
        old: "message_ttl 480* equivalent to new:  *message_ttl 480M*
        old: logdays 5        equivalent to new:  *logdays 5d*

**CHANGE**: in sr_sarra, processing messages on initial ingest must have in their config changed::

       **REPLACE**

       *mirror false*
       *source_from_exchange true*
       *[perhaps some accept/reject sequence]*

       **FOR THIS**

       *mirror true*
       *source_from_exchange true*
       *directory ${PDR}/${YYYYMMDD}/${SOURCE}*
       *[same accept/reject sequence if any]*

PDR means post_document_root... if not provided, its value is the same as document_root.
Any message without a source will be fixed with a value starting with the exchange if
xs_source_*, the option source or the broker username of the originating message. When a message comes
from a source, the option **source_from_exchange true** must be set to make sure to set the message's
headers[source] and headers[from_cluster] to the proper value.


**NOTICE**: cache state file format changed and are mutually unintelligible between versions.  
During upgrade, old cache file will be ignored.  This may cause some files to be accepted a second time.
*FIXME*  work-arounds? 

**ACTION**: must run sr_audit --reset --users foreground to correct permissions, since it was broken in previous release.   



2.17.08
-------

**BUG**: avoid this version to administer pumps because of bug 88: sr_audit creates report routing queues 
even when report_daemons is off, they fill up with messages (since they are never emptied.) This can cause havoc.
If report_daemons is true, then there is no issue.  Also no problem for clients. 

**ACTION**: (must run sr_audit --users foreground to correct permissions.)
users now have permission to create exchanges.  
if corrections not updated on broker, warning messages about exchange declaration failures will occur.

*SHOULD*: remove all *declare exchange* statements in configuration files, though they are harmless.
configurations declare broker side resources (exchanges and queues) by *setup* action.  The resources can be freed 
with the *cleanup* action.  Formerly creation and deletion of exchanges was an administrator activity.

*SHOULD*: cluster routing logic removed ( *cluster*, *gateway_for*, and *cluster_aliases* ) these options are now ignored.
If relying on these options to restrict distribution (no known cases), that will stop working.
cluster propagation restriction to be implemented by plugins at a future release.
should remove all these options from configuration files.

*SHOULD*: should remove all *sftp://*  url lines from credentials.conf files. Configuration of sftp should be done
via openssh configuration, and credential file only used as a last resort.  Harmless if they remain, however.



2.17.07
-------


**CHANGE**: sr_sender *mirror* has been repaired.  if no setting present, then it will now mirror.
to preserve previous behavior, add to configuration::

       mirror off

*NOTICE*: switch from traditional init-style ordering to systemd style -->  action comes before configuration.
was::

      sr_subscriber myconfig start --> sr_subscriber start myconfig 

software issues warning message about the change, but old callup still supported.


*NOTICE*: heartbeat log messages will appear every five minutes in logs, by default, to differentiate no activity
from a hung process.

 
2.17.06
-------

**CHANGE**: Review/Modify all plugins, as file variables of sender and subscriber converged.
   on_msg plugin variable for file naming for subscribers (sr_subscribe,sarra,shovel,winnow) changed.  Replace::

      self.msg.local_file --> self.msg.new_dir and self.msg.new_file

   on_msg plugin variable for file naming for senders now same as for subscribers.  Replace::

      self.remote_file --> self.msg.new_dir and self.msg.new_file

**CHANGE**: by default, the modification time of files is now restored on delivery.  To restore previous behaviour::

      preserve_time off

If preserve_time is on (now default) and a message is received, then it will be rejected if the mtime of
the new file is not newer than the one of the existing file.

**CHANGE**: by default, the permission bits of files is now restored on delivery.  To restore previous behaviour::

      preserve_mode off



2.17.02
-------

*NOTICE*: sr_watch re-implementation. now supports symlinks, multiple traversal methods, etc...
many behaviour improvements. FIXME: ?

**CHANGE**: plugins are now stackable. formerly, when two plugin specifications were given, the newer one
would replace the previous one.  Now both plugins will be executed in the order encountered.
 


