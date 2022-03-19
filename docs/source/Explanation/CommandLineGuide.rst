======================
SR3 Command Line Guide
======================


SR3 - Everything
================

**sr3** is a command line tool to manage `Sarracenia <https://github.com/MetPX/sarracenia>`_ 
configurations, individually or in groups. For the current user, it reads on all
of the configuration files, state files, and consults the process table to determine 
the state of all components. It then makes the change requested.

  **sr3** *options* *action* [ *component/configuration* ... ]

sr3 components are used to publish to and download files from websites or file servers 
that provide `sr3_post(7) <../Reference/sr3_post.7.rst>`_ protocol notifications. Such sites 
publish messages for each file as soon as it is available. Clients connect to a
*broker* (often the same as the server itself) and subscribe to the notifications.
The *sr3_post* notifications provide true push notices for web-accessible folders (WAF),
and are far more efficient than either periodic polling of directories, or ATOM/RSS style 
notifications. Sr_subscribe can be configured to post messages after they are downloaded,
to make them available to consumers for further processing or transfers.

**sr3** can also be used for purposes other than downloading, (such as for 
supplying to an external program) specifying the -n (equal to: *download off*) will
suppress the download behaviour and only post the URL on standard output. The standard
output can be piped to other processes in classic UNIX text filter style.  

The components of sarracenia are groups of defaults on the main algorithm,
to reduce the size of individual components.  The components are:

 - `cpump <#CPUMP>`_ - copy messages from one pump another second one (a C implementation of shovel.)
 - `poll <#POLL>`_ - poll a non-sarracenia web or file server to create messages for processing.
 - `post & watch <#POST OR WATCH>`_ - create messages for files for processing.
 - `sarra <#SARRA>`_ - download file from a remote server to the local one, and re-post them for others.
 - `sender <#SENDER>`_ - send files from a local server to a remote one.
 - `shovel <#SHOVEL>`_ - copy messages, only, not files.
 - `watch <#WATCH>`_ - create messages for each new file that arrives in a directory, or at a set path.
 - `winnow <#WINNOW>`_ - copy messages, suppressing duplicates.
 
All of these components accept the same options, with the same effects.
There is also `sr3_cpump(1) <../Reference/sr3_cpump.1.rst>`_ which is a C version that implements a
subset of the options here, but where they are implemented, they have the same effect.

The **sr3** command usually takes two arguments: an action followed by a list
of configuration files. When any component is invoked, an operation and a 
configuration file are specified. If the configuration is omitted, it means to
apply the action to all configurations. The action is one of:

 - foreground: run a single instance in the foreground logging to stderr
 - restart: stop and then start the configuration.
 - sanity: looks for instances which have crashed or gotten stuck and restarts them.
 - start:  start the configuration running
 - status: check if the configuration is running.
 - stop: stop the configuration from running

The remaining actions manage the resources (exchanges, queues) used by the component on
the broker, or manage the configurations.

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


For example:  *sr3 foreground subscribe/dd* runs the subscribe component with
the dd configuration as a single foreground instance.

The **foreground** action is used when building a configuration or for debugging.
The **foreground** instance will run regardless of other instances which are currently
running.  Should instances be running, it shares the same message queue with them.
A user stop the **foreground** instance by simply using <ctrl-c> on linux
or use other means to kill the process.

After a configuration has been refined, *start* to launch the component as a background 
service (daemon or fleet of daemons whose number is controlled by the *instances* option.) 
If multiple configurations and components need to be run together, the entire fleet 
can be similarly controlled using the `sr3(1) <../Reference/sr3.1.html>`_ command. 

To have components run all the time, on Linux one can use `systemd <https://www.freedesktop.org/wiki/Software/systemd/>`_ integration,
as described in the `Admin Guide <../How2Guides/Admin.rst>`_ On Windows, one can configure a service,
as described in the `Windows user manual <../Tutorials/Windows.html>`_

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


ACTIONS
-------

declare|setup
~~~~~~~~~~~~~

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


dump
~~~~

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


foreground
~~~~~~~~~~

run a single instance of a single configuration as an interactive process logging to the current stderr/terminal output.
for debugging.

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

Also *list examples* shows included configuration templates available as starting points with the *add* action::
    
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

show
~~~~

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
    permDefault=0
    permDirDefault=509
    permLog=384
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
    permCopy=True
    timeCopy=True
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
    

start
~~~~~

launch all configured components::

  $ sr3 start
    gathering global state: procs, configs, state files, logs, analysis - Done. 
    starting...Done


stop
~~~~

stop all processes::

  $ sr3 stop
    gathering global state: procs, configs, state files, logs, analysis - Done. 
    stopping........Done
    Waiting 1 sec. to check if 93 processes stopped (try: 0)
    All stopped after try 0
 


status
~~~~~~

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


CONSUMER
========

Most Metpx Sarracenia components loop on reception and consumption of sarracenia 
AMQP messages. Usually, the messages are `sr3_post(7) <sr3_post.7.rst>`_ messages, 
announcing the availability of a file by publishing its URL ( or a part 
of a file ), but there are also report messages which can be processed using the 
same tools. AMQP messages are published to an exchange 
on a broker (AMQP server). The exchange delivers messages to queues. To receive 
messages, one must provide the credentials to connect to the broker. Once 
connected, a consumer needs to create a queue to hold pending messages.
The consumer must then bind the queue to one or more exchanges so that they put 
messages in its queue.

Once the bindings are set, the program can receive messages. When a message is received,
further filtering is possible using regular expressions onto the AMQP messages.
After a message passes this selection process, and other internal validation, the
component can run an **after_accept** plugin script to perform additional message 
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
Common settings for the queue on broker :

- **queue         <name>         (default: q_<brokerUser>.<programName>.<configName>)**
- **expire        <duration>      (default: 5m  == five minutes. RECOMMEND OVERRIDING)**
- **message_ttl   <duration>      (default: None)**
- **prefetch      <N>            (default: 1)**


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
- **acceptUnmatched   <boolean> (default: False)**
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


NAMING QUEUES
-------------

While in most common cases, a good value is generated by the application, in some cases
there may be a need to override those choices with an explicit user specification.
To do that, one needs to be aware of the rules for naming queues:

1. queue names start with q\_
2. this is followed by <amqpUserName> (the owner/user of the queue's broker username)
3. followed by a second underscore ( _ )
4. followed by a string of the user's choice.

The total length of the queue name is limited to 255 bytes of UTF-8 characters.




POSTING
=======

Just as many components consumer a stream of messages, many components
(often the same ones) also product an output stream of messages.  To make files
available to subscribers, a poster publishes the announcements to an AMQP or 
MQTT server, also called a broker. The post_broker option sets all the 
credential information to connect to the output **AMQP** broker.

**post_broker [amqp|mqtt]{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

Once connected to the source AMQP broker, the program builds notifications after
the download of a file has occurred. To build the notification and send it to
the next hop broker, the user sets these options :

* **post_baseDir     <path>    (optional)**
* **post_topicPrefix <pfx> (default: 'v03')**
* **post_exchange    <name>         (default: xpublic)**
* **post_baseUrl     <url>     (MANDATORY)**

FIXME: Examples of what these are for, what they do...


NAMING EXCHANGES
----------------

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
  - xr_Alice the exchange where Alice reads her report messages from (via sr_shovel).
  - Alice can create a new exchange by just posting to it (with sr3_post or sr_cpost) if it meets the naming rules.

Usually an sr_sarra run by a pump administrator will read from an exchange such as xs_Alice_mydata, 
retrieve the data corresponding to Alice´s *post* message, and make it available on the pump, 
by re-announcing it on the xpublic exchange.


POLLING
=======

Polling is doing the same job as a post, except for files on a remote server.
In the case of a poll, the post will have its url built from the *destination* 
option, with the product's path (*directory*/"matched file").  There is one 
post per file.  The file's size is taken from the directory "ls"... but its 
checksum cannot be determined, so the "sum" header in the posting is set 
to "0,0."

By default, sr_poll sends its post message to the broker with default exchange
(the prefix *xs_* followed by the broker username). The *broker* is mandatory.
It can be given incomplete if it is well defined in the credentials.conf file.

Refer to `sr3_post(1) <sr3_post.1.rst>`_ - to understand the complete notification process.
Refer to `sr3_post(7) <sr3_post.7.rst>`_ - to understand the complete notification format.


These options set what files the user wants to be notified for and where
 it will be placed, and under which name.

- **directory <path>           (default: .)**
- **accept    <regexp pattern> [rename=] (must be set)**
- **reject    <regexp pattern> (optional)**
- **permDefault     <integer>        (default: 0o400)**
- **nodupe_fileAgeMax <duration>   (default 30d)**


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

The **permDefault** option allows users to specify a linux-style numeric octal
permission mask::

  permDefault 040

means that a file will not be posted unless the group has read permission
(on an ls output that looks like: ---r-----, like a chmod 040 <file> command).
The **permDefault** options specifies a mask, that is the permissions must be
at least what is specified.

As with all other components, the **vip** option can be used to indicate
that a poll should be active on only a single node in a cluster. Note that
other nodes participating in the poll, when they don't have the vip, 
will subscribe to the output of the poll to keep their duplicate suppression 
caches current.

files that are more than nodupe_fileAgeMax are ignored. However, this 
can be modified to any specified time limit in the configurations by using 
the option *nodupe_fileAgeMax <duration>*. By default in components
other than poll, it is disabled by being set to zero (0). As it is a 
duration option, units are in seconds by default, but minutes, hours, 
days, and weeks, are available. In the poll component, nodupe_fileAgeMax
defaults to 30 days.

Advanced Polling
~~~~~~~~~~~~~~~~

The built-in Poll lists remote directories and parses the lines returned building 
paramiko.SFTPAttributes structures (similar to os.stat) for each file listed. 
There is a wide variety of customization available because resources to poll 
are so disparate:

* one can implement a *sarracenia.flowcb* callback with a *poll* routine 
  to support such services, replacing the default poller.

* Some servers have non-standard results when listing files, so one can 
  subclass a sarracenia.flowcb.poll callback with the **on_line**
  entry point to normalize their responses and still be able to use the
  builtin polling flow.

* There are many http servers that provide disparately formatted
  listings of files, so that sometimes rather than reformatting individual
  lines, a means of overriding the parsing of an entire page is needed.
  The **on_html_page** entry point in sarracenia.flowcb.poll can be 
  modified by subclassing as well.

* There are other servers that provide different services, not covered
  buy the default poll. One can implement additional *sarracenia.transfer*
  classes to add understanding of them to poll.

The output of a poll is a list of messages built from the file names
and SFTPAttributes records, which can then be filtered by elements
after *gather* in the algorithm.


COMPONENTS
==========

All the components do some combination of polling, consuming, and posting.
with variations that accomplish either forwarding of announcements or
data transfers. The components all apply the same single algorithm,
just starting from different default settings to match common use
cases.


CPUMP
-----

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
the contents.  Polling is only intended to be used for recently modified
files. The *nodupe_fileAgeMax* option eliminates files that are too old 
from consideration. When a file is found that matches a pattern given 
by *accept*, **poll** builds a notification message for that product.

The message is then checked in the duplicate cache (time limited by
nodupe_ttl option.) to prevent posting of files which have already
been seen.

**poll** can be used to acquire remote files in conjunction with an `sarra`_
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


Poll gathers information about remote files, to build messages about them.
The gather method that is built-in uses sarracenia.transfer protocols,
currently implemented are sftp, ftp, and http. 



Repeated Scans and VIP
~~~~~~~~~~~~~~~~~~~~~~

When multiple servers are being co-operating to poll a remote server,
the *vip* setting is used to decide which server will actually poll.
All servers participating subscribe to where **poll** is posting,
and use the results to fill in the duplicate suppression cache, so
that if the VIP moves, the alternate servers have current indications
of what was posted.




POST or WATCH
-------------

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

The *watch* component is used to monitor directories for new files. 
It is equivalent to post (or cpost) with the *sleep* option set to >0.

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


File Partitioning
~~~~~~~~~~~~~~~~~

use of the *blocksize* option has no effect in sr3.  It is used to do file partitioning,
and it will become effective again in the future, with the same semantics.


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


Specific Consuming Requirements
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
queues, and all the standard client side filtering with accept, reject, and after_accept.

Often, a broker will announce files using a remote protocol such as HTTP,
but for the sender it is actually a local file.  In such cases, one will
see a message: **ERROR: The file to send is not local.**
An after_accept plugin will convert the web url into a local file one::

  baseDir /var/httpd/www
  flowcb sarracenia.flowcb.tolocalfile.ToLocalFile

This after_accept plugin is part of the default settings for senders, but one
still needs to specify baseDir for it to function.

If a **post_broker** is set, **sender** checks if the clustername given
by the **to** option if found in one of the message's destination clusters.
If not, the message is skipped.



SETUP 1 : PUMP TO PUMP REPLICATION 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

FIXME: Missing example configuration.



DESTINATION SETUP 2 : METPX-SUNDEW LIKE DISSEMINATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this type of usage, we would not usually repost... but if the
**post_broker** and **post_exchange** (**url**,**on_post**) are set,
the product will be announced (with its possibly new location and new name).
Let's reintroduce the options in a different order
with some new ones to ease explanation.

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



SHOVEL
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


SUBSCRIBE
---------

Subscribe is the normal downloading flow component, that will connect to a broker, download
the configured files, and then forward the messages with an altered baseUrl.


WATCH
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




WINNOW
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

**winnow** can be used to trim messages produced by  post, `sr3_post <sr3_post.1.rst>`_, sr3_cpost, `poll`_ or `watch`_ etc... It is
used when there are multiple sources of the same data, so that clients only download the
source data once, from the first source that posted it.


Configurations
==============

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

(The edit action uses the EDITOR environment variable, if present.)
Once satisfied, one can start the the configuration running::

  $ sr_subscibe foreground q_f71.conf

What goes into the files? See next section:


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


flowCallbacks
=============

Sarracenia makes extensive use of small python code snippets that customize
processing called *flowCallback* Flow_callbacks define and use additional settings::

  flowCallback sarracenia.flowcb.log.Log

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

There is also *flowCallbackPrepend* which adds a flowCallback class to the front
of the list (which determines relative execution order among flowCallback classes.)

   
callback options
----------------

callbacks that are delivered with metpx-sr3 follow the following convention:

* they are placed in the sarracenia/flowcb  directory tree.
* the name of the primary class is the same as the name of file containing it.

so we provide the following syntactic sugar::

  callback log    (is equivalent to *flowCallback sarracenia.flowcb.log.Log* )

There is similarly a *callback_prepend* to fill in.  

Importing Extensions
--------------------

The *import* option works in a way familiar to Python developers,
Making them available for use by the Sarracenia core, or flowCallback.
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
---------------------

There is and older (v2) style of plugins as well. That are usually 
prefixed with the name of the plugin::

  msg_to_clusters DDI
  msg_to_clusters DD

  on_message msg_to_clusters

A setting 'msg_to_clusters' is needed by the *msg_to_clusters* plugin
referenced in the *on_message* the v2 plugins are a little more
cumbersome to write. They are included here for completeness, but
people should use version 3 (either flowCallback, or extensions
discussed next) when possible.

Reasons to use newer style plugins:

* Support for running v2 plugins is accomplished using a flowcb
  called v2wrapper. It performs a lot of processing to wrap up
  the v3 data structures to look like v2 ones, and then has
  to propagate the changes back. It's a bit expensive.

* newer style extensions are ordinary python modules, unlike
  v2 ones which require minor magic incantations.

* when a v3 (flowCallback or imported) module has a syntax error,
  all the tools of the python interpreter apply, providing
  a lot more feedback is given to the coder. with v2, it just
  says there is something wrong, much more difficult to debug.

* v3 api is strictly more powerful than v2, as it works
  on groups of messages, rather than individual ones.



Environment Variables
---------------------

On can also reference environment variables in configuration files,
using the *${ENV}* syntax.  If Sarracenia routines needs to make use
of an environment variable, then they can be set in configuration files::

  declare env HTTP_PROXY=localhost


LOGS and MONITORING
-------------------

- debug
   Setting option debug is identical to use  **logLevel debug**

- logMessageDump  (default: off) boolean flag
  if set, all fields of a message are printed, rather than just a url/path reference.

- logEvents ( default after_accept,after_work,on_housekeeping )
   emit standard log messages at the given points in message processing. 
   other values: on_start, on_stop, post, gather, ... etc...
  
- logLevel ( default: info )
   The level of logging as expressed by python's logging. Possible values are :  critical, error, info, warning, debug.

- --logStdout ( default: False )  EXPERIMENTAL FOR DOCKER use case

   The *logStdout* disables log management. Best used on the command line, as there is 
   some risk of creating stub files before the configurations are completely parsed::

       sr3 --logStdout start

   All launched processes inherit their file descriptors from the parent. so all output is like an interactive session.

   This is in contrast to the normal case, where each instance takes care of its logs, rotating and purging periodically. 
   In some cases, one wants to have other software take care of logs, such as in docker, where it is preferable for all 
   logging to be to standard output.

   It has not been measured, but there is a reasonable likelihood that use of *logStdout* with large configurations (dozens
   of configured instances/processes) will cause either corruption of logs, or limit the speed of execution of all processes
   writing to stdout.

- log_reject <True|False> ( default: False )
   print a log message when *rejecting* messages (choosing not to download the corresponding files)

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

- permLog ( default: 0600 )
   The permission bits to set on log files.

See the `Subscriber Guide <../How2Guides/subscriber.rst>` for a more detailed discussion of logging
options and techniques.




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

- **amqps://usern:passwd@host/ login_method=PLAIN**

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

Credential Details
~~~~~~~~~~~~~~~~~~

You may need to specify additional options for specific credential entries. These details can be added after the end of the URL, with multiple details separated by commas (see examples above).

Supported details:

- ``ssh_keyfile=<path>`` - (SFTP) Path to SSH keyfile
- ``passive`` - (FTP) Use passive mode
- ``active`` - (FTP) Use active mode
- ``binary`` - (FTP) Use binary mode
- ``ascii`` - (FTP) Use ASCII mode
- ``ssl`` - (FTP) Use SSL/standard FTP
- ``tls`` - (FTP) Use FTPS with TLS
- ``prot_p`` - (FTPS) Use a secure data connection for TLS connections (otherwise, clear text is used)
- ``bearer_token=<token>`` (or ``bt=<token>``) - (HTTP) Bearer token for authentication
- ``login_method=<PLAIN|AMQPLAIN|EXTERNAL|GSSAPI>`` - (AMQP) By default, the login method will be automatically determined. This can be overriden by explicity specifying a login method, which may be required if a broker supports multiple methods and an incorrect one is automatically selected.

Note::
 SFTP credentials are optional, in that sarracenia will look in the .ssh directory
 and use the normal SSH credentials found there.

 These strings are URL encoded, so if an account has a password with a special 
 character, its URL encoded equivalent can be supplied.  In the last example above, 
 **%2f** means that the actual password isi: **/dot8**
 The next to last password is:  **De:olonize**. ( %3a being the url encoded value for a colon character. )




PERIODIC PROCESSING
===================

Most processing occurs on receipt of a message, but there is some periodic maintenance
work that happens every *housekeeping* interval (default is 5 minutes.)  Evey housekeeping, all of the
configured *on_housekeeping* plugins are run. By default there are three present:

 * log - prints "housekeeping" in the log.
 * nodupe - ages out old entries in the reception cache, to minimize its size.
 * memory - checks the process memory usage, and restart if too big.

The log will contain messages from all three plugins every housekeeping interval, and
if additional periodic processing is needed, the user can configure addition
plugins to run with the *on_housekeeping* option. 

sanity_log_dead <interval> (default: 1.5*housekeeping)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **sanity_log_dead** option sets how long to consider too long before restarting
a component.

suppress_duplicates <off|on|999> (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The cleanup of expired elements in the duplicate suppression store happens at
each housekeeping.


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



QUEUES and MULTIPLE STREAMS
---------------------------

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
-------------------------------

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
---------

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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


[--blocksize <value>] (default: 0 (auto))
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
See `sr3_cpump(1) <sr3_cpump.1.rst>`_ for details.

[-pbd|--post_baseDir <path>] (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *post_baseDir* option supplies the directory path that, when combined (or found) 
in the given *path*, gives the local absolute path to the data file to be posted.
The *post_baseDir* part of the path will be removed from the posted announcement.
For sftp urls it can be appropriate to specify a path relative to a user account.
Example of that usage would be:  -pbd ~user  -url sftp:user@host
For file: url's, baseDir is usually not appropriate.  To post an absolute path,
omit the -pbd setting, and just specify the complete path as an argument.

post_baseUrl <url> (MANDATORY)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **post_baseUrl** option sets how to get the file... it defines the protocol,
host, port, and optionally, the user. It is best practice to not include 
passwords in urls.

post_exchange <name> (default: xpublic)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **post_exchange** option set under which exchange the new notification
will be posted.  In most cases it is 'xpublic'.

Whenever a publish happens for a product, a user can set to trigger a script.
The option **on_post** would be used to do such a setup.

post_exchange_split   <number>   (default: 0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
----------

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

flowCallback and flowCallbackPrepend <class>
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The flowCallback directive takes a class to load can scan for entry points as an argument::

    flowCallback sarracenia.flowcb.log.Log
   
With this directive in a configuration file, the Log class found in installed package will be used.
That module logs messages *after_accept* (after messages have passed through the accept/reject masks.)
and the *after_work* (after the file has been downloaded or sent). Here is the source code 
for that callback class::

  import json
  import logging
  from sarracenia.flowcb import FlowCB

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
            logger.info("worked successfully: %s " % msg.dumps() )

If you have multiple callbacks configured, they will be called in the same order they are 
configuration file. components in sr3 are often differentiated by the callbacks configured.
For example, a *watch* is a flow with sarracenia.flowcb.gather.file.File class that
is used to scan directories. A Common need when a data source is not easily accessed
with python scripts is to use the script callback::

   flowCallbackPrepend sarracenia.flowcb.script.Script

   script_gather get_weird_data.sh

Using the *_prepend* variant of the *flowCallback* option, will have the Script callback
class's entry point, before the File callback... So A script will be executed, and then
the directory will be checked for new files.  Here is part of the Script callback class::
    
    import logging
    from sarracenia.flowcb import FlowCB
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



ROLES - feeder/admin/declare
----------------------------

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
~~~~~~~~~~

  A subscriber is user that can only subscribe to data and return report messages. Subscribers are
  not permitted to inject data.  Each subscriber has an xs_<user> named exchange on the pump,
  where if a user is named *Acme*, the corresponding exchange will be *xs_Acme*.  This exchange
  is where an sr_subscribe process will send its report messages.

  By convention/default, the *anonymous* user is created on all pumps to permit subscription without
  a specific account.

source
~~~~~~

  A user permitted to subscribe or originate data.  A source does not necessarily represent
  one person or type of data, but rather an organization responsible for the data produced.
  So if an organization gathers and makes available ten kinds of data with a single contact
  email or phone number for questions about the data and its availability, then all of
  those collection activities might use a single 'source' account.

  Each source gets a xs_<user> exchange for injection of data posts, and, similar to a subscriber
  to send report messages about processing and receipt of data. Source may also have an xl_<user>
  exchange where, as per report routing configurations, report messages of consumers will be sent.

feeder
~~~~~~
  
  A user permitted to write to any exchange. Sort of an administrative flow user, meant to pump
  messages when no ordinary source or subscriber is appropriate to do so.  Is to be used in
  preference to administrator accounts to run flows.


User credentials are placed in the credentials files, and *sr_audit* will update
the broker to accept what is specified in that file, as long as the admin password is
already correct.


CONFIGURATION FILES
-------------------

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
are read as defaults for any component on start up.  In the same directory, *~/.config/sarra/credentials.conf* 
contains credentials (passwords) to be used by sarracenia ( `CREDENTIALS`_ for details. )

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



SUNDEW COMPATIBILITY OPTIONS
----------------------------

For compatibility with Sundew, there are some additional delivery options which can be specified.

destfn_script <script> (default:None)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This option defines a script to be run when everything is ready
for the delivery of the product.  The script receives the sr_sender class
instance.  The script takes the parent as an argument, and for example, any
modification to  **parent.msg.new_file**  will change the name of the file written locally.

filename <keyword> (default:WHATFN)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~

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
