
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
   Indicates where configurations files must be changed to get the same behaviour as prior to release.

**ACTION** 
   Indicates a maintenance activity required as part of an upgrade process.

**BUG**
   Indicates a bug serious to indicate that deployment of this version is not recommended.

*NOTICE*
   A behaviour change that will be noticeable during upgrade, but is no cause for concern.

*SHOULD*
   Indicates recommended interventions that are recommended, but not mandatory. If prescribed activity is not done,
   the consequence is either a configuration line that has no effect (wasteful) or the application
   may generate messages.  
   
Installation Instructions
-------------------------

`Installation Guide <Install.rst>`_

git
---

2.19.04b1
---------

*NOTICE*: regression of v03 posting fixed.

2.19.03b6
---------

**BUG**:  regression ... v03 posting stopped working entirely.


2.19.03.b1
----------

*NOTICE*: ubuntu 14.04 & 16.04 regression for python3-amqp fixed.


2.19.02.b2
----------

*CHANGE*: *logrotate* parameter was a duration (how many days to keep daily logs).  It is now
          a count of log files to retain.  *logrotate_interval* is a new option, which accepts a
          duration, to control how often to rotate logs. To maintain compatibility, if a 'd' is 
          after the argument to *logrotate*, it will be ignored, and will be interpreted as a
          simple integer.

*NOTICE*: On ubuntu 14.04 and 16.04, the switch to python3-amqp causes a regression because
          there is a missing API call (*connect*) on the old version of the library included
          with those distributions.

2.19.02.b1
----------

*ACTION*: debian package name changed from *python3-metpx-sarracenia* to *metpx-sarracenia*
          to better match python packaging team guidelines. upgrades will fail, as the
          new package will conflict with the one previously installed.
          one must apt remove python3-metpx-sarracenia prior to installing this version.

*ACTION*: switch AMQP library: python3-amqp replaced python3-amqplib (abandonware library) 
          package dependency means it won´t install automatically over previous version 
          need to apt install, or install the new dependency before you upgrade.

*NOTICE*: On ubuntu 14.04 and 16.04, the switch to python3-amqp causes a regression because
          there is a missing API call (*connect*) on the old version of the library included
          with those distributions.

*NOTICE*: Windows binary installer option available now, much simpler than having to install a
          whole python environment for it.  Can still use any existing python using pip.

*NOTICE*: bug with *remove* introduced in 2.19.01b1 fixed.


2.19.01b1
---------

 **BUG**: the *remove* action sometimes does not work.

*NOTICE*: the format when using -save & -restore has changed to match the `v03 <sr_postv3.7.rst>`_
          payload. Save files created with the new version will not be readable with earlier versions.
          this version can still the old files. (iow: upper compatibility is there, but not downward.)

*CHANGE*: in each message, the attribute name for the time the message was inserted
          into the network is changed from msg.time, to msg.pubtime.
          change of msg.time value will trigger a deprecation warning to be logged.


2.18.09b2
---------

*ACTION*: The recent_files cache file stored in the state directory has change
          encoding for filenames. file names are now encoded as per 
          urllib.parse.quote() routine (for example: space becomes %20)
          it would be advised to --reset (erase the cache file) when upgrading.
        

2.18.08b1
---------

*CHANGE*: sr_subscribe strip, mirror, flatten,  options were formerly global ones.
          Now they are processed in order in the same way as directory options.
          configuration files where these directives appear after accept clauses
          will behave differently. inspection of existing usage indicates that
          users naturally put the accept clauses at the end so it should not
          affect many.
 

upto 2.18.05b4
--------------

Only bug-fixes and improvements, no regressions or changes.


2.18.03b3
---------

*CHANGE*: sr_poll option directory : In some case you might need to get rid of the first '/'.	
                  Previous version had a bug in code that caused it to be removed. This is
                  mostly the case for a protocol that should use a directory in the user's home.

2.18.03b1
---------

*NOTICE*: Just make sure the exchange is declared before any subtopic declarations...
          As they are bound together in the consumer queue and define the messages to receive,
          improper setting may lead to a process that seems to be hung.

2.18.02a1
---------

*CHANGE*: Default broker *dd.weather.gc.ca* removed.  The default caused confusion when configurations
          were absent or invalid, but worked anyways (though not as intended).
          It appears better for usability to make the argument mandatory.

*NOTICE*: OOPS! https download support was missing, no one had noticed.  
          We added it in this release.

2.18.01a5
---------

*NOTICE*: This is likely the last alpha release.  All changes required for feature completeness are done now. 
          No breaking changes in configuration language to be expected for a long time.  
          Stabilizing towards beta.

2.18.01a4
---------

*NOTICE*: Backed out of plugin convention enforcement mentioned in 2.18.01a2.  Now there is a new *plugin*
          option that supports new style, and the old style is left alone.

2.18.01a3
---------

*NOTICE*: New plugin API features disabled on Python < 3.3 (avoid crash on Ubuntu 12.04).

*NOTICE*: Got rid of harmless error message of previous release.


2.18.01a2
---------

*NOTICE*: When using a do_download plugin, a harmless error message is printed on startup:
          [ERROR] sr_config/option 4 Type: <class 'AttributeError'>, Value: 'sr_subscribe' object has no attribute 'do_download_list',  ...
          This error has no effect.

*NOTICE*: Note change to *durable* default from previous version, for transition can specify *durable no* 
          in configuration to use existing queues, and/or --reset to redefine queue with new setting.

*CHANGE*: Plugins convention now enforced.  One must declare a class with some upper case
          characters in the name. Then instantiate the class with a variable that is the all lower case
          version of the class name:

.. code-block:: python

          Class MyPlugin():
              def __init__(self,parent):
                  pass
           
              def on_message(self,parent): 
                  """ prior to this version convention was to use *perform*, but now naming
                       it after it's intended use is preferred. (any name will still work.)
                  """

          myplugin = MyPlugin(self)     
          #prior to this version, myplugin could have any name, now it must be lower case version of class name.
          self.on_message = myplugin.on_message


2.18.01a1
---------

*NOTICE*: All components print their settings on startup.

*NOTICE*: The default for *inflight* was NONE in sr_sender, contrary to what was stated in the documentation and contrary to intent.
          This would cause deliveries using the sender to use the final name without a temporary one being chosen, causing many cases where
          files which weren't complete being picked up when relying on the default configuration.

*NOTICE*: Default prefetch=25 now, was 1. Noticed this was wrong once started printing settings.

*CHANGE*: *inflight* for sender now defaults to '.tmp' when no post_broker is set, and NONE when it is. If this behaviour is undesired,
          one must add *inflight NONE* to the obtain the previous behaviour.
  
*CHANGE*: *durable* default changed from False to True. Existing queues will fail to bind. As transition. 
          All queues should be declared durable.
          For all existing flows, add *durable false* to declaration, and plan migration to durable queue later.


2.17.12a6
---------

*NOTICE*: Heartbeat processing now works correctly.
*NOTICE*: More cases of same bug fixed.

2.17.12a5
---------

*NOTICE*: Found additional cases of 12a2 bug, fixed.


2.17.12a4
---------

*NOTICE*: Fix for 12a2 bug, that caused retries without sleeping. Now it does exponential backoff.


2.17.12a3
---------

*NOTICE*: Added retry_ttl to age files in retry_queue so they eventually age out.

2.17.12a2
---------

**BUG**: sr_sender retry connection no sleep interval, hammers server, fills logs rapidly.

*NOTICE*: Added heartbeat_memory to default plugins, so components periodically restart when leaking.
*NOTICE*: Fixed bug sr_post/sr_watch does not apply *events* option (posts all events regardless).
*NOTICE*: Fixed bug performance regression by switching to 1M byte buffers, and fixed timers.


2.17.12a1
---------

**BUG**: sr_post/sr_watch does not apply *events* option (posts all events regardless).

**BUG**: Performance regression caused by timeouts added changing buffering to use 8K ones.

*CHANGE*: Accept_unmatch now always honoured. Formerly was set by presence/absence of
accept/reject clauses. Now, by default, a file with no accept/reject clauses will 
reject all files in subscribe and sender configurations, and accept all files in all 
other components (post, poll, sarra, shovel, winnow).  For subscribe and sender 
configuration that have no accept and or reject clauses, one must add

*accept_unmatch*

to the end of the configuration file to have it behave the same as prior versions.


*NOTICE*: Generally fixes to recover when operations do not complete.  Pulse & timers.


2.17.11a3
---------

**BUG**: sr_post sometimes requires -p (-path) option before file names, where it didn't before.

*NOTICE*: Fix for message bug in 11a2. 

*NOTICE*: Now prefers amqplib (reverted from preference for pika in 11a1 and 2). Use_pika yes to force usage.

*NOTICE*: sr_watch/sr_post/sr_poll now merged, so sr_watch start will now post whole tree, rather than just differences.
Use of *suppress_duplicates* now encouraged with sr_watch.

*NOTICE*: No other changes...


2.17.11a2
---------

**BUGS**: Ugly log message from syntax error in where:
Message: '%s does not have vip=%s, is sleeping'
Arguments: (('sr_winnow', '192.168.xx.yy'),)
Shows up when using VIP. Fills log with garbage.

*NOTICE*: Bugfixes only. No changes needed vs. 11a1.


2.17.11a1
---------

**BUGS**: Ugly log message from syntax error in where:
Message: '%s does not have vip=%s, is sleeping'
Arguments: (('sr_winnow', '192.168.xx.yy'),)
Shows up when using VIP. Fills log with garbage. 


*SHOULD*: Change document_root -> base_dir (same for post\_ variations.) The code still
understands the old values, but you will see a warning message advising you to change it.

*SHOULD*: Change ${PDR} -> ${PBD} to mirror above change. There will be no visible
effect of this, but at some future release, PDR will be dropped.

*SHOULD*: URL option to post_base_url option.  Will still understand old values, but 
warning will result.

*SHOULD*: Use post\_ versions in sr_post, so now it is post_base_url, post_base_dir, 
post_exchange. Again, code still understands previous settings, but will warn.
  
*NOTICE*: Now prefers to use pika library if available, but falls back to amqplib 
library available on older OS's.  amqplib will be deprecated over time.


2.17.10a3
---------

**BUGS**: Switched to using pika for amqp library, which isn't available < ubuntu 16.04.
    Do not install on systems where pika not available.

**CHANGE**: sr_sender now includes by default: on_message msg_2localfile, so that change
from previous versions @ 2.17.10 no longer required.

**ACTION**: Must run sr_audit --reset --users foreground to correct permissions, since it was broken in previous release.  

Many issues resolved closer to usable.


2.17.10a2
---------

**BUGS**: Do not install this version. Result of major refactor only used for deployment testing.

Strip behaviour bug may be restored, that might solve the send issue.


2.17.10a1
---------

**BUGS**: Do not install this version. Result of major refactor only used for deployment testing.
          Many small issues, a bit numerous to list.

**CHANGE**:  All sr_sender configurations require plugin to read from local files. Please add::

  on_message msg_2localfile
  
Failure to do so will result in *The file to send is not local* message, and send will fail.


**CHANGE**:  Default *expire* setting was 10080 (in mins) which means expire after a week.  Now it is 5 minutes.
**It will also result data loss**, by dropping messages should the default be used in cases where the old value
was expected.  A disconnection of more than 5 minutes will cause the queue to be erased.  To configure what was previously 
the default behaviour, use setting::

       *expire 1W*

Failure to do so, when connecting to configurations with older pumps versions  may result in warning messages about 
mismatched properties when starting up an existing client. 

**CHANGE**: Expire and/or message_ttl settings now in seconds.  To get previous behaviour, append to the value m or M for minutes::

        old: *expire 240*      equivalent to new:  *expire 240M*
        old: "message_ttl 480* equivalent to new:  *message_ttl 480M*
        old: logdays 5        equivalent to new:  *logdays 5d*

**CHANGE**: In sr_sarra, processing messages on initial ingest must have in their config changed::

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
Any message without a source will be fixed with a value starting with the exchange 
xs_source_*, the option source or the broker username of the originating message. When a message comes
from a source, the option **source_from_exchange true** must be set to make sure to set the message's
headers[source] and headers[from_cluster] to the proper value.


**NOTICE**: Cache state file format changed and are mutually unintelligible between versions.  
During upgrade, old cache file will be ignored.  This may cause some files to be accepted a second time.
*FIXME*  work-arounds? 

**ACTION**: Must run sr_audit --reset --users foreground to correct permissions, since it was broken in previous release.   



2.17.08
-------

**BUG**: Avoid this version to administer pumps because of bug 88: sr_audit creates report routing queues 
even when report_daemons is off, they fill up with messages (since they are never emptied). This can cause havoc.
If report_daemons is true, then there is no issue.  Also no problem for clients. 

**ACTION**: (Must run sr_audit --users foreground to correct permissions).
Users now have permission to create exchanges.  
If corrections not updated on broker, warning messages about exchange declaration failures will occur.

*SHOULD*: Remove all *declare exchange* statements in configuration files, though they are harmless.
Configurations declare broker side resources (exchanges and queues) by *setup* action.  The resources can be freed 
with the *cleanup* action.  Formerly creation and deletion of exchanges was an administrator activity.

*SHOULD*: Cluster routing logic removed ( *cluster*, *gateway_for*, and *cluster_aliases* ) these options are now ignored.
If relying on these options to restrict distribution (no known cases), that will stop working.
Cluster propagation restriction to be implemented by plugins at a future release.
Should remove all these options from configuration files.

*SHOULD*: Should remove all *sftp://*  url lines from credentials.conf files. Configuration of sftp should be done
via openssh configuration, and credential file only used as a last resort.  Harmless if they remain, however.



2.17.07
-------


**CHANGE**: sr_sender *mirror* has been repaired.  If no setting present, then it will now mirror.
To preserve previous behavior, add to configuration::

       mirror off

*NOTICE*: Switch from traditional init-style ordering to systemd style -->  action comes before configuration.
Was::

      sr_subscriber myconfig start --> sr_subscriber start myconfig 

Software issues warning message about the change, but old callup still supported.


*NOTICE*: Heartbeat log messages will appear every five minutes in logs, by default, to differentiate no activity
from a hung process.

 
2.17.06
-------

**CHANGE**: Review/modify all plugins, as file variables of sender and subscriber converged.
   on_msg plugin variable for file naming for subscribers (sr_subscribe,sarra,shovel,winnow) changed.  Replace::

      self.msg.local_file --> self.msg.new_dir and self.msg.new_file

   on_msg plugin variable for file naming for senders now same as for subscribers.  Replace::

      self.remote_file --> self.msg.new_dir and self.msg.new_file

**CHANGE**: By default, the modification time of files is now restored on delivery.  To restore previous behaviour::

      preserve_time off

If preserve_time is on (now default) and a message is received, then it will be rejected if the mtime of
the new file is not newer than the one of the existing file.

**CHANGE**: By default, the permission bits of files is now restored on delivery.  To restore previous behaviour::

      preserve_mode off

**NOTICE**: Use the *blocksize* option to determine partitioning strategy. Default is 0 (same as previous default) *parts* deprecated.
      


2.17.02
-------

*NOTICE*: sr_watch re-implementation. Now supports symlinks, multiple traversal methods, etc...
Many behaviour improvements. FIXME: ?

**CHANGE**: Plugins are now stackable. Formerly, when two plugin specifications were given, the newer one
would replace the previous one. Now both plugins will be executed in the order encountered.
 


