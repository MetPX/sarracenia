
==============================
 AMQP - Primer for Sarracenia
==============================

This is a short but rather dense briefing to explain
the motivation for the use of AMQP by the MetPX-Sarracenia
data pump.  Sarracenia is essentially an AMQP application,
so some understanding AMQP is very helpful.

.. contents::

Scope
-----

AMQP is a vast and interesting topic in it's own right.  No attempt is made to explain 
all of it here. This brief just provides a little context, and introduces only 
background concepts needed to understand and/or use Sarracenia.  For more information 
on AMQP itself, a set of links is maintained at 
the `Metpx web site <http://metpx.sourceforge.net/#amqp>`_ but a search engine
will also reveal a wealth of material.


Why Use AMQP?
-------------

- open standard, multiple free implementations.
- low latency message passing.
- encourages asynchronous patterns/methods.
- language, protocol & vendor neutral.
- very reliable.
- robust adoption (next two sections as examples)
 

Where does AMQP Come From?
--------------------------

- Open International standard from financial world.
- Many proprietary similar systems exist, AMQP built to get away from lock-in. Standard is built with long experience of vendor messaging systems, and so quite mature.
- invariably used behind the scenes as a component in server-side processing, not user visible.
- many web companies (soundcloud) 
- seeing good adoption in monitoring and integration for HPC

Intel/Cray HPC Stack
--------------------

`Intel/Cray HPC stack <http://www.intel.com/content/www/us/en/high-performance-computing/aurora-fact-sheet.html>`_ 

.. image:: IntelHPCStack.png
    :scale: 50%
    :align: center


OpenStack
---------

`AMQP is the messaging technology chosen by the OpenStack cloud. <http://docs.openstack.org/developer/nova/rpc.html>`_


.. image:: OpenStackArch.png
    :scale: 70%
    :align: center


How to Adopt AMQP
-----------------

Adopting AMQP is more like adopting XML than it is like adopting FTP.  FTP interoperability 
is easy as choices are limited. With XML, however you get **more palette than painting.** Many 
different dialects, schema methods, etc...  XML will be valid and parse, but without 
additional standardization, data exchange remains uncertain.  For real interoperabiltiy, 
one must standardize specific dialects.  Examples:

     - RSS/Atom, 
     - Common Alerting Protocol (CAP)

AMQP brokers and the client software can connect and send messages, but without 
additional standardization, applications will not communicate.  AMQP calls 
those additional layers *applications*.  AMQP enables every conceivable message 
pattern, so a **well formed application is** built by eliminating features from 
consideration, **choosing the colours to use.**
Sarracenia is an applicaton of AMQP message passing to file transfer.

As CAP narrows XML, Sarracenia narrows the scope of AMQP. This narrowing is necessary to obtain a useful result: Interoperability.  Sarracenia conventions and formats are defined in:

   - `dd_post format man page <http://metpx.sf.net/dd_post.7.html>`_
   - `dd_log format man page <http://metpx.sf.net/dd_log.7.html>`_




Mapping AMQP Concepts to Sarracenia
-----------------------------------

.. image:: AMQP4Sarra.svg
    :scale: 50%
    :align: center

An AMQP Server is called a Broker. *Broker* is sometimes used to refer to the software,
other times server running the broker software (same confusion as *web server*.) In the above diagram, AMQP vocabulary is in Orange, and Sarracenia terms are in blue.
 
There are many different broker software implementations. We use rabbitmq. 
Not trying to be rabbitmq specific, but management functions differ between implementations.
So admin tasks require 'porting' while the main application elements do not.

*Queues* are usually taken care of transparently, but you need to know
   - A Consumer/subscriber creates a queue to receive messages.
   - Consumer queues are *bound* to exchanges (AMQP-speak) 

An *exchange* is a matchmaker between *publisher* and *consumer* queues.
   - A message arrives from a publisher. 
   - message goes to the exchange, is anyone interested in this message?
   - in a *topic based exchange*, the message topic provides the *exchange key*.
   - interested: compare message key to the bindings of *consumer queues*.
   - message is routed to interested *consumer queues*, or dropped if there aren't any.
   
- Multiple processes can share a *queue*, they just take turns removing messages from it.
   - This is used heavily for sr_sara and sr_subcribe multiple instances.

- *Queues* can be *durable*, so even if your subscription process dies, 
  if you come back in a reasonable time and you use the same queue, 
  you will not have missed any messages.

- How to Decide if Someone is Interested.
   - For Sarracenia, we use (AMQP standard) *topic based exchanges*.
   - Subscribers indicate what topics they are interested in, and the filtering occurs server/broker side.
   - Topics are just keywords separated by a dot. wildcards: # matches anything, * matches one word.
   - We create the topic hierarchy from the path name (mapping to AMQP syntax)
   - Resolution & syntax of server filtering is set by AMQP. (. separator, # and * wildcards)
   - Server side filtering is coarse, messages can be further filtered after download using regexp on the actual paths (the reject/accept directives.)

- topic prefix?  We start the topic tree with fixed fields
     - v02 the version/format of sarracenia messages.
     - post ... the message type, this is an announcement 
       of a file (or part of a file) being available.  


Sarracenia is an AMQP Application
---------------------------------

MetPX-Sarracenia is only a light wrapper/coating around AMQP.  

- A MetPX-Sarracenia pump is a python AMQP application that uses an (rabbitmq) 
  broker to co-ordinate SFTP and HTTP client data transfers, and accompanies a 
  web server (apache) and sftp server (openssh) on the same user-facing address.  

- Wherever reasonable, we use their terminology and syntax. 
  If someone knows AMQP, they understand. If not, they can research.

  - Users configure a *broker*, instead of a pump.
  - users explicitly can pick their *queue* names.
  - users set *subtopic*, 
  - topics with dot separator are minimally transformed, rather than encoded.
  - queue *durable*. 
  - we use *message headers* (AMQP-speak for key-value pairs) rather than encoding in JSON or some other payload format.

- reduce complexity through conventions.
   - use only one type of exchanges (Topic), take care of bindings.
   - naming conventions for exchanges and queues.
      - exchanges start with x. 
        - xs_Weather - the exchange for the source (amqp user) named Weather to post messages
        - xpublic -- exchange used for most subscribers.
      - queues start with q

- Internet resources are more useful and reduce our documentation burden.
- We write less code (exposing raw AMQP means less glue.)
- Less potential for bugs/ higher reliability.
- we make minimum number of choices/restrictions
- set sensible defaults.


Review
------

If you understood the rest of the document, this should make sense to you:

An AMQP broker is a server process that houses exchanges and queues used to route messages 
with very low latency.  A publisher sends messages to an exchange, while a consumer reads 
messages from their queue.  Queues are *bound* to exchanges.  Sarracenia just adds a broker
to a web server to provide fast notifications, and uses topic exchanges to enable 
consumers' server side filtering.  The topic tree is based on the file tree you can 
browse if you visit the corresponding web server.

