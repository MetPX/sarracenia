========================
Sarracenia Documentation
========================

.. contents::

* `Admin Guide <Admin.html>`_
* `Developer Guide <Dev.html>`_


Unix Commands
-------------

* `sr_subscribe(1) <sr_subscribe.1.html>`_ - the http/https subscription client.
* `sr_post(1) <sr_post.1.html>`_ - the tool to post individual files.
* `sr_watch(1) <sr_watch.1.html>`_ - the tool to post all changes to a given directory.
* `sr_log(1) <sr_log.1.html>`_ - (Does not exist yet!) the tool to read log messages.

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