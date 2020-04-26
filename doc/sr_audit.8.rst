==========
 SR_Audit 
==========

------------------
Audit Broker State
------------------

:Manual section: 8
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite

.. contents::

SYNOPSIS
========

 **sr_audit** configfile foreground|start|stop|restart|reload|status 

 **sr_audit** --pump  foreground configfile

 **sr_audit** --users foreground configfile

DESCRIPTION
===========

Sr_audit is a daemon that runs periodically to examine what is running 
on a system to fix issues it sees.  When run as a non-administrative user, 
it looks for components which state files indicate are running, but for 
which the corresponding processes are missing.  It will restart those. Any 
running process should also be writing at least a heartbeat message 
to its log file periodically, so if the log file is too old,
the component will be assumed frozen, and restarted.

When run by an administrative user,  Sr_audit configures a broker to 
reflect sarracenia configuration settings.  **Sr_audit** takes one argument: 
the action to perform.  One can also set
a few option in a configuration file: **debug**, **max_queue_size**.

When **Sr_audit** is *started* in admin mode, it connects to the broker 
using the **admin** account. It sleeps the time required to trigger the next heartbeat.

The default behavior of **sr_audit** is to manage and control the queues on the broker.
The queues are validated and deleted if there is no client connected to them and has more 
than **max_queue_size** messages waiting or if there are queues or exchanges that do 
not conform to sarracenia naming conventions (queue names start with **q_"brokerusername"** 
where "brokerusername" is a valid user on the broker).

When configuring a pump, there are other ways of using **sr_audit**.
When **sr_audit** is invoked with **--pump** it helps configuring the pump.
When invoked with **--users** the program manages the users, permissions and exchanges.


OPTIONS
=======


In general, the options for this component are described by the
`sr_subscribe(1) <sr_subscribe.1.rst>`_  page which should be read first.
It fully explains the option configuration language, and how to find
option settings.

There are very few options that **sr_audit** uses:

**admin          <user>    (Mandatory: broker admin user, detailed in credentials.conf)**

**debug          <boolean> (default: False)**

**reset          <boolean> (default: False)**

**set_passwords  <boolean> (default: True)** 

**max_queue_size <int>     (default: 25000 nbr messages in queue)** 

**dry_run  <boolean> (default: False)** 

The **admin** option must be defined and normally be set in the file **default.conf**
and the credential details would be found in the file **credentials.conf**
Normally when users are created, the passwords for communications with the broker are set based
on the values found in the credentials file.

When the *reset* option is given, user passwords and permissions will be reset to their expected
values.  Normally, an existing user's permissions are left untouched by an audit run.

The dry_run option will print what audit would do if run, and make no changes to the
broker.

VERIFY PUMP SETTINGS
====================

Use **sr_audit** invoke with **--pump**  to set up its configuration.  It makes sure the **feeder** 
user credentials are given and the **admin** user is defined and valid.  


MANAGING USERS
==============

When **sr_audit** is invoked with **--users**, the broker's users and exchanges are verified.
The program builds a list of users by their **declare** roles. 
It checks that: **admin**, **feeder**  administrative roles are working.
**sr_audit** makes sure that users configured in sarracenia configurations are present on the broker.  
Missing users are added... with the permissions required for their role. Extra users,
not configured in sarracenia, are deleted. 

To verify user exchanges, **sr_audit** gets the list of exchanges present on the broker.
From the users and roles, it determines the exchanges that should be present and creates the one
missing. Extra exchanges are deleted if their names do not start with 'x'.

When adding or deleting a user, the broker administrator adds or deletes the role declaration for a
username and in the **default.conf** file.  Then he runs **sr_audit --users foreground configfile**. 
The log on standard output would tell the administrator what broker resources were 
added/deleted (users, exchanges, queues, etc).   


 
SEE ALSO
--------

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.rst>`_ - the format of report messages.

`sr_report(1) <sr_report.1.rst>`_ - process report messages.

`sr_post(1) <sr_post.1.rst>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.rst>`_ - the format of announcement messages.

`sr_sarra(8) <sr_sarra.8.rst>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.rst>`_ - the directory watching daemon.

`https://github.com/MetPX/ <https://github.com/MetPX/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
