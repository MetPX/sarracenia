
==============================
Delivery Completion (inflight)
==============================

Failing to properly set file completion protocols is a common source of intermittent and
difficult-to-diagnose file transfer issues. For reliable file transfers, it is 
critical that both the sender and receiver agree on how to represent a file that isn't complete.
The *inflight* option (meaning a file is *in flight* between the sender and the receiver) supports
many protocols appropriate for different situations:

Inflight Table
--------------

+--------------------------------------------------------------------------------------------+
|                                                                                            |
|               Delivery Completion Protocols (in Order of Preference)                       |
|                                                                                            |
+-------------+---------------------------------------+--------------------------------------+
| Method      | Description                           | Application                          |
+=============+=======================================+======================================+
|             |File sent with right name.             |Sending to Sarracenia, and            |
|   NONE      |Send `sr3_post(7) <sr3_post.7.rst>`_   |post only when file is complete       |
|             |by AMQP after file is complete.        |                                      |
|             |                                       |(Best when available)                 |
|             | - fewer round trips (no renames)      | - Default on sr_sarra.               |
|             | - least overhead / highest speed      | - Default on sr_subscribe and sender |
|             |                                       |   when post_broker is set.           |
+-------------+---------------------------------------+--------------------------------------+
|             |Files transferred with a *.tmp* suffix.|sending to most other systems         |
| .tmp        |When complete, renamed without suffix. |(.tmp support built-in)               |
| (Suffix)    |Actual suffix is settable.             |Use to send to Sundew                 |
|             |                                       |                                      |
|             | - requires extra round trips for      |(usually a good choice)               |
|             |   rename (a little slower)            | - default when no post broker set    |
+-------------+---------------------------------------+--------------------------------------+
|             |Files transferred to a subdir or dir   |sending to some other systems         |
| tmp/        |When complete, renamed to parent dir.  |                                      |
| (subdir)    |Actual subdir is settable.             |                                      |
| /dir        |                                       |                                      |
|             |same performance as Suffix method.     |                                      |
+-------------+---------------------------------------+--------------------------------------+
|             |Use Linux convention to *hide* files.  |Sending to systems that               |
| .           |Prefix names with '.'                  |do not support suffix.                |
| (Prefix)    |that need that. (compatibility)        |                                      |
|             |same performance as Suffix method.     |                                      |
+-------------+---------------------------------------+--------------------------------------+
|             |Minimum age (modification time)        |Last choice                           |
|  number     |of the file before it is considered    |guaranteed delay added                |
|  (mtime)    |complete.                              |                                      |
|             |                                       |Receiving from uncooperative          |
|             |Adds delay in every transfer.          |sources.                              |
|             |Vulnerable to network failures.        |                                      |
|             |Vulnerable to clock skew.              |(ok choice with PDS)                  |
+-------------+---------------------------------------+--------------------------------------+

By default ( when no *inflight* option is given ), if the post_broker is set, then a value of NONE
is used because it is assumed that it is delivering to another broker. If no post_broker
is set, the value of '.tmp' is assumed as the best option.

NOTES:
 
  On versions of sr_sender prior to 2.18, the default was NONE, but was documented as '.tmp'
  To ensure compatibility with later versions, it is likely better to explicitly write
  the *inflight* setting.
 
  *inflight* was renamed from the old *lock* option in January 2017. For compatibility with
  older versions, can use *lock*, but name is deprecated.
  
  The old *PDS* software (which predates MetPX Sundew) only supports FTP. The completion protocol 
  used by *PDS* was to send the file with permission 000 initially, and then chmod it to a 
  readable file. This cannot be implemented with SFTP protocol, and is not supported at all
  by Sarracenia.


Frequent Configuration Errors
-----------------------------

**Setting NONE when sending to Sundew.**

   The proper setting here is '.tmp'.  Without it, almost all files will get through correctly,
   but incomplete files will occasionally picked up by Sundew.  

**Using mtime method to receive from Sundew or Sarracenia:**

   Using mtime is last resort. This approach injects delay and should only be used when one 
   has no influence to have the other end of the transfer use a better method. 
 
   mtime is vulnerable to systems whose clocks differ (causing incomplete files to be picked up.)

   mtime is vulnerable to slow transfers, where incomplete files can be picked up because of a 
   networking issue interrupting or delaying transfers. 

   Sources may not to include mtime data in their posts ( *timeCopy* option on post.)


**Setting NONE when delivering to non-Sarracenia destination.**

   NONE is to be used when there is some other means to figure out if a file is delivered.
   For example, when sending to another pump, the sender will post the notification message to 
   the destination after the file is complete, so there is no danger of it being 
   picked up early.

   When used inappropriately, there will occasionally be incomplete files delivered.


