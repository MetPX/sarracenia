
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

`Installation Guide <../Tutorials/Install.rst>`_

git
---

v03
---

not yet released.


v2.xx.yy
--------

There are some major changes in using any version >3.00, compared to 2.x.
Configuration and state files are under the 'sr3' directory (on linux: ~/.config/sr3, and ~/.cache/sr3) 
instead of .sarra. So copy config files that one wants to use from the old ~/.config/sarra to 
~/.config/sr3. The two versions operate independently.

Most v2 plugins (as per *plugin* and *on\_* directives) are honoured via a wrapper class. To build
native v3 plugins, One should investigate the flowCallback (flowcb) class. 

default topicPrefix is just plain 'v03'  as opposed to topic_prefix being 'v02.post' in v2.

sr_audit component is gone.  It's function is replaced by running *sr sanity* as a cron
job (or scheduled task on windows.) to make sure that necessary processes continue to run.

invocation is changed as follows:

old v02:   **sr_subscribe start myflow.conf**

new v03:   **sr3 start subscribe/myflow.conf**

In v3, one can specify a list of configurations to start, and they can be a combination of
any component to be started, or stopped at once.

There are not supposed to be too many Incompatibilities when upgrading from v2.XX.yyy
This is a running list of incompatibilities that result from explicit
choices.  breaking changes:


* in v3, use -- for full word options, like --config, or --broker.  In v2 you could use -config and -broker,
  but that will end badly in v3.  In the old command line parser, -config, and --config were the same, which
  was idiosyncratic.  The new
  command line option parser is built on ArgParse, and interprets a single - as prefix a single option where the
  the subsequent letters are and argument.  Example

  -config hoho.conf  -> in v2 refers to loading the hoho.conf file as a configuration.

  in v3, it will be interpreted as -c (config) load the onfig.conf gile, and hoho.conf is part of some subsequent option.

* loglevel none -> loglevel notset (now passing loglevel setting directly to python logging module, none isn't defined.)

* log messages and output will be completely different, as the logging modules have been re-done.

* dropped settings: use_amqplib, use_pika... replaced by separate per protocol implementation libraries. amqp uses the 'amqp' library which is neither of the above. ( commit 02fad37b89c2f51420e62f2f883a3828d2056de1 )

* dropping on_watch plugins. afaict, no-one uses them.  The way v03 works it would be an after_accept for a watch.
  makes more sense that way anyways.

* plugins that access internals of sr_retry need to be rewritten, as the class is now plugin/retry.py.
  the way to queue something for retry in current plugins is to append them to the failed queue.
  This is only an issue in the flow tests of sr_insects.

* do_download and do_send were 1st pass at *schemed* plugins, I think they should be deprecated/replaced
  by do_get and do_put. unclear whether there is a need for these anymore (download and send plugins are
  at wrong level of abstraction)

* do_download, do_send, do_get, do_put are *schemed* downloads... that is, rather than stacking so that
  all are called, they are registered for particular protocols.  in v2, for example accel_* plugins would
  register the "download" scheme. an on_message entry point would alter the scheme so that the do_* routine
  would be invoked. In v2, the calling signature for all plugins is the same (self, parent) but for
  these do_get and do_put cases, that is quite counter productive. so instead have a calling signature
  identical to built-in protocol get/put... src_file, dst_file, src_offset, dst_offset, len )
  Resolution: just implement new Transfer classes, does not naturally fit in flowcb.

* In v2, mirror default settings used to be False in all components except sr_sarra.
  but the mirror setting was not honoured in shovel, and winnow (bug #358)
  this bug is corrected in v3, but then you notice that the default is wrong.

  In v3, the default for mirror is changed to True for all flows except subscribe, which
  is the least surprising behaviour given the default to False in v2.

* In v2, if you delete a file, and then re-create it, an event will be created.
  In v3, if you do the same, the old entry will be in the nodupe cache, and the event will be suppressed.
  I have noticed this difference, but not sure which version's behaviour is correct.
  it could be fixed, if we decide the old behaviour is right.

* sr_watch, with the *force_polling* option, is much less efficient on v3 than v2 
  for large directory trees (see issue #403 )


