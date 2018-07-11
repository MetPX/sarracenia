
=========
sr_pulse
=========

---------------------------------------------
Sarracenia v02 Pulse Message Format/Protocol
---------------------------------------------

:Date: @Date@
:Version: @Version@
:Manual section: 7
:Manual group: MetPX-Sarracenia


.. contents::



SYNOPSIS
========

**AMQP Topic: <version>.pulse.[tick|message]**

**Body:** *<message>*


DESCRIPTION
===========

sr_pulse messages are sent out periodically (default is every minute) so that subscribers with a very low frequency of subscription matches
will well maintain a connection across firewalls. Consumers can check every heartbeat (10 minutes by default) if they have received
any pulses.  If no pulse has been received, the consumer can try an operation on the channel to confirm connection with the broker.
If no connection is present, then consumers should teardown and re-build it.


AMQP TOPIC
==========

The topic of a pulse message is prefixed with v02.pulse.  The sub-topic is either: *tick* for an ordinary keep-alive message,
or *message* for an administrator message intended for all subscribers.  


THE BODY
========

The body of the message in a *tick* is the standard timestamp (as in an `sr_post(7) <sr_post.7.rst>`_ message) 
Format: *YYYYMMDDHHMMSS.*<decimalseconds>* (Note: The datestamp is always in UTC timezone.)

In the case of a message with the *v02.pulse.message*  topic.  The body is a message to be posted in the logs of all subscribers.


FURTHER READING
===============

https://github.com/MetPX - home page of metpx-sarracenia

http://rabbitmq.net - home page of the AMQP broker used to develop Sarracenia.


SEE ALSO
========

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - the http-only download client.

`sr_post(1) <sr_post.1.rst>`_ - post announcements of specific files.

`sr_post(7) <sr_post.7.rst>`_ - the format of announcement messages.

`sr_report(1) <sr_report.1.rst>`_ - process report messages.

`sr_sarra(8) <sr_sarra.8.rst>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.rst>`_ - the directory watching daemon.
