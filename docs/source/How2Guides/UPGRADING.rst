
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


V2 to Sr3
---------

*NOTICE*: Sr3 is a very deep refactor of Sarracenia. For more detail on the nature
          of the changes, `go here <../Contribution/v03.html>`_ A summary is
          is that v2 was an application written in python that had some plugin facilities,
          where sr3 is a toolkit that naturally provides an API and is far more
          natural to work with for python developers. Sr3 is built with less code, more 
          maintainable code, and supports more features, more naturally.

*NOTICE*: log messages look completely different.

*NOTICE*: When migrating from v2 to sr3, simple configurations will mostly "just work."
          but there cases relying on user built plugins will need a porting effort.
          The built-in plugins provides with Sarracenia have been ported and provide
          examples.

*CHANGE*: file placement. On Linux: ~/.cache/sarra -> ~/.cache/sr3 
          ~/.config/sarra -> ~/.config/sr3
          Similar change on other platforms. The different placement
          allows to run both v2 and sr3 at the same time on the same server.

*CHANGE*: Command line interface (CLI) is different. There is only one main entry_point: sr3.
          so most invocations are different in a pattern like so::

             sr_subscribe start config -> sr3 start subscribe/config

          in sr3 one can specify a series of configurations to operate on in a single 
          command::

             sr3 start poll/airnow subscribe/airnow sender/cmqb
          
*CHANGE*:  in sr3, use -- for full word options, like --config, or --broker.  In v2 you 
           could use -config and -broker, but single dash is reserved for single character options.
           This is a result of sr3 using python standard ArgParse class::

                -config hoho.conf  -> in v2 refers to loading the hoho.conf file as a configuration.

           In sr3, it will be interpreted as -c (config) load the onfig.conf file, and hoho.conf 
           is part of some subsequent option. in sr3::

                --config hoho.conf

           does that is intended.

*CHANGE*: In general, the underscore in options is replaced by camelCase. e.g.:

          v2 loglevel -> sr3 logLevel

          v2 option that are renamed will be understood, but an informational message will be produced on
          startup. Underscore is still use for grouping purposes.
         
*NOTICE*: log messages and output will be completely different.
          New log format includes a prefix with process-id and the routine generating the message.

*CHANGE*: default topic_prefix v02.post -> topicPrefix  v03
          may need to change configurations to override default to get
          compatible configurations.
          
*CHANGE*: v2: *mirror* defaults to False on all components except sr_sarra.
          sr3: *mirror* defaults to True on all components except subscribe.

*NOTICE*: The most common v2 plugins are on_message, and on_file ones 
          (as per *plugin* and *on\_* directives in v2 configuration files) which can 
          be honoured via the `v2wrapper sr3 plugin class <../Reference/flowcb.html#module-sarracenia.flowcb.v2wrapper>`_
          Many other plugins were ported, and the the configuration module recognizes the old
          configuration settings and they are interpreted in the new style.

*NOTICE*: for API users and plugin writers, the v2 plugin format replaced by the `Flow Callback <FlowCallbacks.html>`_
          class. New plugin functionality can mostly be implemented as plugins.
          
*CHANGE*: the v2 do_poll plugins must be replaced by subclassing for `poll <../Reference/flowcb.html#module-sarracenia.flowcb.poll>`_
          Example in `plugin porting <v2ToSr3.html>`_ 

*CHANGE*: The v2 on_html_page plugins are also replaced by subclassing `poll <../Reference/flowcb.html#module-sarracenia.flowcb.poll>`_

*CHANGE*: v2 do_send replaced by send entrypoint in a Flowcb plugin `plugin porting <v2ToSr3.html>`_

*NOTICE*: the v2 accellerator plugins are replaced by built-in accelleration.
          accel_wget_command, accel_scp_command, accel_ftpget_command, accel_ftpput_command,
          accel_scp_command, are now built-in options used by the
          `Transfer <../Reference/flowcb.html#module-sarracenia.transfer>`_ class.
          Adding new transfer protocols is done by sub-classing Transfer.
          
*SHOULD*: v2 on_message -> after_accept should be re-written `plugin porting <v2ToSr3.html>`_

*SHOULD*: v2 on_file -> after_work should be re-written `plugin porting <v2ToSr3.html>`_

*SHOULD*: v2 plugins should to be re-written.  `plugin porting <v2ToSr3.html>`_
          there are many built-in plugins that are ported and automatically
          converted, but external ones must be re-written.

          There are some performance consequences from this compatibility however, so high traffic
          flows will run with less cpu and memory load if the plugins are ported to sr3.
          To build native sr3 plugins, One should investigate the flowCallback (flowcb) class. 

*CHANGE*: on_watch plugins entry_point becomes an sr3 after_accept entrypoint in a flowcb in a watch.

*ACTION*: The **sr_audit component is gone**. Replaced by running *sr sanity* as a cron
          job (or scheduled task on windows.) to make sure that necessary processes continue to run.

*CHANGE*: obsolete settings: use_amqplib, use_pika. the new `sarracenia.moth.amqp <../Reference/code.html#module-sarracenia.moth.amqp>`_
          uses the amqp library.  To use other libraries, one should create new subclasses of sarracenia.moth.

*CHANGE*: sr_retry became `retry.py <../Reference/flowcb.html#module-sarracenia.flowcb.retry>`_. 
          Any plugins accessing internal structures of sr_retry.py need to be re-written. 
          This access is no longer necessary, as the API defines how to put messages on 
          the retry queue (move messages to worklist.failed. )

*NOTICE*: sr3 watch, with the *force_polling* option, is much less efficient 
          on sr3 than v2 for large directory trees (see issue #403 )


