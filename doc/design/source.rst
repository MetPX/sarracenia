
==============
 Data Sources
==============

---------------------------------------------------
Injecting Data into a MetPX-Sarracenia Pump Network
---------------------------------------------------

.. contents::

MetPX-Sarracenia data pumps are most efficient when processes directly communicate.  
Regardless of how it is done, injecting data means telling the pump where the data 
is so that it can be forwarded by the pump.   In the simplest case, it takes the 
data from your account, wherever you have it, providing you give it permission.  
we describe that case first.

SFTP Injection
--------------

Using the sr_post(1) command directly is the most straightforward way to inject data
into the pump network.  To use sr_post, you have to know:

- the name of the local broker: ( say: ddsr.cmc.ec.gc.ca. )
- your authentication info for that broker ( say: user=rnd : password=rndpw )
- your own server name. (say: grumpy.cmc.ec.gc.ca )
- your own user name on your server (say: peter)

Lets say you want the pump to access peter's account via SFTP.  Then you need
to take the pumps public key, and place it in peter's .ssh/authorized_keys.
On the server you are using (*grumpy*), one needs to do something like this::

  wget http://ddsr.cmc.ec.gca/config/pump.pub >>~peter/.ssh/authorized_keys

This will enable the pump to access peter's account on grumpy using his private key. 
So assuming one is logged in to Peter's account on grumpy, one can store the broker
credentials safely:

  echo 'amqps://rnd:rndpw@ddsr.cmc.ec.gc.ca' >> ~/.config/sarra/credentials.conf:


.. Note::

  Passwords are always stored in the credentials.conf file, never
  in other files.

Now we just need to figure out where to send the file to.  
Aim a browser at:

http://ddsr.cmc.ec.gc.ca/doc/Network.txt (and/or html)

+--------------------+--------------------------------------------------------------+
| DDIEDM             | Data Distribution Internal, Edmonton                         |
|                    | Western Data Dissemination hub for Environment Canada        |
|                    | Meteorological Service, 24x7 operations                      |
|                    | Contact: SSC.DataInterchange-EchangeDonnees.SSC@canada.ca    |
|                    | 1-514-421-9999                                               |
+--------------------+--------------------------------------------------------------+
| DDIDOR             | Data Distribution Internal, Dorval                           |
|                    | Eastern Data Dissemination hub for Environment Canada        |
|                    | Meteorological Service, 24x7 operations                      |
|                    | Contact: SSC.DataInterchange-EchangeDonnees.SSC@canada.ca    |
|                    | 1-514-421-9999                                               |
+--------------------+--------------------------------------------------------------+
| ARCHPC             | Central File Server in HPC Dorval.                           |
|                    |                                                              |
|                    | Contact: SSC.BigData-GrosDonnées.SPC@canada.ca               |
|                    | 1-514-421-9999                                               |
+--------------------+--------------------------------------------------------------+
| ENVDATACQ          | All locations required to support Acquitision of Weather,    |
|                    | Climate, Environment data.                                   |
|                    | GEDS_                                                        |
+--------------------+--------------------------------------------------------------+
| OPWXPROD           | All locations required to support Operational Weather        |
|                    | Prediction.                                                  |
|                    | GEDS_                                                        |
+--------------------+--------------------------------------------------------------+
| WXDISSEM           | Weather dissemination, such as weater.gc.ca, dd.weather...   |
|                    | EC.NIRT-ITRN.EC@canada.ca                                    |
|                    | GEDS_                                                        |
+--------------------+--------------------------------------------------------------+
| NRCGAT             | National Research Council Gatineau DC                        |
|                    | Contact: NRC.Helpdesk-BureaudeService.CNRC@canada.ca         |
|                    | 1-613-421-9999                                               |
+--------------------+--------------------------------------------------------------+
| SCIHPC             | The site file systems of the science.gc.ca domain.           |
|                    | Provides direct delivery into Government HPC environment.    |
|                    | Contact: SSC.HPCOptimization-OptimisationCHP.SSC@canada.ca   |
+--------------------+--------------------------------------------------------------+
| BROADCAST          | Send to all switches. Probably best to avoid.                |
|                    | All contacts for all of the above.                           |
|                    | GEDS_                                                        |
+--------------------+--------------------------------------------------------------+

.. _GEDS: http://sage-geds.tpsgc-pwgsc.gc.ca/en/GEDS?pgid=015&dn=CN%3Dpeter.silva%40canada.ca%2COU%3DDI-ED%2COU%3DESIOS-SESES%2COU%3DSC-SI%2COU%3DSMDC-GSCD%2COU%3DSSC-SPC%2CO%3DGC%2CC%3DCA


.. notes:
   FIXME:
   the network.html file... suggest a table in (and accompanying réseau.html)
   not going structured XML because... ok what is the structure of the XML?
   what do we put contacts in?  is there a standard that covers GEDS links?
   what types of ´contact´ will be relevant in future (perhaps ´phone´ isn´t)
   skype?  webex? beehive chat?  Need to consider visibility.
   Network.html on the external facing pumps will likely look different from
   the internal ones.
 
   I´m just making up these destinations to give an idea of the kinds of things
   that should be in there.  I don´t want to start a project to define the
   format that will be readable on all platforms as well as semantic so easily
   machine digestible.  But perhaps we should, or maybe later?
 
   These names correspond to business functions, not the machines that implement
   them.  The names will be implemented as aliases on switches.
   ALLCAPS is just a convention to avoid confusion with hostnames, which are 
   generally lowercase, similar to C convention for macros. 


Lets assume the places you want to send to are:  DDIEDM,DDIDOR,ARCHPC. 
so the sr_post command will look like this:

  sr_post -to DDIEDM,DDIDOR,ARCHPC \
          -broker amqps://rnd@ddsr.cmc.ec.gc.ca/  \
          sftp://peter@grumpy/treefrog/frog.dna

.. note::
   FIXME: unix convention is to place options before arguments.
   man page seems to indicate arguments before options (url is first?)
   probably need to review sr_post man page to clarify.


If you find you are using the same arguments all the time,
it might be convenient to store them in a central configuration::
  
  blacklab% cat >~/.config/sarra/default.conf <<EOT

  broker amqps://rnd@ddsr.cmc.ec.gc.ca/
  to DDIEDM,DDIDOR,ARCHPC
  base_url sftp://peter@grumpy

  EOT

So now the command line for sr_post is just the url to for ddsr to retrieve the
file on grumpy:

  sr_post treefrog/frog.dna

Either way, the command asks ddsr to retrieve the treefrog/frog.dna file by logging 
in to grumpy as peter (using the pump's private key.) to retrieve it, and posting it 
on the switch, for forwarding to the other pump destinations.

similar to sr_subscribe, one can also place configuration files in an sr_post specific
directory:: 

  blacklab% cat >~/.config/sarra/sr_post/dissem.conf <<EOT

  broker amqps://rnd@ddsr.cmc.ec.gc.ca/
  to DDIEDM,DDIDOR,ARCHPC
  base_url sftp://peter@grumpy

  EOT

and then:

  sr_post -c dissem treefrog/frog.dna

If there are different varieties of posting used, configurations can be saved for each
one. 

.. note::
   FIXME: Need to do a real example. this made up stuff isn´t sufficiently helpful.
   FIXME: sr_post does not accept config files right now, says the man page.  True/False?
   sr_post command lines can be a lot simpler if it did.
   FIXME: I invented base_url, does not exist.  If it did, is that the right thing?
   should it have another name?

sr_post typically returns immediately as its only job is to advice the pump of the availability
of files.  The files are not transferred when sr_post returns, so one should note delete files 
after posting without being sure the pump actually picked them up. 

.. NOTE::

  sftp is perhaps the simplest for the user to implement and understand, but it is also
  the most costly in terms of CPU on the server.  All of the work of data transfer is
  done at the python application level, when sftp acquisition is done, which isn´t great.

  a lower cpu version would be for the client to send somehow (sftp?) and then just
  tell where the file is on the pump (basically the sr_sender2 version.)

Note that this example used sftp, but if the file is available on a local web site,
then http work work, or if the data pump and the source server share a file system,
then even a file url could work.  


HTTP Injection
--------------

If we take a similar case, but in this case there is some http accessible space,
the steps are the same or even simpler if no authentication is required for the pump
to acquire the data.  One needs to install a web server of some kind.  

As an example, for lighttpd, the following could be a complete configuration:: 

  cat >/etc/lighttpd/lighttpd.conf <<EOT

  server.modules = ()

  dir-listing.activate = "enable"
  
  server.document-root        = "/var/www"
  server.upload-dirs          = ( "/var/cache/lighttpd/uploads" )
  server.errorlog             = "/var/log/lighttpd/error.log"
  server.pid-file             = "/var/run/lighttpd.pid"
  server.username             = "www-data"
  server.groupname            = "www-data"
  server.port                 = 80
  
  
  index-file.names            = ( "index.php", "index.html", "index.lighttpd.html" )
  url.access-deny             = ( "~", ".inc" )
  
  # default listening port for IPv6 falls back to the IPv4 port
  ## Use ipv6 if available
  include_shell "/usr/share/lighttpd/use-ipv6.pl " + server.port
  include_shell "/usr/share/lighttpd/create-mime.assign.pl"
  include_shell "/usr/share/lighttpd/include-conf-enabled.pl"
  
  EOT

  service lighttpd start

This configuration will show all files under /var/www as folders, running under
the www-data users.  Data posted in such directories must be readable to the www-data
user, to allow the web server to read it.  The server running the web server
is called *blacklab*, and the user on the server is *peter*.  running as peter on blacklab,
a directory is created under /var/www/project/outgoing, that is writable by peter,
which results in a configuration like so::

  cat >>~/.config/sarra/watch/project.conf <<EOT

  broker amqp://feeder@localhost/
  url http://blacklab/
  document_root /var/www/project/outgoing
  to blacklab

  EOT

then a watch is started:

  sr_watch project start

While sr_watch is running, any time a file is created in the *document_root* directory, 
it will be announced to the pump (on localhost, ie. the server blacklab itself.)

 cp frog.dna  /var/www/project/outgoing
  
This triggers a post to the pump.  Any subscribers will then be able to download
the file.

.. note:: 
   FIXME. too much broken for now to really run this easily...
   so creating real demo is deferred.   







Log Messages
------------

If the sr_post worked, that means the pump accepted to take a look at your file.
To find out where your data goes to afterward , one needs to examine source
log messages. It is also important to note that the initial pump, or any other pump 
downstream, may refuse to forward your data for various reasons, that will only
be reported to the source in these log messages.  

To view source log messages, the sr_log command is just a version of sr_subscribe, with the
same options where they make sense. If the configuration file (~/.config/sarra/default.conf) 
is set up, then all that is needed is::

  sr_log

to view log messages indicating what has happenned to the items inserted into the 
network from the same pump using that account (rnd, in the example.) One can trigger 
arbitrary post processing of log messages by using on_message plugin.

.. note::
   FIXME: need some examples.


Sending a File to the Pump
--------------------------

Sometimes it is easier to send the file to the pump, rather than having the pump
pick it up.  Use sr_sender2 to do that. With sr_sender2, the source needs an account 
on the data pump and preferably to have keys stored there.  say rnd.pub.

place the source server and account public key in the ~/.ssh/authorized_keys on the
data pump. so then one adds the necessary credentials to the sr\_ configuration::

  cat >>~/.config/sarra/credentials.conf <<EOT

  sftp://rnd:rndpw@ddsr.cmc.ec.gc.ca/

  EOT

Also need to set up the sr_sender2 configuration::

  blacklab% cat >~/.config/sarra/sr_sender2/dissem.conf <<EOT

  broker amqps://rnd@ddsr.cmc.ec.gc.ca/
  to DDIEDM,DDIDOR,ARCHPC
  base_url sftp://rnd@ddsr.cmc.ec.gc.ca/
  instances 3

  EOT


then do:

  sr_sender2 treefrog/frog.dna

This will result in an sftp being initiated to ddsr, and posting of the file
on ddsr with a file: url in the xs_rnd exchange.   

.. note::
   FIXME: major magic here, as the sender doesn´t know the absolute path
   of the files on the remote pump, how does it compute the file: announcement?

   FIXME: so it shows up on the pump owned by rnd, we likely need to chown
   it to be dd_adm, or something.   ...
   
If the file is large, then there will be several posts of each part of 
the file as it is delivered.  The *instances* option can be used to have
the send proceed in parallel.  In the example above, three concurrent streams
will be used to send the file, provided it is large enough to be sent
in three or more parts.


Large Files
-----------

Larger files are not sent as a single block.  They are sent in parts, and each
part is fingerprinted, so that when files are updated, unchanged portions are
not sent again.  There is a default threshold built into the sr\_ commands, above
which partitioned announcements will be done by default.  This threshold can
be adjusted to taste using the *part_threshold* option.

Different pumps along the route may have different maximum part sizes.  To
traverse a given path, the part must be no larger than the threshold setting
of all the intervening pumps.  A pump will send the source an erroe log
message if it refuses to forward a file.

As each part is announced, so there is a corresponding log message for
each part.  This allows senders to monitor progress of delivery of large
files.

.. note::
   FIXME: part threshold not implemented, currently one has to manually 
   program part headers into dd_post, requiring detailed understanding
   of protocol.

   Do we need to explain in-place vs. not? I think they just naturally
   arise out of how routing goes.  This is perhaps not right in the
   protocol, where it should be the sarra that understands that no
   re-assembly is possible, sender doesn't, so the sarra on Re-Advertiseing
   advertises 'p' instead of 'i', but user does not know or care.

   conclusion: this is usually transparent, just admin's need to know
   should go there. 

Fingerprints
------------

Every piece of data injected into the pumping network needs to have a unique fingerprint,
The fingerprinting algorithm to apply to such data needs to be chosen by the data source. 
This is used by consumers of the data, which could be other pumps, or end subscribers,
to determine if they already have the data or not. Normally, the 'd' algorithm is used,
which applies the well-known Message-Digest 5 (md5sum) algorithm to the data in the file.

When there is one origin for data, this algorithm works well. For high availability, 
production chains will operate in parallel, preferably with no communication between
them.  Items produced by independent chains will naturally have different processing
time and log stamps and serial numbers applied, so the same data processed through 
different chains will not be identical at the binary level.   For products produced 
by different production chains to be accepted as equivalent, they need to have 
the same fingerprint.

One solution for that case is, if the two processing chains will produce data with 
the same name, to checksum based on the file name instead of the data, this is called 'n'.  
In many cases, the names themselves are production chain dependent, so a custom 
algorithm is needed. If a custom algorithm is chosen, it needs to be published on
the network::

 http://dd.cmc.ec.gc.ca/config/msc-radar/sums/

    u.py

So downstream clients can obtain and apply the same algorithm to compare announcements
from multiple sources.

.. note::
   FIXME:
   science fiction again:  no such config directories exist yet. no means to update them.
   search path for checksum algos?  built-in,system-wide,per-source?

   also, if each source defines their own algorithm, then they need to pick the same one
   (with the same name) in order to have a match. 
   FIXME: verify that fingerprint verification includes matching the algorithm as well as value.

   FIXME:  not needed at the beginning, but likely at some point.
   in the mean time, we just talk to people and include their algorithms in the package.

.. NOTE::

  Fingerprint methods that are based on the name, rather than the actual data, 
  will cause the entire file to be re-sent when they are updated.  


Labelling Interesting Flows
---------------------------

Those injecting data have the freeform attribute 'flow' available to assign an arbitrary label
to a message, like a transaction id, to be able to follow a particular file though the network.

  
Advanced Posting
----------------

What if there is some piece of metadata that a data source has chosen for some reason not to
include in the filename hierarchy?  How can data consumers know that information without having
to download the file in order to determine that it is uninteresting.  A typical example would be
weather warnings.  The file names might include weather warnings for an entire country.  If consumers
are only interested in downloading warnings that are local to them, then, a data source could
use the on_post hook in order to add additional headers to the message.

In order to use the additional headers, subscribers would need to implement and on_message hook on their
end, which would examine the non-standard header, and perhaps decide to avoid retrieving the file by
returning false from the hook script.

.. note::
  with great flexibility comes great potential for harm.  the path names should include as much information
  as possible as sarracenia is built to optimize routing using them.  Additional meta-data should be used
  to supplement, rather than replace, the built-in routing. 


Efficiency Considerations 
~~~~~~~~~~~~~~~~~~~~~~~~~

It is not recommended to put overly complex logic in the hook scripts, as they execute synchronously with
post and receive operations.  Note that the use of built-in facilities of AMQP (headers) is done to
explicitly be as efficient as possible.  As an extreme example, including encoded XML into messages
will not affect performance slightly, it will slow processing by orders of magnitude that one will not
be able to compensate for with multiple instances (the penaly is simply too large to overcome.)

Consider, for example, Common Alerting Protocol (CAP) messages for weather alerts.  These alerts routinely 
exceed 100 KBytes in size, wheras a sarracenia message is on the order of 200 bytes.  The sarracenia messages
go to many more recipients than the alert: anyone considering a alert, as oppposed to just the ones
the subscriber is actually interested in, and this metadata will also be included in the log messages,
and so replicated in many additional locations where the data itself will not be present.

Including all the information that is in the CAP would mean just in terms of pure transport 500 times 
more capacity used for a single message.  When there are many millions of messages to transfer, this adds up.
Only minimal information required by the subscriber to make the decision to download or not should be 
added to the message. this example has ignored 

.. note::
  FIXME: I guess we should start making some benchmarks soon.
  Need to establish a baseline...  What is meaningful?
  How many messages per second a subscriber can download?  


