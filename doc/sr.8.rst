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

**sr** declare|dump|setup|start|stop|restart|status 

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
