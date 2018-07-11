=========
SR_Report 
=========

---------------------------------
Select and Process Posted Reports 
---------------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite

.. contents::

SYNOPSIS
========

 **sr_report** foreground|start|stop|restart|reload|status configfile

 **sr_report** cleanup|declare|setup configfile


DESCRIPTION
===========

sr_report is a program to efficiently process reports of file transfers from 
sarracenia. The format of the reports is shown in the `sr_report(7) <sr_report.7.rst>`_ manual 
page.  When clients download a message from a site running sarracenia, they post
information about their success in doing so.  

The **sr_report** command takes two arguments: a configuration file described below,
followed by an action, one of: start|stop|restart|reload|status or foreground... (self described).
sr_report is sr_subscribe with the following settings changed::

  no-download True
  topic-prefix v02.report
  cache off
  accept_unmatch True
  report_back False

The **foreground** action is different. It is used when building a configuration
or debugging things, when the user wants to run the program and its configfile 
interactively...  The **foreground** instance is not concerned by other actions, 
but should the configured instances be running, it shares the same (configured) message queue.

The actions **cleanup**, **declare**, **setup** can be used to manage resources on
the rabbitmq server. The resources are either queues or exchanges. **declare** creates
the resources. **setup** creates and additionally does the bindings of queues.

CONFIGURATION
=============

In general, the options for this component are described by the
`sr_subscribe(1) <sr_subscribe.1.rst>`_  page which should be read first.
It fully explains the option configuration language, and how to find
the option settings.


EXAMPLES
--------

Here is a short complete example configuration file:: 

  broker amqp://dd.weather.gc.ca/

  subtopic model_gem_global.25km.grib2.#
  accept .*

This above file will connect to the dd.weather.gc.ca broker, connecting as
anonymous with password anonymous (defaults) to obtain announcements about
files in the http://dd.weather.gc.ca/model_gem_global/25km/grib2 directory.
All reports of downloads of those files present on the pump will be
accepted for processing by sr_report.



SEE ALSO
--------

`sr_report(7) <sr_report.7.rst>`_ - the format of report messages.

`sr_post(1) <sr_post.1.rst>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.rst>`_ - the format of announcement messages.

`sr_sarra(8) <sr_sarra.8.rst>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - Selectively Download files.

`sr_watch(1) <sr_watch.1.rst>`_ - the directory watching daemon.

`https://github.com/MetPX/ <https://github.com/MetPX/>`_ - sr_report is a component of MetPX-Sarracenia, the AMQP based data pump.
