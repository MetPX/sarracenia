==============
 SR_Audit 
==============

-----------------------------
Audit the state of the broker 
-----------------------------

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


sr_audit is a program to ensure the correctness of the broker.

The **sr_audit** command takes one argument the action start|stop|restart|reload|status... (self described).
A configuration file may be used to set options: **debug**, **max_queue_size** and **sleep**

The **foreground** action is different. It would be used when building a configuration
or debugging things. It is used when the user wants to run the program and/or its configfile 
interactively...   The **foreground** instance is not concerned by other running instances.
It will perform the same actions as the currently running one.
The user would stop using the **foreground** instance by simply pressing <ctrl-c> on linux 
or use other means to kill its process. 

**sr_audit** manages the broker from the **admin** option (describing the user managing the broker)
and its credentials defined in the file  **credentials.conf**. It sleeps **sleep** seconds.

The default behavior of **sr_audit** is to manage and control the queues on the broker.
When it wakes up, it gets all the current queues on the broker. The queues are validated and deleted if
they have no connection and holding more than **max_queue_size** messages, if they do not conform
to the naming standard (name starting with **q_"brokerusername"** where "brokername" is a valid
user on the broker).
**(NOTE: currently for backward support, sr_audit tolerates queues that starts with cmc)**


When configuring a pump, there are other ways of using **sr_audit**.
When **sr_audit** is envoked with **--pump** it helps configuring the pump.
When envoked with **--users** the program manages the users, permissions and exchanges.


VERIFY PUMP SETTINGS
====================

When installing a pump, using **sr_audit** envoke with **--pump**, tells the program to verify the basic
configurations requiered on a pump. It makes sure the **feeder** user credentials are given and the **admin**
user is defined and valid.  It warns and explains if options **cluster,gateway_for,roles**, as well as
the **log2clusters.conf** are missing.


MANAGING USERS
==============

When **sr_audit** is envoked with **--users**, the broker's users and exchanges are verified.
To verify the users, the program builds a list of users by roles from the setting of **users.conf**.
It also considers the standard users :   **root**, **feeder**, **anonymous** and there appropriate roles: 
**admin**, **feeder**, **subscribe**.  After, it makes sure the users are configured on the broker.
Missing users are added... with the permissions requiered for their role. Extra users,
not configured in metpx-sarracenia, are deleted. 

To verify the exchanges, **sr_audit** gets the present exchanges on the broker.
From the users and roles, it determines the exchanges that should be present and creates the one
missing. Extra exchanges are deleted if their names dont start with 'x'.

When adding/deleting a user, the broker administrator would simply add/delete the username and its role
in the **users.conf** file.  Than he runs **sr_audit --users configfile foreground**. The log on standard
output would tell the administrator what broker resources were added/deleted (user,exchanges, queue, etc).
If the broker does not use ldap, the administrator adding a user, has to set this user's password
(once created by sr_audit) with the command run as root on the broker'server :

**rabbitmqctl change_password "user" "password"**

where "user"  is the username added in **users.conf** and "password" its password
on the broker.



CONFIGURATION
=============

Options are placed in the configuration file, one per line, of the form: 

**option <value>** 

Comment lines begins with **#**. 

There is a very limited set of options that **sr_audit** uses.

**admin          <user>    (Mandatory: broker admin user, detailed in credentials.conf)**
**debug          <boolean> (default: false)**
**sleep          <int>     (default: 60 in seconds)** 
**max_queue_size <int>     (default: 25000 nbr messages in queue)** 

The **admin** option must be defined it
normally be set in the file **default.conf**
and the credential details would be found in 
the file **credentials.conf**


 
SEE ALSO
--------

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
