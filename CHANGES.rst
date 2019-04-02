===============
 Release Notes 
===============

lists all changes between versions.

**git repo**

**2.19.04b1**

* new:    adding WMO_mesh_post example.
* bugfix: regression all posts in b6 were v02 (v03 inadvertantly disabled.)
* bugfix: print improvements.
* bugfix: there was an issue with extended attribute in checksums.
* 

**2.19.03b6**

* new:    made code use instance variables instead of repeatedly parsing
*         elements of the message: topic_prefix->version, sum-> event.
*         more robust/easier to maintain.
* bugfix: updated WMO_mesh examples to use v03 and /var/www/html (as per feedback.)
* new:    add post_override_del option to post_override plugin.
*         allows deletion of headers on post.
* bugfix: Issue #175 documentation needs to use amqps for dd.weather, not amqp anymore.
* new:    wmo_mesh example now deletes a bunch of headers to shorten & simplify messages.
* new:    switching http port in flow test to 8001.  8000 is too popular.
* new:    switching flow_test to use hpfx.collab.science.gc.ca instead of dd.weather.gc.ca
* bugfix: Issue #168 have httpd unit test retrieve pick a file <= 2kb.  Big files 
*         were causing hangs in the flow test... this is one fix, but not enough to close
*         the bug.
* new:    Issue #54 is finally closed.
* new:    Issue #54 added xattr_disable to turn off extended attributes feature.
* new:    Issue #54 added version of extended attributes for NTFS.

**2.19.03b5**

* bugfix: transparently accept setxattr failure for readonly files.
* bugfix: several bugs with roundtripping v03->v02 checksums.
* bugfix: changed documentation for rename (used what is changed by strip option) 
* bugfix: found issues with arbitrary-application checksum
* bugfix: mode/atime/mtim restoration was missing for inlined data.
* new:    upgrade wmo_mesh mqtt publishing plugin to work with v03

**2.19.03b4**

* bugfix: conversion from v02 to v03 was broken somewhere else.

**2.19.03b3**

* bugfix: conversion from v02 to v03 was broken.

**2.19.03b2**

* new:    issue #134 added on_data plugin entry point, to allow data tranformation.
* new:    removed recompute_chksum setting. application now decides on its own.
* new:    added post_on_start option so control whether sr_watch posts all files on startup.
* bugfix: issue #172 add inlining of data when the header is missing.  
* dev:    issue #159 Contiguous Integration with travis-ci added, improved testing.
*         testing of four different python versions now automated.
* new:    added msg_rawlog to allow clearer viewing of v02 and v03 messages.

**2.19.03b1**

* new:    issue #166: Added *size* and *blocks* added to v03.post format.
* bugfix: removed some incorrect ERROR messages (originally inserted to aid debugging.)
* bugfix: issue #162: use of python-amqp broken on ubuntu <= 16.04 because *connect* call missing.
* bugfix: issue #160: cleaned up v03 so it has no *sum* header (which should only be present in v02)

**2.19.02b2**

*
* new:    implemented WMO expert team on computing and telecommunication systems
*         (ETCTS, latest meeting: 2019/02) recommendations for changes to v03 format.
* new:    ETCTS201902 v03 whole messages is a single JSON *object* (like a python *dictionary*)
* new:    issue #146 ETCTS201902 v03 timestamps now have a "T" in them.
* new:    issue #148 ETCTS201902 v03 *sum* header changed to *integrity*, encoding changed from hex 
*         to base64.
* new:    issue #147 ETCTS201902 v03 added **inline** support to include file data in the announcements.
*         data is encoded in either utf-8 or base64.
* new:    issue #153 log rotation interval can now be set. Minues if you like.
* bugfix: issue #140 messages on console instead of log.
*


**2.19.02b1**

* new:    Added checksum caching in an extended file attribute (from Issue #54) 
* new:    Issue #130 - moved to new amqp library protocol changed from 0.8 to 0.9.1
* new:    exp_2mqtt.py -> bridge to export to MQTT brokers.
* new:    sample configuration: WMO_Sketch_2mqtt.conf 
* new:    windows installer available. Issue #122
* bugfix: windows Issue #111 - now works with drive specfications (C:)
* bugfix: debian package name, removed python3- prefix matches pypi, 
*         and better compliance with debian standards.
* bugfix: *remove* wouldn't in some circumstances. (bug from in v2.19.01b1)

**2.19.01b1**

* new:    optionally produce and consume experimental v03.post messages, 
*         headers now in body in JSON, removing 255 character limit.
* new:    save/restore format is now the same as the v03 payload.
*         (still reads old ones)
* new:    add post_topic_prefix setting (matches existing consumer topic_prefix)
* new:    added windows_run exe|pyw|py option to allow choosing of how components run.
*         one can invoke .exe files, or the script files with pythonw or python exes.
* new:    added suppress_duplicates_basis path|name|data to tune cache for use cases.
* bugfix: added documentation of preserve_time option (was missing.)
* bugfix: if *preserve_time* is off, posts will not have *atime* and *mtime* headers
* bugfix: if *preserve_mode* is off, posts will not have *mode* 
* bugfix: print a useful message if invalids sum algorithm specified.
* bugfix: change cleanup, setup, declare to connect once and fail, rather than hang.
* bugfix: when sr_post is a one-shot configuration, status makes no sense.

**2.18.12.b4**

* new: print exceptions on failure of makedirs, so "permission denied" is obvious
* documentation: shim\_ options for sarrac
* documentation: made importance of ordering between exchange and subtopic options clearer 
* documentation: change installation instructions so that paramiko is always installed.
* documentation: removed deprecation of *rename* header, there are valid use cases for it.
* documentation: extensive revision of mesh_gts briefing.
* bugfix: in pitcher_client.conf sample config, order of echange_suffix and subtopic option corrected.
* bugfix: copyright is GPLv2 only.  Notices incorrectly listed GPLv2 OR LATER.
* bugfix: more progress on issue #54 (application-defined checksums with extended attributes.)

**2.18.11.b5**

* bugfix:  reverting xattr dependency.

**2.18.11.b4**

* bugfix:  reverting paramiko dependency.
*          changing backslash warning text.

**2.18.11.b3**

* bugfix:  dependencies now correct for windows.
*

**2.18.11.b2**
* bugfix:  windows: Issue #54 support is broken on windows, disabled there.
*          print slashes the right way round on windows in more cases.
*

**2.18.11.b1**

* New:     Issue #54 initial support for *fake* (application defined) checksums.
*
* bugfix:  Issue #118 windows commands started from cmd.exe exit when window closed.
*          Issue #113 crash on sr_post/watch with post_exchange_split
*          Issue #112 windows log rollover 
*          Issue #101 windows git checkout corruption 
*          Issue #100 sr_subscribe add on windows gives files all on one line...
*

**2.18.10b2**

* new      Issue #106 plugins for hydrometric forecast data acquisition.
*          now have many more examples of polls.
* bugfix:  Issue #110 has_vip does not find vips.
*          unit tests referred to non SSL datamart, were broken
*          when it was de-commissioned.
*

**2.18.10b1**

* bugfix   corruption in cache cleaning introduced by pathname encoding.
* new      email ingest support added ( Issue #59 )

**2.18.09b2**

* bugfix   fixed duplicate suppression corruption when files have spaces in their names.
* bugfix   on windows: many issues with on \ vs. / addressed.
* bugfix   on windows, *edit* directive now works using notepad.exe by default.
* bugfix   on windows, *add* adds carriage returns to example files added, so notepad is happy.
* bugfix   on windows, *log* now works.
* bugfix   on windows, *list* now works for individual files.
* new      list now prints out log directory (which is hard to guess on windows)
* bugfix   examples for sr_Pitcher use case where inaccurate.
* bugfix   issue #99 *list* missed some items it should have listed.
* bugfix   *list* no longer list dot files or those ending in ~ (tmp/work/hidden files)

**2.18.09b1**

* bugfix    flow_setup was failing tests on rabbitmq server 3.7.7 (though it still worked.)
*           flow_setup fixed so it works with 14.04 (use python2 for pyftpdlib )
*
*    new    added dd_ping.conf to do easy test of broker function to examples.
*           flow_check.sh now does a spot check, flow_limit.sh limits the length of the test.
* change: flatten, mirror and strip options now affect only succeeding accept clauses. (Issue #80)
* disabling timeouts on windows, as they were not working anyways.
* added ${DD} to substitutions in directives
* added --version option. ( issue #25 )
* added rename option. ( Issue #92 )
* added globbing to include directive ( Issue #31 )
* many corrections to French documentation.
* bugfix issues #85 #86 


**2.18.08b1**

* BUG       claims to be 2.18.07b3 (missed commit of changing that.)
* bugfix    issue #76 sftp login passwords broken when any keys present. (from Marie!)
*           updated configuration for ECCC RDPS (from Sandrine.)
*           close_fds=false for older python to fix flow_test on ubuntu 14.04.
*
*    new    NEXRAD AWS polling (from Marie!)
*           more plugin documentation. 
*           dd.weather.gc.ca polling migrated to amqps.
*           catalogued two contributed implementations (Thanks Canberk & Tanner)


**2.18.07b3**

* bugfix     regression for subprocess api change @ V3.5
*            

**2.18.07b2**

* bugfix      HPC mirroring reports crash in retry logic, work-around, 
*             add try/except around it.
*             retry_ttl unit conversion error (was comparing milliseconds to seconds.) 
* new         poll_email_fetch - query and download from mailboxes. From Marie!
*

**2.18.07b1**

* bugfix      sr_audit now fixes missing instances. (issue #62 & #63 )
*             more output of plugin programs present in logs (issue #63)
*             two different crashes fixed in flow_test.sh
*             filter_wmo2msc directory tree naming improved ( issue #60 )
*             many documentation improvements. (Alain & Marie)
* new         enhanced parsing of date substitution (issue #55 Wahaj!)
*             now have program settings audit.conf  (issue #64 )


**2.18.06b2**

*             sr_poll bug for polling scripts fix from Jun.

**2.18.06b1**

* bugfix      sr_audit now runs for all users (restarts crashed components.)
* new         start post (sleep <= 0) now does nothing.
*             tested and added build instructions for RPM systems.
* doc         French docs done.
*             *sci-fi* (future planned features) removed from docs.
*             website migrated from sf.net to git repo ones (github, gitlab)

**2.18.05b4**

* bugfix      plugin msg_filter_wmo2msc.py fixed
*             sr_poll now uses its own set_dir_pattern to replace variables
*             sr_post/sr_poll/sr_watch fixed that a cache file for instance 000 was created
*             sr_post/sr_poll/sr_watch add caching of 'L' message
* new         sr_amqp for consumer sets channel.basic_recover(requeue=True)
* update      flow_post.sh posts lot of files within one call (load problem fixed)
*             flow_test does not test filename with space anymore
*             flow_test 5 instances for sender
* doc         miscellaneous doc fixups.

**2.18.05b2**

* bugfix       sr_sftp use chdir to see if connection is still alive
*              sr_http some site do not tolerate '//' in path
*              sr_subscribe some code added for sr_sender (lost in inheritance)
*              sr_file if a file does not exist and should be copied/linked just warn (Dominic)
* update       flow_test test2_f61.conf no use of post_total_save (race condition)

**2.18.05b1**

* bugfix       sr_sftp  differentiate put part vs put file 
* new          sr_retry uses caching for message uniqueness
*              sr_ftp,sr_sftp better connection test
* update       sr_poll  default post_base_url from destination url without password
*              sr_subscribe,sr_sender  log attempt
*              sr_subscribe retry.on_heartbeat on startup
*              sr_sender/sr_util if file to send does not exist... give it "attempt" chances
* doc          fixes and translation into french in progress
*              updated examples link, and samples directory cleanup

**2.18.04b5**

* bugfix  open local file read rb (instead of r+b)
*         remove .tmp file if upload does not work
*         sftp link and directory removal (from message)
* update  instance string using 2 digits (and code to migrate to)
*         switch for subprocess.check_call or subprocess.run 
*         give all chances to sigterm to complete
* new     inflight tmp/
*         If things go badly (general exception catch) keep message in retry
*         log when a retry message is dropped because it expires
*         poll accepts https (more test to do...not working with japan)
* doc     expanded description of *expire* setting.
*         Adding hint about use of *expire* option, how it is necessary for operations.
*         default setting is to avoid broker overload, too low for operational use.

**2.18.04b4**

* bugfix  destfn_script was not working
* update  sr_config.run_command presents subprocess check_call or run depending on python version
* new     inflight tmp/

**2.18.04b3**

* testing flow_test standardisation of messages
* bugfix  hb_retry no more dependency with on_start
*         sr_poll make sure all comparaisons are done without of trailing \n
* new     registered do_get,do_put
*         registered plugin, if return None, let python do it
*         plugin accel_scp.py
*         C has its own sarrac git repo
*         sr_config.py  '\ ' backslash_space allowed in options 
*         sr_config.py/sr_message.py  topic encodes  ' ' '#' with %20 %23
* update  flow_test standardisation of messages
*         sr_poll logs a warning when sleep time makes no sense
*         documentation launchpat for sundew
*         sr_audit log a message when --users all is done
*                   make sure heartbeat is in try/except 

**2.18.04b2**

* testing: Added recovery of flow_test stuck in retrying state.
* bugfix  C Truncate all headers and topic so they don't exceed 255 (AMQP limit.)
*         C Try to avoid being in conflict with stdin/out/err  open/close + 2 dup
*         C Valgrind hygiene: if nanosecond timestamp was 0, weird stuff happenned.  Fixed.
*           now valgrind does not complain at all.
*         C libsrshim enforced checks on commands'status
*         C any Python, topic and path with # encoded into %23 (as blank into %20)
* update  sr_audit hb_police_queues to check queue as admin, 
*           hb_sanity to check processes and sanity_log_dead option added            
*           no sleep option, sleep computed to trigger next heartbeat
*         sr_rabbit rabbit dependant commands placed in this file
* new     plugin do_send_log

**2.18.04b1**

* testing:retries on python side to validate products and routing
*         flow_post: loop on sorted individial products (spaces in path)... symlinks considered
* new     sr_subscribe: traceback logs when doing badly
*         sr_audit heartbeat works ... needs a config in audit/x.conf for now.
*         plugins: hp_sanity  uses sr sanity to check if program in strange state and log age to restart
*                  do_simulation logs protocol steps... instead of doing the actual download or send of a product
*         sr_config sundew_dirpattern provide a mean to use $RYYYY... etc in directory
* bugfix  C changes to return proper status of shimmed functions
*         C Get log file descriptor out of the danger zone also
*         C renameorlink put back code when oldname exists and processes it if link too
*         sr_retry : no more uses of self.activity and conditional retry heartbeat changed

**2.18.03b1**

* testing: changes derived expanded flow_test coverage
*        plugin msg_stopper with env MAX_MESSAGES
*        filename with spaces: ls_file_index (poll,sftp,ftp), sr_post.c, flow_post.sh
*        flow config changes : reject (hourly,today,yesterday xml)
*        plugins   : msg_pclean_f9*.py
*        sr_subscribe logging fix
* new    realpath_filter (PY and C), realpath also named realpath_post
*        sr sanity  check pid/process  and log age if older than heartbeat * 1.5
*        sr_audit not finished (heartbeat)
* bugfix Rotation of retry messages ajusted under certain conditions
* update msg_filter_wmo2msc.py requiered operationnaly now

**2.18.03a4**

* C      libsrshim dup3 (like dup2 for redirection)
* bugfix amqp.connection not working now showing reference to 'msg'

**2.18.03a3**

* bugfix sr using cleanup_parent (was cleanup)
* bugfix unlink cache_file under try:except
* bugfix sender posting fix from msg.new_*
* bugfix with exchange_suffix
* bugfix on plugins (return T/F) for on_start/on_stop incomplete
*        show on_stop/start plugin/modules at startup
* C      realpath_post T/F, realpath_filter T/F
* C      libsrshim processes  redirections  (dup2)
* subscribe on_report plugin implemented... and report_log plugin given as an example
* subscribe module check_consumer_options

**2.18.03a2**

* bugfix: C: revert stat passed to sr_post because used for hardlink
* rename option and in message header put back

**2.18.03a1**

* bugfix: C: on rename/mv : realpath option and stat attributes unused for oldname
* rename option and in message header withdrawn

**2.18.02a2**

* bugfix: C: posting, link... would cause problem depending on realpath value
* bugfix: C: posting, post_base_directory that started and/or ended with / might be missing a . in topic.
* documentation: renamed cp.py -> accel_cp.py, wget.py --> accel_wget.py

**2.18.02a1**

* change: no default broker (was dd.weather.gc.ca) caused more trouble than help.
* feature: pluggable checksum algorithms implemented.
* feature: sr_poll is now recursive.
* feature: can use URL's in config & 'include' directives... also: remote_config_url added.
* feature: python https & ftps download support added. (was an omission.)
* feature: code now has msg_count available (number of queued messages at broker.)
* feature: config can use api instance variables from application ex.: ${broker.username}
* plugins: on_start/on_stop support completed,  
* plugins: root_chown.py, trace_on_stop.py
* plugins: hb_memory now prints cpu usage.
* bugfix: C: queue_name random seed wasn't. 
* bugfix: *restart* no longer restarts unless old process is really gone (used to kill and hope.)
* bugfix: sr_log2save.py was broken (old log file format), now runs on post_log at least
* bugfix: path option when varsub and post_base_dir was implied
* bugfix: posting remote file via polling: length = 0 when message has minimal infos
* bugfix: sr_poll.py cache.check only if cache enabled
* bugfix: sr_post rename paths wrong  oldname/newname (post_base_dir was not removed)
* bugfix: sr_post/sr_poll on_post events now have new_dir/new_file as per other plugin entry points.
* bugfix: C: components crash on add when SR_CONFIG_EXAMPLES is not set. Now complain and error exit.
* performance: added dictionary to speed up cache when multiple entries have same sum.
* flow_tests: unit tests, mirroring, will cope with log rotations

**2.18.01a5**

* added *exchange_suffix* and *post_exchange_suffix*
* *cleanup* action aborts if running. (py and C)
* *cleanup* action removes .cache files and directories. (py and C)
* *remove* action calls cleanup. (py and C)
* Documentation: added mirroring use case.
* retry logic refactored. performance substantially improved. more correct.
* added detection of too short heartbeat interval.
* C: added prefetch option.
* many improvements to flow_tests (improved QA)
* sftp will now not report an error if a file it is supposed to delete is not there. (jobs is done.)
* re-worked wget plugin so the stdout and stderr are printed.
* list action now prints properly (includes the examples) when user has no configurations.
* added pitcher and sci2ec use cases to examples.

**2.18.01a4**

* made new style plugin examples work with older python.
* added new style: cp.py and wget.py plugins.
* fix: the new api was broken by old python fix.

**2.18.01a3**

* fix to error message about *object has no attribute 'do_download_list'* 
* disable new plugin api on python < 3.4 to avoid error messages.

**2.18.01a2**

* likely fix included for 1 in 200 file missing in HPC mirroring.
* added on_start, and on_stop to plugins available.
* combined plugin parser for all plugins in one module. Improved error checking.
* C: now imports version info from python, so C version is meaningful (instead of always 1.0.0)
* fixed: column width hack for older versions was busted.

**2.18.01a1**

* C: made consumer tag meaningful (identifies hostname and pid of consumer.)
* added version check and work around because get_terminal_width on python3.2 ( ubuntu 12.04 )
* C: subscribers creating consumer for each message. api/usage wrong. Fixed.
* added log_settings to display all settings on startup.
* noticed wrong default settings on startup:  durable was false, should be true.
* noticed wrong default settings on startup:  prefetch was 1, supposed to be 25.
* flow_test: redirected much output to log files.
* flow_test: added some libcshim (via cp command) based posting (in c diagram.)
* flow_test: moved sr_poster code into flow_setup, so it is started at beginning instead of run in flow_check.
* Corrected that *inflight* option was NONE on sender.  It was documented and intended to be '.tmp'.
  now it defaults to '.tmp' but if there is a post_broker, it defaults to NONE.
* added info messages for cases where msg_received, but the log does not say what happenned (rename/link/mv cases.)
* times used to be truncated to milliseconds, now the natural number of places after the decimal are retained.
* C: fix: mv called from shim where no directory in old file name caused malformed *oldname* field in resulting post.
* C: fix: segfault if credentials.conf is missing.

**2.17.12a8**

* added exponential backoff on failure to main processing loop in sr_subscribe.
* added exponential backoff to main retry loop in sr_consumer.
* now recovers from syntax errors in retry files (json.decode errors.)
* c: segault in mv if there's no slashes in the source path, oops!
* added identifiers to differentiate all the Type: messages from exceptions.

**2.17.12a7**

* C: added SR_CONFIG_EXAMPLES environment variable.
* C: change C to use four digit instance numbers to match python.
* C: add *declare* option for variables. 
* C: Remove *flow* option.
* fixed: second field in options was not being checked for variable substitution.
* fixed: remove did not work for disabled configurations.
* added sr_pulse.7 man page.
* made 'add' look in sample directories.
* 'enable' and 'remove' weren't working.
* 'list' now includes sample configurations, if available.
* change retry_ttl to default to the value of 'expire'.  Can still override.
* C: realpath wasn't properly applied in shim library cases.
* removed 's' from the 'headers' option in python, to match C.
* python added 'expiry' as synonym for 'expire', to match C.
* C: realpath only applied if an absolute path was supplied, now works for relative ones also.
* heartbeat_memory uses psutil.memory_info, on python 3.4 (in ubuntu 14.04) that routine is called get_memory_info.
  added an if statement so it works for all cases.

**2.17.12a6**

* heartbeat processing surrounded by exception to avoid cpu-hang when plugin has an error.
* list categorizes configuration files.
* list now prints the directories containing configuration files for each category.
* list prints plugins available also, and listing a particular plugin works now as well.
* list now uses a PAGER, if configured, and *more* by default, rather than cat.
* Normally stderr is redirected to logs, but when debug was set it wasn't. Now it always goes to logs.
* added messages so heartbeat processing is visible.
* sr_shovel would freak out if cache was set. fixed.
* fixed heartbeat_memory so it works in sr_watch.
* C: implemented *source* option
* C: corrected picking of "main file" for configuration name.

**2.17.12a5**

* added exponential backoff to download failures.
* inactive work committed for long lasting flow tests (deletion while in progress.)
* C: added exponential backoff to retry, avoid hammering servers when they're sick.

**2.17.12a4**
* added exponential backoff on retry, so it doesn't SPAM/hammer server when retrying.

**2.17.12a3**

* added retry_ttl to have retry queue give up eventually.
* changed behaviour to try *attempts* times before putting in the retry queue
* buffering changed from 8K to 1M (awful performance regression due to timeouts on small bufs.)

**2.17.12a2**

* bugfix: sr_watch was ignoring event option.
* C: added recovery code after posting errors.
* heartbeat_memory plugin added by default to control runaway memory leaks.
* support added to python for N checksum (already in C version.)

**2.17.12a1**

* bugfix: sr_post sometimes required -p.  It shouldn't.
* Semantics of *accept_unmatch* changed. Before the option was ignored, and set based
  on the existenceof accept/reject clauses. This caused some strange behaviours.
  now *accept_unmatch* setting is honoured.  default to False in subscribe and sender,
  and to True in all other components (winnow, shovel, post, poll.)
* bugfix: report_exchange option was ignored and overridden.
* undocumented, and unused option 'use_pattern' withdrawn.
* heartbeat_cache plugin added in option parsing rather than forced at end.
* sr_poll now supports sum algorithms other than z to support polling of local files.
* documentation bugfix: invalid links to sr_subscribe.7 corrected to sr_subscribe.1
* testing added cases to simulate communications problems, such as message corruption.
* bugfix: SENDER=X, filename would be =X, instead of X.
* bugfix: sender used to print "Sends:" before sending a file, now prints "Sent:" afterward.
* retry logic changed. Now write to a retry queue file, and try again when there is a lapse.
  so it doesn't get "stuck" on old files, but keeps sending new stuff. catches up gradually.
* timeouts for many parts of transfer processing added.
* transfer code consolidated into one location rather that repeating in each protocol.
* *Pulse* messages added, to ensure connection stays live.
* some round-tripping added in heartbeat processing to ensure connection remains live.
* C: fixed: was putting wrong checksum in posted messages.
* C: now retries connection to broker forever (used to give up after one try.)
* C: bugfix: pbu synonym for post_base_url, was not accepted, corrected.
* C: fixed when renaming across file systems, it would fail, rather than copying the file.

**2.17.11a3**

* sr_post -p|-path optional ending arguments are postpaths
* sr_config  by default use_pika only if amqplib not available
* sr_poll  vip written once, heartbeat_check before vip check
* sr_instances sr_post foreground as a special case (no config)
* sr_subscribe heartbeat_check before vip checking
* sr_util startup_args generalized/simplified 
* sr_util sumflg 0,random(0,100)
* sr_watch merged into sr_post (inherited from sr_post now)
* sr_watch post directory content at startup (if not cached)
* sr_subscribe  revert onfly_checksum set to message checksum in case unset


**2.17.11a2**

* C: fixed: build configuration directories if missing (used to segfault.)
* C: fixed: *debug* setting misinterpreted.
* C: fixed: option base_dir, should have been post_base_dir
* sr_watch remnants of old cache code causing problems, removed.
* sr_watch fix for mtime check of file which was renamed.
* documentation improvements.
* fixed: list,get,remove,edit,log not working for other than subscribe.
* excessive debug messaging removed.


**2.17.11a1**

* sr_subscribe bug fix for SOURCE 
* sr_subscribe add module __on_file__
* sr_sender    as flow test demonstrate, option post_base_url is not mandatory
* sr_instances propagate action and permits edition of general files (admin,defaults,credentials)
* sr_instances adds actions : add, disable, edit, enable, list, log, remove
* sr_instances calls configure before build_parent to have all options set
* sr_post/sr_watch get rid of useless lock stuff... fixed cache problems
* sr_poll      able to use standard sr_file...
* sr_(s)ftp/http  when preserve_mode is true... bug fix on setting value of mode
* sr_file     adding some support for polling (standardisation)
* sr_consumer file queuename ends with .qname and link to old file (to preserve version compat)
* sr_config   late of user_log_dir and user_cache_dir to insert hostname if statehost is True
* sr_config   statehost inserts hostname in user_cache_dir and user_log_dir
* sr_config   module declare_option  makes program know about plugin options
*             so program would warn only on real unknown or erronous options
* sr_config   withdrawal of recursive option, set to True everywhere applicable
* sr_config   log setup easier, supports loglevel none meaning no logs
* sr_amqp.py  when using pika, no log if delete_queue and queue not found
* sr_amqp.py  option use_pika to use or not pika when available
* sr_amqp.py  mixing amqplib and pika depending of availability
* sr_*        withdraw msg.headers['filename'],  msg.headers['flow']
* sr_*        reenforcement of base_dir, post_broker, post_exchange, post_base_dir, post_base_url

**2.17.10a4**

* C: msg pretty printer now includes user defined headers.
* C: loglevel now accepts words: none, critical, error, warning, info, debug. (like python version.)
* C: logevel numbers inverted (formerly 99 was be very quiet, no 0 is quiet.)
* switched library dependency from amqplib to pika.
* fix for no_download switch which wasn´t impeding downloads.

**2.17.10a3**

* C: directories posted during rename. not sure what effect is.
* documentation consolidated to sr_subscribe, much duplication gone.
* C: sr_cpost force_polling works properly now (using cache.)
* C: bugfix double free segfault on exit.
* C: added directory support to sr_post_rename
* C: libsrshim: added support for the truncate(2) system call.
* many fixes based on deployment testing.
* support files names with spaces in them.
* call on_file plugins when symbolic link created.
* sr_config    : environment variable substituted for option value
* sr_sender    : on_msg msg_2localfile now by default (so no longer need to specify for every sender.)
* sr_subscribe : changing determination of source (source_from_exchange or missing)
* rmdir support (python only.)

**2.17.10a2**

* add regexp option to strip.
* now support environment variables in config files with ${var}
* bugfix: misbehaved when file names have blanks in them.
* added -header option to sr_post.
* fix for bug #74 - error messages on shutdown of amqps connection.
* C: cpost setup/cleanup/declare/restart etc... some were broken, fixed.
* C: added sighandler to avoid cache corruption when terminating.
* C: add rename support to cpost (was only in libcshim and python before.)
* C: bugfix: C was inventing fields if not provided (mode=0, mtime="").
* C: added tx.select & tx.confirm (publish acknowledgements)
* C: FIXME: not yet: basic_ack (consumer acknowledges only after successful processing, rather than on receipt.)
* C: integrated into flow_tests.

**2.17.10a1**

* cleanup/declare/setup actions (all programs): no exit, log with configname
* sr_subscribe/sr_sarra/sr_sender : do_task plugin (initialised to proper module for now)
* sr_subscribe: headers' source and from_cluster forced when source_from_exchange
* sr_subscribe: add substitution for ${DR} ${PDR} ${YYYYMMDD} ${SOURCE} ${HH}
* sr_subscribe  log ignore message when already in cache
* sr_subscribe: events option is consider to perform link and delete messages
* sr_subscribe: modified to be a base class instantiated from most programs
* sr_subscribe: integration of restore_queue, process report_daemons, save/restore
* sr_subscribe: help module : treats sr_shovel,sr_winnow,sr_sarra cases
* sr_sender: for R and L messages skip offset/length setting in module set_local()
* sr_shovel: caching optional default to False
* sr_config: some save,restore and cache defaults
* sr_config: inflight supports duration_from_str (for sr_watch/post)
* sr_config: duration_from_str  time suffix [sS] [mM] [hH] [dD] [wW] where applicable
* sr_config: module configure cleans up extended options (proper reload)
* sr_config: option -headers to add,delete or reset user's  key,value pair in message headers
* sr_ftp,sr_sftp: connect/reconnect resets cdir (current dir)
* sr_ftp,sr_sftp,sr_http: standardisation, http exception (no hang)
* sr_ftp,sr_sftp,sr_http: fix Eric's os.getcwd bug, add preventive fp.flush and os.fsync
* msg_total.py: plugin skip total byte increment when no partstr in message
* sr_message: move support with oldname/newname (impact watch,post,subscribe,sarra,sender to come)
* sr_message: srcpath turned to baseurl, set_notice(baseurl,relpath) --impacts all programs--
* sr_message: trim_headers for user added headers key,value pair  --impacts all programs--
* sr_cache: module cache.check_msg ... process correctly message without parts (sum L and R)
* sr_audit,sr speed up through class instantiation and direct broker connection
* sr_audit fix permissions for source and subscribe users
* sr_amqp,sr_pika: cleanup skip removal of exchanges xpublic,xreport,xwinnow*
* sr_util:  startup_args catches -help when only args given
* flow_test: several changes to make it more reliable.

**2.17.09a1**

* FIXME: do old cache files need to be deleted during upgrade? update RELEASE_NOTES
* expire DEFAULT CHANGED:  7 days -> 5 minutes.  Avoiding pump overloading turns out to be critical.
* new plugin msg_to_clusters, simplified replacement of inter-cluster routing logic.
* sr_watch, returned to recursive formulation of sr_watch, reduces overhead substantially.
* flow_test now includes ftp download test.
* flow_test now uses sr_audit, queues and exchanges extant now tested.
* flow_test now waits for queues to drain (so it works more often.)
* fix (bug# 88) for sr_audit creating report queues with no consumers. 
* sr_poll and plugin/poll_script.py post with parent.post  (srcpath,relpath instead of url)
* flow_templates under poll|post|watch modified not to generate errors in flow logs
* flow_templates shovel t_dd[12].conf  reject .*citypage.*  to avoid errors in flow logs
* plugin/msg_by_user.py now considers msg.report_user for v02.report messages (correct error in flow logs)
* flow_check.sh shows classified list of errors in log or report No error found
* sr_poster unused in sr_poll, sr_winnow, sr_sender, sr_shovel
* sr_winnow, sr_subscribe supports caching on messages
* sr_config  post_url option equivalent to url
* sr_subscribe support posting if post_broker is set (and other post options)
* plugin heartbeat_cache : cache clean/save + stats if cache_stat = True
* all program consuming... calls heartbeat_check themselves
* move hearbeat code from sr_consumer to sr_config
* cache is cleaned every heartbeat.


**2.17.08a1**

* sr_pika tested with flow stuff...
* sr uses .config/sarra/post directory ... check for option sleep to call sr_cpost
* throttle use better time function
* sr_message  topic without filename
* sr_http  timeout + self test
* sr_sftp self test works
* sr_sftp/sr_ftp call self.close on download or send problems
* sr_sftp minimal credentials based on SSH configs being ok
* sr_sftp read/uses ~/.ssh/config if needed/provided
* sr_sender sftp/ftp bugfix now honours *mirror true* default. was ignored before.
* sr_cache same algorithm as the C implementation
* getting rid of cluster routing logic, gateway_for/, to be implemented with plugins.
* debian packaging for C. 
* C posting library, including sr_cpost that replicates post and watch is complete.
* C libc shim that calls C posting library complete.
* getting rid of random checksums (L & R -> SHA512 digest.)

**2.17.07a4**

* changed *chmod* interpretation. Was obsolete in favour of umask, now an option to override umask.
* bug fixes for chmod not being done in a number of situations where it was required.

**2.17.07a3**

* on_heartbeat support added to sr_watch.

**2.17.07a2**

* on_post plugins were broken in 2.17.07a1 
* on_heartbeat now defaults to heartbeat_log as one would expect, and documented both.

**2.17.07a1**

* sr_sarra bug fix os\_.exit
* All sarra programs have standard invoke : pgm [args] action config... old way still supported (MG)
* sr_util defines a function startup_args to parse sarra program arguments (MG)
* sr_audit --users : makes sure exchanges/queues configured on pump are setup (MG)
* all programs manage exchanges/queues through action 'cleanup','declare','setup' (MG)
* sr_poll nows supports http (MG)
* sr_poll start posting without parts when it has no clue for size (MG)
* on_html_page added in config and sr_poll with default http_page.py (MG)
* on_watch added in config and sr_watch (MG)
* sr_http.py now has a valid class sr_http (used in sr_poll) (MG)
* mode bits limited to the last four digits (upper digits non portable anyways.)
* C implementation of libsrshim, libsarra, sr_cpost, and sr_subjsondump  in C (not packaged yet.)
* fixed bogus error message from backward compatibility plugins.
* added mtime check to sarra and sr_subscribe so that if of new file is <= file_on_disk, then don't download.

**2.17.06a3**

* git repo url was wrong. Thanks Canadian Tire!
* compatibility editing local_file (full path) now results in setting new_dir and new_file.
* still harmonizing sender vs. subsribe api senders use parent.new_file, subs use parent.msg.new_file
* fixed sender using ftp broken by error message referring to *remote_urlstr* ( replaced by *new_urlstr* )
* files were created as public write because umask was overridden. Dunno why it was there in the first place.
* strip fixed in sr_subscribe.
* flatten fixed in sr_config.
* crasher bug when sr_sender doesn´t have a post_broker.

**2.17.06a2**

* added chmod_log for log files, which were defaulting to public writable... no idea why, set default to 600.
* changed posting default for to_clusters from ALL to the hostname of the broker.
* moved accept/reject processing into sr_poster.post, so automatically honoured when using plugin scripts that call it.
* fix bug#86 DESTFNSCRIPT in one accept would be used by subsequent ones.
* fix bug#51 now use new_path, rather than local_path in consumers, and remote_path in senders. all can use same plugins.
  includes warnings for existing plugins to change their variable names, old ones should still work, just prompt warning in log.


**2.17.06a1**

* Added default value of 'ALL' for *to_clusters* of  and *gateway_for* to make those options... optional.
* Adding *preserve_time* option (default: True), to have mtime from source reflected in files written.
* Adding *preserve_mode* option (default: True)  the move mode bits from source reflected in files written.
* deprecating *interface* setting, code from Jun. one less thing to set. Now scans all interfaces for *vip*
* polling script should still sleep for *sleep* seconds if the script fails. busyloop is bad.
* added download_dd plugin, which does multiple process copies (striping individual files.)
* documentation improvement: made *blocksize* the main partitioning option, *parts* is developer only.
  there was an error in that usage of parts actually referred partially to blocksize
* fixed blocksize=1 to mean send entire file, not 1 byte blocks.
* fix bug#66 for sr_sender to put the actual file name on the destination (after destfn, etc...) 
* sr_sarra: suppressedn excessive messages about who has vip in debug mode.
* sr_sarra:  fixed -strip.  Did not work at all before.
* added the poll_script.py plugin as an example for sr_poll.
* fix from Eric for wrong permissions in sr_sftp.
* removed useless import in line_mode.py plugin which breaks it on python 3.2
* fix from Eric for wrong permissions in sr_ftp. (bug #84)
* added version strings to components log and usage outputs.
* added sr_poll to flow_test (from Daniel)
* some re-organizing of code in sr_watch.
* implement 0400 default permission mask in sr_poll.
* note on how to encode special characters in passwords in credentials.conf
* some plugin improvements from Dominic Racette.

**2.17.03a5**

* added sr_watchb... the old implementation as a backup in case the new sr_watch is busted.
* attempted fix for sr_watch permission denied issue.  Reformulated how recursion is done.
  now it just queues up issues for later.

**2.17.03a4**

* attempted fix for bug #79 (.tmp file stay when download fails.) not tested.
* added 's', SHA512 checksum support.
* after a shovel has restored a queue from a save file, it now exits.
* on repeated saves, the json save files came out different for the same messages.
  Fixed by adding sort_keys=True to dumps. now save of same files is bitwise identical.
* added 'attempt' setting to make the number of retries programmable.
* fixed on_line plugins being broken in sr_poll.
* fixed 'reject' not working in sr_poll.
* added -save_file option to shovel and sender to allow arbitrary locations for save files. 
* report_daemons False option setting now stops report routing shovels from starting.
* added file_age.py to plugins examples.

**2.17.03a3**

* added sr_log2save a little filter to extract reloadable messages from log files.

**2.17.03a2**
*  release of a1 broke in the middle, had to use a new tag.

**2.17.03a1**

* feature #61: save/restore Deal with large queues on brokers by persisting to disk.
* bug #77: fixed. crash on file deletion when inflight is numeric. 
* feature #61, sr_sender -save/-restore to avoid broker queues implemented.
* bug #78: fixed. posting symlinks now works.
* bug #76: fixed. sr_audit will now only start if the admin option is set in default.conf
  only need one sr_audit for each pump.  having more isn't a problem, but dozens are stupid.
  for deployment to a cluster, need to run on hundreds of nodes, stop running hundreds of useless instances.
* sr_watch now indicates the exchange being published to on startup.
* feature #56: system startup (init file and/or systemd service) now installed with package. might be a bit shaky...
* bug (not submitted) problem with truncation on sftp sender, missing argument.
* developer: flow test improvement: added verification of content sent by sr_sender.
* bug (not submitted) all DESTFNSCRIPT are broken in last release.  Fixed now.
* sr_subscribe with no directory spec was broken. default to pwd as one would expect. Fixed now.
* changed build-dep from python-docutils -> python3-docutils.

**2.17.02a1**

* Summary: added some understanding of symbolic links. 
*          sr_watch will be faster in many cases, many improvements.
*          sr_post now accepts normal file specifications (more than 1, and relative paths)
*          Any component can now use vip/interface for active/passive.  Cluster configurations more flexible. 
*          programming: can have more than one plugin for on_*, they now stack sequentially.
*          programming: do_download plugin examples added for use of wget or scp.
*          other small improvements.
*
* Details:
* Added symbolic link processing (sr_watch, sr_post, sr_sarra, sr_subscribe, sr_sender)
  Caveat: links are mirrored as-is.  Likely the wrong thing to do for absolute ones. Suggestions bug#70 welcome.
* sr_post: now works with relative paths, and * etc... can post multiple files and/or directories at once.
* sr_post: simplified partitioning options:  blocksize eliminated, replaced by 'parts'
* sr_post: parts 0 - autocompute part size, 1- always send files in a single part, <sz> used a fixed size.
* sr_watch: events keywords changed: modified->modify, created->create, deleted->delete.
* sr_watch: event keyword for links:  link - mirror symbolic links
* sr_watch: added inflight xx  to ignore files until they have not been modified for > xx seconds.
* sr_watch: symbolic link processing significantly changes paths produced, as realpath no longer used.
  This should be perceived as an improvement (paths look more familiar).
* sr_watch: enabled inotify observer (can be hundreds of times faster to notice a change in a large tree.)
* sr_watch: added *force_polling* toggle option to allow user selection of slower method (polling observer)
* sr_watch: added *follow_symlinks* toggle option. 
* sr_watch: process groups of events with a single cache lock/unlock.  Provides 4-10x speedup.
* sr_watch: added 'realpath' option.  Earlier versions use 'realpath' all the time, which changes
  paths read significantly when directories are symbolically linked.  So default was changed to not do that.
  Can obtain old behaviour by spcifying this option (listed as a developer option.)
* plugins: are now stackable, when on_message encountered it is added to the list of plugins, 
  rather than replacing a single one.
* plugins: added alternate downloading examples:  (download_scp, download_wget,  msg_download )
  This is used to invoke high speed xfer mechanism, such as bbcp.
* sum 0: the sum 0 algorithm is changed to produce random checksum, rather than constant 0 to improve load balancing.
* sr_audit: changed 'role' directive to 'declare' to allow declaration of things beside users. See following line:
* sr_audit: added 'declare exchange' to permit creation of exchanges.
* developer: flow test improvement: essentially re-written to improve reliability, and shorten.
* developer: flow test improvement: now checks every item, rather than sampling, results more reassurring.
* developer: flow test improvement: cumulative status (of all tests.)
* developer: flow test improvement: compare actual downloads vs. watch.
* developer: flow test improvement: programmable number of items to collect before verifying.
* feature #59: #!/usr/bin/python3 -> #!/usr/bin/env python3 ... harmless... 
* feature #56: started. systemd support file begun, more testing required.
* feature #54: done. added Active/passive options to all components (vip & interface support.)
* feature #53: done. sr_watch 'inflight' implements mtime work.
* feature #52: done. plugin-stacking.
* bug #74: workaround ( sr_post to an ssl broker prints scary (but harmless) message after succeeding, messge suppressed. )
* bug #73: sr_sender overwriting files with shorter new versions leaves old content) fixed.
  General bug fix for over-writing of files when new shorter than old (sftp mostly)
* bug #72: fixed ( sr_sender -strip now works. )
* bug #71: fixed ( sr_audit user creation ) 
* bug #70: started ( sr_watch symbolic link handling ) mitigated.  Unclear if really fixed.
* bug #68: fixed ( sr_sarra part of flow test improvements above.)
* bug #67: fixed ( config files always parsed twice. )
* bug #45: fixed ( sr_sarra will not delete local files ) 

**2.16.11a4**

* Added moving of log directory from var/log -> log, and replacement of var directory with a symlink.
* Added setting of passwords by default for broker users by sr_audit.
* Added --reset flag interpretation by sr_audit so that permissions can be updated easily for all users.
  So now when upgrading after 'log' -> 'report' transition, just do:
    
  ``sr_audit --reset True --users foreground``
    
  and it will overwrite all the permission regexp's of the broker users.
  If someone has funny permissions, that could be a problem.  
* Added 'set_passwords' flag to sr_audit, defaulting to True.
  if set to false, users are given blank passwords.... not sure if this is useful.
  trying to understand what to do with this in the case of LDAP based users.  
* Added creation of send directory to flow_setup.sh 
* un-commented the over-ride default exchange for reporting in tsource2send.conf...
  it still needs overriding.  
* Corrected the regexp permission masks to allow sources to write to any
  exchange that starts with xs_<user>... rather than just specifically that source.  
* Corrected the regexp permissions to allow reading by subs from same.  
* Reverted patch in sarra that broke download URL's.
* Add old log exchanges to sr_audit for compatibility with pre-transition clients.
* Changed test of sender to compare against the ones watch, rather than subscriber.
* Added measurable test to flow test for sender.
* Adding sr_watch to flow_test.
* Added sr_sender to flow test.
* Removing '/var' so log files are in the normal place now.
* Optimizing the flow_test script (so it's shorter, more straightforward and regular.) 
* Documentation cleanup

**2.16.11a3**

* Fixing a cosmetic but ugly bug. Caused by the URL fix
* Add unready list to prevent posting unreadable files

**2.16.11a2**

* fix bug #61: change outputs to better present URL's in logs.
* just naming of some routines that were imported from sundew, add prefix ``metpx_``...
* fix bug #54:  Adds interpretation of sundew-specific delivery options to sr_subscribe.

**2.1611a1**

* Another String too long fix.
* Potential fix for bug #55 (chdir)

**2.16.10a2**

* Fix issue #42 (header length in AMQP)
* Numerous doc changes

**2.16.10a1**

* Fixes to self test suite
* Added calls to the usage strings on a bunch of components
* Added centralized time format conversion in sr_util
* Added sr_report(1) manual page.
* Bugfix for headers too long.
* Patch to sr_poll to prevent crashing with post_exchange_split.
* Tentative fix for bug #50 improper requirement of write permissions
* Process headers dynamically
* Documentation Updates.

**2.16.08a1**

* Major Change: Changed "log" to "report" in all components.
* Added test case for sr_sender
* Documentation Update

**2.16.07a3**

* Ian's fix for sr_sender borked with post_exchange_split.
* Jun's fix for chmod and chmod_dir to be octal.

**2.16.07a2**

* Fixed typos that broke the package install in debian

**2.16.07a1**

* Added post_exchange_split config option (allows multiple cooperating sr_winnow instances) code, test suite mode, and documentation.
* fix logger output to file (bug #39 on sf)
* sr_amqp: Modified truncated exponential backoff to use multiplication instead of a table. So can modify max interval far more easily.  Also values are better.
* nicer formatting of sleep debug print.
* sr_post/sr_watch: added atime and mtime to post. (FR #41)
* sr_watch: handle file rename in watch directory (addresses bug #40)
* sr_watch: fix for on_post trigger to be called after filtering events.
* sr_sender: Added chmod_dir support (bug #28)
* plugin work: Made 'script incorrect' message more explicit about what is wrong in the script.
* plugin work: word smithery, replaced 'script' by 'plugin' in execfile. so the messages refer to 'plugin' errors.
* Added plugin part_check, which verbosely checks checksums,
* plugin work: Added dmf_renamers, modified for current convention, and word smithery in programmers guide.
* Tested (de-bugged) the missing file_rxpipe plugin, added it to the default list.
* Documentation improvements: sundew compatibility options to sr_subscribe.
* Documentation improvements: moving code from subscriber to programming guide.
* Added a note for documenting difference between senders and subscription clients in the message plugins.
* Made reference to credentials.conf more explicit in all the command line component man pages. (Ian didn't understand he needed it... was not obvious.)
* Moved information about how to access credentials from plugin code from subscriber guide to programming guide.
* Turned a bit of the sr_watch man page into a CAVEAT section.
* Added a note about how file renaming is (poorly) handled at the moment.
* Test suite: removing overwrites of config files from test_sr_watch.sh
* Test suite: Continuing the quest:  getting rid of passwords in debug output,
* Test suite: adding explicit mention of exchange wherever possible.
* Fixed self-test to authenticate to broker as tfeed, but look for messages from tsource.

**v2.16.05a2**
  
* plugins improved.
* sr_winnow fixed.
* stop printing passwords in log files.
* beginnings of flow_test implemented. ( self-testing configuration with multiple components fed.)

**v2.16.05a1**

* something about log message settings and permissions.
* reviewing log message generation (older versions too voluble.)
* setting a plugin to None removes it.
* moved logging mostly into plugins to make it more modular.
* added permission of user to read own exchange.
* added plugin examples to subscriber guide.
* working through Michel's self-tests, trying to get them to work.
* Added Programmer Guide.
* sr_sender modified to use truncated exponential backoff (to avoid hammering sites when they are down.)
* some credits.

**v2.16.03a10**

* documentation fixes.
* fixed sr_audit which had been broken.
* added 'foreground' to start/stop/status in usage statements.
* Daluma input on sr_watch.
* stop sr_audit from downloading rabbitmqadmin into cwd.
* Michel retired :-)

**v2.16.01a8**

* for earlier releases, please consult git log.

**v2.16.01a3**

**v2.16.01a2**

**v2.16.01a1**

**v2.15.12a4**

**v2.15.12a3**

**v2.15.12a2**

**v2.15.12a1**

* first version with all components extant.
* Build/tag process introduced.
* until now, had just been using master branch in git. 

**0.0.1**
* development began in 2013.

* Initial release
