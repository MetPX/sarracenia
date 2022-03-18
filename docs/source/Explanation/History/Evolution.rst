=============================
History/Context of Sarracenia
=============================

**MetPX-Sarracenia** is a product of the Meteorological Product Exchange Project, 
originated in Environment Canada, but now run by Shared Services Canada on their 
behalf. The project started in 2004, with the goal of providing a free stack that 
implements World Meteorological Organization standard real-time data exchange, 
and also adjacent needs.  `Sundew <https://github.com/MetPX/Sundew>`_ was the 
first generation WMO 386 (GTS) switch.

In 2007, when MetPX was originally open sourced, the staff responsible were part of
Environment Canada. In honour of the Species At Risk Act (SARA), to highlight the plight
of disappearing species which are not furry (the furry ones get all the attention) and
because search engines will find references to names which are more unusual more easily,
the original MetPX WMO switch was named after a carnivorous plant on the Species At
Risk Registry: The *Thread-leaved Sundew*.

Sundew, the WMO switch, also needed compatibility with existing internal transfer 
mechanisms based heavily on FTP. It worked, but the GTS itself is obsolete in many 
deep ways, and work started in 2009 extending Sundew to leverage new technologies, 
such as message queueing protocols, starting in 2008. Versions of Sundew are 
generally labelled < 1.0

The initial prototypes of Sarracenia leveraged MetPX Sundew, Sarracenia's ancestor. 
Sundew plugins were developed to create announcements for files delivered by Sundew,
and Dd_subscribe was initially developed as a download client for **dd.weather.gc.ca**, an
Environment Canada website where a wide variety of meteorological products are made
available to the public. It is from the name of this site that the Sarracenia
suite takes the dd\_ prefix for its tools. The initial version was deployed in
2013 on an experimental basis as dd_subscribe. 

dd_subscribe Renaming
---------------------

The new project (MetPX-Sarracenia) has many components, is used for more than
distribution, and more than one website, and causes confusion for sysadmins thinking
it is associated with the dd(1) command (to convert and copy files).  So, components
were switched to use the sr\_ prefix. The following year, support of 
checksums was added, and in the fall of 2015, the feeds were updated to v02.

We eventually ran into the limits of this extension approach, and in 2015 we 
started `Sarracenia <https://github.com/MetPX/Sarracenia>`_
as a ground-up second generation replacement, unburdened by strict legacy GTS compatibility.
Sarracenia (version 2) was initially a prototype, and many changes of many kinds occurred during it's lifetime.
It is still (in 2022) the only version operationally deployed. It went through three changes in operational
message format (exp, v00, and v02.) It supports hundreds of thousands file transfers per hour 24/7
in Canada.

Where Sundew supports a wide variety of file formats, protocols, and conventions
specific to the real-time meteorology, Sarracenia takes a step further away from
specific applications and is a ruthlessly generic tree replication engine, which
should allow it to be used in other domains. The initial prototype client, dd_subscribe,
in use since 2013, was sort of a logical dead end. A path forward was described
with the `Sarracenia in 10 Minutes <https://www.youtube.com/watch?v=G47DRwzwckk>`_
in November 2015, which led to dd_subscribe's replacement in 2016 by the full blown 
Sarracenia package, with all components necessary for production as well as 
consumption of file trees.

The organization behind MetPX has moved to Shared Services Canada in 2011, but when
it came time to name a new module, we kept with a theme of carnivorous plants, and
chose another one indigenous to some parts of Canada: *Sarracenia*, a variety
of insectivorous pitcher plants. We like plants that eat meat!

Sarracenia was initially called v2, as in the second data pumping architecture
in the MetPX project, (v1 being Sundew.) a good timeline of deployments/acheivements
is `here <mesh_gts.html#Maturity>`_. While it proved very promising, 
worked quite well, Over the years a number of limitations with the existing 
implementation became clear:

* The poor support for python developers. v2 code is not at all idiomatic Python.
* the odd plugin logic, with poor error reporting.
* The inability to process groups of messages.
* The inability to add other queueing protocols (limited to rabbitmq/AMQP.)
* Difficulty of adding transfer protocols.

In 2020, Development began on `Version 3 <../Contribution/v03.html>`_, now
dubbed Sr3. Sr3 is about 30% less code that v2, offers a much improved API,
and supports additional message protocols, rather than just rabbitmq.

Fewer Klocs, Better klocs
-------------------------

+-------+----------------------------+------------+---------------------------------------------------+
|                        History of Data Pumping Applications for Environment Canada                  |
+-------+----------------------------+------------+---------------------------------------------------+
| Era   | Application                | Code size  | Features                                          |
+-------+----------------------------+------------+---------------------------------------------------+
| 1980s | Tandem, PDS (domestic GTS) |  500kloc   | X.25, WMO Socket, AM Socket, FTP (push only)      |
+-------+----------------------------+------------+---------------------------------------------------+
| 2000s | Sundew                     |   30kloc   | WMO Socket/TCP, FTP, SFTP (push only)             |
+-------+----------------------------+------------+---------------------------------------------------+
| 2010s | Sarracenia v2              |   25kloc   | AMQP, HTTP, SFTP, FTP (pub/sub and push)          |
+-------+----------------------------+------------+---------------------------------------------------+
| 2020s | Sarracenia v3 (sr3)        |   15kloc   | AMQP, MQTT, HTTP, SFTP, API (pub/sub and push)    |
+-------+----------------------------+------------+---------------------------------------------------+


Deployments/Use Cases
---------------------

Deployment status in 2015: `Sarracenia in 10 Minutes Video (5:26 in) <https://www.youtube.com/watch?v=G47DRwzwckk&t=326s>`_

Deployment status in 2018: `Deployments as of January 2018 <deployment_2018.html>`_


