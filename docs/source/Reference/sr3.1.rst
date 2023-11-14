=====
 SR3 
=====

------------------
sr3 Sarracenia CLI
------------------

:Manual section: 1 
:Date: |today|
:Version: |release|
:Manual group: MetPX-Sarracenia


SYNOPSIS
========

**sr3** *options* *action* [ *component/config* ... ] 

DESCRIPTION
===========

Sr3 is a tool to manage a fleet of daemons, whose output is mostly
in log files. Sr3 allows one to start, stop, and inquire the status of configured
Sarracenia flows. It is the primary command line entry point to 
Sarracenia 3 ( https://metpx.github.io/sarracenia/ )
When sr3 is started up, it reads the entire configuration tree, and the status of all flows
can be queried with, for example *sr3 status*. When *component/config* is given it is to
have sr3 operate on a subset of all the configurations present.

* If you already familiar in general with Sarracenia, and are looking for information about 
  specific options or directives, best to look at `sr3 Options (7) <sr3_options.7.html>`_
* To more easily get started, have a look at `the Subscriber Guide on github <../How2Guides/subscriber.html>`_
* For a general guide to the interface: see the `Command Line Guide <../Explanation/CommandLineGuide.html>`_

The command line has three major elements:  
* options
* action
* component/config

A flow is a group of processes running using a common component/config.

OPTIONS
=======

Most options are stored in configuration files referred to by the *component/config* indicated
by the listing file, but on occasion, one may wish to use command line to override
values in the configuration file.  Options are defined in `Sr3 Options (7) <sr3_options.7.html>`_
Refer to that manual page for a full discussion. There is one exception::

   -h (or --help) 

The help option is only available on the command line. It is used to get a prompt
describing the subset of options available to override config file values.


ACTIONS
=======

The type of action to take. One of:

 - add:           copy to the list of available configurations.
 - cleanup:       deletes the component's resources on the server.
 - convert:       copy a configuration from v2 to sr3 location, updating on the way.
 - declare:       creates the component's resources on the server.
 - disable:       mark a configuration as ineligible to run.
 - edit:          modify an existing configuration.
 - enable:        mark a configuration as eligible to run.
 - features:      what parts of sr3 are working?
 - foreground: run a single instance in the foreground logging to stderr
 - list:          list all the configurations available.
 - list plugins:  list all the plugins available.
 - list examples:  list all the plugins available.
 - remove:        remove a configuration.
 - restart: stop and then start the configuration.
 - run:  run as a master process (like start, but don't return.)
 - sanity: looks for instances which have crashed or gotten stuck and restarts them.
 - show           view an interpreted version of a configuration file.
 - start:  start the configuration running
 - status: check if the configuration is running.
 - stop: stop the configuration from running

    

COMPONENTS
==========

`The Flow Algorithm <../Explanation/Concepts.html#the-flow-algorithm>`_ is what is
run by all sr3 processes. The flow algorithm's behaviour is customized by options,
some of which control optional modules (flowcallbacks) Each component has a 
different set of default option settings to cover a common use case. 

* `cpump <../Explanation/CommandLineGuide.html#cpump>`_ - copy notification messages from one pump another second one (a C implementation of shovel.)
* `flow <../Explanation/CommandLineGuide.html#flow>`_ - flux générique, pas de valeurs par défaut, bonne base pour la construction de flux personalisés.
* `poll <../Explanation/CommandLineGuide.html#poll>`_ - poll a non-sarracenia web or file server to create notification messages for processing.
* `post|sr3_post|sr_cpost|watch <../Explanation/CommandLineGuide.html#post-or-watch>`_ - create notification messages for files for processing.
* `sarra <../Explanation/CommandLineGuide.html#sarra>`_ - download file from a remote server to the local one, and re-post them for others.
* `sender <../Explanation/CommandLineGuide.html#sender>`_ - send files from a local server to a remote one.
* `shovel <../Explanation/CommandLineGuide.html#shovel>`_ - copy notification messages, only, not files.
* `watch <../Explanation/CommandLineGuide.html#watch>`_ - create notification messages for each new file that arrives in a directory, or at a set path.
* `winnow <../Explanation/CommandLineGuide.html#winnow>`_ - copy notification messages, suppressing duplicates.


CONFIGURATIONS
==============

When a *component/configuration* pair is specified on the command line,
It is actually building the effective configuration from:

 1. default.conf

 2. admin.conf

 3. <component>.conf (subscribe.conf, audit.conf, etc...)

 4. <component>/<config>.conf

Settings in an individual .conf file are read in after the default.conf
file, and so can override defaults. Options specified on
the command line override configuration files.

While one can manage configuration files using the *add*, *remove*,
*list*, *edit*, *disable*, and *enable* actions, one can also do all
of the same activities manually by manipulating files in the settings
directory. The configuration files for an sr3 configuration
called *myflow* would be here:

 - linux: ~/.config/sarra/subscribe/myflow.conf (as per: `XDG Open Directory Specication <https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.rst>`_ )

 - Windows: %AppDir%/science.gc.ca/sarra/myflow.conf , this might be:
   C:\Users\peter\AppData\Local\science.gc.ca\sarra\myflow.conf

 - MAC: FIXME.

The top of the tree has  *~/.config/sarra/default.conf* which contains settings that
are read as defaults for any component on start up.  In the same
directory, *~/.config/sarra/credentials.conf* contains credentials (passwords) to
be used by sarracenia ( `CREDENTIALS <sr3_credentials.7.html>`_ for details. )

One can also set the XDG_CONFIG_HOME environment variable to override default placement, or
individual configuration files can be placed in any directory and invoked with the
complete path. When components are invoked, the provided file is interpreted as a
file path (with a .conf suffix assumed.) If it is not found as a file path, then the
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

Remote Configurations
---------------------

One can specify URI's as configuration files, rather than local files. Example:

  - **--config http://dd.weather.gc.ca/alerts/doc/cap.conf**

On startup, sr3 checks if the local file cap.conf exists in the
local configuration directory.  If it does, then the file will be read to find
a line like so:

  - **--remote_config_url http://dd.weather.gc.ca/alerts/doc/cap.conf**

In which case, it will check the remote URL and compare the modification time
of the remote file against the local one. The remote file is not newer, or cannot
be reached, then the component will continue with the local file.

If either the remote file is newer, or there is no local file, it will be downloaded,
and the remote_config_url line will be prepended to it, so that it will continue
to self-update in future.


Logs
----

for the logs, look in ~/.cache/sr3/logs (on linux. Other platforms, will vary.)
To find them on any platform::

    fractal% sr3 list
    User Configurations: (from: /home/peter/.config/sr3 )
    admin.conf                       credentials.conf                 default.conf                     
    logs are in: /home/peter/.cache/sr3/log

Last line indicates the directory.



EXAMPLES
========

Here is a short complete example configuration file:: 

  broker amqps://dd.weather.gc.ca/

  subtopic model_gem_global.25km.grib2.#
  accept .*

This above file will connect to the dd.weather.gc.ca broker, connecting as
anonymous with password anonymous (defaults) to obtain notification messages about
files in the http://dd.weather.gc.ca/model_gem_global/25km/grib2 directory.
All files which arrive in that directory or below it will be downloaded 
into the current directory (or just printed to standard output if -n option 
was specified.) 

A variety of example configuration files are available here:

 `https://github.com/MetPX/sarracenia/tree/main/sarra/examples <https://github.com/MetPX/sarracenia/tree/main/sarra/examples>`_





SEE ALSO
========


**User Commands:**

`sr3_post(1) <sr3_post.1.html>`_ - post file notification messages (python implementation.)

`sr3_cpost(1) <sr3_cpost.1.html>`_ - post file announcemensts (C implementation.)

`sr3_cpump(1) <sr3_cpump.1.html>`_ - C implementation of the shovel component. (copy notification messages)

**Formats:**

`sr3_credentials(7) <sr3_credentials.7.html>`_ - Convert logfile lines to .save Format for reload/resend.

`sr3_options(7) <sr3_options.7.html>`_ - Convert logfile lines to .save Format for reload/resend.

`sr3_post(7) <sr3_post.7.html>`_ - The format of notification messages.

**Home Page:**

`https://metpx.github.io/sarracenia <https://metpx.github.io/sarracenia>`_ - Sarracenia: a real-time pub/sub data sharing management toolkit

