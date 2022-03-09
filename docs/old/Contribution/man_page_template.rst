==========
 SR3_TITLE 
==========

--------
sr_title
--------

:Manual section: 1 
:Date: @Date@
:Version: @Version@
:Manual group: MetPX-Sarracenia

.. contents::

SYNOPSIS
========

**sr_title** foreground|start|stop|restart|reload|status configfile
**sr_title** cleanup|declare|setup configfile

DESCRIPTION
===========

**sr_title** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do 
eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea 
commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit
esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat 
cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id 
est laborum. `sr_subscribe(7) <sr3.1.rst#subscribe>`_ 
with some limitations.  

 - doesn't download data, only circulates posts.
 - runs as only a single instance (no multiple instances). 
 - does not support any plugins.
 - does not support vip for high availability.
 - different regular expression library: POSIX vs. python.
 - does not support regex for the strip command (no non-greedy regex).

It can therefore act as a drop-in replacement for:

   `sr_report(1) <sr3.1.rst#report>`_ - process report messages.

   `sr_shovel(8) <sr3.1.rst#shovel>`_ - process shovel messages.

   `sr_winnow(8) <sr3.1.rst#winnow>`_ - process winnow messages.


The **sr_cpump** command takes two arguments: an action start|stop|restart|reload|status... (self described)
followed by a configuration file.

The **foreground** action is used when debugging a configuration, when the user wants to 
run the program and its configfile interactively...   The **foreground** instance 
is not concerned by other actions.  The user would stop using the **foreground** instance 
by simply <ctrl-c> on linux or use other means to send SIGINT or SIGTERM to the process.

The actions **cleanup**, **declare**, **setup** can be used to manage resources on
the rabbitmq server. The resources are either queues or exchanges. **declare** creates
the resources. **setup** creates and additionally does the bindings of queues.

The actions **add**, **remove**, **edit**, **list**, **enable**, **disable** act
on configurations.

CONFIGURATION
=============

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium 
doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore 
veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim
ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia
consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque
porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, 
adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore 
et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis 
nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid 
ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea
voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem
eum fugiat quo voluptas nulla pariatur?"




ENVIRONMENT VARIABLES
=====================

If the SR_CONFIG_EXAMPLES variable is set, then the *add* directive can be used
to copy examples into the user's directory for use and/or customization.

An entry in the ~/.config/sarra/default.conf (created via sr_subscribe edit default.conf )
could be used to set the variable::

  declare env SR_CONFIG_EXAMPLES=/usr/lib/python3/dist-packages/sarra/examples

The value should be available from the output of a list command from the python
implementation.

SEE ALSO
========

`sr3_report(7) <sr3.1.rst#report>`_ - the format of report messages.

`sr3_report(1) <sr3.1.rst#report>`_ - process report messages.

`sr3_post(1) <sr3_post.1.rst>`_ - post announcemensts of specific files.

`sr3_post(7) <sr_post.7.rst>`_ - the format of announcements.

`sr3_subscribe(1) <sr3.1.rst#subscribe>`_ - the download client.

`sr3_watch(1) <sr3.1.rst#watch>`_ - the directory watching daemon.
