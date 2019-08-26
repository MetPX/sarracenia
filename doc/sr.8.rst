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

Call the corresponding function for each configuration.


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
  gathering global state: procs, configs, state files, logs, analysis - Done. 
  status...
  sr_audit: running 1 (OK)
  sr_cpost: running 1 (OK)
  sr_cpump: running 2 (OK)
  sr_poll: running 2 (OK)
  sr_report: running 3 (OK)
  sr_sarra: running 1 (OK)
  sr_sender: running 1 (OK)
  sr_shovel: running 4 (OK)
  sr_subscribe: running 10 (OKd)
  sr_watch: running 1 (OK)
  sr_winnow: running 2 (OK)
  total running: configs: 27, processes: 93
  blacklab% 
  
OK means that all configurations are running all instances.
OKd means that some while configurations are running, some are disabled (and are not running.)

Sample OK status (when sr is stopped)::

  blacklab% sr status
  gathering global state: procs, configs, state files, logs, analysis - Done. 
  status...
  sr_audit: running 0 (missing)
  sr_cpost: all 1 stopped
  sr_cpump: all 2 stopped
  sr_poll: all 2 stopped
  sr_report: all 3 stopped
  sr_sarra: all 1 stopped
  sr_sender: all 1 stopped
  sr_shovel: all 4 stopped
  sr_subscribe: all 10 stopped
  sr_watch: all 1 stopped
  sr_winnow: all 2 stopped
  blacklab%
  
Sample status when something is wrong::

  blacklab% sr status
  gathering global state: procs, configs, state files, logs, analysis - Done. 
  status...
  sr_audit: running 1 (OK)
  sr_cpost: running 1 (OK)
  sr_cpump: running 2 (OK)
  sr_poll: running 2 (OK)
  sr_report: running 3 (OK)
  sr_sarra: running 1 (OK)
  sr_sender: running 1 (OK)
  sr_shovel: running 4 (OK)
  sr_subscribe: mixed status
    disabled: amqp_f30.conf 
     partial: cfile_f44 
     running: local_sub, cdnld_f21, cclean_f91, rabbitmqtt_f31, u_sftp_f60, ftp_f70, amqp_f30, cp_f61, q_f71 
  sr_watch: running 1 (OK)
  sr_winnow: running 2 (OK)
  blacklab% 

Since there is a problem with sr_subscribe, more information 
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
