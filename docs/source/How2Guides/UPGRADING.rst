
---------------
 UPGRADE GUIDE
---------------

This file documents changes in behaviour to provide guidance to those upgrading 
from a previous version. Sections are titled to indicate changes needed when
upgrading to that version. To upgrade across several versions, one needs to start
at the version after the one installed, and heed all notifications for interim
versions. While configuration language stability is an important 
goal, on occasion changes cannot be avoided. This file does not document new 
features, but only changes that cause concern during upgrades. The notices 
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
   
The sections in are entitled by the changes taking place at the level in question.

Installation Instructions
-------------------------

`Installation Guide <../Tutorials/Install.rst>`_

git
---


V2 to sr3
---------

sr3 is a very deep refactor of sarracenia. For more detail on the nature
of the changes, `go here <../Contribution/v03.html>`_ A summary is
is that v2 was an application written in python that had some plugin facilities,
where sr3 is a toolkit that naturally provides an API and is far more
natural to work with for python developers. Sr3 is built with less code, more maintainable
code, and supports more features, more naturally.

When migrating from v2 to sr3, simple configurations will mostly "just work."
but there cases relying on user built plugins will need a porting effort.

were there are some major changes in using any version >=3.00, compared to 2.x.
Configuration and state files are under the 'sr3' directory (on linux: ~/.config/sr3, and ~/.cache/sr3) 
instead of .sarra. So copy config files that one wants to use from the old ~/.config/sarra to 
~/.config/sr3. The two versions operate independently.

This allows one to run v2 and sr3 in parallel on the same server, and gradually transition.

The most common v2 plugins are on_message, and on_file ones (as per *plugin* and *on\_* 
directives in configuration files) which can be honoured via the 
`v2wrapper sr3 plugin class <../Reference/flowcb.html#module-sarracenia.flowcb.v2wrapper>`_
Many other plugins were ported, and the the configuration module recognizes the old
configuration settings and they are interpreted in the new style.

There are some performance consequences from this compatibility however, so high traffic
flows will run with less cpu and memory load if the plugins are ported to sr3.
To build native sr3 plugins, One should investigate the flowCallback (flowcb) class. 

Another difference is In sr3, the default topicPrefix is just plain 'v03' as opposed to 'v02.post' in v2.
So one may need to specify topicPrefix when migrating flows and keeping v02 flows.

The **sr_audit component is gone**.  It's function is replaced by running *sr sanity* as a cron
job (or scheduled task on windows.) to make sure that necessary processes continue to run.

The cli is different also, invocation is changed as follows:

old v02:   **sr_subscribe start myflow.conf**

new sr3:   **sr3 start subscribe/myflow.conf**

In Sr3, one can specify a list of configurations to start, and they can be a combination of
any component to be started, or stopped at once.

There are not supposed to be too many Incompatibilities when upgrading from v2.XX.yyy
This is a running list of incompatibilities that result from explicit
choices.  breaking changes:

* in sr3, use -- for full word options, like --config, or --broker.  In v2 you could use -config and -broker,
  but that will end badly in sr3. In the old command line parser, -config, and --config were the same, which
  was idiosyncratic.  The new command line option parser is built on ArgParse, and interprets a single - 
  as prefix a single option where the the subsequent letters are and argument. Example:

  -config hoho.conf  -> in v2 refers to loading the hoho.conf file as a configuration.

  in sr3, it will be interpreted as -c (config) load the onfig.conf file, and hoho.conf is part of some subsequent option.

* loglevel none -> logLevel notset (now passing loglevel setting directly to python logging module, none isn't defined.)

* log messages and output will be completely different, as the logging modules have been re-done.

* dropped settings: use_amqplib, use_pika... replaced by separate per protocol implementation libraries. amqp uses the 'amqp' library which is neither of the above. ( commit 02fad37b89c2f51420e62f2f883a3828d2056de1 )

* dropping on_watch plugins. afaict, no-one ever used them.  The way sr3 works, it would be an after_accept for a watch.

* plugins that access internals of sr_retry need to be rewritten, as the class is now plugin/retry.py.
  The way to queue something for retry in current plugins is to append them to the failed queue.
  This is only an issue in the flow tests of sr_insects.

* plugins are very different. For more information: `plugin porting <v2ToSr3.html>`_

* In v2, mirror default settings used to be False in all components except sr_sarra.
  but the mirror setting was not honoured in shovel, and winnow (bug #358)
  this bug is corrected in sr3, but then you notice that the default is wrong.

  In sr3, the default for mirror is changed to True for all flows except subscribe, 
  which is the least surprising behaviour given the default to False in v2.

* In v2, if you delete a file, and then re-create it, an event will be created.
  In sr3, if you do the same, the old entry will be in the nodupe cache, and the event will be suppressed.
  I have noticed this difference, but not sure which version's behaviour is correct.
  it could be fixed, if we decide the old behaviour is right.

* sr_watch, with the *force_polling* option, is much less efficient on sr3 than v2 
  for large directory trees (see issue #403 )


