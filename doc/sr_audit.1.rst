==============
 SR_Audit 
==============

-----------------------------
Audit the state of the broker 
-----------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite



SYNOPSIS
========

 **sr_audit** configfile foreground|start|stop|restart|reload|status

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

**sr_audit** connects to the broker defined by the **feeder** option which can be overwritten by
option **broker**. It sleeps **sleep** seconds.  When it wakes up, it builds lists of users by 
roles from the setting of **users.conf**,  and considers the standard users :   
**root**, **feeder**, **anonymous** with there appropriate roles : **admin**, **feeder**, **subscribe**.

Than it gets all the current queues on the broker. The queues are validated and deleted if
they are holding more than **max_queue_size** messages, if they do not conform to the naming
standard *mely starting with *q_"brokerusername"** where "brokername" is a valid user on the broker.
**(NOTE: currently for backward support, sr_audit tolerates queues that starts with cmc)**

After, it gets the users configured on the broker. Missing users configured in **users.conf**  
but not on the broker are added... with the permissions requiered for their role. Extra users
on the broker that are not configured in metpx-sarracenia are deleted. 

Similar processing is done to the exchanges. **sr_audit** gets the exchanges on the broker.
From the users and roles, it determines the exchanges that are valid or created the one
missing. If some extra exchanges are found they are deleted.

When adding a user, the broker administrator would simply add the username and its role
in the **users.conf** file.  Within at most **sleep** seconds, the user would be created
onto the broker and so would the exchanges it will use. If the broker would not use ldap
the administrator would have to set this user's password (once created by sr_audit) with
the command run as root on the broker'server :

**rabbitmqctl change_password "user" "password"**

where "user"  is the username added in **users.conf** and "password" its password
on the broker.


CONFIGURATION
=============

Options are placed in the configuration file, one per line, of the form: 

**option <value>** 

Comment lines begins with **#**. 

There is a very limited set of options that **sr_audit** uses.

**broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**
**debug          <boolean> (default: false)**
**sleep          <int>     (default: 60 in seconds)** 
**max_queue_size <int>     (default: 25000 nbr messages in queue)** 

The broker option defaults to the value of option 'feeder' that would
normally be set in the file **default.conf**


 
SEE ALSO
--------

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
