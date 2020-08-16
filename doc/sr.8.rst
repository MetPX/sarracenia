====
 SR 
====

----------------------------
sr Sarracenia Management CLI
----------------------------

:Manual section: 1 
:Date: @Date@
:Version: @Version@
:Manual group: MetPX-Sarracenia

.. contents::

SYNOPSIS
========

**sr** declare|dump|list|show|setup|start|stop|restart|status 

DESCRIPTION
===========

**sr** is a global startup/status/shutdown tool to manage grouped configurations.
For the current user, it reads on all of the configuration files, state files, and 
consults the process table to determine the state of all components.  It then 
makes the change requested.

In general, sr will print a '.' to signify progress (sometimes a dot 
represents a configuration, other times a process) 

**declare|setup**

Call the corresponding function for each configuration::


  blacklab% sr declare
  gathering global state: procs, configs, state files, logs, analysis - Done. 
  declare...
  ...............................Done
  
  2019-08-25 11:58:19,383 [INFO] sr_poll pulse declare
  2019-08-25 11:58:19,383 [INFO] Using amqp module (AMQP 0-9-1)
  2019-08-25 11:58:19,440 [INFO] declaring exchange xpublic (bunnymaster@localhost)
  
  2019-08-25 11:58:19,500 [INFO] sr_poll f62 declare
  2019-08-25 11:58:19,500 [INFO] Using amqp module (AMQP 0-9-1)
  2019-08-25 11:58:19,537 [INFO] declaring exchange xs_tsource_poll (tsource@localhost)
  
  ...

  blacklab% 

The points represent the launching of the processes to run the operation for one configuration.
The outputs are the results after they complete.

**dump**

print the three data structure used by sr.  There are three lists:  

* processes thought to be related to sr.

* configurations present

* contents of the state files.

*dump** is used for debugging or to get more detail than provided by status:: 

    Running Processes
         4238: name:sr_poll.py cmdline:['/usr/bin/python3', '/home/peter/src/sarracenia/sarra/sr_poll.py', '--no', '1', 'start', 'pulse']
         .
         . 
         .
    Configs
       cpost 
           veille_f34 : {'status': 'running', 'instances': 1}

    States
       cpost
           veille_f34 : {'instance_pids': {1: 4251}, 'queue_name': None, 'instances_expected': 0, 'has_state': False, 'missing_instances': []}

    Missing
       

It is quite long, and so a bit too much information to look at in a raw state.
Usually used in conjunction with linux filters, such as grep.
for example::

    blacklab% ./sr.py dump  | grep stopped
        WMO_mesh_post : {'status': 'stopped', 'instances': 0}
    	shim_f63 : {'status': 'stopped', 'instances': 0}
    	test2_f61 : {'status': 'stopped', 'instances': 0}

    blacklab% ./sr.py dump  | grep disabled
        amqp_f30.conf : {'status': 'disabled', 'instances': 5}
    blacklab%

provides easy method to determine which configurations are in a particular state.
Another example, if *sr status* reports sr_shovel/pclean_f90 as being partial, then 
one can use dump to get more detail::

    blacklab% ./sr.py dump | grep pclean_f90
    4404: name:sr_shovel.py cmdline:['/usr/bin/python3', '/home/peter/src/sarracenia/sarra/sr_shovel.py', '--no', '1', 'start', 'pclean_f90']
    4415: name:sr_shovel.py cmdline:['/usr/bin/python3', '/home/peter/src/sarracenia/sarra/sr_shovel.py', '--no', '3', 'start', 'pclean_f90']
    4417: name:sr_shovel.py cmdline:['/usr/bin/python3', '/home/peter/src/sarracenia/sarra/sr_shovel.py', '--no', '4', 'start', 'pclean_f90']
    4420: name:sr_shovel.py cmdline:['/usr/bin/python3', '/home/peter/src/sarracenia/sarra/sr_shovel.py', '--no', '5', 'start', 'pclean_f90']
        pclean_f90 : {'status': 'partial', 'instances': 5}
        pclean_f90 : {'instance_pids': {4: 4417, 3: 4415, 2: 4412, 1: 4404, 5: 4420}, 'queue_name': 'q_tfeed.sr_shovel.pclean_f90', 'instances_expected': 5, 'has_state': False, 'missing_instances': [2]}


*list* shows the user the configuration files present::

    fractal% sr list
    User Configurations: (from: /home/peter/.config/sarra )
    cpost/pelle_dd1_f04.conf         cpost/pelle_dd2_f05.conf         cpost/veille_f34.conf            
    cpump/xvan_f14.conf              cpump/xvan_f15.conf              poll/f62.conf                    
    post/shim_f63.conf               post/t_dd1_f00.conf              post/t_dd2_f00.conf              
    post/test2_f61.conf              sarra/download_f20.conf          sender/tsource2send_f50.conf     
    shovel/rabbitmqtt_f22.conf       subscribe/amqp_f30.conf          subscribe/cclean_f91.conf        
    subscribe/cdnld_f21.conf         subscribe/cfile_f44.conf         subscribe/cp_f61.conf            
    subscribe/ftp_f70.conf           subscribe/q_f71.conf             subscribe/rabbitmqtt_f31.conf    
    subscribe/u_sftp_f60.conf        watch/f40.conf                   admin.conf                       
    credentials.conf                 default.conf                     
    logs are in: /home/peter/.cache/sarra/log
    
The last line says which directory the log files are in.

Also *list examples* shows included configuration templates available as starting points with the *add* command::
    
    fractal% sr list examples
    Sample Configurations: (from: /home/peter/Sarracenia/v03_wip/sarra/examples )
    cpump/cno_trouble_f00.inc        poll/aws-nexrad.conf             poll/pollingest.conf             
    poll/pollnoaa.conf               poll/pollsoapshc.conf            poll/pollusgs.conf               
    poll/pulse.conf                  post/WMO_mesh_post.conf          sarra/wmo_mesh.conf              
    sender/ec2collab.conf            sender/pitcher_push.conf         shovel/no_trouble_f00.inc        
    subscribe/WMO_Sketch_2mqtt.conf  subscribe/WMO_Sketch_2v3.conf    subscribe/WMO_mesh_CMC.conf      
    subscribe/WMO_mesh_Peer.conf     subscribe/aws-nexrad.conf        subscribe/dd_2mqtt.conf          
    subscribe/dd_all.conf            subscribe/dd_amis.conf           subscribe/dd_aqhi.conf           
    subscribe/dd_cacn_bulletins.conf subscribe/dd_citypage.conf       subscribe/dd_cmml.conf           
    subscribe/dd_gdps.conf           subscribe/dd_ping.conf           subscribe/dd_radar.conf          
    subscribe/dd_rdps.conf           subscribe/dd_swob.conf           subscribe/ddc_cap-xml.conf       
    subscribe/ddc_normal.conf        subscribe/downloademail.conf     subscribe/ec_ninjo-a.conf        
    subscribe/hpfx_amis.conf         subscribe/local_sub.conf         subscribe/pitcher_pull.conf      
    subscribe/sci2ec.conf            subscribe/subnoaa.conf           subscribe/subsoapshc.conf        
    subscribe/subusgs.conf           watch/master.conf                watch/pitcher_client.conf        
    watch/pitcher_server.conf        watch/sci2ec.conf                
    fractal% 

**show**

View all configuration settings (the result of all parsing... what the flow components actually see)::

    fractal% $PYTHONPATH/sarra/sr.py --debug show subscribe/q_f71
    
    Config of subscribe/q_f71: 
    _Config__admin=amqp://bunnymaster@localhost
    _Config__broker=amqp://tsource@localhost
    _Config__post_broker=None
    accept_unmatch=True
    accept_unmatched=False
    auto_delete=False
    baseDir=None
    batch=100
    bind=True
    bindings=[('v03.post', 'xs_tsource_poll', '#')]
    bufsize=1048576
    bytes_per_second=None
    bytes_ps=0
    cfg_run_dir='/home/peter/.cache/sarra/subscribe/q_f71'
    chmod=0
    chmod_dir=509
    chmod_log=384
    config='q_f71'
    currentDir='/home/peter/.cache/sarra/log'
    debug=False
    declare=True
    declared_exchanges=['xpublic', 'xcvan01']
    delete=False
    destfn_script=None
    directory='//home/peter/sarra_devdocroot/recd_by_srpoll_test1'
    documentRoot=None
    download=False
    durable=True
    env=environ({'SHELL': '/bin/bash', 'SESSION_MANAGER': 'local/fractal:@/tmp...'
    exchange='xs_tsource_poll'
    exchange_suffix='poll'
    expire=3600.0
    feeder='amqp://tfeed@localhost/'
    file_total_interval='0'
    filename=None
    flatten='/'
    hostdir='fractal'
    hostname='fractal'
    housekeeping=30
    inflight=None
    inline=False
    inline_encoding='guess'
    inline_max=4096
    instances=1
    logFormat='%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s'
    logLevel='info'
    log_reject=True
    lr_backupCount=5
    lr_interval=1
    lr_when='midnight'
    masks=[('.*', '//home/peter/sarra_devdocroot/recd_by_srpoll_test1', None, re...'
    message_strategy={'reset': True, 'stubborn': True, 'failure_duration': '5m'}
    message_ttl=0
    mirror=True
    msg_total_interval='0'
    plugins=['sarra.plugin.accel_scp.ACCEL_SCP']
    post_baseDir=None
    post_baseUrl=None
    post_documentRoot=None
    post_exchanges=[]
    prefetch=25
    preserve_mode=True
    preserve_time=True
    program_name='subscribe'
    pstrip='.*sent_by_tsource2send/'
    queue_filename='/home/peter/.cache/sarra/subscribe/q_f71/sr_subscribe.q_f71.tsource.qname'
    queue_name='q_tsource.sr_subscribe.q_f71.68760401.09509451'
    randid='b486'
    realpath_post=False
    report_daemons=False
    reset=False
    resolved_qname='q_tsource.sr_subscribe.q_f71.68760401.09509451'
    settings={}
    sleep=0.1
    statehost=False
    strip=0
    subtopic=None
    suppress_duplicates=0
    suppress_duplicates_basis='data'
    timeout=300
    tls_rigour='normal'
    topic_prefix='v03.post'
    undeclared=['msg_total_interval', 'file_total_interval']
    users={'tsub': 'subscriber', 'tsource': 'source', 'anonymous': 'subscriber',...'
    v2plugin_options=[]
    v2plugins={'plugin': ['msg_total_save', 'file_total_save']}
    vhost='/'
    vip=None
    

**start**

launch all configured components::

  blacklab% sr start
  gathering global state: procs, configs, state files, logs, analysis - Done. 
  starting............................................................................................Done
  blacklab% 


**stop**

stop all processes::

  blacklab% sr stop
  gathering global state: procs, configs, state files, logs, analysis - Done. 
  stopping.............................................................................................Done
  Waiting 1 sec. to check if 93 processes stopped (try: 0)
  All stopped after try 0
  blacklab% 


**status**

Sample OK status (sr is running)::

  blacklab% sr status
  reading procs: .... Done reading 451 procs!
  gathering global state: procs, configs, state files, logs, analysis - Done. 
  status 
  Component  State      Good?  Qty Configurations-i(r/e)-r(Retry)
  ---------  -----      -----  --- ------------------------------
  audit      running    OK       1
  cpost      running    OK       1 veille_f34-i1/1
  cpump      running    OK       4 xvan_f15-i1/1, xvan_f14-i1/1, pelle_dd2_f05-i1/1, pelle_dd1_f04-i1/1
  poll       running    OK       2 pulse-i1/1, f62-i1/1
  report     running    OK       3 twinnow01_f10-i1/1, twinnow00_f10-i1/1, tsarra_f20-i1/1
  sarra      running    OK       1 download_f20-i5/5
  sender     running    OK       1 tsource2send_f50-i10/10
  shovel     running    OK       5 t_dd2_f00-i3/3, pclean_f90-i5/5-r228, rabbitmqtt_f22-i5/5, t_dd1_f00-i3/3, pclean_f92-i5/5
  subscribe  running    OK       9 cdnld_f21-i5/5, cclean_f91-i5/5, rabbitmqtt_f31-i5/5, u_sftp_f60-i5/5, cfile_f44-i5/5, ftp_f70-i5/5, amqp_f30-i5/5, cp_f61-i5/5, q_f71-i5/5
  watch      running    OK       1 f40-i1/1
  winnow     running    OK       2 t00_f10-i1/1, t01_f10-i1/1
  total running configs: 29 ( processes: 95 missing: 0 stray: 0 )
  blacklab% 

OK means that all configurations are running all instances. The configurations are listed at right. For each configuraion, there
is -i followed by the number of instance processes running, and the number configured (that should be running.) when the two
aren't the same, there is a missing instance.  For shovel configuration pclean_f90, once can see that there are 5 instances running
or 5 configured, but there are also 228 messages in the retry queue.
OKd means that some while configurations are running, some are disabled (and are not running.)

More complete status::

  blacklab% sr status
  reading procs: ..... Done reading 523 procs!
  gathering global state: procs, configs, state files, logs, analysis - Done. 
  status 
  Component  State      Good?  Qty Configurations-i(r/e)-r(Retry)
  ---------  -----      -----  --- ------------------------------
  audit      running    OK       1
  cpost      running    OK       1 veille_f34-i1/1
  cpump      mixed      mult     4
        2 stopped: pelle_dd2_f05, pelle_dd1_f04 
        1 partial: xvan_f15-i0/1 
        1 running: xvan_f14-i1/1 
  poll       running    OK       2 pulse-i1/1, f62-i1/1
  report     running    OK       3 twinnow01_f10-i1/1, twinnow00_f10-i1/1, tsarra_f20-i1/1
  sarra      running    OK       1 download_f20-i5/5
  sender     running    OK       1 tsource2send_f50-i10/10
  shovel     mixed      mult     5
        2 stopped: t_dd2_f00, t_dd1_f00 
        3 running: pclean_f90-i5/5-r1144, rabbitmqtt_f22-i5/5, pclean_f92-i5/5 
  subscribe  running    OK       9 cdnld_f21-i5/5, cclean_f91-i5/5-r342, rabbitmqtt_f31-i5/5, u_sftp_f60-i5/5, cfile_f44-i5/5, ftp_f70-i5/5, amqp_f30-i5/5, cp_f61-i5/5, q_f71-i5/5
  watch      running    OK       1 f40-i1/1
  winnow     running    OK       2 t00_f10-i1/1, t01_f10-i1/1
  total running configs: 24 ( processes: 86 missing: 1 stray: 0 )
  blacklab% 

Since there is a problem with sr_cpump and sr_shovel, more information 
is given. The disabled configuration is printed, and the partially 
running one lists. A partially running configuration is one where 
some instance processes are missing.





CONFIGURATION
=============

There is no configuration for sr. All components are configured individually.  


ENVIRONMENT VARIABLES
=====================

There are no environment variables used by sr.  See individual components for
their needs.

BUGS
====

sr looks in the configuration files for the *instance* option, and expects a number there.
If *instances* comes from an include file, or is a variable value (not a raw number) sr
will not use it properly.


SEE ALSO
========

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - the download client. (<-- The Main man page!)

`sr_report(7) <sr_report.7.rst>`_ - the format of report messages.

`sr_report(1) <sr_report.1.rst>`_ - process report messages.

`sr_post(1) <sr_post.1.rst>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.rst>`_ - the format of announcements.

`sr_watch(1) <sr_watch.1.rst>`_ - the directory watching daemon.

`dd_subscribe(1) <dd_subscribe.1.rst>`_ - the http-only download client.
