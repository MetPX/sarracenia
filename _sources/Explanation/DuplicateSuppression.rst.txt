
Duplicate Suppression
=====================

When forwarding products in networks, one needs to avoid *storms* or loops of data transmission,
where the same data circulates infinitely in the network, (for example: A sends a file to B, B sends it to C,
C sends it back to A. If A sends it to B again, we have an infinite loop or *storm* if the volume is large enough. )

Another main feature of mission critical processing is having multiple systems produce the same data, or 
hot backup systems being available. If the strategy is to have both production and backup systems both
running at once, one will always have multiple copies of the same data being in the network, with the 
backup being blocked at some point. The potential for loops, or sending out redundant copies of data, 
consuming excessive bandwidth and processing power, is high.

It turns out that duplicate suppression is deceptively complex. There is not one method of
duplicate suppression that is appropriate for all cases, so sr3 allows for customization.
The *sarracenia.flowcb.nodupe* module implements duplicate suppression by default but can be used
for more flexible filtering.

Duplicate suppression must:
  * derive a notification message key.
  * if a notification message has been received with the same key and and path, then it is a duplicate.

Duplicates are dropped to avoid further processing.

A notification message key is preferably derived from the *Identity* field of the notification
message. If the producer does not provide an identity checksum, algorithms may fall
back on other metadata: *mtime*, *size*, *pubTime.* Since pubTime is a mandatory
field, a key can always be derived, but it's effectiveness in a particular use case
is not assured. (the sarracenia.flowcb.nodupe.NoDupe.deriveKey(self,msg) helper routine 
provides a standard key, given a message.)

in all methods, one can turn on duplicate suppression with the following option
in the config file::

   nodupe_ttl 300|off|on

When supplied a number, that indicates the lifetime, in seconds of entries in the 
duplicate suppresion memory (e.g. 300 seconds == 5 minutes.)



Standard (path and data oriented)
---------------------------------


**method**: when products have the same key and path, they are duplicates.

Two routes can receive the same product, with the same relative path. In normal processing,
the products should be identical, and *Identity* checksums for it should be the same,



FIXME: the normal case when multiple intervening pumps.


Data Oriented
-------------

**method**: when products the same key, they are duplicates.

in the config file either::
 

    nodupe_basis data

or::

    flowcb_prepend sarracenia.flowcb.nodupe.data.Data

overrides the standard duplicate suppression key generation to include only the data 
checksum. This module adjusts the *path* field that the standard duplicateion suppression field uses.
The *flowcb_prepend* directive ensures that it is called before the built-in duplicate suppression.

products that are the same should have identical checksums, regardless of path. Used when
multiple sources produce the same product. (Note: all zero-length files are identical,
it could be that products with unrelated purpose have identical content. scoping is
usually important when this option is applied.)


Name Oriented
-------------

**method**: when products have the same file name, they are duplicates.

In the config file, either::

    nodupe_basis data

or::

    flowcb_prepend sarracenia.flowcb.nodupe.name.Name

Override the standard duplicate suppression key generation to use only the file name.

When multiple sources produce a product, but the result is not binary identical, and no
appropriate Identity method is available, then then one needs a different approach.
Since the two sources are not, generally, synchronized, 

URP
~~~

Radar production is done, in one case, on many different (6? ) operational servers producing
"identical" products. They are identical in the sense that they are based on the same
input, and have the same semantic meaning, but details of processing mean that none of
the products are binary identical.  

The different servers are used as different "sources" so the relative path of products
from the different sources will not be the same, but every product that has the same
file name is interchangeable ("identical" for our purposes.) So using the file name
is correct in this case.

 
Files That Change Too Often (mdelaylatest)
------------------------------------------

**method**: wait until file is x seconds old before forwarding.  

NOTE: This is an additional filter to duplicate suppression, and the above 
methods can be used in conjunction with mdelaylatest. this filter is ideally
applied before duplicate suppression to reduce the database size. 

In the configuration file::

    mdelay 30
    flowcb_prepend sarracenia.flowcb.mdelaylatest.MDelayLatest

Delay all files by 30 seconds, if multiple versions are produced before the file
is 30 seconds old, then only send the last one, when it is 30 seconds old.

use case:
In some cases, there are data sources that overwrite files very often.
If the files are large (take a long time to copy) or there is queuing (the subscriber
is some time behind the producer.), an algorithm could overwrite a file, or 
append to it, three or four times before having a "final" version that will last some time. 

if network has a propagation delay that is longer than the overwrite period, then by 
the time the consumer requests the file, it will be different (potentially causing checksum mismatches.)
or, if it is fast enough, copying a file that will not last more than a few seconds 
could be a waste of bandwidth and processing.


Weatheroffice citypages
~~~~~~~~~~~~~~~~~~~~~~~

( https://hpfx.collab.science.gc.ca/YYYYMMDD/WXO-DD/citypage_weather/ )

The citypages are a compound product (derived from many separate upstream products.)
The script that creates the citypage products seems to write a header, then some records,
then at the very end, a footer.  there were many cases of files being transmitted
as *invalid xml* because the footer is missing, leaving some XML entities incomplete.  
One must wait until the script has finished writing the file before creating a notification message.

HPC mirrorring
~~~~~~~~~~~~~~

In the high speed mirroring of data between high performance computing clusters, 
shell scripts often spend time appending records to files, perhaps hundreds of times per second.
Once the script is complete, the file becomes read-only for consumers.  It is not useful
to transmit these intermediate values. A 100 byte file monitored using the shim library
or an sr_watch, could be modified hundreds of times, causing a copy for every modification potentially
triggering hundreds of copies. It is better to wait for the end of the update process,
for the file to be quiescent, before posting a notification message.


Files That are Too Old
----------------------

**method**: files that are too old are dropped.

in the configuration file::

    fileAgeMax 600

Files which are older than 600 seconds (10 minutes) will not be considerred for transfer.

This is usually used with polls that have very long lasting directories on a remote 
server. example: a remote server has a permanent database of remote files.

It is often the case that nodupe_ttl should be greater than nodupe_fileAgeMax to prevent
files from aging out of the cache before they are considered "too old" and then being 
(erroneously) re-ingested.  A warning message is emitted if this is the case in a poll
on startup.


Roll Your Own
-------------

In the configuration file::

    your_settings 
    flowcb_prepend your_class.YourClass

If none of the built-in methods of duplicate suppression work for your use case, you can
subclass sarracenia.flowcb.nodupe and derive keys in a different way. See the 
sarracenia.flowcb.nodupe.name and sarracenia.flowcb.nodupe.data classes for examples of
how to do so.

One can also implement a filter that sets the *nodupe_override* field in the message::

  msg['nodupe_override] = { 'key': your_key, 'path': your_path }

and the standard duplicate suppression method will use the provided key and value.
There is also a helper function available in the nodupe class::

  def deriveKey(self, msg) --> str

which will look at the fields in the message and derive the *normal* key that would be 
generated for a message, which you can then modify if only looking for a small change.


