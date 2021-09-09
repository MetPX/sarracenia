=====
 SR3 
=====

------------------
sr3 Sarracenia CLI
------------------

:Manual section: 1 
:Date: @Date@
:Version: @Version@
:Manual group: MetPX-Sarracenia


SYNOPSIS
========

**sr3** add|cleanup|declare|disable|dump|enable|foreground|list|remove|restart|sanity|setup|show|start|stop|status|overview _configs_ 

DESCRIPTION
===========


**sr3** is a command line tool to manage `Sarracenia <https://github.com/MetPX/sarracenia>`_ configurations, individually or in groups.
For the current user, it reads on all of the configuration files, state files, and consults the process table to determine the 
state of all components.  It then makes the change requested.

This man page is a reference, sort of a dictionary for the entire application, and may be a bit much to chew off at first.
If you already familiar in general with Sarracenia, and are looking for information about specific options or directives, 
check the table of `Contents`_
To more easily get started, have a look at `the Subscriber Guide on github <../How2Guides/subscriber.rst>`_

sr3 components are used to publish to and download files from websites or file servers 
that provide `sr3_post(7) <sr3_post.7.rst>`_ protocol notifications. Such sites 
publish messages for each file as soon as it is available. Clients connect to a
*broker* (often the same as the server itself) and subscribe to the notifications.
The *sr3_post* notifications provide true push notices for web-accessible folders (WAF),
and are far more efficient than either periodic polling of directories, or ATOM/RSS style 
notifications. Sr_subscribe can be configured to post messages after they are downloaded,
to make them available to consumers for further processing or transfers.

**sr3** can also be used for purposes other than downloading, (such as for 
supplying to an external program) specifying the -n (*notify_only*, or *no_download*) will
suppress the download behaviour and only post the URL on standard output. The standard
output can be piped to other processes in classic UNIX text filter style.  

**sr3** is very configurable and is the basis for other components of Sarracenia:

 - `cpump|sr_cpump`_ - copy messages from one pump another second one (a C implementation of shovel.)
 - `poll`_ - poll a non-sarracenia web or file server to create messages for processing.
 - `post|sr3_post|sr_cpost`_ - create messages for files for processing.
 - `sarra`_ - download file from a remote server to the local one, and re-post them for others.
 - `sender`_ - send files from a local server to a remote one.
 - `shovel`_ - copy messages, only, not files.
 - `watch`_ - create messages for each new file that arrives in a directory, or at a set path.
 - `winnow`_ - copy messages, suppressing duplicates.
 
All of these components accept the same options, with the same effects.
There is also `sr_cpump(1) <sr3_cpump.1.rst>`_ which is a C version that implements a
subset of the options here, but where they are implemented, they have the same effect.

The **sr3** command takes two arguments: an action ``start|stop|restart|reload|status``, 
followed by a list of configuration files

When any component is invoked, an operation and a configuration file are specified. 
The operation is one of:

 - foreground: run a single instance in the foreground logging to stderr
 - restart: stop and then start the configuration.
 - sanity: looks for instances which have crashed or gotten stuck and restarts them.
 - start:  start the configuration running
 - status: check if the configuration is running.
 - stop: stop the configuration from running

Note that the *sanity* check is invoked by heartbeat processing in sr_audit on a regular basis.
The remaining operations manage the resources (exchanges, queues) used by the component on
the rabbitmq server, or manage the configurations.

 - cleanup:       deletes the component's resources on the server.
 - declare:       creates the component's resources on the server.
 - setup:         like declare, additionally does queue bindings.
 - add:           copy to the list of available configurations.
 - list:          list all the configurations available. 
 - list plugins:  list all the plugins available. 
 - list examples:  list all the plugins available. 
 - show           view an interpreted version of a configuration file.
 - edit:          modify an existing configuration.
 - remove:        remove a configuration.
 - disable:       mark a configuration as ineligible to run. 
 - enable:        mark a configuration as eligible to run. 


For example:  *sr_subscribe foreground dd* runs the sr_subscribe component with
the dd configuration as a single foreground instance.

The **foreground** action is used when building a configuration or for debugging.
The **foreground** instance will run regardless of other instances which are currently
running.  Should instances be running, it shares the same message queue with them.
A user stop the **foreground** instance by simply using <ctrl-c> on linux
or use other means to kill the process.

After a configuration has been refined, *start* to launch the component as a background 
service (daemon or fleet of daemons whose number is controlled by the *instances* option.) 
If multiple configurations and components need to be run together, the entire fleet 
can be similarly controlled using the `sr(8) <sr.8.rst>`_ command. 

.. TODO: Where to find the new sr.8 docs... fix link above

To have components run all the time, on Linux one can use `systemd <https://www.freedesktop.org/wiki/Software/systemd/>`_ integration,
as described in the `Admin Guide <../How2Guides/Admin.rst>`_ On Windows, one can configure a service,
as described in the `Windows user manual <../Tutorials/Windows.rst>`_

The actions **cleanup**, **declare**, **setup** can be used to manage resources on
the rabbitmq server. The resources are either queues or exchanges. **declare** creates
the resources. **setup** creates and additionally binds the queues.

The **add, remove, list, edit, enable & disable** actions are used to manage the list 
of configurations.  One can see all of the configurations available using the **list**
action.   to view available plugins use **list plugins**.  Using the **edit** option, 
one can work on a particular configuration.  A *disabled* configuration will not be 
started or restarted by the **start**,  
**foreground**, or **restart** actions. It can be used to set aside a configuration
temporarily. 


Contents
========

.. contents::


COMMANDS
========

**declare|setup**

Call the corresponding function for each configuration::

  $ sr3 declare
    declare: 2020-09-06 23:22:18,043 [INFO] root declare looking at cpost/pelle_dd1_f04 
    2020-09-06 23:22:18,048 [INFO] sarra.moth.amqp __putSetup exchange declared: xcvan00 (as: amqp://tfeed@localhost/) 
    2020-09-06 23:22:18,049 [INFO] sarra.moth.amqp __putSetup exchange declared: xcvan01 (as: amqp://tfeed@localhost/) 
    2020-09-06 23:22:18,049 [INFO] root declare looking at cpost/veille_f34 
    2020-09-06 23:22:18,053 [INFO] sarra.moth.amqp __putSetup exchange declared: xcpublic (as: amqp://tfeed@localhost/) 
    2020-09-06 23:22:18,053 [INFO] root declare looking at cpost/pelle_dd2_f05 
    ...
    2020-09-06 23:22:18,106 [INFO] root declare looking at cpost/pelle_dd2_f05 
    2020-09-06 23:22:18,106 [INFO] root declare looking at cpump/xvan_f14 
    2020-09-06 23:22:18,110 [INFO] sarra.moth.amqp __getSetup queue declared q_tfeed.sr_cpump.xvan_f14.23011811.49631644 (as: amqp://tfeed@localhost/) 
    2020-09-06 23:22:18,110 [INFO] sarra.moth.amqp __getSetup um..: pfx: v03, exchange: xcvan00, values: #
    2020-09-06 23:22:18,110 [INFO] sarra.moth.amqp __getSetup binding q_tfeed.sr_cpump.xvan_f14.23011811.49631644 with v03.# to xcvan00 (as: amqp://tfeed@localhost/)
    2020-09-06 23:22:18,111 [INFO] root declare looking at cpump/xvan_f15 
    2020-09-06 23:22:18,115 [INFO] sarra.moth.amqp __getSetup queue declared q_tfeed.sr_cpump.xvan_f15.50074940.98161482 (as: amqp://tfeed@localhost/) 

Declares the queues and exchanges related to each configuration.
One can also invoke it with --users, so that it will declare users as well as exchanges and queues::

  $ sr3 --users declare
    2020-09-06 23:28:56,211 [INFO] sarra.rabbitmq_admin add_user permission user 'ender' role source  configure='^q_ender.*|^xs_ender.*' write='^q_ender.*|^xs_ender.*' read='^q_ender.*|^x[lrs]_ender.*|^x.*public$' 
    ...


**dump**

print the three data structure used by sr.  There are three lists:  

* processes thought to be related to sr.

* configurations present

* contents of the state files.

**dump** is used for debugging or to get more detail than provided by status:: 

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

  $ sr3 dump  | grep stopped
    WMO_mesh_post : {'status': 'stopped', 'instances': 0}
    shim_f63 : {'status': 'stopped', 'instances': 0}
    test2_f61 : {'status': 'stopped', 'instances': 0}

  $ sr3 dump  | grep disabled
    amqp_f30.conf : {'status': 'disabled', 'instances': 5}


provides easy method to determine which configurations are in a particular state.
Another example, if *sr status* reports sender/tsource2send_f50 as being partial, then 
one can use dump to get more detail::

  $ sr3 dump | grep sender/tsource2send_f50
    49308: name:sr3_sender.py cmdline:['/usr/bin/python3', '/usr/lib/python3/dist-packages/sarracenia/instance.py', '--no', '1', 'start', 'sender/tsource2send_f50']
    q_tsource.sr_sender.tsource2send_f50.58710892.12372870: ['sender/tsource2send_f50']


**foreground** 

run a single instance of a single configuration as an interactive process logging to the current stderr/terminal output.
a configuration m

**list** 

shows the user the configuration files present::

  $ sr3 list
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
    
  $ sr3 list examples
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


  $ sr3 add dd_all.conf
    add: 2021-01-24 18:04:57,018 [INFO] sarracenia.sr add copying: /usr/lib/python3/dist-packages/sarracenia/examples/subscribe/dd_all.conf to /home/peter/.config/sr3/subscribe/dd_all.conf 
  $ sr3 edit dd_all.conf

The **add, remove, list, edit, enable & disable** actions are used to manage the list
of configurations.  One can see all of the configurations available using the **list**
action.   to view available plugins use **list plugins**.  Using the **edit** option,
one can work on a particular configuration.  A *disabled* sets a configuration aside
(by adding *.off* to the name) so that it will not be started or restarted by 
the **start**, **foreground**, or **restart** actions. 

**show**

View all configuration settings (the result of all parsing... what the flow components actually see)::

  $ sr3 --debug show subscribe/q_f71
    
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
    bindings=[('v03', 'xs_tsource_poll', '#')]
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
    inline_only=False
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
    topicPrefix='v03'
    undeclared=['msg_total_interval', 'file_total_interval']
    users={'tsub': 'subscriber', 'tsource': 'source', 'anonymous': 'subscriber',...'
    v2plugin_options=[]
    v2plugins={'plugin': ['msg_total_save', 'file_total_save']}
    vhost='/'
    vip=None
    

**start**

launch all configured components::

  $ sr3 start
    gathering global state: procs, configs, state files, logs, analysis - Done. 
    starting...Done


**stop**

stop all processes::

  $ sr3 stop
    gathering global state: procs, configs, state files, logs, analysis - Done. 
    stopping........Done
    Waiting 1 sec. to check if 93 processes stopped (try: 0)
    All stopped after try 0
 


**status**

Sample OK status (sr is running)::

  $ sr3 status
    status: 
    Component/Config                         State        Run  Miss   Exp Retry
    ----------------                         -----        ---  ----   --- -----
    cpost/pelle_dd1_f04                      stopped        0     0     0     0
    cpost/pelle_dd2_f05                      stopped        0     0     0     0
    cpost/veille_f34                         partial        0     1     1     0
    cpump/xvan_f14                           partial        0     1     1     0
    cpump/xvan_f15                           partial        0     1     1     0
    poll/f62                                 running        1     0     1     0
    post/shim_f63                            stopped        0     0     0     0
    post/t_dd1_f00                           stopped        0     0     0     0
    post/t_dd2_f00                           stopped        0     0     0     0
    post/test2_f61                           stopped        0     0     0     0
    report/tsarra_f20                        running        1     0     1     0
    sarra/download_f20                       running        1     0     1     0
    sender/tsource2send_f50                  running        1     0     1     0
    shovel/rabbitmqtt_f22                    running        1     0     1     0
    subscribe/amqp_f30                       running        1     0     1     0
    subscribe/cclean_f91                     running        1     0     1     0
    subscribe/cdnld_f21                      running        1     0     1     0
    subscribe/cfile_f44                      running        1     0     1     0
    subscribe/cp_f61                         running        1     0     1     0
    subscribe/dd_all                         stopped        0     0     0     0
    subscribe/ftp_f70                        running        1     0     1     0
    subscribe/q_f71                          running        1     0     1     0
    subscribe/rabbitmqtt_f31                 running        1     0     1     0
    subscribe/u_sftp_f60                     running        1     0     1     0
    watch/f40                                running        1     0     1     0
          total running configs:  15 ( processes: 15 missing: 3 stray: 0 )


The configurations are listed on the left. For each configuraion, the state
will be:

* stopped:  no processes are running.
* running:  all processes are running. 
* partial:  some processes are running.
* disabled: configured not to run.

The columns to the right give more information, detailing how many processes are Running, and Missing ones.
The Expected entry lists how many processes should be running based on the configuration, and whether it is stopped
or not.  The contents of the Run and Miss columns should always add up to what is in the Exp column.

The last column is the number of messages stored in the local retry queue, indicating what channels are having
processing difficulties. Here is an example of seeing that a single configuration is running, stopping it, 
cleaning it out::

  $ sr3 status
    status: 
    Component/Config                         State        Run  Miss   Exp Retry
    ----------------                         -----        ---  ----   --- -----
    subscribe/dd_all                         running        5     0     1     0
          total running configs:   1 ( processes: 5 missing: 0 stray: 0 )

  $ sr3 stop subscribe/dd_all
    Stopping: sending SIGTERM ..... ( 5 ) Done
    Waiting 1 sec. to check if 5 processes stopped (try: 0)
    Waiting 2 sec. to check if 3 processes stopped (try: 1)
    pid: 818881-['/usr/bin/python3', '/usr/lib/python3/dist-packages/sarracenia/instance.py', '--no', '3', 'start'] does not match any configured instance, sending it TERM
    Waiting 4 sec. to check if 3 processes stopped (try: 2)
    All stopped after try 2
    
  $ sr3 cleanup subscribe/dd_all
    cleanup: queues to delete: [(ParseResult(scheme='amqps', netloc='anonymous:anonymous@dd.weather.gc.ca', path='/', params='', query='', fragment=''), 'q_anonymous.sr_subscribe.dd_all.47257736.46056854')]
    removing state file: /home/peter/.cache/sr3/subscribe/dd_all/sr_subscribe.dd_all.anonymous.qname
    
  $ sr3 remove subscribe/dd_all
    2021-01-24 23:57:59,800 [INFO] root remove FIXME remove! ['subscribe/dd_all']
    2021-01-24 23:57:59,800 [INFO] root remove removing /home/peter/.config/sr3/subscribe/dd_all.conf 
    
  $ sr3 status
    status: 
    Component/Config                         State        Run  Miss   Exp Retry
    ----------------                         -----        ---  ----   --- -----
          total running configs:   0 ( processes: 0 missing: 0 stray: 0 )
    

COMPONENTS
==========

CPUMP|sr_cpump
---------------

*cpump** is an implementation of the `shovel`_ component in C.
On an individual basis, it should be faster than a single python downloader,
with some limitations.

 - doesn't download data, only circulates posts. (shovel, not subscribe)
 - runs as only a single instance (no multiple instances).
 - does not support any plugins.
 - does not support vip for high availability.
 - different regular expression library: POSIX vs. python.
 - does not support regex for the strip command (no non-greedy regex).

It can therefore usually, but not always, act as a drop-in replacement for `shovel`_ and `winnow`_

The C implementation may be easier to make available in specialized environments,
such as High Performance Computing, as it has far fewer dependencies than the python version.
It also uses far less memory for a given role.  Normally the python version
is recommended, but there are some cases where use of the C implementation is sensible.

**sr_cpump** connects to a *broker* (often the same as the posting broker)
and subscribes to the notifications of interest. If _suppress_duplicates_ is active, 
on reception of a post, it looks up the message's **integity** field in its cache.  If it is 
found, the file has already come through, so the notification is ignored. If not, then 
the file is new, and the **sum** is added to the cache and the notification is posted.



POLL
----

**poll** is a component that connects to a remote server to
check in various directories for some files. When a file is
present, modified or created in the remote directory, the program will
notify about the new product.

The notification protocol is defined here `sr3_post(7) <sr3_post.7.rst>`_

**poll** connects to a *broker*.  Every *sleep* seconds, it connects to
a *destination* (sftp, ftp, ftps). For each of the *directory* defined, it lists
the contents. When a file matches a pattern given by *accept*, **sr_poll** builds
a notification for that product and sends it to the *broker*. The matching content
of the *directory* is kept in a file for reference. Should a matching file be changed,
or created at a later iteration, a new notification is sent.

**sr_poll** can be used to acquire remote files in conjunction with an `sarra`_
subscribed to the posted notifications, to download and repost them from a data pump.

The destination option specify what is needed to connect to the remote server

**destination protocol://<user>@<server>[:port]**

::
      (default: None and it is mandatory to set it )

The *destination* should be set with the minimum required information...
**sr_poll**  uses *destination* setting not only when polling, but also
in the sr3_post messages produced.

For example, the user can set :

**destination ftp://myself@myserver**

And complete the needed information in the credentials file with the line  :

**ftp://myself:mypassword@myserver:2121  passive,binary**

POLLING SPECIFICATIONS
~~~~~~~~~~~~~~~~~~~~~~

These options set what files the user wants to be notified for and where
 it will be placed, and under which name.

- **filename  <option>         (optional)**
- **directory <path>           (default: .)**
- **accept    <regexp pattern> [rename=] (must be set)**
- **reject    <regexp pattern> (optional)**
- **chmod     <integer>        (default: 0o400)**
- **poll_without_vip  <boolean> (default: True)**
- **file_time_limit <duration>   (default 60d)**

The option *filename* can be used to set a global rename to the products.
Ex.:

**filename  rename=/naefs/grib2/**

For all posts created, the *rename* option would be set to '/naefs/grib2/filename'
because I specified a directory (path that ends with /).

The option *directory*  defines where to get the files on the server.
Combined with  **accept** / **reject**  options, the user can select the
files of interest and their directories of residence.

The  **accept**  and  **reject**  options use regular expressions (regexp) to match URL.
These options are processed sequentially.
The URL of a file that matches a  **reject**  pattern is not published.
Files matching an  **accept**  pattern are published.
Again a *rename*  can be added to the *accept* option... matching products
for that *accept* option would get renamed as described... unless the *accept* matches
one file, the *rename* option should describe a directory into which the files
will be placed (prepending instead of replacing the file name).

The directory can have some patterns. These supported patterns concern date/time .
They are fixed...

**${YYYY}         current year**
**${MM}           current month**
**${JJJ}          current julian**
**${YYYYMMDD}     current date**

**${YYYY-1D}      current year   - 1 day**
**${MM-1D}        current month  - 1 day**
**${JJJ-1D}       current julian - 1 day**
**${YYYYMMDD-1D}  current date   - 1 day**

::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*

        directory /mylocaldirectory/${YYYYMMDD}/mydailies
        accept    .*observations.*

The **chmod** option allows users to specify a linux-style numeric octal
permission mask::

  chmod 040

means that a file will not be posted unless the group has read permission
(on an ls output that looks like: ---r-----, like a chmod 040 <file> command).
The **chmod** options specifies a mask, that is the permissions must be
at least what is specified.

As with all other components, the **vip** option can be used to indicate
that a poll should be active on only a single node in a cluster. Note that
as the poll will maintain state (such as the list of files that exist on the
remote hosts), by default, the vip will only keep the component from posting,
but the actual poll will still happen, which can involve a high an unnecessary
load on the nodes that do not have the vip.

To have the nodes which do not have the vip perform no work, for example
if the corresponding sarra components have *delete* set, so that no state
persistence is needed in the poll, set the **poll_without_vip** option
to *False* (or *off*). This reduces overhead forty-fold in some measured
cases.

By default, files that are more than 2 months are not posted. However, this 
can be modified to any specified time limit in the configurations by using 
the option *file_time_limit <duration>*. By default, seconds are used, but 
one can specify hours, days or weeks with 1, 1h, 1d, 1w respectively. 

POSTING SPECIFICATIONS
~~~~~~~~~~~~~~~~~~~~~~

These options set what files the user wants to be notified for and where
**sr_poll** polls the availability of file on a remote server by creating
an announcment for it.  Subscribers use `sr_subscribe <#subscribe>`_
to consume the announcement and download the file (or **sr_sarra**).
To make files available to subscribers, **sr_poll** sends the announcements to
an AMQP or MQTT server, also called a broker.  Format of argument to the *broker* option::

       [amqp|amqps]://[user[:password]@]host[:port][/vhost]

The announcement will have its url built from the *destination* option, with
the product's path (*directory*/"matched file").  There is one post per file.
The file's size is taken from the directory "ls"... but its checksum cannot
be determined, so the "sum" header in the posting is set to "0,0."

By default, sr_poll sends its post message to the broker with default exchange
(the prefix *xs_* followed by the broker username). The *broker* is mandatory.
It can be given incomplete if it is well defined in the credentials.conf file.

Refer to `sr3_post(1) <sr3_post.1.rst>`_ - to understand the complete notification process.
Refer to `sr3_post(7) <sr3_post.7.rst>`_ - to understand the complete notification format.

Here it is important to say that :

The *sum=0,0* is used because no checksum computation was performed. It is often
desirable to use the *sum=z,s* to have downloaders calculate a useful checksum as
they download for use by others.

The *parts=1,fsiz,1,0,0* is used and the file's size is taken from the ls of the file.
Under **sr_sarra** these fields could be reset.

ADVANCED FEATURES
~~~~~~~~~~~~~~~~~

There are ways to insert scripts into the flow of messages and file downloads:
Should you want to implement tasks in various part of the execution of the program:

- **on_line      <script>        (default: line_mode)**
- **do_poll      <script>        (default: None)**
- **on_post      <script>        (default: None)**
- **on_html_page <script>        (default: html_page)**

The **on_line** plugin gives scripts that can read each line of an 'ls' on the polled
site, to interpret it further. It returns True if the line should be further processed,
or False to reject it.  By default, there is a line_mode plugin included with the package
which implements the comparison of file permissions on the remote server against
the **chmod** mask.

If the poll fetches using the http protocol, the 'ls' like entries must be derived from
an html page. The default plugin **html_page** provided with the package, gives an idea of
how to parse such a page into a python directory manageable by **sr_poll**.


post|sr3_post|sr_cpost
----------------------

**sr3_post** posts the availability of a file by creating an announcement.
In contrast to most other sarracenia components that act as daemons,
sr3_post is a one shot invocation which posts and exits.
To make files available to subscribers, **sr3_post** sends the announcements
to an AMQP or MQTT server, also called a broker.

This manual page is primarily concerned with the python implementation,
but there is also an implementation in C, which works nearly identically.
Differences:

 - plugins are not supported in the C implementation.
 - C implementation uses POSIX regular expressions, python3 grammar is slightly different.
 - when the *sleep* option ( used only in the C implementation) is set to > 0,
   it transforms sr_cpost into a daemon that works like `watch`_.

Mandatory Settings
~~~~~~~~~~~~~~~~~~

The [*-pbu|--post_baseUrl url,url,...*] option specifies the location
subscribers will download the file from.  There is usually one post per file.
Format of argument to the *post_baseUrl* option::

       [ftp|http|sftp]://[user[:password]@]host[:port]/
       or
       file:

When several urls are given as a comma separated list to *post_baseUrl*, the
url´s provided are used round-robin style, to provide a coarse form of load balancing.

The [*-p|--path path1 path2 .. pathN*] option specifies the path of the files
to be announced. There is usually one post per file.
Format of argument to the *path* option::

       /absolute_path_to_the/filename
       or
       relative_path_to_the/filename

The *-pipe* option can be specified to have sr3_post read path names from standard
input as well.


An example invocation of *sr3_post*::

 sr3_post -pb amqp://broker.com -pbu sftp://stanley@mysftpserver.com/ -p /data/shared/products/foo 

By default, sr3_post reads the file /data/shared/products/foo and calculates its checksum.
It then builds a post message, logs into broker.com as user 'guest' (default credentials)
and sends the post  to defaults vhost '/' and default exchange. The default exchange
is the prefix *xs_* followed by the broker username, hence defaulting to 'xs_guest'.
A subscriber can download the file /data/shared/products/foo by authenticating as user stanley
on mysftpserver.com using the sftp protocol to broker.com assuming he has proper credentials.
The output of the command is as follows ::

 [INFO] Published xs_guest v03.data.shared.products.foo '20150813161959.854 sftp://stanley@mysftpserver.com/ /data/shared/products/foo' sum=d,82edc8eb735fd99598a1fe04541f558d parts=1,4574,1,0,0

In MetPX-Sarracenia, each post is published under a certain topic.
The log line starts with '[INFO]', followed by the **topic** of the
post. Topics in *AMQP* are fields separated by dot. Note that MQTT topics use
a slash (/) as the topic separator.  The complete topic starts with
a topicPrefix (see option), version *v03*, 
followed by a subtopic (see option) here the default, the file path separated with dots
*data.shared.products.foo*. 

The second field in the log line is the message notice.  It consists of a time
stamp *20150813161959.854*, and the source URL of the file in the last 2 fields.

The rest of the information is stored in AMQP message headers, consisting of key=value pairs.
The *sum=d,82edc8eb735fd99598a1fe04541f558d* header gives file fingerprint (or checksum
) information.  Here, *d* means md5 checksum performed on the data, and *82edc8eb735fd99598a1fe04541f558d*
is the checksum value. The *parts=1,4574,1,0,0* state that the file is available in 1 part of 4574 bytes
(the filesize.)  The remaining *1,0,0* is not used for transfers of files with only one part.

Another example::

 sr3_post -pb amqp://broker.com -pbd /data/web/public_data -pbu http://dd.weather.gc.ca/ -p bulletins/alphanumeric/SACN32_CWAO_123456

By default, sr3_post reads the file /data/web/public_data/bulletins/alphanumeric/SACN32_CWAO_123456
(concatenating the post_baseDir and relative path of the source url to obtain the local file path)
and calculates its checksum. It then builds a post message, logs into broker.com as user 'guest'
(default credentials) and sends the post to defaults vhost '/' and exchange 'xs_guest'.

A subscriber can download the file http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 using http
without authentication on dd.weather.gc.ca.

SHIM LIBRARY USAGE
~~~~~~~~~~~~~~~~~~

Rather than invoking a sr3_post to post each file to publish, one can have processes automatically
post the files they right by having them use a shim library intercepting certain file i/o calls to libc
and the kernel. To activate the shim library, in the shell environment add::

  export SR_POST_CONFIG=shimpost.conf
  export LD_PRELOAD="libsrshim.so.1"

where *shimpost.conf* is an sr_cpost configuration file in
the ~/.config/sarra/post/ directory. An sr_cpost configuration file is the same
as an sr3_post one, except that plugins are not supported.  With the shim
library in place, whenever a file is written, the *accept/reject* clauses of
the shimpost.conf file are consulted, and if accepted, the file is posted just
as it would be by sr3_post. If using with ssh, where one wants files which are
scp'd to be posted, one needs to include the activation in the .bashrc and pass
it the configuration to use::

  expoert LC_SRSHIM=shimpost.conf

Then in the ~/.bashrc on the server running the remote command::

  if [ "$LC_SRSHIM" ]; then
      export SR_POST_CONFIG=$LC_SRSHIM
      export LD_PRELOAD="libsrshim.so.1"
  fi
       
SSH will only pass environment variables that start with LC\_ (locale) so to get it
passed with minimal effort, we use that prefix.


Shim Usage Notes
----------------

This method of notification does require some user environment setup.
The user environment needs to the LD_PRELOAD environment variable set
prior to launch of the process. Complications that remain as we have
been testing for two years since the shim library was first implemented:

* if we want to notice files created by remote scp processes (which create non-login shells)
  then the environment hook must be in .bashrc. and using an environment
  variable that starts with *LC_* to have ssh transmit the configuration value without
  having to modify sshd configuration in typical linux distributions.
  ( full discussion: https://github.com/MetPX/sarrac/issues/66 )

* code that has certain weaknesses, such as in FORTRAN a lack of IMPLICIT NONE
  https://github.com/MetPX/sarracenia/issues/69 may crash when the shim library
  is introduced. The correction needed in those cases has so far been to correct
  the application, and not the library.
  ( also: https://github.com/MetPX/sarrac/issues/12 )

* codes using the *exec* call ot `tcl/tk <www.tcl.tk>`_, by default considers any
  output to file descriptor 2 (standard error) as an error condition.
  these messages can be labelled as INFO, or WARNING priority, but it will
  cause the tcl caller to indicate a fatal error has occurred.  Adding
  *-ignorestderr*  to invocations of *exec* avoids such unwarranted aborts.

* Complex shell scripts can experience an inordinate performance impact.
  Since *high performance shell scripts* is an oxymoron, the best solution,
  performance-wise is to re-write the scripts in a more efficient scripting
  language such as python  ( https://github.com/MetPX/sarrac/issues/15 )

* Code bases that move large file hierarchies (e.g. *mv tree_with_thousands_of_files new_tree* )
  will see a much higher cost for this operation, as it is implemented as
  a renaming of each file in the tree, rather than a single operation on the root.
  This is currently considered necessary because the accept/reject pattern matching
  may result in a very different tree on the destination, rather than just the
  same tree mirrored. See below for details.

* *export SR_SHIMDEBUG=1* will get your more output than you want. use with care.


**Rename Processing**

It should be noted that file renaming is not as simple in the mirroring case as in the underlying
operating system. While the operation is a single atomic one in an operating system, when
using notifications, there are accept/reject cases that create four possible effects.

+---------------+---------------------------+
|               |    old name is:           |
+---------------+--------------+------------+
| New name is:  |  *Accepted*  | *Rejected* |
+---------------+--------------+------------+
|  *Accepted*   |   rename     |   copy     |
+---------------+--------------+------------+
|  *Rejected*   |   remove     |   nothing  |
+---------------+--------------+------------+

When a file is moved, two notifications are created:

*  One notification has the new name in the *relpath*, while containing and *oldname*
   field pointing at the old name.  This will trigger activities in the top half of
   the table, either a rename, using the oldname field, or a copy if it is not present

   at the destination.

*  A second notification with the oldname in *relpath* which will be accepted
   again, but this time it has the *newname* field, and process the remove action.

While the renaming of a directory at the root of a large tree is a cheap atomic operation
in Linux/Unix, mirroring that operation requires creating a rename posting for each file
in the tree, and thus is far more expensive.





SARRA
-----

**sarra** is a program that Subscribes to file notifications,
Acquires the files and ReAnnounces them at their new locations.
The notification protocol is defined here `sr3_post(7) <sr3_post.7.rst>`_

**sarra** connects to a *broker* (often the same as the remote file server
itself) and subscribes to the notifications of interest. It uses the notification
information to download the file on the local server it's running on.
It then posts a notification for the downloaded files on a broker (usually on the local server).

**sarra** can be used to acquire files from `sr3_post(1) <sr3_post.1.rst>`_
or `watch`_  or to reproduce a web-accessible folders (WAF),
that announce its products.

The **sr_sarra** is an `sr_subscribe(1) <#subscribe>`_  with the following presets::

   mirror True


Specific consuming requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the messages are posted directly from a source, the exchange used is 'xs_<brokerSourceUsername>'.
To protect against malicious users, administrators should set *source_from_exchange* to **True**.
Such messages may not contain a source nor an origin cluster fields
or a malicious user may set the values incorrectly.


- **source_from_exchange  <boolean> (default: False)**

Upon reception, the program will set these values in the parent class (here 
cluster is the value of option **cluster** taken from default.conf):

msg['source']       = <brokerUser>
msg['from_cluster'] = cluster

overriding any values present in the message. This setting
should always be used when ingesting data from a
user exchange.


SENDER
------

**sender** is a component derived from `subscribe`_
used to send local files to a remote server using a file transfer protocol, primarily SFTP.
**sender** is a standard consumer, using all the normal AMQP settings for brokers, exchanges,
queues, and all the standard client side filtering with accept, reject, and on_message.

Often, a broker will announce files using a remote protocol such as HTTP,
but for the sender it is actually a local file.  In such cases, one will
see a message: **ERROR: The file to send is not local.**
An on_message plugin will convert the web url into a local file one::

  baseDir /var/httpd/www
  on_message msg_2localfile

This on_message plugin is part of the default settings for senders, but one
still needs to specify baseDir for it to function.

If a **post_broker** is set, **sender** checks if the clustername given
by the **to** option if found in one of the message's destination clusters.
If not, the message is skipped.


DESTINATION UNAVAILABLE
~~~~~~~~~~~~~~~~~~~~~~~

If the server to which the files are being sent is going to be unavailable for
a prolonged period, and there is a large number of messages to send to it, then
the queue will build up on the broker. As the performance of the entire broker
is affected by large queues, one needs to minimize such queues.

The *-save* and *-restore* options are used get the messages away from the broker
when a very large a queue will certainly build up.
The *-save* option copies the messages to a (per instance) disk file (in the same directory
that stores state and pid files), as json encoded strings, one per line.
When a queue is building up::

   sr3 stop sender/<config> 
   sr3 -save start sender/<config> 

And run the sender in *save* mode (which continually writes incoming messages to disk)
in the log, a line for each message written to disk::

  2017-03-03 12:14:51,386 [INFO] sr_sender saving 2 message 
       topic: v03.home.peter.sarra_devdocroot.sub.SASP34_LEMM_031630__LEDA_60215

Continue in this mode until the absent server is again available.  At that point::

   sr3 stop sender/<config> 
   sr3 -restore start sender/<config> 

While restoring from the disk file, messages like the following will appear in the log::

  2017-03-03 12:15:02,969 [INFO] sr_sender restoring message 29 of 34: 
    topic: v03.home.peter.sarra_devdocroot.sub.ON_02GD022_daily_hydrometric.csv


After the last one::

  2017-03-03 12:15:03,112 [INFO] sr_sender restore complete deleting save 
    file: /home/peter/.cache/sarra/sender/tsource2send/sr_sender_tsource2send_0000.save 


and the sr_sender will function normally thereafter.


SETUP 1 : PUMP TO PUMP REPLICATION 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

 - **mirror             <boolean>   (default: True)**
 - **baseDir      <directory> (None)**

 - **destination        <url>       (MANDATORY)**
 - **do_send            <script>    (None)**
 - **kbytes_ps          <int>       (default: 0)**
 - **post_baseDir <directory> (default: '')**

 - **to               <clustername> (default: <post_broker host>)**
 - **on_post           <script>     (default: None)**
 - **post_broker        amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**
 - **url                <url>       (default: destination)**

For pump replication, **mirror** is set to True (default).

**baseDir** supplies the directory path that, when combined with the relative
one in the selected notification gives the absolute path of the file to be sent.
The default is None which means that the path in the notification is the absolute one.

In a subscriber, the baseDir represents the prefix to the relative path on the upstream
server, and is used as a pattern to be replaced in the currently selected base directory
(from a *baseDir* or *directory* option) in the message fields: 'link', 'oldname', 'newname'
which are used when mirroring symbolic links, or files that are renamed.

The **destination** defines the protocol and server to be used to deliver the products.
Its form is a partial url, for example:  **ftp://myuser@myhost**
The program uses the file ~/.conf/sarra/credentials.conf to get the remaining details
(password and connection options).  Supported protocol are ftp, ftps and sftp. Should the
user need to implement another sending mechanism, he would provide the plugin script
through option **do_send**.

On the remote site, the **post_baseDir** serves the same purpose as the
**baseDir** on this server.  The default is None which means that the delivered path
is the absolute one.

Now we are ready to send the product... for example, if the selected notification looks like this :

**20150813161959.854 http://this.pump.com/ relative/path/to/IMPORTANT_product**

**sr_sender**  performs the following pseudo-delivery:

Sends local file [**baseDir**]/relative/path/to/IMPORTANT_product
to    **destination**/[**post_baseDir**]/relative/path/to/IMPORTANT_product
(**kbytes_ps** is greater than 0, the process attempts to respect
this delivery speed... ftp,ftps,or sftp)

At this point, a pump-to-pump setup needs to send the remote notification...
(If the post_broker is not set, there will be no posting... just products replication)

The selected notification contains all the right information
(topic and header attributes) except for url field in the
notice... in our example :  **http://this.pump.com/**

By default, **sr_sender** puts the **destination** in that field.
The user can overwrite this by specifying the option **post_baseUrl**. For example:

**post_baseUrl http://remote.apache.com**

The user can provide an **on_post** script. Just before the message is
published on the **post_broker**  and **post_exchange**, the
**on_post** script is called... with the **sr_sender** class instance as an argument.
The script can perform whatever you want... if it returns False, the message will not
be published. If True, the program will continue processing from there.


DESTINATION SETUP 2 : METPX-SUNDEW LIKE DISSEMINATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this type of usage, we would not usually repost... but if the
**post_broker** and **post_exchange** (**url**,**on_post**) are set,
the product will be announced (with its possibly new location and new name).
Let's reintroduce the options in a different order
with some new ones to ease explanation.


 - **mirror             <boolean>   (default: True)**
 - **baseDir      <directory> (None)**

 - **destination        <url>       (MANDATORY)**
 - **post_baseDir <directory> (default: '')**

 - **directory          <path>      (MANDATORY)**
 - **on_message            <script> (default: None)**
 - **accept        <regexp pattern> (default: None)**
 - **reject        <regexp pattern> (default: None)**

There are 2 differences with the previous case :
the **directory**, and the **filename** options.

The **baseDir** is the same, and so are the
**destination**  and the **post_baseDir** options.

The **directory** option defines another "relative path" for the product
at its destination.  It is tagged to the **accept** options defined after it.
If another sequence of **directory**/**accept** follows in the configuration file,
the second directory is tagged to the following accepts and so on.

The  **accept/reject**  patterns apply to message notice url as above.
Here is an example, here some ordered configuration options :

::

  directory /my/new/important_location

  accept .*IMPORTANT.*

  directory /my/new/location/for_others

  accept .*

If the notification selected is, as above, this :

**20150813161959.854 http://this.pump.com/ relative/path/to/IMPORTANT_product**

It was selected by the first **accept** option. The remote relative path becomes
**/my/new/important_location** ... and **sr_sender**  performs the following pseudo-delivery:

sends local file [**baseDir**]/relative/path/to/IMPORTANT_product
to    **destination**/[**post_baseDir**]/my/new/important_location/IMPORTANT_product


Usually this way of using **sr_sender** would not require posting of the product.
But if **post_broker** and **post_exchange** are provided, and **url** , as above, is set to
**http://remote.apache.com**,  then **sr_sender** would reconstruct :

Topic: **v03.my.new.important_location.IMPORTANT_product**

Notice: **20150813161959.854 http://remote.apache.com/ my/new/important_location/IMPORTANT_product**



shovel
------

shovel copies messages on one broker (given by the *broker* option) to
another (given by the *post_broker* option.) subject to filtering
by (*exchange*, *subtopic*, and optionally, *accept*/*reject*.)

The *topicPrefix* option must to be set to:

 - **v03** to shovel `sr3_postv2(7) <sr3_postv2.7.rst>`_ messages

.. TODO: Above links to a potentially removed file..

shovel is a flow with the following presets::
   
   no-download True
   suppress_duplicates off


subscribe
---------

Subscribe is the normal downloading flow component, that will connect to a broker, download
the configured files, and then forward the messages with an altered baseUrl.


watch
-----

Watches a directory and publishes posts when files in the directory change
( added, modified, or deleted). Its arguments are very similar to  `sr3_post <sr3_post.1.rst>`_.
In the MetPX-Sarracenia suite, the main goal is to post the availability and readiness
of one's files. Subscribers use  *sr_subscribe*  to consume the post and download the files.

Posts are sent to an AMQP server, also called a broker, specified with the option [ *-pb|--post_broker broker_url* ].

The [*-post_baseUrl|--pbu|--url url*] option specifies the protocol, credentials, host and port to which subscribers
will connect to get the file.

Format of argument to the *url* option::

       [ftp|http|sftp]://[user[:password]@]host[:port]/
       or
       [ftp|http|sftp]://[user[:password]@]host[:port]/
       or
       file:


The [*-p|--path path*] option tells *sr_watch* what to look for.
If the *path* specifies a directory, *sr_watches* creates a post for any time
a file in that directory is created, modified or deleted.
If the *path* specifies a file,  *sr_watch*  watches only that file.
In the announcement, it is specified with the *path* of the product.
There is usually one post per file.


FIXME: in version 3 does it work at all without a configuration.
An example of an execution of  *sr_watch*  checking a file::

 sr3_watch -s sftp://stanley@mysftpserver.com/ -p /data/shared/products/foo -pb amqp://broker.com --action start

Here,  *sr_watch*  checks events on the file /data/shared/products/foo.
Default events settings reports if the file is modified or deleted.
When the file gets modified,  *sr_watch*  reads the file /data/shared/products/foo
and calculates its checksum.  It then builds a post message, logs into broker.com as user 'guest' (default credentials)
and sends the post to defaults vhost '/' and post_exchange 'xs_stanley' (default exchange)

A subscriber can download the file /data/shared/products/foo  by logging as user stanley
on mysftpserver.com using the sftp protocol to  broker.com assuming he has proper credentials.

The output of the command is as follows ::

 [INFO] v03.data.shared.products.foo '20150813161959.854 sftp://stanley@mysftpserver.com/ /data/shared/products/foo'
       source=guest parts=1,256,1,0,0 sum=d,fc473c7a2801babbd3818260f50859de 

In MetPX-Sarracenia, each post is published under a certain topic.
After the '[INFO]' the next information gives the \fBtopic*  of the
post. Topics in  *AMQP*  are fields separated by dot. In MetPX-Sarracenia
it is made of a  *topicPrefix*  by default : version  *v03* , 
followed by the  *subtopic*  by default : the file path separated with dots, here, *data.shared.products.foo*

After the topic hierarchy comes the body of the notification.  It consists of a time  *20150813161959.854* ,
and the source url of the file in the last 2 fields.

The remaining line gives informations that are placed in the amqp message header.
Here it consists of  *source=guest* , which is the amqp user,  *parts=1,256,0,0,1* ,
which suggests to download the file in 1 part of 256 bytes (the actual filesize), trailing 1,0,0
gives the number of block, the remaining in bytes and the current
block.  *sum=d,fc473c7a2801babbd3818260f50859de*  mentions checksum information,

here,  *d*  means md5 checksum performed on the data, and  *fc473c7a2801babbd3818260f50859de*
is the checksum value.  When the event on a file is a deletion, sum=R,0  R stands for remove.

Another example watching a file::

 sr3_watch -dr /data/web/public_data -s http://dd.weather.gc.ca/ -p bulletins/alphanumeric/SACN32_CWAO_123456 -pb amqp://broker.com --action start

By default, sr_watch checks the file /data/web/public_data/bulletins/alphanumeric/SACN32_CWAO_123456
(concatenating the baseDir and relative path of the source url to obtain the local file path).
If the file changes, it calculates its checksum. It then builds a post message, logs into broker.com as user 'guest'
(default credentials) and sends the post to defaults vhost '/' and post_exchange 'sx_guest' (default post_exchange)

A subscriber can download the file http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 using http
without authentication on dd.weather.gc.ca.

An example checking a directory::

 sr3_watch -dr /data/web/public_data -pbu http://dd.weather.gc.ca/ -p bulletins/alphanumeric -pb amqp://broker.com -action start

Here, sr_watch checks for file creation(modification) in /data/web/public_data/bulletins/alphanumeric
(concatenating the baseDir and relative path of the source url to obtain the directory path).
If the file SACN32_CWAO_123456 is being created in that directory, sr_watch calculates its checksum.
It then builds a post message, logs into broker.com as user 'guest'

A subscriber can download the created/modified file http://dd.weather.gc.ca/bulletins/alphanumeric/SACN32_CWAO_123456 using http
without authentication on dd.weather.gc.ca.


[-pos|--post_on_start]
~~~~~~~~~~~~~~~~~~~~~~

When starting sr_watch, one can either have the program post all the files in the directories watched
or not.



winnow
------

the **winnow** component subscribes to file notifications and reposts them, suppressing redundant 
ones by comparing their fingerprints (or checksums).  The **Integrity** header stores a file's 
fingerprint as described in the `sr3_post(7) <sr3_post.7.rst>`_ man page.

**winnow** has the following options forced::

   no-download True  
   suppress_duplicates on
   accept_unmatch True

The suppress_duplicates lifetime can be adjusted, but it is always on.

**winnow** connects to a *broker* (often the same as the posting broker)
and subscribes to the notifications of interest. On reception of a notification,
it looks up its **sum** in its cache.  If it is found, the file has already come through,
so the notification is ignored. If not, then the file is new, and the **sum** is added
to the cache and the notification is posted.

**winnow** can be used to trim messages produced by  `post|sr3_post|sr_cpost`_, `poll`_ or `watch`_ etc... It is
used when there are multiple sources of the same data, so that clients only download the
source data once, from the first source that posted it.



DESCRIPTION
===========

Documentation
-------------

While manual pages provide an index or reference for all options,
new users will find the guides provide more helpful examples and walk 
throughs and should start with them.

Users:

* `Installation <../Tutorials/Install.rst>`_ - initial installation.
* `Subscriber Guide <../How2Guides/subscriber.rst>`_ - effective downloading from a pump (mostly on Linux)
* `Windows User Guide <../Tutorials/Windows.rst>`_ - Windows specific variations.
* `Source Guide <../How2Guides/source.rst>`_ - effective uploading to a pump
* `Programming Guide <../Explanation/SarraPluginDev.rst>`_ - Programming custom plugins for workflow integration.

Administrators:

* `Admin Guide <../How2Guides/Admin.rst>`_ - Configuration of Pumps
* `Upgrade Guide <../How2Guides/UPGRADING.rst>`_ - MUST READ when upgrading pumps.
 
Contributors:

* `Developer Guide <../Contribution/Development.rst>`_ - contributing to sarracenia development.

Meta:

* `Overview <../Explanation/sarra.rst>`_ - Introduction.
* `Concepts <../Explanation/Concepts.rst>`_ - Concepts and Glossary

There are also other manual pages available here: `See Also`_

Some quick hints are also available when the command line is invoked with 
either the *help* action, or *-help* op **help** to have a component print 
a list of valid options. 


Configurations
--------------

If one has a ready made configuration called *q_f71.conf*, it can be 
added to the list of known ones with::

  sr_subscribe add q_f71.conf

In this case, xvan_f14 is included with examples provided, so *add* finds it in the examples
directory and copies into the active configuration one. 
Each configuration file manages the consumers for a single queue on
the broker. To view the available configurations, use::

  $ sr_subscribe list

    configuration examples: ( /usr/lib/python3/dist-packages/sarra/examples/subscribe ) 
              all.conf     all_but_cap.conf            amis.conf            aqhi.conf             cap.conf      cclean_f91.conf 
        cdnld_f21.conf       cfile_f44.conf        citypage.conf       clean_f90.conf            cmml.conf cscn22_bulletins.conf 
          ftp_f70.conf            gdps.conf         ninjo-a.conf           q_f71.conf           radar.conf            rdps.conf 
             swob.conf           t_f30.conf      u_sftp_f60.conf 
  
    user plugins: ( /home/peter/.config/sarra/plugins ) 
          destfn_am.py         destfn_nz.py       msg_tarpush.py 
  
    general: ( /home/peter/.config/sarra ) 
            admin.conf     credentials.conf         default.conf
  
    user configurations: ( /home/peter/.config/sarra/subscribe )
       cclean_f91.conf       cdnld_f21.conf       cfile_f44.conf       clean_f90.conf         ftp_f70.conf           q_f71.conf 
            t_f30.conf      u_sftp_f60.conf


one can then modify it using::

  $ sr_subscribe edit q_f71.conf

(The edit command uses the EDITOR environment variable, if present.)
Once satisfied, one can start the the configuration running::

  $ sr_subscibe foreground q_f71.conf

What goes into the files? See next section:


Option Syntax
-------------

Options are placed in configuration files, one per line, in the form::

    option <value>

For example::

    debug true
    debug

sets the *debug* option to enable more verbose logging.  If no value is specified,
the value true is implicit, so the above are equivalent.  A second example 
configuration line::

  broker amqps://anonymous@dd.weather.gc.ca

In the above example, *broker* is the option keyword, and the rest of the line is the 
value assigned to the setting. Configuration files are a sequence of settings, one per line. 
Note:

* the files are read from top to bottom, most importantly for *directory*, *strip*, *mirror*,
  and *flatten* options apply to *accept* clauses that occur after them in the file.

* The forward slash (/) as the path separator in Sarracenia configuration files on all 
  operating systems. Use of the backslash character as a path separator (as used in the 
  cmd shell on Windows) may not work properly. When files are read on Windows, the path
  separator is immediately converted to the forward slash, so all pattern matching,
  in accept, reject, strip etc... directives should use forward slashes when a path
  separator is needed.
  
Example::

    directory A
    accept X

Places files matching X in directory A.

vs::
    accept X
    directory A

Places files matching X in the current working directory, and the *directory A* setting 
does nothing in relation to X.

To provide non-functional descriptions of configurations, or comments, use lines that begin with a **#**.

**All options are case sensitive.**  **Debug** is not the same as **debug** nor **DEBUG**.
Those are three different options (two of which do not exist and will have no effect,
but should generate an ´unknown option warning´).

Options and command line arguments are equivalent.  Every command line argument
has a corresponding long version starting with '--'.  For example *-u* has the
long form *--url*. One can also specify this option in a configuration file.
To do so, use the long form without the '--', and put its value separated by a space.
The following are all equivalent:

  - **url <url>**
  - **-u <url>**
  - **--url <url>**

Settings are interpreted in order.  Each file is read from top to bottom.
For example:

sequence #1::

  reject .*\.gif
  accept .*


sequence #2::

  accept .*
  reject .*\.gif


.. note::
   FIXME: does this match only files ending in 'gif' or should we add a $ to it?
   will it match something like .gif2 ? is there an assumed .* at the end?


In sequence #1, all files ending in 'gif' are rejected. In sequence #2, the 
accept .* (which accepts everything) is encountered before the reject statement, 
so the reject has no effect.  Some options have global scope, rather than being
interpreted in order.  for thoses cases, a second declaration overrides the first.

Options to be reused in different config files can be grouped in an *include* file:

  - **--include <includeConfigPath>**

The includeConfigPath would normally reside under the same config dir of its
master configs. If a URL is supplied as an includeConfigPATH, then a remote 
configuraiton will be downloaded and cached (used until an update on the server 
is detected.) See `Remote Configurations`_ for details.

Environment variables, and some built-in variables can also be put on the
right hand side to be evaluated, surrounded by ${..} The built-in variables are:
 
 - ${BROKER_USER} - the user name for authenticating to the broker (e.g. anonymous)
 - ${PROGRAM}     - the name of the component (sr_subscribe, sr_shovel, etc...)
 - ${CONFIG}      - the name of the configuration file being run.
 - ${HOSTNAME}    - the hostname running the client.
 - ${RANDID}      - a random id that will be consistent within a single invocation.

Option Order
~~~~~~~~~~~~

When a component is started up, a series of configuration files are read in
the following sequence:

 1. default.conf

 2. admin.conf

 3. <prog>.conf (subscribe.conf, audit.conf, etc...)

 4. <progr>/<config>.conf

Settings in an individual .conf file are read in after the default.conf
file, and so can override defaults. Options specified on
the command line override configuration files.

flow_callback options
~~~~~~~~~~~~~~~~~~~~~

Sarracenia makes extensive use of small python code snippets that customize
processing called *flow_callbacks* Flow_callbacks define and use additional settings::

  flow_callback sarracenia.flowcb.log.Log

There is also a shorter form to express the same thing::

  callback log

Either way, the module refers to the sarracenia/flowcb/msg/log.py file in the
installed package. In that file, the Log class is the one searched for entry
points. The log.py file included in the package is like this::

  from sarracenia.flowcb import FlowCB
  import logging

  logger = logging.getLogger( __name__ ) 

  class Log(Plugin):

    def after_accept(self,worklist):
        for msg in worklist.incoming:
            logger.info( "msg/log received: %s " % msg )
        return worklist

It's a normal python class, declared as a child of the sarracenia.flowcb.FlowCB
class. The methods (function names) in the plugin describe when
those routines will be called. For more details consult the 
`Programmer's Guide <../Explanation/SarraPluginDev.rst>`_

To add special processing of messages, create a module in the python
path, and have it include entry points. 

There is also *flow_callbacks_prepend* which adds a flow_callback class to the front
of the list (which determines relative execution order among flow_callback classes.)

   
callback options
~~~~~~~~~~~~~~~~

callbacks that are delivered with metpx-sr3 follow the following convention:

* they are placed in the sarracenia/flowcb  directory tree.
* the name of the primary class is the same as the name of file containing it.

so we provide the following syntactic sugar::

  callback log    (is equivalent to *flow_callback sarracenia.flowcb.log.Log* )

There is similarly a *callback_prepend* to fill in.  

Importing Extensions
~~~~~~~~~~~~~~~~~~~~

The *import* option works in a way familiar to Python developers,
Making them available for use by the Sarracenia core, or flow_callbacks.
Developers can add additional protocols for messages or 
file transfer.  For example::

  import torr

would be a reasonable name for a Transfer protocol to retrieve
resources with bittorrent protocol. A skeleton of such a thing
would look like this:: 


  import logging

  logger = logging.getLogger(__name__)

  import sarracenia.transfer

  class torr(sarracenia.transfer.Transfer):
      pass

  logger.warning("loading")

For more details on implementing extensions, consult the
`Programmer's Guide <../Explanation/SarraPluginDev.rst>`_

Deprecated v2 plugins
~~~~~~~~~~~~~~~~~~~~~

There is and older (v2) style of plugins as well. That are usually 
prefixed with the name of the plugin::

  msg_to_clusters DDI
  msg_to_clusters DD

  on_message msg_to_clusters

A setting 'msg_to_clusters' is needed by the *msg_to_clusters* plugin
referenced in the *on_message* the v2 plugins are a little more
cumbersome to write. They are included here for completeness, but
people should use version 3 (either flow_callbacks, or extensions
discussed next) when possible.

Reasons to use newer style plugins:

* Support for running v2 plugins is accomplished using a flowcb
  called v2wrapper. It performs a lot of processing to wrap up
  the v3 data structures to look like v2 ones, and then has
  to propagate the changes back. It's a bit expensive.

* newer style extensions are ordinary python modules, unlike
  v2 ones which require minor magic incantations.

* when a v3 (flow_callback or imported) module has a syntax error,
  all the tools of the python interpreter apply, providing
  a lot more feedback is given to the coder. with v2, it just
  says there is something wrong, much more difficult to debug.

* v3 api is strictly more powerful than v2, as it works
  on groups of messages, rather than individual ones.



Environment Variables
~~~~~~~~~~~~~~~~~~~~~

On can also reference environment variables in configuration files,
using the *${ENV}* syntax.  If Sarracenia routines needs to make use
of an environment variable, then they can be set in configuration files::

  declare env HTTP_PROXY=localhost


LOGS and MONITORING
-------------------

As sr3 components usually run as a daemon (unless invoked in *foreground* mode) 
one normally examines its log file to find out how processing is going.  When only
a single instance is running, one can view the log of the running process like so::

   sr3 log subscribe/*myconfig*

Where *myconfig* is the name of the running configuration. Log files 
are placed as per the XDG Open Directory Specification. There will be a log file 
for each *instance* (download process) of an sr_subscribe process running the myflow configuration::

   in linux: ~/.cache/sarra/log/sr_subscribe_myflow_01.log

One can override placement on linux by setting the XDG_CACHE_HOME environment variable, as
per: `XDG Open Directory Specification <https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.html>`_ 
Log files can be very large for high volume configurations, so the logging is very configurable.

To begin with, one can select the logging level:

- debug
   Setting option debug is identical to use  **loglevel debug**

- logLevel ( default: info )
   The level of logging as expressed by python's logging. Possible values are :  critical, error, info, warning, debug.

- log_reject <True|False> ( default: False )
   print a log message when *rejecting* messages (choosing not to download the corresponding files)

rejecting messages:

* rejecting pattern -- based on accept/reject clause, excluding a file from processing.

* rejecting duplicate -- based on suppress_duplicates settings (recent file cache) 

* rejecting loop -- directories in a tree refer to each other causing the same directory to be scanned redundantly, perhaps in an infinite loop.


One can also get finer grained control over logging by using flow_callbacks. For example, the default settings
typically include which logs each file after it has been downloaded, but not
when the message is received. To have a line in the log for each message received set::

   FIXME: v2 example, wrong for v3

   after_accept msg_rawlog

There are similar plugins available for different parts of processing::

   after_work file_log (default)

   on_posts post_log
   
etc... One can also modify the provided plugins, or write new ones to completely change the logging.

At the end of the day (at midnight), these logs are rotated automatically by 
the components, and the old log gets a date suffix. The directory in which 
the logs are stored can be overridden by the **log** option, the number of 
rotated logs to keep are set by the **logrotate** parameter. The oldest log 
file is deleted when the maximum number of logs has been reach and this 
continues for each rotation. An interval takes a duration of the interval and 
it may takes a time unit suffix, such as 'd\|D' for days, 'h\|H' for hours, 
or 'm\|M' for minutes. If no unit is provided logs will rotate at midnight.
Here are some settings for log file management:

- log <dir> ( default: ~/.cache/sarra/log ) (on Linux)
   The directory to store log files in.

- statehost <False|True> ( default: False )
   In large data centres, the home directory can be shared among thousands of 
   nodes. Statehost adds the node name after the cache directory to make it 
   unique to each node. So each node has it's own statefiles and logs.
   example, on a node named goofy,  ~/.cache/sarra/log/ becomes ~/.cache/sarra/goofy/log.

- logrotate <max_logs> ( default: 5 )
   Maximum number of logs archived.

- logrotate_interval <duration>[<time_unit>] ( default: 1 )
   The duration of the interval with an optional time unit (ie 5m, 2h, 3d)

- chmod_log ( default: 0600 )
   The permission bits to set on log files.




CREDENTIALS
-----------

One normally does not specify passwords in configuration files.  Rather they are placed 
in the credentials file::

   sr_subscribe edit credentials

For every url specified that requires a password, one places 
a matching entry in credentials.conf.
The broker option sets all the credential information to connect to the  **RabbitMQ** server 

- **broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqps://anonymous:anonymous@dd.weather.gc.ca/ )

For all **sarracenia** programs, the confidential parts of credentials are stored
only in ~/.config/sarra/credentials.conf.  This includes the destination and the broker
passwords and settings needed by components.  The format is one entry per line.  Examples:

- **amqp://user1:password1@host/**
- **amqps://user2:password2@host:5671/dev**

- **sftp://user5:password5@host**
- **sftp://user6:password6@host:22  ssh_keyfile=/users/local/.ssh/id_dsa**

- **ftp://user7:password7@host  passive,binary**
- **ftp://user8:password8@host:2121  active,ascii**

- **ftps://user7:De%3Aize@host  passive,binary,tls**
- **ftps://user8:%2fdot8@host:2121  active,ascii,tls,prot_p**
- **https://ladsweb.modaps.eosdis.nasa.gov/ bearer_token=89APCBF0-FEBE-11EA-A705-B0QR41911BF4**


In other configuration files or on the command line, the url simply lacks the
password or key specification.  The url given in the other files is looked
up in credentials.conf.

Note::
 SFTP credentials are optional, in that sarracenia will look in the .ssh directory
 and use the normal SSH credentials found there.

 These strings are URL encoded, so if an account has a password with a special 
 character, its URL encoded equivalent can be supplied.  In the last example above, 
 **%2f** means that the actual password isi: **/dot8**
 The next to last password is:  **De:olonize**. ( %3a being the url encoded value for a colon character. )


CONSUMER
========

Most Metpx Sarracenia components loop on reception and consumption of sarracenia 
AMQP messages.  Usually, the messages of interest are `sr3_post(7) <sr3_post.7.rst>`_ 
messages, announcing the availability of a file by publishing its URL ( or a part 
of a file ), but there are also `sr_report(7) <#report>`_ messages which 
can be processed using the same tools. AMQP messages are published to an exchange 
on a broker (AMQP server). The exchange delivers messages to queues. To receive 
messages, one must provide the credentials to connect to the broker (AMQP message 
pump). Once connected, a consumer needs to create a queue to hold pending messages.
The consumer must then bind the queue to one or more exchanges so that they put 
messages in its queue.

Once the bindings are set, the program can receive messages. When a message is received,
further filtering is possible using regular expressions onto the AMQP messages.
After a message passes this selection process, and other internal validation, the
component can run an **on_message** plugin script to perform additional message 
processing. If this plugin returns False, the message is discarded. If True, 
processing continues.

The following sections explains all the options to set this "consuming" part of
sarracenia programs.



Setting the Broker 
------------------

**broker [amqp|mqtt]{s}://<user>:<password>@<brokerhost>[:port]/<vhost>**

A URI is used to configure a connection to a message pump, either
an MQTT or an AMQP broker. Some Sarracenia components set a reasonable default for 
that option.  provide the normal user,host,port of connections. In most configuration files,
the password is missing. The password is normally only included in the credentials.conf file.

Sarracenia work has not used vhosts, so **vhost** should almost always be **/**.

for more info on the AMQP URI format: ( https://www.rabbitmq.com/uri-spec.html )


either in the default.conf or each specific configuration file.
The broker option tell each component which broker to contact.

**broker [amqp|mqtt]{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::
      (default: None and it is mandatory to set it ) 

Once connected to an AMQP broker, the user needs to bind a queue
to exchanges and topics to determine the messages of interest.



Creating the Queue
------------------

Once connected to an AMQP broker, the user needs to create a queue.

Setting the queue on broker :

- **queue         <name>         (default: q_<brokerUser>.<programName>.<configName>)**
- **durable       <boolean>      (default: True)**
- **expire        <duration>      (default: 5m  == five minutes. RECOMMEND OVERRIDING)**
- **message_ttl   <duration>      (default: None)**
- **prefetch      <N>            (default: 1)**
- **reset         <boolean>      (default: False)**
- **restore       <boolean>      (default: False)**
- **restore_to_queue <queuename> (default: None)**
- **save          <boolean>      (default: False)**
- **declare_queue <boolean>      (default: True)**
- **bind_queue    <boolean>      (default: True)**


Usually components guess reasonable defaults for all these values
and users do not need to set them.  For less usual cases, the user
may need to override the defaults.  The queue is where the notifications
are held on the server for each subscriber.

[ queue|queue_name|qn <name>]
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, components create a queue name that should be unique. The 
default queue_name components create follows the following convention: 

   **q_<brokerUser>.<programName>.<configName>.<random>.<random>** 

Where:

* *brokerUser* is the username used to connect to the broker (often: *anonymous* )

* *programName* is the component using the queue (e.g. *sr_subscribe* ),

* *configName* is the configuration file used to tune component behaviour.

* *random* is just a series of characters chosen to avoid clashes from multiple
  people using the same configurations

Users can override the default provided that it starts with **q_<brokerUser>**.

When multiple instances are used, they will all use the same queue, for trivial
multi-tasking. If multiple computers have a shared home file system, then the
queue_name is written to: 

 ~/.cache/sarra/<programName>/<configName>/<programName>_<configName>_<brokerUser>.qname

Instances started on any node with access to the same shared file will use the
same queue. Some may want use the *queue_name* option as a more explicit method
of sharing work across multiple nodes.



durable <boolean> (default: True)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **durable** option, if set to True, means writes the queue
on disk if the broker is restarted.

expire <duration> (default: 5m  == five minutes. RECOMMEND OVERRIDING)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **expire**  option is expressed as a duration... it sets how long should live
a queue without connections. 

A raw integer is expressed in seconds, if the suffix m,h,d,w
are used, then the interval is in minutes, hours, days, or weeks. After the queue expires,
the contents are dropped, and so gaps in the download data flow can arise.  A value of
1d (day) or 1w (week) can be appropriate to avoid data loss. It depends on how long
the subscriber is expected to shutdown, and not suffer data loss.

if no units are given, then a decimal number of seconds can be provided, such as
to indicate 0.02 to specify a duration of 20 milliseconds.

The **expire** setting must be overridden for operational use. 
The default is set low because it defines how long resources on the broker will be assigned,
and in early use (when default was 1 week) brokers would often get overloaded with very 
long queues for left-over experiments.  


message_ttl <duration>  (default: None)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **message_ttl**  option set the time a message can live in the queue.
Past that time, the message is taken out of the queue by the broker.

prefetch <N> (default: 1)
~~~~~~~~~~~~~~~~~~~~~~~~~

The **prefetch** option sets the number of messages to fetch at one time.
When multiple instances are running and prefetch is 4, each instance will obtain up to four
messages at a time.  To minimize the number of messages lost if an instance dies and have
optimal load sharing, the prefetch should be set as low as possible.  However, over long
haul links, it is necessary to raise this number, to hide round-trip latency, so a setting
of 10 or more may be needed.

reset <boolean> (default: False)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When **reset** is set, and a component is (re)started, its queue is
deleted (if it already exists) and recreated according to the component's
queue options.  This is when a broker option is modified, as the broker will
refuse access to a queue declared with options that differ from what was
set at creation.  It can also be used to discard a queue quickly when a receiver 
has been shut down for a long period. If duplicate suppression is active, then
the reception cache is also discarded.

The AMQP protocol defines other queue options which are not exposed
via sarracenia, because sarracenia itself picks appropriate values.

save/restore
~~~~~~~~~~~~

The **save** option is used to read messages from the queue and write them
to a local file, saving them for future processing, rather than processing
them immediately.  See the `Sender Destination Unavailable`_ section for more details.
The **restore** option implements the reverse function, reading from the file
for processing.  

If **restore_to_queue** is specified, then rather than triggering local
processing, the messages restored are posted to a temporary exchange 
bound to the given queue.  For an example, see `Shovel Save/Restore`_ 

declare_queue/bind_queue
~~~~~~~~~~~~~~~~~~~~~~~~

On startup, by default, Sarracenia redeclares resources and bindings to ensure they
are uptodate.  If the queue already exists, These flags can be 
set to False, so no attempt to declare the queue is made, or it´s bindings. 
These options are useful on brokers that do not permit users to declare their queues.




AMQP QUEUE BINDINGS
-------------------

Once one has a queue, it must be bound to an exchange.
Users almost always need to set these options. Once a queue exists
on the broker, it must be bound to an exchange. Bindings define which
messages (URL notifications) the program receives. The root of the topic
tree is fixed to indicate the protocol version and type of the
message (but developers can override it with the **topicPrefix**
option.)

These options define which messages (URL notifications) the program receives:

 - **exchange      <name>         (default: xpublic)** 
 - **exchange_suffix      <name>  (default: None)** 
 - **topicPrefix  <amqp pattern> (default: v03 -- developer option)** 
 - **subtopic      <amqp pattern> (no default, must appear after exchange)** 

exchange <name> (default: xpublic) and exchange_suffix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The convention on data pumps is to use the *xpublic* exchange. Users can establish
private data flow for their own processing. Users can declare their own exchanges
that always begin with *xs_<username>*, so to save having to specify that each
time, one can just set *exchange_suffix kk* which will result in the exchange
being set to *xs_<username>_kk* (overriding the *xpublic* default). 
These settings must appear in the configuration file before the corresponding 
*topicPrefix* and *subtopic* settings.

subtopic <amqp pattern> (default: #)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Within an exchange's postings, the subtopic setting narrows the product selection.
To give a correct value to the subtopic,
one has the choice of filtering using **subtopic** with only AMQP's limited wildcarding and
length limited to 255 encoded bytes, or the more powerful regular expression 
based  **accept/reject**  mechanisms described below. The difference being that the 
AMQP filtering is applied by the broker itself, saving the notices from being delivered 
to the client at all. The  **accept/reject**  patterns apply to messages sent by the 
broker to the subscriber. In other words,  **accept/reject**  are client side filters, 
whereas **subtopic** is server side filtering.  

It is best practice to use server side filtering to reduce the number of announcements sent
to the client to a small superset of what is relevant, and perform only a fine-tuning with the 
client side mechanisms, saving bandwidth and processing for all.

topicPrefix is primarily of interest during protocol version transitions, 
where one wishes to specify a non-default protocol version of messages to 
subscribe to. 

Usually, the user specifies one exchange, and several subtopic options.
**Subtopic** is what is normally used to indicate messages of interest.
To use the subtopic to filter the products, match the subtopic string with
the relative path of the product.

For example, consuming from DD, to give a correct value to subtopic, one can
browse the our website  **http://dd.weather.gc.ca** and write down all directories
of interest.  For each directory tree of interest, write a  **subtopic**
option as follow:

 **subtopic  directory1.*.subdirectory3.*.subdirectory5.#**

::

 where:  
       *                matches a single directory name 
       #                matches any remaining tree of directories.

note:
  When directories have these wild-cards, or spaces in their names, they 
  will be URL-encoded ( '#' becomes %23 )
  When directories have periods in their name, this will change
  the topic hierarchy.

  FIXME: 
      hash marks are URL substituted, but did not see code for other values.
      Review whether asterisks in directory names in topics should be URL-encoded.
      Review whether periods in directory names in topics should be URL-encoded.
 
One can use multiple bindings to multiple exchanges as follows::

  exchange A
  subtopic directory1.*.directory2.#

  exchange B
  subtopic *.directory4.#

Will declare two separate bindings to two different exchanges, and two different file trees.
While default binding is to bind to everything, some brokers might not permit
clients to set bindings, or one might want to use existing bindings.
One can turn off queue binding as follows::

  subtopic None

(False, or off will also work.)





Client-side Filtering
---------------------

We have selected our messages through **exchange**, **subtopic** and
perhaps patterned  **subtopic** with AMQP's limited wildcarding which
is all done by the broker (server-side). The broker puts the 
corresponding messages in our queue. The subscribed component 
downloads these messages.  Once the message is downloaded, Sarracenia 
clients apply more flexible client side filtering using regular expressions.

Brief Introduction to Regular Expressions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Regular expressions are a very powerful way of expressing pattern matches. 
They provide extreme flexibility, but in these examples we will only use a
very trivial subset: The . is a wildcard matching any single character. If it
is followed by an occurrence count, it indicates how many letters will match
the pattern. The * (asterisk) character, means any number of occurrences.
So:

 - .* means any sequence of characters of any length. In other words, match anything.

 - cap.* means any sequence of characters that starts with cap.

 - .*CAP.* means any sequence of characters with CAP somewhere in it. 

 - .*cap means any sequence of characters that ends with CAP.  In the case 
   where multiple portions of the string could match, the longest one is selected.

 - .*?cap same as above, but *non-greedy*, meaning the shortest match is chosen.

Please consult various internet resources for more information on the full
variety of matching possible with regular expressions:

 - https://docs.python.org/3/library/re.html
 - https://en.wikipedia.org/wiki/Regular_expression
 - http://www.regular-expressions.info/ 


accept, reject and accept_unmatch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **accept    <regexp pattern> (optional)**
- **reject    <regexp pattern> (optional)**
- **accept_unmatch   <boolean> (default: False)**
- **baseUrl_relPath   <boolean> (default: False)**

The  **accept**  and  **reject**  options process regular expressions (regexp).
The regexp is applied to the the message's URL for a match.

If the message's URL of a file matches a **reject**  pattern, the message
is acknowledged as consumed to the broker and skipped.

One that matches an **accept** pattern is processed by the component.

In many configurations, **accept** and **reject** options are mixed
with the **directory** option.  They then relate accepted messages
to the **directory** value they are specified under.

After all **accept** / **reject**  options are processed, normally
the message is acknowledged as consumed and skipped. To override that
default, set **accept_unmatch** to True. The **accept/reject** 
settings are interpreted in order. Each option is processed orderly 
from top to bottom. For example:

sequence #1::

  reject .*\.gif
  accept .*

sequence #2::

  accept .*
  reject .*\.gif


In sequence #1, all files ending in 'gif' are rejected.  In sequence #2, the accept .* (which
accepts everything) is encountered before the reject statement, so the reject has no effect.

It is best practice to use server side filtering to reduce the number of announcements sent
to the component to a small superset of what is relevant, and perform only a fine-tuning with the
client side mechanisms, saving bandwidth and processing for all. More details on how
to apply the directives follow:

Normally the relative path (appended to the base directory) for files which are downloaded
will be set according to the relPath header included in the message.  if *baseUrl_relPath*
is set, however, the message's relPath will be prepended with the sub-directories from
the message's baseUrl field.

ACCELERATION
------------

Some protocols permit an binary downloader to be used in place of the default
pure python code. There is overhead in spawning a binary downloader, and so
for smaller files it is faster and/or more efficient to use built-in processing.

accel_treshold <byte count> (default: 0- disabled.)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The accel_threshold indicates the minimum size of file being transferred for
which a binary downloader will be launched.

accel_xx_command 
~~~~~~~~~~~~~~~~

Can specify alternate binaries for downloaders to tune for specific cases.

+-----------------------------------+--------------------------------+
|  Option                           |  Defaul value                  |
+-----------------------------------+--------------------------------+
|  accel_wget_command               |  /usr/bin/wget %s -O %d        |
+-----------------------------------+--------------------------------+
|  accel_scp_command                |  /usr/bin/scp %s %d            |
+-----------------------------------+--------------------------------+
|  accel_cp_command                 |  /usr/bin/cp  %s %d            |
+-----------------------------------+--------------------------------+
|  accel_ftpget_command             |  /usr/bin/ncftpget %s %d       |
+-----------------------------------+--------------------------------+
|  accel_ftpput_command             |  /usr/bin/ncftpput %s %d       |
+-----------------------------------+--------------------------------+

use the %s to stand-in for the name of the source file, and %d for the
file being written.  An example setting to override with::

   accel_cp_command dd if=%s of=%d bs=4096k



DELIVERY SPECIFICATIONS
-----------------------

These options set what files the user wants and where it will be placed,
and under which name.

- **accel_threshold  <byte count> (default: 0)** 
- **accept    <regexp pattern> (must be set)** 
- **accept_unmatch   <boolean> (default: off)**
- **attempts     <count>          (default: 3)**
- **batch     <count>          (default: 100)**
- **default_mode     <octalint>       (default: 0 - umask)**
- **default_dir_mode <octalint>       (default: 0755)**
- **delete    <boolean>>       (default: off)**
- **directory <path>           (default: .)** 
- **discard   <boolean>        (default: off)**
- **baseDir <path>       (default: /)**
- **flatten   <string>         (default: '/')** 
- **heartbeat <count>                 (default: 300 seconds)**
- **inline   <boolean>         (default: False)**
- **inline_max   <counts>         (default: 1024)**
- **inline_only   <boolean>       (default: False)**
- **inplace       <boolean>        (default: On)**
- **kbytes_ps <count>               (default: 0)**
- **inflight  <string>         (default: .tmp or NONE if post_broker set)** 
- **message_count_max <count> (default: 0 == DISABLED)**
- **message_rate_max <float>   (default: 0 == DISABLED)**
- **message_rate_min <float>   (default: 0 == DISABLED)**
- **mirror    <boolean>        (default: off)** 
- **no_download|notify_only    <boolean>        (default: off)** 
- **outlet    post|json|url    (default: post)** 
- **overwrite <boolean>        (default: off)** 
- **preserve_mode <boolean>  (default: on)**
- **preserve_time <boolean>  (default: on)**
- **reject    <regexp pattern> (optional)** 
- **retry    <boolean>         (default: On)** 
- **retry_ttl    <duration>         (default: same as expire)** 
- **source_from_exchange  <boolean> (default: off)**
- **strip     <count|regexp>   (default: 0)**
- **suppress_duplicates   <off|on|999[smhdw]>     (default: off)**
- **suppress_duplicates_basis   <data|name|path>     (default: path)**
- **timeout     <float>         (default: 0)**
- **tls_rigour   <lax|medium|strict>  (default: medium)**
- **xattr_disable  <boolean>  (default: off)**



attempts <count> (default: 3)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **attempts** option indicates how many times to 
attempt downloading the data before giving up.  The default of 3 should be appropriate 
in most cases.  When the **retry** option is false, the file is then dropped immediately.

When The **retry** option is set (default), a failure to download after prescribed number
of **attempts** (or send, in a sender) will cause the message to be added to a queue file 
for later retry.  When there are no messages ready to consume from the AMQP queue, 
the retry queue will be queried.

retry_ttl <duration> (default: same as expire)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **retry_ttl** (retry time to live) option indicates how long to keep trying to send 
a file before it is aged out of a the queue.  Default is two days.  If a file has not 
been transferred after two days of attempts, it is discarded.

timeout <float> (default: 0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **timeout** option, sets the number of seconds to wait before aborting a
connection or download transfer (applied per buffer during transfer).

inflight <string> (default: .tmp or NONE if post_broker set)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **inflight**  option sets how to ignore files when they are being transferred
or (in mid-flight betweeen two systems). Incorrect setting of this option causes
unreliable transfers, and care must be taken.  See `Delivery Completion (inflight)`_ 
for more details.

The value can be a file name suffix, which is appended to create a temporary name during 
the transfer.  If **inflight**  is set to **.**, then it is a prefix, to conform with 
the standard for "hidden" files on unix/linux.  
If **inflight**  ends in / (example: *tmp/* ), then it is a prefix, and specifies a 
sub-directory of the destination into which the file should be written while in flight. 

Whether a prefix or suffix is specified, when the transfer is 
complete, the file is renamed to its permanent name to allow further processing.

When posting a file with sr3_post, sr_cpost, or sr3_watch, the  **inflight**  option 
can also be specified as a time interval, for example, 10 for 10 seconds.  
When set to a time interval, file posting process ensures that it waits until 
the file has not been modified in that interval. So a file will 
not be processed until it has stayed the same for at least 10 seconds. 
If you see the error message::

    inflight setting: 300, not for remote

It is because the time interval setting is only supported by sr3_post/sr_cpost/sr3_watch.
in looking at local files before generating a post, it is not used as say, a means
of delaying sending files.

Lastly, **inflight** can be set to *NONE*, which case the file is written directly
with the final name, where the recipient will wait to receive a post notifying it
of the file's arrival.  This is the fastest, lowest overhead option when it is available.
It is also the default when a *post_broker* is given, indicating that some
other process is to be notified after delivery.

delete <boolean> (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the **delete** option is set, after a download has completed successfully, the subscriber
will delete the file at the upstream source.  Default is false.

batch <count> (default: 100)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **batch** option is used to indicate how many files should be transferred 
over a connection, before it is torn down, and re-established.  On very low 
volume transfers, where timeouts can occur between transfers, this should be
lowered to 1.  For most usual situations the default is fine. For higher volume
cases, one could raise it to reduce transfer overhead. It is only used for file
transfer protocols, not HTTP ones at the moment.

directory <path> (default: .)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *directory* option defines where to put the files on your server.
Combined with  **accept** / **reject**  options, the user can select the
files of interest and their directories of residence (see the  **mirror**
option for more directory settings).

The  **accept**  and  **reject**  options use regular expressions (regexp) to match URL.
These options are processed sequentially. 
The URL of a file that matches a  **reject**  pattern is never downloaded.
One that matches an  **accept**  pattern is downloaded into the directory
declared by the closest  **directory**  option above the matching  **accept** option.
**accept_unmatch** is used to decide what to do when no reject or accept clauses matched.

::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*

mirror <boolean> (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **mirror**  option can be used to mirror the dd.weather.gc.ca tree of the files.
If set to  **True**  the directory given by the  **directory**  option
will be the basename of a tree. Accepted files under that directory will be
placed under the subdirectory tree leaf where it resides under dd.weather.gc.ca.
For example retrieving the following url, with options::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif
mirror settings can be changed between directory options.

strip <count|regexp> (default: 0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can modify the relative mirrored directories with the **strip** option. 
If set to N  (an integer) the first 'N' directories from the relative path 
are removed. For example::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   strip     3
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/WGJ/201312141900_WGJ_PRECIP_SNOW.gif
when a regexp is provide in place of a number, it indicates a pattern to be removed
from the relative path.  For example if::

   strip  .*?GIF/

Will also result in the file being placed the same location. 
Note that strip settings can be changed between directory options.

NOTE::
    with **strip**, use of **?** modifier (to prevent regular expression *greediness* ) is often helpful. 
    It ensures the shortest match is used.

    For example, given a file name:  radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.GIF
    The expression:  .*?GIF   matches: radar/PRECIP/GIF
    whereas the expression: .*GIF matches the entire name.

flatten <string> (default: '/')
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **flatten**  option is use to set a separator character. The default value ( '/' )
nullifies the effect of this option.  This character replaces the '/' in the url 
directory and create a "flatten" filename from its dd.weather.gc.ca path.  
For example retrieving the following url, with options::

 http://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/12/015/CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

   flatten   -
   directory /mylocaldirectory
   accept    .*model_gem_global.*

would result in the creation of the filepath::

 /mylocaldirectory/model_gem_global-25km-grib2-lat_lon-12-015-CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

One can also specify variable substitutions to be performed on arguments to the directory 
option, with the use of *${..}* notation::

   SOURCE   - the amqp user that injected data (taken from the message.)
   BD       - the base directory
   BUP      - the path component of the baseUrl (aka base url path) 
   BUPL     - the last element of the baseUrl path.
   PBD      - the post base dir
   YYYYMMDD - the current daily timestamp.
   HH       - the current hourly timestamp.
   *var*    - any environment variable.

The YYYYMMDD and HH time stamps refer to the time at which the data is processed by
the component, it is not decoded or derived from the content of the files delivered.
All date/times in Sarracenia are in UTC.

Refer to *source_from_exchange* for a common example of usage.  Note that any sarracenia
built-in value takes precedence over a variable of the same name in the environment.
Note that flatten settings can be changed between directory options.

baseDir <path> (default: /)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**baseDir** supplies the directory path that, when combined with the relative
one in the selected notification gives the absolute path of the file to be sent.
The default is None which means that the path in the notification is the absolute one.

**FIXME**::
    cannot explain this... do not know what it is myself. This is taken from sender.
    in a subscriber, if it is set... will it download? or will it assume it is local?
    in a sender.

inline <boolean> (default: False)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When posting messages, The **inline** option is used to have the file content
included in the post. This can be efficient when sending small files over high
latency links, a number of round trips can be saved by avoiding the retrieval
of the data using the URL.  One should only inline relatively small files,
so when **inline** is active, only files smaller than **inline_max** bytes
(default: 1024) will actually have their content included in the post messages.
If **inline_only** is set, and a file is larger than inline_max, the file
will not be posted.


inplace <boolean> (default: On)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Large files may be sent as a series of parts, rather than all at once.
When downloading, if **inplace** is true, these parts will be appended to the file 
in an orderly fashion. Each part, after it is inserted in the file, is announced to subscribers.
This can be set to false for some deployments of sarracenia where one pump will 
only ever see a few parts, and not the entirety, of multi-part files. 

The **inplace** option defaults to True. 
Depending of **inplace** and if the message was a part, the path can
change again (adding a part suffix if necessary).

outlet post|json|url (default: post)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **outlet** option is used to allow writing of posts to file instead of
posting to a broker. The valid argument values are:

**post:**

  post messages to an post_exchange

  **post_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**
  **post_exchange     <name>         (MANDATORY)**
  **post_topicPrefix <string>       (default: "v03")**
  **on_post           <script>       (default: None)**

  The **post_broker** defaults to the input broker if not provided.
  Just set it to another broker if you want to send the notifications
  elsewhere.

  The **post_exchange** must be set by the user. This is the exchange under
  which the notifications will be posted.

**json:**

  write each message to standard output, one per line in the same json format used for
  queue save/restore by the python implementation.

**url:**

  just output the retrieval URL to standard output.

FIXME: The **outlet** option came from the C implementation ( *sr_cpump*  ) and it has not
been used much in the python implementation. 

overwrite <boolean> (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **overwrite**  option,if set to false, avoid unnecessary downloads under these conditions :

1- the file to be downloaded is already on the user's file system at the right place and

2- the checksum of the amqp message matched the one of the file.

The default is False. 

discard <boolean> (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **discard**  option,if set to true, deletes the file once downloaded. This option can be
usefull when debugging or testing a configuration.

source_from_exchange <boolean> (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **source_from_exchange** option is mainly for use by administrators.
If messages received are posted directly from a source, the exchange used 
is 'xs_<brokerSourceUsername>'. Such messages could be missing *source* and *from_cluster* 
headings, or a malicious user may set the values incorrectly.
To protect against both problems, administrators should set the **source_from_exchange** option.

When the option is set, values in the message for the *source* and *from_cluster* headers will then be overridden::

  self.msg.headers['source']       = <brokerUser>
  self.msg.headers['from_cluster'] = cluster

replacing any values present in the message. This setting should always be used when ingesting data from a
user exchange. These fields are used to return reports to the origin of injected data.
It is commonly combined with::

       *mirror true*
       *source_from_exchange true*
       *directory ${PBD}/${YYYYMMDD}/${SOURCE}*
  
To have data arrive in the standard format tree.

heartbeat <count> (default: 300 seconds)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **heartbeat** option sets how often to execute periodic processing as determined by 
the list of on_heartbeat plugins. By default, it prints a log message every heartbeat.

shim_defer_posting_to_exit (EXPERIMENTAL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  (option specific to libsrshim)
  Postpones file posting until the process exits.
  In cases where the same file is repeatedly opened and appended to, this
  setting can avoid redundant posts.  (default: False)

shim_post_minterval *interval* (EXPERIMENTAL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  (option specific to libsrshim)
  If a file is opened for writing and closed multiple times within the interval,
  it will only be posted once. When a file is written to many times, particularly
  in a shell script, it makes for many posts, and shell script affects performance.
  subscribers will not be able to make copies quickly enough in any event, so
  there is little benefit, in say, 100 posts of the same file in the same second.
  It is wise set an upper limit on the frequency of posting a given file. (default: 5s)
  Note: if a file is still open, or has been closed after its previous post, then
  during process exit processing it will be posted again, even if the interval
  is not respected, in order to provide the most accurate final post.


shim_skip_parent_open_files (EXPERIMENTAL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  (option specific to libsrshim)
  The shim_skip_ppid_open_files option means that a process checks
  whether the parent process has the same file open, and does not
  post if that is the case. (default: True)


suppress_duplicates <off|on|999[smhdw]> (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When **suppress_duplicates** (also **cache** ) is set to a non-zero time interval, each new message
is compared against ones received within that interval, to see if it is a duplicate. 
Duplicates are not processed further. What is a duplicate? A file with the same name (including 
parts header) and checksum. Every *hearbeat* interval, a cleanup process looks for files in the 
cache that have not been referenced in **cache** seconds, and deletes them, in order to keep 
the cache size limited. Different settings are appropriate for different use cases.

A raw integer interval is in seconds, if the suffix m,h,d, or w are used, then the interval 
is in minutes, hours, days, or weeks. After the interval expires the contents are 
dropped, so duplicates separated by a large enough interval will get through.
A value of 1d (day) or 1w (week) can be appropriate.  Setting the option without specifying
a time will result in 300 seconds (or 5 minutes) being the expiry interval.

**Use of the cache is incompatible with the default *parts 0* strategy**, one must specify an 
alternate strategy.  One must use either a fixed blocksize, or always never partition files. 
One must avoid the dynamic algorithm that will change the partition size used as a file grows.

**Note that the duplicate suppresion store is local to each instance**. When N 
instances share a queue, the first time a posting is received, it could be 
picked by one instance, and if a duplicate one is received it would likely 
be picked up by another instance. **For effective duplicate suppression with instances**, 
one must **deploy two layers of subscribers**. Use 
a **first layer of subscribers (sr_shovels)** with duplicate suppression turned 
off and output with *post_exchange_split*, which route posts by checksum to 
a **second layer of subscibers (sr_winnow) whose duplicate suppression caches are active.**
  
suppress_duplicates_basis <data|name|path> (default: path)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A keyword option (alternative: *cache_basis* ) to identify which files are compared for 
duplicate suppression purposes. Normally, the duplicate suppression uses the entire path
to identify files which have not changed. This allows for files with identical 
content to be posted in different directories and not be suppressed. In some
cases, suppression of identical files should be done regardless of where in 
the tree the file resides.  Set 'name' for files of identical name, but in
different directories to be considered duplicates. Set to 'data' for any file, 
regardless of name, to be considered a duplicate if the checksum matches.


kbytes_ps <count> (default: 0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**kbytes_ps** is greater than 0, the process attempts to respect this delivery
speed in kilobytes per second... ftp,ftps,or sftp)

**FIXME**: kbytes_ps... only implemented by sender? or subscriber as well, data only, or messages also?

message_count_max <count> (default: 0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If **message_count_max** is greater than zero, the flow will exit after processing the given
number of messages.  This is normally used only for debugging.

message_rate_max <float> (default: 0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if **message_rate_max** is greater than zero, the flow attempts to respect this delivery
speed in terms of messages per second. Note that the throttle is on messages obtained or generated 
per second, prior to accept/reject filtering. the flow will sleep to limit the processing rate.


message_rate_min <float> (default: 0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if **message_rate_min** is greater than zero, and the flow detected is lower than this rate,
a warning message will be produced:



preserve_time (default: on)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

On unix-like systems, when the *ls* commend or a file browser shows modification or 
access times, it is a display of the posix *st_atime*, and *st_ctime* elements of a 
struct struct returned by stat(2) call.  When *preserve_time* is on, headers
reflecting these values in the messages are used to restore the access and modification 
times respectively on the subscriber system. To document delay in file reception,
this option can be turned off, and then file times on source and destination compared.

When set in a posting component, it has the effect of eliding the *atime* and *mtime* 
headers from the messages.

default_mode, default_dir_mode, preserve_mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Permission bits on the destination files written are controlled by the *preserve_mode* directives.
*preserve_modes* will apply the mode permissions posted by the source of the file.
If no source mode is available, the *default_mode* will be applied to files, and the
*default_dir_mode* will be applied to directories. If no default is specified,
then the operating system  defaults (on linux, controlled by umask settings)
will determine file permissions. (Note that the *chmod* option is interpreted as a synonym
for *default_mode*, and *chmod_dir* is a synonym for *default_dir_mode*).

When set in a posting component, it has the effect of eliding the *mode* 
header from the messages.

recompute_chksum <boolean> (Always on now)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

recompute_chksum option has been removed in 2.19.03b2. Recomputing will occur
whenever appropriate without the need for a setting.

tls_rigour (default: medium)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

tls_rigour can be set to: *lax, medium, or strict*, and gives a hint to the 
application of how to configure TLS connections. TLS, or Transport Level 
Security (used to be called Secure Socket Layer (SSL)) is the wrapping of 
normal TCP sockets in standard encryption. There are many aspects of TLS 
negotiations, hostname checking, Certificate checking, validation, choice of 
ciphers. What is considered secure evolves over time, so settings which, a few
years ago, were considered secure, are currently aggressively deprecated. This
situation naturally leads to difficulties in communication due to different
levels of compliance with whatever is currently defined as rigourous encryption.

If a site being connected to, has, for example, and expired certificate, and 
it is nevertheless necessary to use it, then set tls_rigour to *lax* and
the connection should succeed regardless.





xattr_disable (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, on receipt of files, the mtime and checksum are written to a file's
extended attributes (on unix/linux/mac) or to alternate data stream called *sr_.json*
(on windows on NTFS.) This can save re-reading the file to re-calculate the checksum.
Some use cases may not want files to have Alternate Data Streams or extended 
attributes to be used.

Delivery Completion (inflight)
------------------------------

Failing to properly set file completion protocols is a common source of intermittent and
difficult-to-diagnose file transfer issues. For reliable file transfers, it is 
critical that both the sender and receiver agree on how to represent a file that isn't complete.
The *inflight* option (meaning a file is *in flight* between the sender and the receiver) supports
many protocols appropriate for different situations:

+--------------------------------------------------------------------------------------------+
|                                                                                            |
|               Delivery Completion Protocols (in Order of Preference)                       |
|                                                                                            |
+-------------+---------------------------------------+--------------------------------------+
| Method      | Description                           | Application                          |
+=============+=======================================+======================================+
|             |File sent with right name.             |Sending to Sarracenia, and            |
|   NONE      |Send `sr3_post(7) <sr3_post.7.rst>`_   |post only when file is complete       |
|             |by AMQP after file is complete.        |                                      |
|             |                                       |(Best when available)                 |
|             | - fewer round trips (no renames)      | - Default on sr_sarra.               |
|             | - least overhead / highest speed      | - Default on sr_subscribe and sender |
|             |                                       |   when post_broker is set.           |
+-------------+---------------------------------------+--------------------------------------+
|             |Files transferred with a *.tmp* suffix.|sending to most other systems         |
| .tmp        |When complete, renamed without suffix. |(.tmp support built-in)               |
| (Suffix)    |Actual suffix is settable.             |Use to send to Sundew                 |
|             |                                       |                                      |
|             | - requires extra round trips for      |(usually a good choice)               |
|             |   rename (a little slower)            | - default when no post broker set    |
+-------------+---------------------------------------+--------------------------------------+
|             |Files transferred to a subdir.         |sending to some other systems         |
| tmp/        |When complete, renamed to parent dir.  |                                      |
| (subdir)    |Actual subdir is settable.             |                                      |
|             |                                       |                                      |
|             |same performance as Suffix method.     |                                      |
+-------------+---------------------------------------+--------------------------------------+
|             |Use Linux convention to *hide* files.  |Sending to systems that               |
| .           |Prefix names with '.'                  |do not support suffix.                |
| (Prefix)    |that need that. (compatibility)        |                                      |
|             |same performance as Suffix method.     |                                      |
+-------------+---------------------------------------+--------------------------------------+
|             |Minimum age (modification time)        |Last choice                           |
|  number     |of the file before it is considered    |guaranteed delay added                |
|  (mtime)    |complete.                              |                                      |
|             |                                       |Receiving from uncooperative          |
|             |Adds delay in every transfer.          |sources.                              |
|             |Vulnerable to network failures.        |                                      |
|             |Vulnerable to clock skew.              |(ok choice with PDS)                  |
+-------------+---------------------------------------+--------------------------------------+

By default ( when no *inflight* option is given ), if the post_broker is set, then a value of NONE
is used because it is assumed that it is delivering to another broker. If no post_broker
is set, the value of '.tmp' is assumed as the best option.

NOTES:
 
  On versions of sr_sender prior to 2.18, the default was NONE, but was documented as '.tmp'
  To ensure compatibility with later versions, it is likely better to explicitly write
  the *inflight* setting.
 
  *inflight* was renamed from the old *lock* option in January 2017. For compatibility with
  older versions, can use *lock*, but name is deprecated.
  
  The old *PDS* software (which predates MetPX Sundew) only supports FTP. The completion protocol 
  used by *PDS* was to send the file with permission 000 initially, and then chmod it to a 
  readable file. This cannot be implemented with SFTP protocol, and is not supported at all
  by Sarracenia.


Frequent Configuration Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Setting NONE when sending to Sundew.**

   The proper setting here is '.tmp'.  Without it, almost all files will get through correctly,
   but incomplete files will occasionally picked up by Sundew.  

**Using mtime method to receive from Sundew or Sarracenia:**

   Using mtime is last resort. This approach injects delay and should only be used when one 
   has no influence to have the other end of the transfer use a better method. 
 
   mtime is vulnerable to systems whose clocks differ (causing incomplete files to be picked up.)

   mtime is vulnerable to slow transfers, where incomplete files can be picked up because of a 
   networking issue interrupting or delaying transfers. 

   Sources may not to include mtime data in their posts ( *preserve_time* option on post.)


**Setting NONE when delivering to non-Sarracenia destination.**

   NONE is to be used when there is some other means to figure out if a file is delivered.
   For example, when sending to another pump, the sender will post the announcement to 
   the destination after the file is complete, so there is no danger of it being 
   picked up early.

   When used inappropriately, there will occasionally be incomplete files delivered.


On Windows
==========

The python tools are ubiquitously installed with the operating system on Linux,
and installation methods are somewhat more consistent there.  On Windows,
there is a wide variety of methods of installation, stemming from the
variety of python distributions available. The various methods conflict, to the
extent that using the .exe files, as one would expect using winpython, does not
work at all when installed using Anaconda. 

A setting is provided *windows_run* to allow selection. the choices are:

* exe - run sr_subscribe.exe as installed by pip (what one would expect to start)

* pyw - run the pythonw.exe executable with sr_subscribe.py (or sr_subscribe-script.py) 
  as the argument. (sometimes needed to have the component continue to run
  after calling process is terminated.

* py - run the python.exe executable with sr_subscribe.py (or sr_subscribe-script.py) 
  as the argument. (sometimes also works.)



PERIODIC PROCESSING
===================

Most processing occurs on receipt of a message, but there is some periodic maintenance
work that happens every *heartbeat* (default is 5 minutes.)  Evey heartbeat, all of the
configured *on_heartbeat* plugins are run. By default there are three present:

 * hb_log - prints "heartbeat" in the log.
 * hb_cache - ages out old entries in the cache, to minimize its size.
 * hb_memory - checks the process memory usage, and restart if too big.
 * hb_pulse - confirms that connectivity with brokers is still good. Restores if needed.
 * hb_sanity - runs sanity check.

The log will contain messages from all three plugins every heartbeat interval, and
if additional periodic processing is needed, the user can configure addition
plugins to run with the *on_heartbeat* option. 

sanity_log_dead <interval> (default: 1.5*heartbeat)
---------------------------------------------------

The **sanity_log_dead** option sets how long to consider too long before restarting
a component.

suppress_duplicates <off|on|999> (default: off)
-----------------------------------------------

The cleanup of expired elements in the duplicate suppression store happens at
each heartbeat.


ERROR RECOVERY
==============

The tools are meant to work well unattended, and so when transient errors occur, they do
their best to recover elegantly.  There are timeouts on all operations, and when a failure
is detected, the problem is noted for retry.  Errors can happen at many times:
 
 * Establishing a connection to the broker.
 * losing a connection to the broker
 * establishing a connection to the file server for a file (for download or upload.)
 * losing a connection to the server.
 * during data transfer.
 
Initially, the programs try to download (or send) a file a fixed number (*attempts*, default: 3) times.
If all three attempts to process the file are unsuccessful, then the file is placed in an instance's
retry file. The program then continues processing of new items. When there are no new items to
process, the program looks for a file to process in the retry queue. It then checks if the file
is so old that it is beyond the *retry_expire* (default: 2 days). If the file is not expired, then
it triggers a new round of attempts at processing the file. If the attempts fail, it goes back
on the retry queue.

This algorithm ensures that programs do not get stuck on a single bad product that prevents
the rest of the queue from being processed, and allows for reasonable, gradual recovery of 
service, allowing fresh data to flow preferentially, and sending old data opportunistically
when there are gaps.

While fast processing of good data is very desirable, it is important to slow down when errors
start occurring. Often errors are load related, and retrying quickly will just make it worse.
Sarracenia uses exponential back-off in many points to avoid overloading a server when there
are errors. The back-off can accumulate to the point where retries could be separated by a minute
or two. Once the server begins responding normally again, the programs will return to normal
processing speed.


EXAMPLES
========

Here is a short complete example configuration file:: 

  broker amqps://dd.weather.gc.ca/

  subtopic model_gem_global.25km.grib2.#
  accept .*

This above file will connect to the dd.weather.gc.ca broker, connecting as
anonymous with password anonymous (defaults) to obtain announcements about
files in the http://dd.weather.gc.ca/model_gem_global/25km/grib2 directory.
All files which arrive in that directory or below it will be downloaded 
into the current directory (or just printed to standard output if -n option 
was specified.) 

A variety of example configuration files are available here:

 `https://github.com/MetPX/sarracenia/tree/master/sarra/examples <https://github.com/MetPX/sarracenia/tree/master/sarra/examples>`_


NAMING EXCHANGES AND QUEUES
===========================

While in most common cases, a good value is generated by the application, in some cases
there may be a need to override those choices with an explicit user specification.
To do that, one needs to be aware of the rules for naming queues:

1. queue names start with q\_
2. this is followed by <amqpUserName> (the owner/user of the queue's broker username)
3. followed by a second underscore ( _ )
4. followed by a string of the user's choice.

The total length of the queue name is limited to 255 bytes of UTF-8 characters.

The same applies for exchanges.  The rules for those are:

1. Exchange names start with x
2. Exchanges that end in *public* are accessible (for reading) by any authenticated user.
3. Users are permitted to create exchanges with the pattern:  xs_<amqpUserName>_<whatever> such exchanges can be written to only by that user. 
4. The system (sr_audit or administrators) create the xr_<amqpUserName> exchange as a place to send reports for a given user. It is only readable by that user.
5. Administrative users (admin or feeder roles) can post or subscribe anywhere.

For example, xpublic does not have xs\_ and a username pattern, so it can only be posted to by admin or feeder users.
Since it ends in public, any user can bind to it to subscribe to messages posted.
Users can create exchanges such as xs_<amqpUserName>_public which can be written to by that user (by rule 3), 
and read by others (by rule 2.) A description of the conventional flow of messages through exchanges on a pump.  
Subscribers usually bind to the xpublic exchange to get the main data feed. This is the default in sr_subscribe.

Another example, a user named Alice will have at least two exchanges:

  - xs_Alice the exhange where Alice posts her file notifications and report messages (via many tools).
  - xr_Alice the exchange where Alice reads her report messages from (via sr_report).
  - Alice can create a new exchange by just posting to it (with sr3_post or sr_cpost) if it meets the naming rules.

Usually an sr_sarra run by a pump administrator will read from an exchange such as xs_Alice_mydata, 
retrieve the data corresponding to Alice´s *post* message, and make it available on the pump, 
by re-announcing it on the xpublic exchange.




QUEUES and MULTIPLE STREAMS
===========================

When executed,  **sr_subscribe**  chooses a queue name, which it writes
to a file named after the configuration file given as an argument to **sr_subscribe**
with a .queue suffix ( ."configfile".queue). 
If sr_subscribe is stopped, the posted messages continue to accumulate on the 
broker in the queue.  When the program is restarted, it uses the queuename 
stored in that file to connect to the same queue, and not lose any messages.

File downloads can be parallelized by running multiple sr_subscribes using
the same queue.  The processes will share the queue and each download 
part of what has been selected.  Simply launch multiple instances
of sr_subscribe in the same user/directory using the same configuration file. 

You can also run several sr_subscribe with different configuration files to
have multiple download streams delivering into the the same directory,
and that download stream can be multi-streamed as well.

.. Note::

  While the brokers keep the queues available for some time, Queues take resources on 
  brokers, and are cleaned up from time to time.  A queue which is not accessed for 
  a long (implementation dependent) period will be destroyed.  A queue which is not
  accessed and has too many (implementation defined) files queued will be destroyed.
  Processes which die should be restarted within a reasonable period of time to avoid
  loss of notifications.


report_back and report_exchange
===============================

For each download, by default, an amqp report message is sent back to the broker.
This is done with option :

- **report_back <boolean>        (default: True)** 
- **report_exchange <report_exchangename> (default: xreport|xs_*username* )**

When a report is generated, it is sent to the configured *report_exchange*. Administrative
components post directly to *xreport*, whereas user components post to their own 
exchanges (xs_*username*). The report daemons then copy the messages to *xreport* after validation.

These reports are used for delivery tuning and for data sources to generate statistical information.
Set this option to **False**, to prevent generation of reports.


INSTANCES
=========

Sometimes one instance of a component and configuration is not enough to process & send all available notifications.

**instances      <integer>     (default:1)**

The instance option allows launching several instances of a component and configuration.
When running sr_sender for example, a number of runtime files are created.
In the ~/.cache/sarra/sender/configName directory::

  A .sr_sender_configname.state         is created, containing the number instances.
  A .sr_sender_configname_$instance.pid is created, containing the PID  of $instance process.

In directory ~/.cache/sarra/log::

  A .sr_sender_configname_$instance.log  is created as a log of $instance process.

.. NOTE::
  known bug in the management interface `sr <sr.8.rst>_`  means that instance should
  always be in the .conf file (not a .inc) and should always be an number 
  (not a substituted variable or other more complex value.

.. note::  
  FIXME: indicate Windows location also... dot files on Windows?


.. Note::

  While the brokers keep the queues available for some time, Queues take resources on 
  brokers, and are cleaned up from time to time.  A queue which is not
  accessed and has too many (implementation defined) files queued will be destroyed.
  Processes which die should be restarted within a reasonable period of time to avoid
  loss of notifications.  A queue which is not accessed for a long (implementation dependent)
  period will be destroyed. 

.. Note::
   FIXME  The last sentence is not really right...sr_audit does track the queues' age. 
          sr_audit acts when a queue gets to the max_queue_size and not running.
          

vip - ACTIVE/PASSIVE OPTIONS
----------------------------

**sr_subscribe** can be used on a single server node, or multiple nodes
could share responsibility. Some other, separately configured, high availability
software presents a **vip** (virtual ip) on the active server. Should
the server go down, the **vip** is moved on another server.
Both servers would run **sr_subscribe**. It is for that reason that the
following options were implemented:

 - **vip          <string>          (None)**

When you run only one **sr_subscribe** on one server, these options are not set,
and sr_subscribe will run in 'standalone mode'.

In the case of clustered brokers, you would set the options for the
moving vip.

**vip 153.14.126.3**

When **sr_subscribe** does not find the vip, it sleeps for 5 seconds and retries.
If it does, it consumes and processes a message and than rechecks for the vip.


POSTING OPTIONS
===============

When advertising files downloaded for downstream consumers, one must set 
the rabbitmq configuration for an output broker.

The post_broker option sets all the credential information to connect to the 
output **AMQP** broker.

**post_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

Once connected to the source AMQP broker, the program builds notifications after
the download of a file has occurred. To build the notification and send it to
the next hop broker, the user sets these options :

 - **[--blocksize <value>]            (default: 0 (auto))**
 - **[--outlet <post|json|url>]       (default: post)**
 - **[-pbd|--post_baseDir <path>]    (optional)**
 - **[-ptp|--post_topicPrefix <pfx>] (default: 'v03')**
 - **post_exchange     <name>         (default: xpublic)**
 - **post_exchange_split   <number>   (default: 0)**
 - **post_baseUrl          <url>     (MANDATORY)**
 - **on_post           <script>       (default: None)**


[--blocksize <value>] (default: 0 (auto))
-----------------------------------------

This **blocksize** option controls the partitioning strategy used to post files.
The value should be one of::

   0 - autocompute an appropriate partitioning strategy (default)
   1 - always send entire files in a single part.
   <blocksize> - used a fixed partition size (example size: 1M )

Files can be announced as multiple parts.  Each part has a separate checksum.
The parts and their checksums are stored in the cache. Partitions can traverse
the network separately, and in parallel.  When files change, transfers are
optimized by only sending parts which have changed.

The *outlet* option allows the final output to be other than a post.  
See `sr_cpump(1) <sr_cpump.1.rst>`_ for details.

[-pbd|--post_baseDir <path>] (optional)
----------------------------------------

The *post_baseDir* option supplies the directory path that, when combined (or found) 
in the given *path*, gives the local absolute path to the data file to be posted.
The *post_baseDir* part of the path will be removed from the posted announcement.
For sftp urls it can be appropriate to specify a path relative to a user account.
Example of that usage would be:  -pbd ~user  -url sftp:user@host
For file: url's, baseDir is usually not appropriate.  To post an absolute path,
omit the -pbd setting, and just specify the complete path as an argument.

post_baseUrl <url> (MANDATORY)
------------------------------

The **post_baseUrl** option sets how to get the file... it defines the protocol,
host, port, and optionally, the user. It is best practice to not include 
passwords in urls.

post_exchange <name> (default: xpublic)
---------------------------------------

The **post_exchange** option set under which exchange the new notification
will be posted.  In most cases it is 'xpublic'.

Whenever a publish happens for a product, a user can set to trigger a script.
The option **on_post** would be used to do such a setup.

post_exchange_split   <number>   (default: 0)
---------------------------------------------

The **post_exchange_split** option appends a two digit suffix resulting from 
hashing the last character of the checksum to the post_exchange name,
in order to divide the output amongst a number of exchanges.  This is currently used
in high traffic pumps to allow multiple instances of sr_winnow, which cannot be
instanced in the normal way.  Example::

    post_exchange_split 5
    post_exchange xwinnow

will result in posting messages to five exchanges named: xwinnow00, xwinnow01,
xwinnow02, xwinnow03 and xwinnow04, where each exchange will receive only one fifth
of the total flow.

Remote Configurations
---------------------

One can specify URI's as configuration files, rather than local files. Example:

  - **--config http://dd.weather.gc.ca/alerts/doc/cap.conf**

On startup, sr_subscribe checks if the local file cap.conf exists in the 
local configuration directory.  If it does, then the file will be read to find
a line like so:

  - **--remote_config_url http://dd.weather.gc.ca/alerts/doc/cap.conf**

In which case, it will check the remote URL and compare the modification time
of the remote file against the local one. The remote file is not newer, or cannot
be reached, then the component will continue with the local file.

If either the remote file is newer, or there is no local file, it will be downloaded, 
and the remote_config_url line will be prepended to it, so that it will continue 
to self-update in future.

Extensions
==========

One can override or add functionality with python scripting.

Sarracenia comes with a variety of example plugins, and uses some to implement base functionality,
such as logging (implemented by default use of msg_log, file_log, post_log plugins)::
  
$ sr3 list fcb
  Provided callback classes: ( /home/peter/Sarracenia/sr3/sarracenia ) 
  flowcb/filter/deleteflowfiles.py flowcb/filter/fdelay.py          flowcb/filter/pclean_f90.py      flowcb/filter/pclean_f92.py
  flowcb/gather/file.py            flowcb/gather/message.py         flowcb/line_log.py               flowcb/line_mode.py 
  flowcb/log.py                    flowcb/nodupe.py                 flowcb/pclean.py                 flowcb/post/message.py
  flowcb/retry.py                  flowcb/sample.py                 flowcb/script.py                 flowcb/v2wrapper.py
  flowcb/work/rxpipe.py            
$ 

Users can place their own scripts in the script sub-directory of their config directory 
tree ( on Linux, the ~/.config/sarra/plugins).  

flow_callback and flow_callback_prepend <class>
-----------------------------------------------

The flow_callback directive takes a class to load can scan for entry points as an argument::

    flow_callback sarracenia.flowcb.log.Log
   
With this directive in a configuration file, the Log class found in installed package will be used.
That module logs messages *after_accept* (after messages have passed through the accept/reject masks.)
and the *after_work* (after the file has been downloaded or sent). Here is the source code 
for that callback class::

  import json
  import logging
  from sarracenia.flowcb import FlowCB
  from sarracenia.flowcb.gather import msg_dumps

  logger = logging.getLogger(__name__)


  class Log(FlowCB):
    def __init__(self, options):

        # FIXME: should a logging module have a logLevel setting?
        #        just put in a cookie cutter for now...
        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, options.logLevel.upper()))
        else:
            logger.setLevel(logging.INFO)

    def after_accept(self, worklist):
        for msg in worklist.incoming:
            logger.info("accepted: %s " % msg_dumps(msg) )

    def after_work(self, worklist):
        for msg in worklist.ok:
            logger.info("worked successfully: %s " % msg_dumps(msg) )

If you have multiple callbacks configured, they will be called in the same order they are 
configuration file. components in sr3 are often differentiated by the callbacks configured.
For example, a *watch* is a flow with sarracenia.flowcb.gather.file.File class that
is used to scan directories. A Common need when a data source is not easily accessed
with python scripts is to use the script callback::

   flow_callback_prepend sarracenia.flowcb.script.Script

   script_gather get_weird_data.sh

Using the *_prepend* variant of the *flow_callback* option, will have the Script callback
class's entry point, before the File callback... So A script will be executed, and then
the directory will be checked for new files.  Here is part of the Script callback class::
    
    import logging
    from sarracenia.flowcb import FlowCB
    from sarracenia.flowcb.gather import msg_dumps
    import subprocess
    
    logger = logging.getLogger(__name__)
    
    
    class Script(FlowCB):
    
       .
       .
       .
    
        def run_script( self, script ):
            try: 
                subprocess.run( self.o.script_gather, check=True )
            except Exception as err:
                logging.error("subprocess.run failed err={}".format(err))
                logging.debug("Exception details:", exc_info=True)
    
    
        def gather(self ):
            if hasattr( self.o, 'script_gather') and self.o.script_gather is not None :
                self.run_script( self.o.script_gather )
            return []
    
     
Integrity
---------

One can use the *import* directive to add new checksum algorithms by sub-classing
sarracenia.integrity.Integrity.

Transfer 
--------

One can add support for additional methods of downloading data by sub-classing
sarracenia.transfer.Transfer.

Transfer protocol scripts should be declared using the **import** option.
Aside the targetted built-in function(s), a module **registered_as** that defines
a list of protocols that these functions provide.  Example :

def registered_as(self) :
       return ['ftp','ftps']


See the `Programming Guide <../Explanation/SarraPluginDev.rst>`_ for more information on Extension development.


Queue Save/Restore
==================


Sender Destination Unavailable
------------------------------

If the server to which the files are being sent is going to be unavailable for
a prolonged period, and there is a large number of messages to send to them, then
the queue will build up on the broker. As the performance of the entire broker
is affected by large queues, one needs to minimize such queues.

The *-save* and *-restore* options are used get the messages away from the broker
when too large a queue will certainly build up.
The *-save* option copies the messages to a (per instance) disk file (in the same directory
that stores state and pid files), as json encoded strings, one per line.
When a queue is building up::

   sr_sender stop <config> 
   sr_sender -save start <config> 

And run the sender in *save* mode (which continually writes incoming messages to disk)
in the log, a line for each message written to disk::

  2017-03-03 12:14:51,386 [INFO] sr_sender saving 2 message topic: v03.home.peter.sarra_devdocroot.sub.SASP34_LEMM_031630__LEDA_60215

Continue in this mode until the absent server is again available.  At that point::

   sr_sender stop <config> 
   sr_sender -restore start <config> 

While restoring from the disk file, messages like the following will appear in the log::

  2017-03-03 12:15:02,969 [INFO] sr_sender restoring message 29 of 34: topic: v03.home.peter.sarra_devdocroot.sub.ON_02GD022_daily_hydrometric.csv


After the last one::

  2017-03-03 12:15:03,112 [INFO] sr_sender restore complete deleting save file: /home/peter/.cache/sarra/sender/tsource2send/sr_sender_tsource2send_0000.save 


and the sr_sender will function normally thereafter.



Shovel Save/Restore
-------------------

If a queue builds up on a broker because a subscriber is unable to process
messages, overall broker performance will suffer, so leaving the queue lying around
is a problem. As an administrator, one could keep a configuration like this
around::

  % more ~/tools/save.conf
  broker amqp://tfeed@localhost/
  topicPrefix v03
  exchange xpublic

  post_rate_limit 50
  on_post post_rate_limit
  post_broker amqp://tfeed@localhost/

The configuration relies on the use of an administrator or feeder account.
Note the queue which has messages in it, in this case q_tsub.sr_subscribe.t.99524171.43129428. Invoke the shovel in save mode to consume messages from the queue
and save them to disk::

  % cd ~/tools
  % sr_shovel -save -queue q_tsub.sr_subscribe.t.99524171.43129428 foreground save.conf

  2017-03-18 13:07:27,786 [INFO] sr_shovel start
  2017-03-18 13:07:27,786 [INFO] sr_sarra run
  2017-03-18 13:07:27,786 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2017-03-18 13:07:27,788 [WARNING] non standard queue name q_tsub.sr_subscribe.t.99524171.43129428
  2017-03-18 13:07:27,788 [INFO] Binding queue q_tsub.sr_subscribe.t.99524171.43129428 with key v03.# from exchange xpublic on broker amqp://tfeed@localhost/
  2017-03-18 13:07:27,790 [INFO] report_back to tfeed@localhost, exchange: xreport
  2017-03-18 13:07:27,792 [INFO] sr_shovel saving to /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save for future restore
  2017-03-18 13:07:27,794 [INFO] sr_shovel saving 1 message topic: v03.observations.swob-ml.20170318.CPSL.2017-03-18-1600-CPSL-AUTO-swob.xml
  2017-03-18 13:07:27,795 [INFO] sr_shovel saving 2 message topic: v03.hydrometric.doc.hydrometric_StationList.csv
          .
          .
          .
  2017-03-18 13:07:27,901 [INFO] sr_shovel saving 188 message topic: v03.hydrometric.csv.ON.hourly.ON_hourly_hydrometric.csv
  2017-03-18 13:07:27,902 [INFO] sr_shovel saving 189 message topic: v03.hydrometric.csv.BC.hourly.BC_hourly_hydrometric.csv

  ^C2017-03-18 13:11:27,261 [INFO] signal stop
  2017-03-18 13:11:27,261 [INFO] sr_shovel stop


  % wc -l /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save
  189 /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save
  % 

The messages are written to a file in the caching directory for future use, with
the name of the file being based on the configuration name used. The file is in
json format, one message per line (lines are very long) and so filtering with other tools
is possible to modify the list of saved messages. Note that a single save file per
configuration is automatically set, so to save multiple queues, one would need one configurations
file per queue to be saved.  Once the subscriber is back in service, one can return the messages
saved to a file into the same queue::

  % sr_shovel -restore_to_queue q_tsub.sr_subscribe.t.99524171.43129428 foreground save.conf

  2017-03-18 13:15:33,610 [INFO] sr_shovel start
  2017-03-18 13:15:33,611 [INFO] sr_sarra run
  2017-03-18 13:15:33,611 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2017-03-18 13:15:33,613 [INFO] Binding queue q_tfeed.sr_shovel.save with key v03.# from exchange xpublic on broker amqp://tfeed@localhost/
  2017-03-18 13:15:33,615 [INFO] report_back to tfeed@localhost, exchange: xreport
  2017-03-18 13:15:33,618 [INFO] sr_shovel restoring 189 messages from save /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save 
  2017-03-18 13:15:33,620 [INFO] sr_shovel restoring message 1 of 189: topic: v03.observations.swob-ml.20170318.CPSL.2017-03-18-1600-CPSL-AUTO-swob.xml
  2017-03-18 13:15:33,620 [INFO] msg_log received: 20170318165818.878 http://localhost:8000/ observations/swob-ml/20170318/CPSL/2017-03-18-1600-CPSL-AUTO-swob.xml topic=v03.observations.swob-ml.20170318.CPSL.2017-03-18-1600-CPSL-AUTO-swob.xml lag=1034.74 sundew_extension=DMS:WXO_RENAMED_SWOB:MSC:XML::20170318165818 source=metpx mtime=20170318165818.878 sum=d,66f7249bd5cd68b89a5ad480f4ea1196 to_clusters=DD,DDI.CMC,DDI.EDM,DDI.CMC,CMC,SCIENCE,EDM parts=1,5354,1,0,0 toolong=1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ß from_cluster=DD atime=20170318165818.878 filename=2017-03-18-1600-CPSL-AUTO-swob.xml 
     .
     .
     .
  2017-03-18 13:15:33,825 [INFO] post_log notice=20170318165832.323 http://localhost:8000/hydrometric/csv/BC/hourly/BC_hourly_hydrometric.csv headers={'sundew_extension': 'BC:HYDRO:CSV:DEV::20170318165829', 'toolong': '1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ß', 'filename': 'BC_hourly_hydrometric.csv', 'to_clusters': 'DD,DDI.CMC,DDI.EDM,DDI.CMC,CMC,SCIENCE,EDM', 'sum': 'd,a22b2df5e316646031008654b29c4ac3', 'parts': '1,12270407,1,0,0', 'source': 'metpx', 'from_cluster': 'DD', 'atime': '20170318165832.323', 'mtime': '20170318165832.323'}
  2017-03-18 13:15:33,826 [INFO] sr_shovel restore complete deleting save file: /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save 


  2017-03-18 13:19:26,991 [INFO] signal stop
  2017-03-18 13:19:26,991 [INFO] sr_shovel stop
  % 

All the messages saved are returned to the named *return_to_queue*. Note that the use of the *post_rate_limit*
plugin prevents the queue from being flooded with hundreds of messages per second. The rate limit to use will need
to be tuned in practice.

By default the file name for the save file is chosen to be in ~/.cache/sarra/shovel/<config>_<instance>.save.
To choose a different destination, *save_file* option is available::

  sr_shovel -save_file `pwd`/here -restore_to_queue q_tsub.sr_subscribe.t.99524171.43129428 ./save.conf foreground

will create the save files in the current directory named here_000x.save where x is the instance number (0 for foreground.)




ROLES - feeder/admin/declare
============================

*of interest only to administrators*

Administrative options are set using::

  sr_subscribe edit admin

The *feeder* option specifies the account used by default system transfers for components such as
sr_shovel, sr_sarra and sr_sender (when posting). 

- **feeder    amqp{s}://<user>:<pw>@<post_brokerhost>[:port]/<vhost>**

- **admin   <name>        (default: None)**

The admin user is used to do maintenance operations on the pump such as defining
the other users. Most users are defined using the *declare* option. The feeder can also be declared in that
way.

- **declare <role> <name>   (no defaults)**

subscriber
----------

  A subscriber is user that can only subscribe to data and return report messages. Subscribers are
  not permitted to inject data.  Each subscriber has an xs_<user> named exchange on the pump,
  where if a user is named *Acme*, the corresponding exchange will be *xs_Acme*.  This exchange
  is where an sr_subscribe process will send its report messages.

  By convention/default, the *anonymous* user is created on all pumps to permit subscription without
  a specific account.

source
------

  A user permitted to subscribe or originate data.  A source does not necessarily represent
  one person or type of data, but rather an organization responsible for the data produced.
  So if an organization gathers and makes available ten kinds of data with a single contact
  email or phone number for questions about the data and its availability, then all of
  those collection activities might use a single 'source' account.

  Each source gets a xs_<user> exchange for injection of data posts, and, similar to a subscriber
  to send report messages about processing and receipt of data. Source may also have an xl_<user>
  exchange where, as per report routing configurations, report messages of consumers will be sent.

feeder
------
  
  A user permitted to write to any exchange. Sort of an administrative flow user, meant to pump
  messages when no ordinary source or subscriber is appropriate to do so.  Is to be used in
  preference to administrator accounts to run flows.


User credentials are placed in the credentials files, and *sr_audit* will update
the broker to accept what is specified in that file, as long as the admin password is
already correct.


CONFIGURATION FILES
===================

While one can manage configuration files using the *add*, *remove*,
*list*, *edit*, *disable*, and *enable* actions, one can also do all
of the same activities manually by manipulating files in the settings
directory.  The configuration files for an sr_subscribe configuration 
called *myflow* would be here:

 - linux: ~/.config/sarra/subscribe/myflow.conf (as per: `XDG Open Directory Specication <https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.rst>`_ ) 


 - Windows: %AppDir%/science.gc.ca/sarra/myflow.conf , this might be:
   C:\Users\peter\AppData\Local\science.gc.ca\sarra\myflow.conf

 - MAC: FIXME.

The top of the tree has  *~/.config/sarra/default.conf* which contains settings that
are read as defaults for any component on start up.  In the same directory, *~/.config/sarra/credentials.conf* contains credentials (passwords) to be used by sarracenia ( `CREDENTIALS`_ for details. )

One can also set the XDG_CONFIG_HOME environment variable to override default placement, or 
individual configuration files can be placed in any directory and invoked with the 
complete path.   When components are invoked, the provided file is interpreted as a 
file path (with a .conf suffix assumed.)  If it is not found as a file path, then the 
component will look in the component's config directory ( **config_dir** / **component** )
for a matching .conf file.

If it is still not found, it will look for it in the site config dir
(linux: /usr/share/default/sarra/**component**).

Finally, if the user has set option **remote_config** to True and if he has
configured web sites where configurations can be found (option **remote_config_url**),
The program will try to download the named file from each site until it finds one.
If successful, the file is downloaded to **config_dir/Downloads** and interpreted
by the program from there.  There is a similar process for all *plugins* that can
be interpreted and executed within sarracenia components.  Components will first
look in the *plugins* directory in the users config tree, then in the site
directory, then in the sarracenia package itself, and finally it will look remotely.


SEE ALSO
========


**User Commands:**

`sr3_post(1) <sr3_post.1.rst>`_ - post announcemensts of specific files.

`sr_log2save(8) <sr3_log2save.8.rst>`_ - Convert logfile lines to .save Format for reload/resend.

.. TODO: Link above refers to non-existant file?

**Formats:**

`sr3_post(7) <sr3_post.7.rst>`_ - The v03 format of announcement messages.

`sr3_postv2(7) <sr3_postv2.7.rst>`_ - The v02 format of announcement messages.

**Home Page:**

`https://github.com/MetPX/ <https://github.com/MetPX>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.

BUGS
====

sr3 looks in the configuration files for the *instance* option, and expects a number there.
If *instances* comes from an include file, or is a variable value (not a raw number) sr
will not use it properly.


DEVELOPER ONLY OPTIONS
======================

The SR_DEV_APPNAME environment variable can be set so that the application configuration and state directories
are created under a different name.  This is used in development to be able to have many configurations
active at once.  It enables more testing than always working with the developer´s *real* configuration.

Example:  export SR_DEV_APPNAME=sr-hoho... when you start up a component on a linux system, it will 
look in ~/.config/sr-hoho/ for configuration files, and write state files in the ~/.cache/sr-hoho
directory.


SUNDEW COMPATIBILITY OPTIONS
============================

For compatibility with Sundew, there are some additional delivery options which can be specified.

destfn_script <script> (default:None)
-------------------------------------

This option defines a script to be run when everything is ready
for the delivery of the product.  The script receives the sr_sender class
instance.  The script takes the parent as an argument, and for example, any
modification to  **parent.msg.new_file**  will change the name of the file written locally.

filename <keyword> (default:WHATFN)
---------------------------------------

From **metpx-sundew** the support of this option give all sorts of possibilities
for setting the remote filename. Some **keywords** are based on the fact that
**metpx-sundew** filenames are five (to six) fields strings separated by for colons.

The default value on Sundew is NONESENDER, but in the interest of discouraging use
of colon separation in files, the default in Sarracenia is WHATFN

The possible keywords are :


**WHATFN**
 - the first part of the Sundew filename (string before first :)

**HEADFN**
 - HEADER part of the sundew filename

**SENDER**
 - the Sundew filename may end with a string SENDER=<string> in this case the <string> will be the remote filename

**NONE**
 - deliver with the complete Sundew filename (without :SENDER=...)

**NONESENDER**
 - deliver with the complete Sundew filename (with :SENDER=...)

**TIME**
 - time stamp appended to filename. Example of use: WHATFN:TIME

**DESTFN=str**
 - direct filename declaration str

**SATNET=1,2,3,A**
 - cmc internal satnet application parameters

**DESTFNSCRIPT=script.py**
 - invoke a script (same as destfn_script) to generate the name of the file to write


**accept <regexp pattern> [<keyword>]**

keyword can be added to the **accept** option. The keyword is any one of the **filename**
options.  A message that matched against the accept regexp pattern, will have its remote_file
plied this keyword option.  This keyword has priority over the preceeding **filename** one.

The **regexp pattern** can be use to set directory parts if part of the message is put
to parenthesis. **sr_sender** can use these parts to build the directory name. The
rst enclosed parenthesis strings will replace keyword **${0}** in the directory name...
the second **${1}** etc.

Example of use::


      filename NONE

      directory /this/first/target/directory

      accept .*file.*type1.*

      directory /this/target/directory

      accept .*file.*type2.*

      accept .*file.*type3.*  DESTFN=file_of_type3

      directory /this/${0}/pattern/${1}/directory

      accept .*(2016....).*(RAW.*GRIB).*


A selected message by the first accept would be delivered unchanged to the first directory.

A selected message by the second accept would be delivered unchanged to the second directory.

A selected message by the third accept would be renamed "file_of_type3" in the second directory.

A selected message by the forth accept would be delivered unchanged to a directory.

It's named  */this/20160123/pattern/RAW_MERGER_GRIB/directory* if the message would have a notice like:

**20150813161959.854 http://this.pump.com/ relative/path/to/20160123_product_RAW_MERGER_GRIB_from_CMC**


Field Replacements
------------------

In MetPX Sundew, there is a much more strict file naming standard, specialised for use with 
World Meteorological Organization (WMO) data.   Note that the file naming convention predates, and 
bears no relation to the WMO file naming convention currently approved, but is strictly an internal 
format.   The files are separated into six fields by colon characters.  The first field, DESTFN, 
gives the WMO (386 style) Abbreviated Header Line (AHL) with underscores replacing blanks::

   TTAAii CCCC YYGGGg BBB ...  

(see WMO manuals for details) followed by numbers to render the product unique (as in practice, 
though not in theory, there are a large number of products which have the same identifiers).
The meanings of the fifth field is a priority, and the last field is a date/time stamp.  
The other fields vary in meaning depending on context.  A sample file name::

   SACN43_CWAO_012000_AAA_41613:ncp1:CWAO:SA:3.A.I.E:3:20050201200339

If a file is sent to sarracenia and it is named according to the Sundew conventions, then the 
following substitution fields are available::

  ${T1}    replace by bulletin's T1
  ${T2}    replace by bulletin's T2
  ${A1}    replace by bulletin's A1
  ${A2}    replace by bulletin's A2
  ${ii}    replace by bulletin's ii
  ${CCCC}  replace by bulletin's CCCC
  ${YY}    replace by bulletin's YY   (obs. day)
  ${GG}    replace by bulletin's GG   (obs. hour)
  ${Gg}    replace by bulletin's Gg   (obs. minute)
  ${BBB}   replace by bulletin's bbb
  ${RYYYY} replace by reception year
  ${RMM}   replace by reception month
  ${RDD}   replace by reception day
  ${RHH}   replace by reception hour
  ${RMN}   replace by reception minutes
  ${RSS}   replace by reception second

The 'R' fields come from the sixth field, and the others come from the first one.
When data is injected into sarracenia from Sundew, the *sundew_extension* message header
will provide the source for these substitions even if the fields have been removed
from the delivered file names.


DEPRECATED SETTINGS
-------------------

These settings pertain to previous versions of the client, and have been superceded.

- **lock      <locktext>         (renamed to inflight)** 


HISTORY
=======

Sarracenia is part of the MetPX (Meteorological Product Exchanger.) project.
The initial prototypes leveraged MetPX Sundew, Sarracenia's ancestor. Sundew
plugins were developed to create announcements for files delivered by Sundew,
and Dd_subscribe was initially developed as a download client for **dd.weather.gc.ca**, an 
Environment Canada website where a wide variety of meteorological products are made 
available to the public. It is from the name of this site that the sarracenia 
suite takes the dd\_ prefix for its tools. The initial version was deployed in 
2013 on an experimental basis. The following year, support of checksums
was added, and in the fall of 2015, the feeds were updated to v02. 

In 2007, when MetPX was originally open sourced, the staff responsible were part of
Environment Canada. In honour of the Species At Risk Act (SARA), to highlight the plight
of disappearing species which are not furry (the furry ones get all the attention) and
because search engines will find references to names which are more unusual more easily, 
the original MetPX WMO switch was named after a carnivorous plant on the Species At
Risk Registry: The *Thread-leaved Sundew*.  

The organization behind MetPX has since moved to Shared Services Canada, but when
it came time to name a new module, we kept with a theme of carnivorous plants, and 
chose another one indigenous to some parts of Canada: *Sarracenia*, a variety
of insectivorous pitcher plants. We like plants that eat meat!  

Sarracenia was initially called v2, as in the second data pumping architecture
in the MetPX project, (v1 being Sundew.) Over the years a number of limitations
with the existing implementation became clear:  

* The poor support for python developers.
* the odd plugin logic, with very poor error reporting.
* The inability to process groups of messages.
* The inability to add other queueing protocols (limited to rabbitmq/AMQP.)

in 2020, Development began on v03.

V03 is a deep refactor of Sarracenia, bringing support for MQTT in addition to AMQP,
and pluggable organization that makes it easy to add other message queueing protocols.
whereas v02 was an application that one could add snippets of python code to customize
to a certain degree, V03 is a set of python APIs with used to implement a CLI. It
can be used by application programmers in a much more piecemeal/lego-style way.


dd_subscribe Renaming
---------------------

The new project (MetPX-Sarracenia) has many components, is used for more than 
distribution, and more than one website, and causes confusion for sysadmins thinking
it is associated with the dd(1) command (to convert and copy files).  So, we switched
all the components to use the sr\_ prefix.

