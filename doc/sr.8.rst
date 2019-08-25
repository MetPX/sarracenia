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

**sr** declar|dump|setup|start|stop|restart|status 

DESCRIPTION
===========

**sr** is a global startup/status/shutdown tool to manage grouped configurations.
For the current user, it reads on all of the configuration files, state files, and 
consults the process table to determine the state of all components.  It then 
makes the change requested.

In general, sr will operate on all the processes, printing a '.' for item processed
(sometimes a dot represents a configuration, other times a process) to signify
progress. 

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
  
  .
  .
  .

  blacklab% 

The points represent the launching of the processes to run the operation for one configuration.
The outputs are the results after they complete.


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

SEE ALSO
========

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - the download client. (<-- The Main man page!)

`sr_report(7) <sr_report.7.rst>`_ - the format of report messages.

`sr_report(1) <sr_report.1.rst>`_ - process report messages.

`sr_post(1) <sr_post.1.rst>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.rst>`_ - the format of announcements.

`sr_watch(1) <sr_watch.1.rst>`_ - the directory watching daemon.

`dd_subscribe(1) <dd_subscribe.1.rst>`_ - the http-only download client.
