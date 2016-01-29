========================
Sarracenia Documentation
========================

.. contents::

* `Installation <Install.html>`_
* `Subscriber Guide <subscribe.html>`_ - effective downloading from a pump.
* `Source Guide <subscribe.html>`_ - effective uploading to a pump
* `Admin Guide <Admin.html>`_ - Configuration of Pumps
* `Developer Guide <Dev.html>`_ - contributing to sarracenia development.
* `sr_config(7) <sr_subscribe.7.html>`_ - Overview of Configuration for commands.


Unix Commands
-------------

* `sr_post(1) <sr_post.1.html>`_ - the tool to post individual files.
* `sr_subscribe(1) <sr_subscribe.1.html>`_ - the http/https subscription client.
* `sr_log(1) <sr_log.1.html>`_ - (Does not exist yet!) the tool to read log messages.
* `sr_watch(1) <sr_watch.1.html>`_ - the tool to post all changes to a given directory.

Administrative Daemons
-----------------------

* `sr_sarra(8) <sr_sarra.8.html>`_ - Subscribe, Acquire And Re-Advertise...  the main pump.
* `sr_log2clusters(8) <sr_log2clusters.8.html>`_ - daemon to copy log messages to other clusters.
* `sr_log2source(8) <sr_log2source.8.html>`_ - daemon to copy log messages to the originating source.


Formats/Protocols
------------------

* `sr_post(7) <sr_post.7.html>`_ - the format of postings. Posted by watch and post, consumed by subscribe.
* `sr_log(7) <sr_log.7.html>`_ - the format of log messages. Sent by consumers, for sources to measure reach.
* `log2clusters(7) <log2clusters.7.html>`_ - configuration of log routing between clusters.
