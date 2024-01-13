
---------------
 UPGRADE GUIDE
---------------

This document describes changes in behaviour to provide guidance to those upgrading 
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
   may generate notification messages.  
   
The sections in are entitled by the changes taking place at the level in question.

Installation Instructions
-------------------------

`Installation Guide <../Tutorials/Install.rst>`_

git
---

3.0.47
------

*CHANGE*: config option, strftime options, offset grammar changed:
in v2 you had ${YYYYMMDD-70m}, in sr3 it should be ${%o-70m%Y%m%d}
in 3.0.47, moved the time offset parsing to the beginning of the pattern.

*CHANGE*: default value of *filename* setting is now *None* instead of
'WHATFN', which reduces compatibility with Sundew, but makes behaviour
less surprising when not using/familiar with Sundew. This *None* setting
is the same as used by v2, so it should improve compatibility with 
sarracenia v2 configurations.


3.0.45
------

*CHANGE*: config option: logRotateInterval units was days, is now 
     a time interval (seconds) like all other intervals.



3.0.41
------

*CHANGE*: v03 post format field renamed: "integrity" is now "identity"

    * current version will read messsages with *integrity* and map them to *identity*.
    * current version will post with *identity*, so older versions will miss them.
    * https://github.com/MetPX/sarracenia/issues/703
    * metpx-sr3c >= v3.23.06  (equivalent compatible C implementation)
    * metpx-sarracenia >= v2.23.06 (equivalent v2 compatible (legacy) version.)


3.0.40
------

*CHANGE*: the default format in which messages are posted is v03, but as of this
    version, to override the format, one must use *post_format v02*
    prior to this version, setting of post_topicPrefix was sufficient.
    Now both settings are needed.

*CHANGE*:  Python API breaking changes

    for sarracenia.moth, now specify broker as options['broker'] instead of as
    a separate parameter:

    before:

    * Moth(broker: url, options: dict, is_subsubscriber: bool) -> Config
    * pubFactory( broker, options ) -> Config
    * subFactory( broker, options ) -> Config
           
    after:
     
    * Moth( options: dict, is_subscribe: bool) -> Config
    * pubFactory( options ) -> Config
    * subFactory( options ) -> Config
           
    sarracenia.config API:

     now should call **sarracenia.config.finalize()**
     after having set options  and before being used.
     This routine reconciles the settings provided and builds
     some derived ones.



3.0.37
------

*BUG*: *sr3 cleanup* does not work at all. 
       https://github.com/MetPX/sarracenia/issues/669


3.0.26
------

*CHANGE*: event options (logEvents, and fileEvents) now replace previous value
          used to be unioned (or'd) with previous value.  now can preface
          the set elements with + to get the previous behaviour.
          Also - is available to remove an element from a set option.
          (sr3 convert now prefixes v2 values with +)

*CHANGE*: fileEvents, new events present *mkdir*, and *rmdir*, some adjustment
          to fileEvents settings may now be required.

3.0.25
------

*CHANGE*: default value for acceptUnmatched is now True for all components.
          prior to this release, default was False in subscribe component,
          and True for all others.


3.0.23
------

*NOTICE*: now prefer strftime date specification in patterns, in place of 
          ones inherited from Sundew. converted by sr3 convert.

*CHANGE*: removed *please_stop_immediately* option added in 3.0.22
          (all components now stop more quickly, so not needed.)

3.0.22
------

*CHANGE*: *destination*, when used in a poll is replaced by *pollUrl*

*CHANGE*: *destination*, when used in a sender is replaced by *sendTo*

*ACTION*: replace *destination* settings in affected configurations.
          (automatically taken care of in v2 when converting.)

*NOTICE*: when a file is renamed, sr3 has always only processed one of the two messages
          produced to announce it, for compatibility with v2 naming.
          there is now an option: v2compatRenameDoublePost in sr3 to post only a single message
          when a file is renamed.  This is now the default behaviour.

3.0.17
------

*CHANGE*: The "Vendor" string is now "MetPX" instead of "science.gc.ca".
     This affects some file placement particularly on Windows.

*CHANGE*: v03 notification message encoding changed: *Identity* checksum is now optional.
          (details: https://github.com/MetPX/sarracenia/issues/547 )
          *md5sum* is no longer defined, replaced with *none* in sr3.

*CHANGE*: v03 notification message encoding changed for symbolic links, and file renames
     and removals. There is now a 'fileOp' field for these dataless file operations.
     The *Identity* sum is now used exclusively for checksums.


3.0.15
------

*NOTICE*: re-instating debian and windows packages by removing hard requirements for python modules
    which are difficult to satisfy. From 3.0.15, dependencies are modular. 

*CHANGE*: there are now four "extras" configured for pip packages for metpx-sr3.

  * amqp - ability to communicate with AMQP (rabbitmq) brokers

  * mqtt - ability to communicate with MQTT brokers

  * ftppoll - ability to poll FTP servers

  * vip  - enable vip (Virtual IP) settings to implement singleton processing for high availability support.

  with pip installation, one can include all the extras via::

      pip install metpx-sr3[all]

  with Linux packages, install the corresponding native packages to activate the corresponding features

  on Ubuntu, respectively::

      apt install python3-amqp 
      apt install python3-magic 
      apt install python3-paramiko 
      apt install python3-paho-mqtt 
      apt install python3-dateparser python3-tz
      apt install python3-netifaces

  sr3 looks for the relevant modules on startup and automatically enables support for the relevant features.

**CHANGE**: file placement of denoting disabled configurations. it used to be that
     ~/.config/sr3/component/x.conf would be renamed x.conf.off when disabling.
     Now instead a file called ~/.cache/sr3/component/x/disabled is created.
     Configuration files are no longer changed by this sort of routine intervention.

3.0.14
------

initial beta.

*NOTICE*: only pip packages currently work. No Debian packages on launchpad.net
          nor any windows packages.


V2 to Sr3
---------

*NOTICE*: Sr3 is a very deep refactor of Sarracenia. For more detail on the nature
          of the changes, `go here <../Contribution/v03.html>`_ Briefly, where v2 
          is an application written in python that had a small extension facility,
          Sr3 is a toolkit that naturally provides an API and is far more
          pythonic. Sr3 is built with less code, more maintainable code, and 
          supports more features, and more naturally.

**CHANGE**: log messages look completely different. Any log parsing will have to be reviewed.
          New log format includes a prefix with process-id and the routine generating the notification message.

**CHANGE**: default message format in sr3 is v03. in v2, the default format was v2.

**CHANGE**: default topicPrefix and post_topicPrefix in sr3 is 'v03' ... in v2 it 
          was 'v02.post'
        
*NOTICE*: When migrating from v2 to sr3, simple configurations will mostly "just work."
          However, cases relying on user built plugins will require effort to port.
          The built-in plugins provided with Sarracenia have been ported as updated
          examples.

**CHANGE**: file placement. On Linux: ~/.cache/sarra -> ~/.cache/sr3 
          ~/.config/sarra -> ~/.config/sr3
          Similar change on other platforms. The different placement
          allows to run both v2 and sr3 at the same time on the same server.

*NOTICE*: to change configurations from v2 to sr3, rather than copying the file
          from one directory to the other, use of the convert directive is recommended::

              sr3 convert subscribe/mine.conf

          will make all mechanical conversions of directive names from v2 to sr3 automatically.
          only custom plugin work need to be manually ported, as described below.

*NOTICE*: In sr3 the winnowing or duplicate suppression algorithm (implemented by sarracenia.flowcb.nodupe.NoDupe.py)
          is separate from the data source's checksum algorithm. 

          In v2, the checksum algorithm had to be harmonized with the 
          data source checksum. In sr3 one can select any checksumming method,
          and still customize how message key and path are selected to allow for 
          full customization of duplicate suppression.
          
 
**CHANGE**: Command line interface (CLI) is different. There is only one main entry_point: sr3.
          so most invocations are different in a pattern like so::

             sr_subscribe start config -> sr3 start subscribe/config

          in sr3 one can specify a series of configurations to operate on in a single 
          command::

             sr3 start poll/airnow subscribe/airnow sender/cmqb
          
**CHANGE**: in sr3, use -- for full word options, like --config, or --broker.  In v2 you 
           could use -config and -broker, but single dash is reserved for single character options.
           This is a result of sr3 using python standard ArgParse class::

                -config hoho.conf  -> in v2 refers to loading the hoho.conf file as a configuration.

           In sr3, it will be interpreted as -c (config) load the onfig.conf file, and hoho.conf 
           is part of some subsequent option. in sr3::

                --config hoho.conf

           does that as intended.

**CHANGE**: sr3 poll works very differently from v2.

          ============================================== =====================================================
          v2 behaviour                                   sr3 behaviour
          ---------------------------------------------- -----------------------------------------------------
          all participants in a vip poll remote always   One node (with vip) polls remote.
          all participants in a vip update ls_files      nodes subscribe to the output exchange          
          poll builds strings to describe files          poll builds stat(2) like paramiko.SftpAttributes() 
          participants rely on their ls_files for state  poll uses flowcb.nodupe module like rest of sr3
          file_time_limit to ignore older files          nodupe_fileAgeMax 
          *destination* gives where to poll              *pollUrl*
          *directory* gives remote directory to list     *path* used like in *post* and *watch*
          need *accept* per *directory*                  need only one *accept*
          *get* is a sort of remote pattern filtering    *accept* same as used by all other components.
          do_poll plugins used to override default       *poll* entry point in flow callbacks
          *do_poll* used to *HTTP GET* periodically      flowcb.scheduled more elegant.
          ============================================== =====================================================

          The sr3 convert function takes care of the necessary configuration changes, but plugins
          need ground up rewrites, as they work completely differently.

          All of the changes makes poll's use of the configuration language less different than how it is 
          used in other components. For example, *directory* was confusing because it is used to determine 
          the source directory to be polled. In all other components it refers to the download location. 
          The *path* option replaces it, poll uses it the same *post* and *watch* do: 
          to denote the paths that should be observed.
      
          In sr3 when vip setting is present, poll will create a queue bound to the post_broker/post_exchange 
          in order to see the posts done by other participants in the queue. queue naming options are therefore
          useful in sr3

          
**CHANGE**: In general, underscores in options are replaced with camelCase. e.g.:

          v2 loglevel -> sr3 logLevel

          v2 options that are renamed will be understood, but an informational message will be produced on
          startup. Underscore is still use for grouping purposes. Options which have changed:

          ========================= ==================
          **v2 Option**             **v3 Option**
          ------------------------- ------------------
          accel_scp_threshold       accelThreshold
          accel_wget_threshold      accelThreshold
          accept_unmatch            acceptUnmatched
          accept_unmatched          acceptUnmatched
          base_dir                  baseDir
          basedir                   baseDir
          baseurl                   baseUrl
          bind_queue                queueBind
          cache                     nodupe_ttl
          cache_basis               nodupe_basis
          caching                   nodupe_ttl
          chmod                     permDefault
          chmod_dir                 permDirDefault
          chmod_log                 permLog
          declare_exchange          exchangeDeclare
          declare_queue             queueDeclare
          default_dir_mode          permDirDefault
          default_log_mode          permLog
          default_mode              permDefault
          destination               pollUrl in Poll
          destination               sendTo in Sender
          document_root             documentRoot
          e                         fileEvents
          events                    fileEvents
          exchange_split            exchangeSplit
          file_time_limit           nodupe_fileAgeMax
          hb_memory_baseline_file   MemoryBaseLineFile
          hb_memory_max             MemoryMax
          hb_memory_multiplier      MemoryMultiplier
          heartbeat                 housekeeping
          instance                  instances
          ll                        logLevel
          logRotate                 logRotateCount
          logRotate_interval        logRotateInterval
          log_format                logFormat
          log_reject                logReject
          logdays                   logRotateCount
          loglevel                  logLevel
          no_duplicates             nodupe_ttl
          post_base_dir             post_baseDir
          post_base_url             post_baseUrl
          post_basedir              post_baseDir
          post_baseurl              post_baseUrl
          post_document_root        post_documentRoot
          post_exchange_split       post_exchangeSplit
          post_rate_limit           messageRateMax
          post_topic_prefix         post_topicPrefix
          preserve_mode             permCopy
          preserve_time             timeCopy
          queue_name                queueName
          report_back               report
          source_from_exchange      sourceFromExchange
          sum                       identity
          suppress_duplicates       nodupe_ttl
          suppress_duplicates_basis nodupe_basis
          topic_prefix              topicPrefix
          ========================= ==================
    
**CHANGE**: default topic_prefix v02.post -> topicPrefix  v03
          may need to change configurations to override default to get
          compatible configurations.
          
**CHANGE**: v2: *mirror* defaults to False on all components except sarra.
          sr3: *mirror* defaults to True on all components except subscribe.

*NOTICE*: The most common v2 plugins are on_message, and on_file 
          (as per *plugin* and *on\_* directives in v2 configuration files) which can 
          be honoured via the `v2wrapper sr3 plugin class <../Reference/flowcb.html#module-sarracenia.flowcb.v2wrapper>`_
          Many other plugins were ported, and the the configuration module 
          recognizes the old configuration settings and they are interpreted 
          in the new style. the known conversions can be viewed by starting
          a python interpreter::


            Python 3.8.10 (default, Nov 26 2021, 20:14:08) 
            [GCC 9.3.0] on linux
            Type "help", "copyright", "credits" or "license" for more information.
            >>> import sarracenia.config,pprint
            >>> pp=pprint.PrettyPrinter()
            >>> pp.pprint(sarracenia.config.convert_to_v3)
            {
             'do_send':   {
                            'file_email':           ['flowCallback',
                                                     'sarracenia.flowcb.send.email.Email']
                          },
             'ls_file_index':                       ['continue'],
             'no_download':                         ['download',
                                                     'False'],
             'notify_only':                         ['download',
                                                     'False'],

             'on_message':{
                            'msg_2http':            ['flow_callback',
                                                     'sarracenia.flowcb.accept.tohttp.ToHttp'],
                            'msg_2local':           ['flow_callback',
                                                     'sarracenia.flowcb.accept.tolocal.ToLocal'],
                            'msg_2localfile':       ['flow_callback',
                                                     'sarracenia.flowcb.accept.tolocalfile.ToLocalFile'],
                            'msg_WMO_type_suffix':  ['flow_callback',
                                                     'sarracenia.flowcb.accept.wmotypesuffix.WmoTypeSuffix'],
                            'msg_by_source':        ['continue'],
                            'msg_by_user':          ['continue'],
                            'msg_delay':            ['flow_callback',
                                                     'sarracenia.flowcb.accept.messagedelay.MessageDelay'],
                            'msg_delete':           ['flow_callback',
                                                     'sarracenia.flowcb.filter.deleteflowfiles.DeleteFlowFiles'],
                            'msg_download':         ['continue'],
                            'msg_download_baseurl': ['flow_callback',
                                                     'sarracenia.flowcb.accept.downloadbaseurl.DownloadBaseUrl'],
                            'msg_dump':             ['continue'],
                            'msg_fdelay':           ['continue'],
                            'msg_from_cluster':     ['continue'],
                            'msg_gts2wistopic':     ['continue'],
                            'msg_hour_tree':        ['flow_callback',
                                                     'sarracenia.flowcb.accept.hourtree.HourTree'],
                            'msg_http_to_https':    ['flow_callback',
                                                     'sarracenia.flowcb.accept.httptohttps.HttpToHttps'],
                            'msg_log':              ['logEvents',
                                                     'after_accept'],
                            'msg_overwrite_sum':    ['continue'],
                            'msg_print_lag':        ['flow_callback',
                                                     'sarracenia.flowcb.accept.printlag.PrintLag'],
                            'msg_rawlog':           ['logEvents', 'after_accept'],
                            'msg_rename4jicc':      ['flow_callback',
                                                     'sarracenia.flowcb.accept.rename4jicc.Rename4Jicc'],
                            'msg_rename_dmf':       ['flow_callback',
                                                     'sarracenia.flowcb.accept.renamedmf.RenameDMF'],
                            'msg_rename_whatfn':    ['flow_callback',
                                                     'sarracenia.flowcb.accept.renamewhatfn.RenameWhatFn'],
                            'msg_renamer':          ['flow_callback',
                                                     'sarracenia.flowcb.accept.renamer.Renamer'],
                            'msg_save':             ['flow_callback',
                                                     'sarracenia.flowcb.accept.save.Save'],
                            'msg_skip_old':         ['flow_callback',
                                                     'sarracenia.flowcb.accept.skipold.SkipOld'],
                            'msg_speedo':           ['flow_callback',
                                                     'sarracenia.flowcb.accept.speedo.Speedo'],
                            'msg_stdfiles':         ['continue'],
                            'msg_stopper':          ['continue'],
                            'msg_sundew_pxroute':   ['flow_callback',
                                                     'sarracenia.flowcb.accept.sundewpxroute.SundewPxRoute'],
                            'msg_test_retry':       ['flow_callback',
                                                     'sarracenia.flowcb.accept.testretry.TestRetry'],
                            'msg_to_clusters':      ['flow_callback',
                                                     'sarracenia.flowcb.accept.toclusters.ToClusters'],
                            'msg_total':            ['continue'],
                            'msg_total_save':       ['continue'],
                            'post_hour_tree':       ['flow_callback',
                                                     'sarracenia.flowcb.accept.posthourtree.PostHourTree'],
                            'post_long_flow':       ['flow_callback',
                                                     'sarracenia.flowcb.accept.longflow.LongFLow'],
                            'post_override':        ['flow_callback',
                                                     'sarracenia.flowcb.accept.postoverride.PostOverride'],
                            'post_total':           ['continue'],
                            'post_total_save':      ['continue'],
                            'wmo2msc':              ['flow_callback',
                                                     'sarracenia.flowcb.filter.wmo2msc.Wmo2Msc']
                           },
             'on_post':    {
                            'post_log':             ['logEvents', 'after_work']
                           },
             'plugin':     {
                            'accel_scp':            ['continue'],
                            'accel_wget':           ['continue'],
                            'msg_fdelay':           ['flowCallback',
                                                     'sarracenia.flowcb.filter.fdelay.FDelay'],
                            'msg_pclean_f90':       ['flowCallback',
                                                     'sarracenia.flowcb.filter.pclean_f90.PClean_F90'],
                            'msg_pclean_f92':       ['flowCallback',
                                                     'sarracenia.flowcb.filter.pclean_f92.PClean_F92']
                           },
             'windows_run':                         ['continue'],
             'xattr_disable':                       ['continue']
            }
            >>> 

          The options listed as 'continue' are obsolete ones, superceded by default processing, or rendered
          unnecessary by changes in the implementation.

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
          This access is no longer necessary, as the API defines how to put notification messages on 
          the retry queue (move notification messages to worklist.failed. )

*NOTICE*: sr3 watch, with the *force_polling* option, is much less efficient 
          on sr3 than v2 for large directory trees (see issue #403 )
          Ideally, one does not use *force_polling* at all.

