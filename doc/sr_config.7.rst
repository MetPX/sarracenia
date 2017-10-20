===========
 SR_CONFIG 
===========

-------------------------------------
Overview of Sarra Configuration Files
-------------------------------------

:Manual section: 7
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite



SYNOPSIS
========

 - **sr_component** [foreground|start|stop|restart|status|cleanup|declare|setup] <config> 
 - **<config_dir>**/ [ default.conf ]
 - **<config_dir>**/ [ sarra | subscribe | report | sender | watch ] / <config.conf>
 - **<config_dir>**/ scripts / <script.py>


DESCRIPTION
===========

Metpx Sarracenia components are the programs that can be invoked from the command line: 
examples are: sr_subscribe, sr_sarra, sr_sender, sr_report, When any component is invoked, 
a configuration file and an operation are specified.  The operation is one of:

 - foreground:  run a single instance in the foreground logging to stderr
 - restart: stop and then start the configuration.
 - start:  start the configuration running
 - status: check if the configuration is running.
 - stop: stop the configuration from running 

The remaining operations manage the resources (exchanges,queues) used by the component on
the rabbitmq server.

 - cleanup:  deletes the component's resources on the server
 - declare:  creates the component's resources on the server
 - setup:    like declare, additionnaly does queue bindings 

For example:  *sr_subscribe foreground dd* runs the sr_subcribe component with 
the dd configuration as a single foreground instance.

The **foreground** action is used when building a configuration or for debugging. 
The **foreground** instance will run regardless of other instances which are currently 
running.  Should instances be running, it shares the same message queue with them.
A user stop the **foreground** instance by simply using <ctrl-c> on linux
or use other means to kill the process.


.. contents::


HELP
----

**help** has a component print a list of valid options.

.. note::
   FIXME: Cannot find a component where help works.  Remove? 
   FIXME: OK: sr_post -h works. but not sr_post 'help' (interpreted as a file, naturally.)

**-V**  has a component print out a version identifier and exit.



OPTIONS
=======


Finding Option Files
--------------------

Metpx Sarracenia is configured using a tree of text files using a common
syntax.  The location of config dir ( as per `XDG Open Directory Specication <https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.html>`_ ) is platform dependent (see python appdirs)::

 - linux: ~/.config/sarra 

 - Windows: %AppDir%/science.gc.ca/sarra, this might be:
   C:\Users\peter\AppData\Local\science.gc.ca\sarra

The top of the tree contains a file 'default.conf' which contains settings that
are read as defaults for any component on start up. One can also use the XDG_CONFIG_HOME 
environment variable to override default placement, or individual configuration 
files can be placed in any directory and invoked with the complete path.   When components
are invoked, the provided file is interpreted as a file path (with a .conf
suffix assumed.)  If it is not found as file path, then the component will
look in the component's config directory ( **config_dir** / **component** )
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





Content has been moved to `sr_subscribe(1) <sr_subscribe.1.html>`_


SEE ALSO
========

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_report(1) <sr_report.1.html>`_ - process report messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
