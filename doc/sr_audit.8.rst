==============
 SR_Audit 
==============

------------------
Audit Broker State
------------------

:Manual section: 8
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite



SYNOPSIS
========

 **sr_audit** configfile foreground|start|stop|restart|reload|status
 **sr_audit** --pump  configfile foreground
 **sr_audit** --users configfile foreground

DESCRIPTION
===========


Sr_audit configures a broker to reflect sarracenia configuration settings.
**Sr_audit** takes one argument: the action to perform.  One can also set
a few option in a configuration file: **debug**, **max_queue_size** and **sleep**

When **Sr_audit** is *started*, it connects to the broker using the **admin** account. 

It sleeps **sleep** seconds.

The default behavior of **sr_audit** is to manage and control the queues on the broker.
The queues are validated and deleted if there is no client connected to it and has more 
than **max_queue_size** messages waiting.  If there are queues or exchanges that do not conform
to sarracenia naming conventions (queue names start with **q_"brokerusername"** 
where "brokerusername" is a valid user on the broker).

**(FIXME, NOTE: currently for backward support, sr_audit tolerates queues that starts with cmc)**

When configuring a pump, there are other ways of using **sr_audit**.
When **sr_audit** is invoked with **--pump** it helps configuring the pump.
When invoked with **--users** the program manages the users, permissions and exchanges.


OPTIONS
=======


In general, the options for this component are described by the
`sr_config(7) <sr_config.7.html>`_  page which should be read first.
It fully explains the option configuration language, and how to find
option settings.


VERIFY PUMP SETTINGS
====================

Use **sr_audit** invoke with **--pump**  to set up it's configuration.  It makes sure the **feeder** 
user credentials are given and the **admin** user is defined and valid.  It warns and explains 
if options **cluster,gateway_for,roles**, as well as the **log2clusters.conf** are missing.


MANAGING USERS
==============

When **sr_audit** is invoked with **--users**, the broker's users and exchanges are verified.
The program builds a list of users by *roles*. 
It checks that users :   **root**, **feeder**, **anonymous** and have appropriate roles: **admin**, **feeder**, **subscribe**.  
Next, it makes sure that users configured in sarracenia configurations are present on the broker.  
Missing users are added... with the permissions required for their role. Extra users,
not configured in sarracenia, are deleted. 

To verify user exchanges, **sr_audit** gets the list of exchanges present on the broker.
From the users and roles, it determines the exchanges that should be present and creates the one
missing. Extra exchanges are deleted if their names do not start with 'x'.

When adding or deleting a user, the broker administrator adds or delete the role declaration for a
username and in the **default.conf** file.  Then he runs **sr_audit --users configfile foreground**. 
The log on standard output would tell the administrator what broker resources were 
added/deleted (user,exchanges, queue, etc).  If the broker does not use ldap, the administrator 
adding a user, has to set this user's password (after it has been created by sr_audit) with 
the following command run as root on the broker'server :

**rabbitmqctl change_password "user" "password"**

where "user"  is the username added and "password" its password
on the broker.


CONFIGURATION
=============

There are very few options that **sr_audit** uses:

**admin          <user>    (Mandatory: broker admin user, detailed in credentials.conf)**

**debug          <boolean> (default: false)**

**sleep          <int>     (default: 60 in seconds)** 

**max_queue_size <int>     (default: 25000 nbr messages in queue)** 

The **admin** option must be defined it normally be set in the file **default.conf**
and the credential details would be found in the file **credentials.conf**


 
SEE ALSO
--------

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
