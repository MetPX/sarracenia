
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
          of the changes, `go here <../Contribution/v03.html>`_ Briefly, where v2 
          is an application written in python that had a small extension facility,
          Sr3 is a toolkit that naturally provides an API and is far more
          pythonic. Sr3 is built with less code, more maintainable code, and 
          supports more features, and more naturally.

**CHANGE**: log messages look completely different. Any log parsing will have to be reviewed.
          New log format includes a prefix with process-id and the routine generating the message.

*NOTICE*: When migrating from v2 to sr3, simple configurations will mostly "just work."
          but there cases relying on user built plugins will need a porting effort.
          The built-in plugins provides with Sarracenia have been ported and provide
          examples.

**CHANGE**: file placement. On Linux: ~/.cache/sarra -> ~/.cache/sr3 
          ~/.config/sarra -> ~/.config/sr3
          Similar change on other platforms. The different placement
          allows to run both v2 and sr3 at the same time on the same server.

**CHANGE**: Command line interface (CLI) is different. There is only one main entry_point: sr3.
          so most invocations are different in a pattern like so::

             sr_subscribe start config -> sr3 start subscribe/config

          in sr3 one can specify a series of configurations to operate on in a single 
          command::

             sr3 start poll/airnow subscribe/airnow sender/cmqb
          
**CHANGE**:  in sr3, use -- for full word options, like --config, or --broker.  In v2 you 
           could use -config and -broker, but single dash is reserved for single character options.
           This is a result of sr3 using python standard ArgParse class::

                -config hoho.conf  -> in v2 refers to loading the hoho.conf file as a configuration.

           In sr3, it will be interpreted as -c (config) load the onfig.conf file, and hoho.conf 
           is part of some subsequent option. in sr3::

                --config hoho.conf

           does that is intended.

**CHANGE**: In general, the underscore in options is replaced by camelCase. e.g.:

          v2 loglevel -> sr3 logLevel

          v2 option that are renamed will be understood, but an informational message will be produced on
          startup. Underscore is still use for grouping purposes. Options which have changed::

            accel_scp_threshold -> accelThreshold
            accel_wget_threshold -> accelThreshold
            accel_xxx_command -> accelXxxCommand
            accept_unmatch -> acceptUnmatched
            accept_unmatched -> acceptUnmatched
            basedir -> baseDir
            base_dir -> baseDir
            baseurl -> baseUrl
            bind_queue -> queueBind
            declare_exchange -> exchangeDeclare
            declare_queue -> queueDeclare
            cache -> nodupe_ttl
            document_root -> documentRoot
            no_duplicates -> nodupe_ttl
            caching -> nodupe_ttl
            cache_basis -> nodupe_basis
            e  -> fileEvents
            events  -> fileEvents
            instance -> instances
            chmod -> permDefault
            default_mode -> permDefault
            chmod_dir -> permDirDefault
            default_dir_mode -> permDirDefault
            chmod_log -> permLog
            default_log_mode -> permLog
            file_time_limit  -> nodupe_fileAgeMax
            heartbeat -> housekeeping
            hb_memory_baseline_file  -> MemoryBaseLineFile
            hb_memory_max  -> MemoryMax
            hb_memory_multiplier  -> MemoryMultiplier
            log_format -> logFormat
            ll -> logLevel
            loglevel -> logLevel
            logdays -> lr_backupCount
            logrotate -> lr_backupCount
            logrotate_interval -> lr_interval
            post_base_dir -> post_baseDir
            post_basedir -> post_baseDir
            post_base_url -> post_baseUrl
            post_baseurl -> post_baseUrl
            post_document_root -> post_documentRoot
            post_rate_limit -> messageRateMax
            post_topic_prefix  -> post_topicPrefix
            preserve_mode  -> permCopy
            preserve_time  -> timeCopy
            suppress_duplicates  -> nodupe_ttl
            suppress_duplicates_basis  -> nodupe_basis
            topic_prefix  -> topicPrefix
    
**CHANGE**: default topic_prefix v02.post -> topicPrefix  v03
          may need to change configurations to override default to get
          compatible configurations.
          
**CHANGE**: v2: *mirror* defaults to False on all components except sarra.
          sr3: *mirror* defaults to True on all components except subscribe.

*NOTICE*: The most common v2 plugins are on_message, and on_file ones 
          (as per *plugin* and *on\_* directives in v2 configuration files) which can 
          be honoured via the `v2wrapper sr3 plugin class <../Reference/flowcb.html#module-sarracenia.flowcb.v2wrapper>`_
          Many other plugins were ported, and the the configuration module recognizes the old
          configuration settings and they are interpreted in the new style.
          the known conversions::

           convert_to_v3 = {
               'ls_file_index' : [ 'continue' ],
               'plugin': {
                   'msg_fdelay': ['flowCallback', 'sarracenia.flowcb.filter.fdelay.FDelay'],
                   'msg_pclean_f90':
                   ['flowCallback', 'sarracenia.flowcb.filter.pclean_f90.PClean_F90'],
                   'msg_pclean_f92':
                   ['flowCallback', 'sarracenia.flowcb.filter.pclean_f92.PClean_F92'],
                   'accel_wget': ['continue'],
                   'accel_scp': ['continue'],
               },
               'do_send': {
                  'file_email' : [ 'flowCallback', 'sarracenia.flowcb.send.email.Email' ],
               },
               'no_download': [ 'download', 'False' ],
               'notify_only': [ 'download', 'False' ],
               'on_message': {
                   'msg_print_lag': [ 'flow_callback', 'sarracenia.flowcb.accept.printlag.PrintLag'],
                   'msg_skip_old': [ 'flow_callback', 'sarracenia.flowcb.accept.skipold.SkipOld'],
                   'msg_test_retry': [ 'flow_callback', 'sarracenia.flowcb.accept.testretry.TestRetry'],
                   'msg_to_clusters': [ 'flow_callback', 'sarracenia.flowcb.accept.toclusters.ToClusters'],
                   'msg_save': [ 'flow_callback', 'sarracenia.flowcb.accept.save.Save'],
                   'msg_2localfile': [ 'flow_callback', 'sarracenia.flowcb.accept.tolocalfile.ToLocalFile'],
                   'msg_rename_whatfn': [ 'flow_callback', 'sarracenia.flowcb.accept.renamewhatfn.RenameWhatFn'],
                   'msg_rename_dmf': [ 'flow_callback', 'sarracenia.flowcb.accept.renamedmf.RenameDMF'],
                   'msg_hour_tree': [ 'flow_callback', 'sarracenia.flowcb.accept.hourtree.HourTree'],
                   'msg_renamer': [ 'flow_callback', 'sarracenia.flowcb.accept.renamer.Renamer'],
                   'msg_2http': [ 'flow_callback', 'sarracenia.flowcb.accept.tohttp.ToHttp'],
                   'msg_2local': [ 'flow_callback', 'sarracenia.flowcb.accept.tolocal.ToLocal'],
                   'msg_http_to_https': [ 'flow_callback', 'sarracenia.flowcb.accept.httptohttps.HttpToHttps'],
                   'msg_speedo': [ 'flow_callback', 'sarracenia.flowcb.accept.speedo.Speedo'],
                   'msg_WMO_type_suffix': [ 'flow_callback', 'sarracenia.flowcb.accept.wmotypesuffix.WmoTypeSuffix'],
                   'msg_sundew_pxroute': [ 'flow_callback', 'sarracenia.flowcb.accept.sundewpxroute.SundewPxRoute'],
                   'msg_rename4jicc': [ 'flow_callback', 'sarracenia.flowcb.accept.rename4jicc.Rename4Jicc'],
                   'post_override': [ 'flow_callback', 'sarracenia.flowcb.accept.postoverride.PostOverride'],
                   'post_hour_tree': [ 'flow_callback', 'sarracenia.flowcb.accept.posthourtree.PostHourTree'],
                   'post_long_flow': [ 'flow_callback', 'sarracenia.flowcb.accept.longflow.LongFLow'],
                   'msg_delay': [ 'flow_callback', 'sarracenia.flowcb.accept.messagedelay.MessageDelay'],
                   'msg_download_baseurl': [ 'flow_callback', 'sarracenia.flowcb.accept.downloadbaseurl.DownloadBaseUrl'],
                   'msg_from_cluster': ['continue'],
                   'msg_stdfiles': ['continue'],
                   'msg_fdelay': ['continue'],
                   'msg_stopper': ['continue'],
                   'msg_overwrite_sum': ['continue'],
                   'msg_gts2wistopic': ['continue'],
                   'msg_download': ['continue'],
                   'msg_by_source': ['continue'],
                   'msg_by_user': ['continue'],
                   'msg_dump': ['continue'],
                   'msg_total': ['continue'],
                   'msg_total_save': ['continue'],
                   'post_total': ['continue'],
                   'post_total_save': ['continue'],
                   'wmo2msc': [ 'flow_callback', 'sarracenia.flowcb.filter.wmo2msc.Wmo2Msc'],
                   'msg_delete': [ 'flow_callback', 'sarracenia.flowcb.filter.deleteflowfiles.DeleteFlowFiles'],
                   'msg_log': ['logEvents', 'after_accept'],
                   'msg_rawlog': ['logEvents', 'after_accept']
               },
               'on_post': {
                   'post_log': ['logEvents', 'after_work']
               },
           }

*NOTICE*: for API users and plugin writers, the v2 plugin format is entirely replaced by 
          the `Flow Callback <FlowCallbacks.html>`_ class. New plugin functionality 
          can mostly be implemented as plugins.
          
**CHANGE**: the v2 do_poll plugins must be replaced by subclassing for `poll <../Reference/flowcb.html#module-sarracenia.flowcb.poll>`_
          Example in `plugin porting <v2ToSr3.html>`_ 

**CHANGE**: The v2 on_html_page plugins are also replaced by subclassing `poll <../Reference/flowcb.html#module-sarracenia.flowcb.poll>`_

**CHANGE**: v2 do_send replaced by send entrypoint in a Flowcb plugin `plugin porting <v2ToSr3.html>`_

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

**CHANGE**: on_watch plugins entry_point becomes an sr3 after_accept entrypoint in a flowcb in a watch.

*ACTION*: The **sr_audit component is gone**. Replaced by running *sr sanity* as a cron
          job (or scheduled task on windows.) to make sure that necessary processes continue to run.

**CHANGE**: obsolete settings: use_amqplib, use_pika. the new `sarracenia.moth.amqp <../Reference/code.html#module-sarracenia.moth.amqp>`_
          uses the amqp library.  To use other libraries, one should create new subclasses of sarracenia.moth.
          
**CHANGE**: statehost is now a boolean flag, fqdn option no longer implemented.
          if this is a problem, submit an issue. It's just not considered worthwhile for now.

**CHANGE**: sr_retry became `retry.py <../Reference/flowcb.html#module-sarracenia.flowcb.retry>`_. 
          Any plugins accessing internal structures of sr_retry.py need to be re-written. 
          This access is no longer necessary, as the API defines how to put messages on 
          the retry queue (move messages to worklist.failed. )

*NOTICE*: sr3 watch, with the *force_polling* option, is much less efficient 
          on sr3 than v2 for large directory trees (see issue #403 )
          Ideally, one does not use *force_polling* at all.

