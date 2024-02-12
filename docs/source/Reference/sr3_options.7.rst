
===========
SR3 OPTIONS
===========

------------------------------
SR3 Configuration File Format
------------------------------

:manual section: 7
:Date: |today|
:Version: |release|
:Manual group: MetPX-Sarracenia

SYNOPSIS
========

::

  name value
  name value for use
  name value_${substitution}
  .
  .
  .     

DESCRIPTION
===========

Options are placed in configuration files, one per line, in the form::

    option <value>

For example::

    debug true
    debug

sets the *debug* option to enable more verbose logging. If no value is specified,
the value true is implicit, so the above are equivalent. A second example::

  broker amqps://anonymous@dd.weather.gc.ca

In the above example, *broker* is the option keyword, and the rest of the line is the
value assigned to the setting. Configuration files are a sequence of settings, one per line.
Note:

* the files are read from top to bottom, most importantly for *directory*, *strip*, *mirror*,
  and *flatten* options apply to *accept* clauses that occur after them in the file.

* The forward slash (/) as the path separator in Sarracenia configuration files on all
  operating systems. Use of the backslash character as a path separator (as used in the
  cmd shell on Windows) may not work properly. When files are read on Windows, the path
  separator is immediately converted to the forward slash, so all pattern matching,
  in accept, reject, strip etc... directives should use forward slashes when a path
  separator is needed.

* **#** is the prefix for lines of non-functional descriptions of configurations, or comments.
  Same as shell and/or python scripts.

* **All options are case sensitive.**  **Debug** is not the same as **debug** nor **DEBUG**.
  Those are three different options (two of which do not exist and will have no effect,
  but will generate an ´unknown option' warning).


The file has an inherent order, in that it is read from top to bottom, so options
set on one line often affect later lines::

   mirror off
   directory /data/just_flat_files_here_please
   accept .*flatones.*

   mirror on
   directory /data/fully_mirrored
   accept .* 

In the above snippet the *mirror* setting is off, then the directoy value is set,
so files whose name includes *flatones* will all be place in the */data/just_flat_files_here_please* 
directory. For files which don't have that name, they will not be picked up
by the first accept, and so the mirror on, and the new directory setting will tak over,
and those other files will land in /data/fully_mirrored. A second example:

sequence #1::

  reject .*\.gif
  accept .*


sequence #2::

  accept .*
  reject .*\.gif


.. note::
   FIXME: does this match only files ending in 'gif' or should we add a $ to it?
   will it match something like .gif2 ? is there an assumed .* at the end?


In sequence #1, all files ending in 'gif' are rejected. In sequence #2, the
accept .* (which accepts everything) is encountered before the reject statement,
so the reject has no effect. Some options have global scope, rather than being
interpreted in order. For thoses cases, the last declaration overrides the
ones higher in the file..

Variables
=========

One can include substitutions in option values. They are represented by ${name}.
The name can be an ordinary environment variable, or a chosen from a number of 
built-in ones. For example::

        varTimeOffset -5m
        directory /mylocaldirectory/${%Y%m%d}/mydailies
        accept    .*observations.*

        rename hoho.${%o-1h%Y%m%d_%H%M%S.%f}.csv

In the last example above, the *varTimeOffset* will modify the evaluation of YYYYMMDD to be 5m in the past.
In the rename option, the time to be substituted is one hour in the past.
One can also specify variable substitutions to be performed on arguments to the directory
option, with the use of *${..}* notation:

* %...     - a `datetime.strftime() <https://docs.python.org/3/library/datetime.html#datetime.date.strftime>`_ 

  * compatible date/time formatting string augmented by an offset duration suffix (o- for in the past, o+ for in the future)
  * example (complex date):  ${%Y/%m/%d_%Hh%M:%S.%f} --> 2022/12/04_17h36:34.014412 
  * example (add offset):  ${%o-1h%Y/%m/%d_%Hh%M:%S.%f} --> 2022/12/04_16h36:34.014412 

* time offset begin a strtime pattern with %o for an offset +-1(s/m/h/d/w) units.

* SOURCE   - the amqp user that injected data (taken from the notification message.)
* BD       - the base directory
* BUP      - the path component of the baseUrl (or: baseUrlPath) 
* BUPL     - the last element of the baseUrl path. (or: baseUrlPathLast)
* PBD      - the post base dir
* *var*    - any environment variable.
* BROKER_USER - the user name for authenticating to the broker (e.g. anonymous)
* POST_BROKER_USER - the user name for authenticating to the post_broker (e.g. anonymous)
* PROGRAM     - the name of the component (subscribe, shovel, etc...)
* CONFIG      - the name of the configuration file being run.
* HOSTNAME    - the hostname running the client.
* RANDID      - a random id that will be consistent within a single invocation.

The %Y%m%d and %h time stamps refer to the time at which the data is processed by
the component, it is not decoded or derived from the content of the files delivered.
All date/times in Sarracenia are in UTC. use the varTimeOffset setting to adjust
from the current time.

Refer to *sourceFromExchange* for a common example of usage. Note that any sarracenia
built-in value takes precedence over a variable of the same name in the environment.
Note that flatten settings can be changed between directory options.

Note::

   the ${% date substitutions are present, the interpretation of % patterns in filenames 
   by strftime, may mean it is necessary to escape precent characters them via doubling: %%

Sundew Compatible Substituions 
------------------------------

In `MetPX Sundew <../Explanation/Glossary.html#sundew>`_, there is a much more strict 
file naming standard, specialised for use with World Meteorological 
Organization (WMO) data. Note that the file naming convention predates, and
bears no relation to the WMO file naming convention currently approved, but is strictly an internal
format. The files are separated into six fields by colon characters. The first field, DESTFN,
gives the WMO (386 style) Abbreviated Header Line (AHL) with underscores replacing blanks::

   TTAAii CCCC YYGGGg BBB ...  

(see WMO manuals for details) followed by numbers to render the product unique (as in practice,
though not in theory, there are a large number of products which have the same identifiers).
The meanings of the fifth field is a priority, and the last field is a date/time stamp.
The other fields vary in meaning depending on context. A sample file name::

   SACN43_CWAO_012000_AAA_41613:ncp1:CWAO:SA:3.A.I.E:3:20050201200339

If a file is sent to sarracenia and it is named according to the Sundew conventions, then the
following substitution fields are available::

  ${T1}    replace by bulletin's T1
  ${T2}    replace by bulletin's T2
  ${A1}    replace by bulletin's A1
  ${A2}    replace by bulletin's A2
  ${ii}    replace by bulletin's ii
  ${CCCC}  replace by bulletin's CCCC
  ${YY}    replace by bulletin's YY   (obs. day)
  ${GG}    replace by bulletin's GG   (obs. hour)
  ${Gg}    replace by bulletin's Gg   (obs. minute)
  ${BBB}   replace by bulletin's bbb
  ${RYYYY} replace by reception year
  ${RMM}   replace by reception month
  ${RDD}   replace by reception day
  ${RHH}   replace by reception hour
  ${RMN}   replace by reception minutes
  ${RSS}   replace by reception second
  YYYYMMDD - the current daily timestamp. (v2 compat, prefer strftime %Y%m%d )
  HH       - the current hourly timestamp. (v2 compat, prefer strftime %h )
  JJJ      - the current hourly timestamp. (v2 compat, prefer strftime %j )


The 'R' fields come from the sixth field, and the others come from the first one.
When data is injected into sarracenia from Sundew, the *sundew_extension* notification message header
will provide the source for these substitions even if the fields have been removed
from the delivered file names.

Note:: 

   The version 2 compatible date strings (e.g. YYYYMMDD) originate with obsolete 
   WMO practices, and support will be removed at a future date. Please use strftime 
   style patterns in new configurations. 


SR_DEV_APPNAME
~~~~~~~~~~~~~~

The SR_DEV_APPNAME environment variable can be set so that the application configuration and state directories
are created under a different name. This is used in development to be able to have many configurations
active at once. It enables more testing than always working with the developer´s *real* configuration.

Example:  export SR_DEV_APPNAME=sr-hoho... when you start up a component on a linux system, it will
look in ~/.config/sr-hoho/ for configuration files, and write state files in the ~/.cache/sr-hoho
directory.

OPTION TYPES
============

sr3 options come in several types:

count      
    integer count type. 

duration   
    a floating point number indicating a quantity of seconds (0.001 is 1 milisecond)
    modified by a unit suffix ( m-minute, h-hour, w-week ) 

flag       
    an option that has only True or False values (aka: a boolean value)

float
    a floating point number.

list
    a list of string values, each succeeding occurrence catenates to the total.
    all v2 plugin options are declared of type list.

set
    a set of string values, each succeeding occurrence is unioned to the total.

size
    integer size. Suffixes k, m, and g for kilo, mega, and giga (base 2) multipliers.

str
    an string value
   

OPTIONS
=======

The actual options are listed below. Note that they are case sensitive, and
only a subset are available on the command line. Those that are available
on the command line have the same effect as when specified in configuration
files.

The options available in configuration files:


accelThreshold <size> default: 0 (disabled.)
---------------------------------------------------

The accelThreshold indicates the minimum size of file being transferred for
which a binary downloader will be launched.

accelXxxCommand 
----------------

Can specify alternate binaries for downloaders to tune for specific cases.

+-----------------------------------+--------------------------------+
|  Option                           |  Defaul value                  |
+-----------------------------------+--------------------------------+
|  accelWgetCommand                 |  /usr/bin/wget %s -O %d        |
+-----------------------------------+--------------------------------+
|  accelScpCommand                  |  /usr/bin/scp %s %d            |
+-----------------------------------+--------------------------------+
|  accelCpCommand                   |  /usr/bin/cp  %s %d            |
+-----------------------------------+--------------------------------+
|  accelFtpgetCommand               |  /usr/bin/ncftpget %s %d       |
+-----------------------------------+--------------------------------+
|  accelFtpputCommand               |  /usr/bin/ncftpput %s %d       |
+-----------------------------------+--------------------------------+

use the %s to stand-in for the name of the source file, and %d for the
file being written.  An example setting to override with::

   accelCpCommand dd if=%s of=%d bs=4096k


accept, reject and acceptUnmatched
----------------------------------


- **accept     <regexp pattern> (optional) [<keywords>]**
- **reject     <regexp pattern> (optional)**
- **acceptUnmatched   <boolean> (default: True)**

The  **accept**  and  **reject**  options process regular expressions (regexp).
The regexp is applied to the the notification message's URL for a match.

If the notification message's URL of a file matches a **reject**  pattern, the notification message
is acknowledged as consumed to the broker and skipped.

One that matches an **accept** pattern is processed by the component.

In many configurations, **accept** and **reject** options are mixed
with the **directory** option.  They then relate accepted notification messages
to the **directory** value they are specified under.

After all **accept** / **reject**  options are processed, normally
the notification message is accepted for further processing. To override that
default, set **acceptUnmatched** to False. The **accept/reject**
settings are interpreted in order. Each option is processed orderly
from top to bottom. For example:

sequence #1::

  reject .*\.gif
  accept .*

sequence #2::

  accept .*
  reject .*\.gif


In sequence #1, all files ending in 'gif' are rejected.  In sequence #2, the accept .* (which
accepts everything) is encountered before the reject statement, so the reject has no effect.

It is best practice to use server side filtering to reduce the number of notification messages sent
to the component to a small superset of what is relevant, and perform only a fine-tuning with the
client side mechanisms, saving bandwidth and processing for all. More details on how
to apply the directives follow:

The  **accept**  and  **reject**  options use regular expressions (regexp) to match URL.
These options are processed sequentially.
The URL of a file that matches a  **reject**  pattern is not published.
Files matching an  **accept**  pattern are published.
Again a *rename*  can be added to the *accept* option... matching products
for that *accept* option would get renamed as described... unless the *accept* matches
one file, the *rename* option should describe a directory into which the files
will be placed (prepending instead of replacing the file name).

The **permDefault** option allows users to specify a linux-style numeric octal
permission mask::

  permDefault 040

means that a file will not be posted unless the group has read permission
(on an ls output that looks like: ---r-----, like a chmod 040 <file> command).
The **permDefault** options specifies a mask, that is the permissions must be
at least what is specified.

The **regexp pattern** can be used to set directory parts if part of the notification message is put
to parenthesis. **sender** can use these parts to build the directory name. The
rst enclosed parenthesis strings will replace keyword **${0}** in the directory name...
the second **${1}** etc.

Example of use::


      filename NONE

      directory /this/first/target/directory

      accept .*file.*type1.*

      directory /this/target/directory

      accept .*file.*type2.*

      accept .*file.*type3.*  DESTFN=file_of_type3

      directory /this/${0}/pattern/${1}/directory

      accept .*(2016....).*(RAW.*GRIB).*


A selected notification message by the first accept would be delivered unchanged to the first directory.

A selected notification message by the second accept would be delivered unchanged to the second directory.

A selected notification message by the third accept would be renamed "file_of_type3" in the second directory.

A selected notification message by the forth accept would be delivered unchanged to a directory.

It's named  */this/20160123/pattern/RAW_MERGER_GRIB/directory* if the notification message would have a notice like:

**20150813161959.854 http://this.pump.com/ relative/path/to/20160123_product_RAW_MERGER_GRIB_from_CMC**


acceptSizeWrong: <boolean> (default: False)
-------------------------------------------

When a file is downloaded and its size does not match the one advertised, it is
normally rejected, as a failure. This option accepts the file even with the wrong
size. helpful when file is changing frequently, and there is some queueing, so
the file is changed by the time it is retrieved.


attempts <count> (default: 3)
-----------------------------

The **attempts** option indicates how many times to
attempt downloading the data before giving up.  The default of 3 should be appropriate
in most cases.  When the **retry** option is false, the file is then dropped immediately.

When The **retry** option is set (default), a failure to download after prescribed number
of **attempts** (or send, in a sender) will cause the notification message to be added to a queue file
for later retry.  When there are no notification messages ready to consume from the AMQP queue,
the retry queue will be queried.


baseDir <path> (default: /)
----------------------------

**baseDir** supplies the directory path that, when combined with the relative
one in the selected notification gives the absolute path of the file to be sent.
The default is None which means that the path in the notification is the absolute one.

Sometimes senders subscribe to local xpublic, which are http url's, but sender
needs a localfile, so the local path is built by concatenating::

   baseDir + relative path in the baseUrl + relPath

When used for reception, it specifies the root of the tree that upstream files are assumed
to be from, to be replaced on download by either post_baseDir or the *directory* setting
in effect.


baseUrl_relPath <flag> (default: off)
-------------------------------------

Normally, the relative path (baseUrl_relPath is False, appended to the base directory) for 
files which are downloaded will be set according to the relPath header included 
in the notification message. If *baseUrl_relPath* is set, however, the notification message's relPath will
be prepended with the sub-directories from the notification message's baseUrl field.


batch <count> (default: 100)
----------------------------

The **batch** option is used to indicate how many files should be transferred
over a connection, before it is torn down, and re-established.  On very low
volume transfers, where timeouts can occur between transfers, this should be
lowered to 1.  For most usual situations the default is fine. For higher volume
cases, one could raise it to reduce transfer overhead. It is only used for file
transfer protocols, not HTTP ones at the moment.

blocksize <size> default: 0 (auto)
-----------------------------------

NOTE: **EXPERIMENTAL** sr3, expected to return in future version**
This **blocksize** option controls the partitioning strategy used to post files.
The value should be one of::

   0 - autocompute an appropriate partitioning strategy (default)
   1 - always send entire files in a single part.
   <blocksize> - used a fixed partition size (example size: 1M )

Files can be announced as multiple parts.  Each part has a separate checksum.
The parts and their checksums are stored in the cache. Partitions can traverse
the network separately, and in parallel.  When files change, transfers are
optimized by only sending parts which have changed.

The *outlet* option allows the final output to be other than a post.
See `sr3_cpump(1) <sr3_cpump.1.html>`_ for details.

broker
------

**broker [amqp|mqtt]{s}://<user>:<password>@<brokerhost>[:port]/<vhost>**

A URI is used to configure a connection to a notification message pump, either
an MQTT or an AMQP broker. Some Sarracenia components set a reasonable default for
that option.  provide the normal user,host,port of connections. In most configuration files,
the password is missing. The password is normally only included in the 
`credentials.conf <sr3_credentials.7.html>`_ file.

Sarracenia work has not used vhosts, so **vhost** should almost always be **/**.

for more info on the AMQP URI format: ( https://www.rabbitmq.com/uri-spec.html )


either in the default.conf or each specific configuration file.
The broker option tell each component which broker to contact.

**broker [amqp|mqtt]{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::
      (default: None and it is mandatory to set it ) 

Once connected to an AMQP broker, the user needs to bind a queue
to exchanges and topics to determine the notification messages of interest.


bufsize <size> (default: 1MB)
-----------------------------

Files will be copied in *bufsize*-byte blocks. for use by transfer protocols.


byteRateMax <size> (default: 0)
--------------------------------

**byteRateMax** is greater than 0, the process attempts to respect this delivery
speed in kilobytes per second... ftp,ftps,or sftp)

**FIXME**: byteRateMax... only implemented by sender? or subscriber as well, data only, or notification messages also?

callback <classSpec> 
--------------------

**callback** appends a flowcallback class to the list of those to be called during processing.

Most customizable processing or "plugin" logic, is implemented using the flow callback class.
At different points in notification message processing, flow callback classes define
entry_points that match that point in processing. for for every such point in the processing,
there is a list of flow callback routines to call.

`FlowCallback Reference <flowcb.html>`_

the *classSpec* is similar to an *import* statement from python. It uses the python search
path, and also includes ~/.config/sr3/plugins.  There is some shorthand to make usage 
shorter for common cases.  for example:

  callback log 

Sarracenia will first attempt, to prepend *log* with *sarracenia.flowcb.log* and then
instantiate the callback instance as an item of class sarracenia.flowcb.Log.  If it does not
find such a class, then it will attempt to find a class name *log*, and instantiate an
object *log.Log.*

More detail here `FlowCallback load_library <flowcb.html#sarracenia.flowcb.load_library>`_


callback_prepend <classSpec> 
----------------------------

identical to callback, but meant to specify functions to be executed early, that is prepended
to the list of plugins to run.



dangerWillRobinson (default: omitted)
-------------------------------------

This option is only recognized as a command line option. It is specified when an operation is expected
to have irreversibly destructive or perhaps unexpected effects. for example::

   sr3 stop

will stop running components, but not those that are being run in the foreground. Stopping those
may be surprising to the analysts that will be looking at them, so that is not done by default::

  sr3 --dangerWillRobinson stop

stops stops all components, including the foreground ones. Another example would be the *cleanup*
action. This option deletes queues and exchanges related to a configuration, which can be
destructive to flows. By default, cleanup only operates on a single configuration at a time.
One can specify this option to wreak greater havoc.



declare 
-------

env NAME=Value
  On can also reference environment variables in configuration files,
  using the *${ENV}* syntax.  If Sarracenia routines needs to make use
  of an environment variable, then they can be set in configuration files::

    declare env HTTP_PROXY=localhost

exchange exchange_name
  using the admin url, declare the exchange with *exchange_name*

subscriber
  A subscriber is user that can only subscribe to data and return report notification messages. Subscribers are
  not permitted to inject data.  Each subscriber has an xs_<user> named exchange on the pump,
  where if a user is named *Acme*, the corresponding exchange will be *xs_Acme*.  This exchange
  is where an subscribe process will send its report notification messages.

  By convention/default, the *anonymous* user is created on all pumps to permit subscription without
  a specific account.

source
  A user permitted to subscribe or originate data.  A source does not necessarily represent
  one person or type of data, but rather an organization responsible for the data produced.
  So if an organization gathers and makes available ten kinds of data with a single contact
  email or phone number for questions about the data and its availability, then all of
  those collection activities might use a single 'source' account.

  Each source gets a xs_<user> exchange for injection of data notification messages, and, similar to a subscriber
  to send report notification messages about processing and receipt of data. Source may also have an xl_<user>
  exchange where, as per report routing configurations, report notification messages of consumers will be sent.

feeder
  A user permitted to write to any exchange. Sort of an administrative flow user, meant to pump
  notification messages when no ordinary source or subscriber is appropriate to do so.  Is to be used in
  preference to administrator accounts to run flows.

User credentials are placed in the `credentials.conf <sr3_credentials.7.html>`_ 
file, and *sr3 --users declare* will update
the broker to accept what is specified in that file, as long as the admin password is
already correct.

debug
-----

Setting option debug is identical to use  **logLevel debug**


delete <boolean> (default: off)
-------------------------------

When the **delete** option is set, after a download has completed successfully, the subscriber
will delete the file at the upstream source.  Default is false.

discard <boolean> (default: off)
--------------------------------

The  **discard**  option,if set to true, deletes the file once downloaded. This option can be
useful when debugging or testing a configuration.

directory <path> (default: .)
-----------------------------

The *directory* option defines where to put the files on your server.
Combined with  **accept** / **reject**  options, the user can select the
files of interest and their directories of residence (see the  **mirror**
option for more directory settings).

The  **accept**  and  **reject**  options use regular expressions (regexp) to match URL.
These options are processed sequentially.
The URL of a file that matches a  **reject**  pattern is never downloaded.
One that matches an  **accept**  pattern is downloaded into the directory
declared by the closest  **directory**  option above the matching  **accept** option.
**acceptUnmatched** is used to decide what to do when no reject or accept clauses matched.

::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*


destfn_script <script> (default:None)
-------------------------------------

This Sundew compatibility option defines a script to be run when everything is ready
for the delivery of the product.  The script receives the sender class
instance.  The script takes the parent as an argument, and for example, any
modification to  **parent.msg.new_file**  will change the name of the file written locally.

download <flag> (default: True)
--------------------------------

used to disable downloading in subscribe and/or sarra component.
set False by default in shovel or winnow components.


dry_run <flag> (default: False)
-------------------------------

Run in simulation mode with respect to file transfers. Still connects to a broker and downloads and processes
messages, but transfers are disabled, for use when testing a sender, or a downloader, say to run in parallel
with an existing one, and compare the logs to see if the sender is configured to send the same files as
the old one (implemented with some other system.)


durable <flag> (default: True)
----------------------------------

The AMQP **durable** option, on queue declarations. If set to True, 
the broker will preserve the queue across broker reboots.
It means writes the queue is on disk if the broker is restarted.

fileEvents <event,event,...>
----------------------------

A comma separated list of file event types to monitor.
Available file events:  create, delete, link, modify, mkdir, rmdir
to only add events to the current list start the event list with a plus sign (+).
To remove them, prefix with a minus sign (-).

The *create*, *modify*, and *delete* events reflect what is expected: a file being created, modified, or deleted.
If *link* is set, symbolic links will be posted as links so that consumers can choose
how to process them. If it is not set, then no symbolic link events will ever be posted.

.. note::
   move or rename events result in a special double post pattern, with one post as the old name
   and a field *newname* set, and a second post with the new name, and a field *oldname* set. 
   This allows subscribers to perform an actual rename, and avoid triggering a download when possible.

   FIXME: rename algorithm improved in v3 to avoid use of double post... just

exchange <name> (default: xpublic) and exchangeSuffix
------------------------------------------------------

The convention on data pumps is to use the *xpublic* exchange. Users can establish
private data flow for their own processing. Users can declare their own exchanges
that always begin with *xs_<username>*, so to save having to specify that each
time, one can just set *exchangeSuffix kk* which will result in the exchange
being set to *xs_<username>_kk* (overriding the *xpublic* default).
These settings must appear in the configuration file before the corresponding
*topicPrefix* and *subtopic* settings.


exchangeDeclare <flag>
----------------------

On startup, by default, Sarracenia redeclares resources and bindings to ensure they
are uptodate. If the exchange already exists, this flag can be set to False, 
so no attempt to exchange the queue is made, or it´s bindings.
These options are useful on brokers that do not permit users to declare their exchanges.



expire <duration> (default: 5m  == five minutes. RECOMMEND OVERRIDING)
----------------------------------------------------------------------

The  **expire**  option is expressed as a duration... it sets how long should live
a queue without connections.

A raw integer is expressed in seconds, if the suffix m,h,d,w
are used, then the interval is in minutes, hours, days, or weeks. After the queue expires,
the contents are dropped, and so gaps in the download data flow can arise.  A value of
1d (day) or 1w (week) can be appropriate to avoid data loss. It depends on how long
the subscriber is expected to shutdown, and not suffer data loss.

if no units are given, then a decimal number of seconds can be provided, such as
to indicate 0.02 to specify a duration of 20 milliseconds.

The **expire** setting must be overridden for operational use.
The default is set low because it defines how long resources on the broker will be assigned,
and in early use (when default was 1 week) brokers would often get overloaded with very
long queues for left-over experiments.


filename <keyword> (default:None)
-----------------------------------

From **metpx-sundew**, the support of this option give all sorts of possibilities
for setting the remote filename. Some **keywords** are based on the fact that
**metpx-sundew** filenames are five (to six) fields strings separated by for colons.

The default value on Sundew is NONESENDER, but in the interest of discouraging use
of colon separation in files, the default in Sarracenia is WHATFN

The possible keywords are :

**None**
 - the filename is not modified at all. (different from NONE!) 
   turn off any Sundew compatibility filename processing.

**WHATFN**
 - the first part of the Sundew filename (string before first :)

**HEADFN**
 - HEADER part of the sundew filename

**SENDER**
 - the Sundew filename may end with a string SENDER=<string> in this case the <string> will be the remote filename

**NONE**
 - deliver with the complete Sundew filename (without :SENDER=...)

**NONESENDER**
 - deliver with the complete Sundew filename (with :SENDER=...)

**TIME**
 - time stamp appended to filename. Example of use: WHATFN:TIME

**DESTFN=str**
 - direct filename declaration str

**SATNET=1,2,3,A**
 - cmc internal satnet application parameters

**DESTFNSCRIPT=script.py**
 - invoke a script (same as destfn_script) to generate the name of the file to write



flatten <string> (default: '/')
-------------------------------

The  **flatten**  option is use to set a separator character. The default value ( '/' )
nullifies the effect of this option.  This character replaces the '/' in the url
directory and create a "flatten" filename from its dd.weather.gc.ca path.
For example retrieving the following url, with options::

 http://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/12/015/CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

   flatten   -
   directory /mylocaldirectory
   accept    .*model_gem_global.*

would result in the creation of the filepath::

 /mylocaldirectory/model_gem_global-25km-grib2-lat_lon-12-015-CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

flowMain (default: None)
------------------------

By default, a flow will run the sarracenia.flow.Flow class, which implements the Flow algorithm generically.
The generic version does no data transfer, only creating and manipulating messages. That is appropriate for 
shovel, winnow, post & watch components, but components that transfer or transform data need
to define additional behaviour by sub-classing Flow. Examples: sarracenia.flow.sender, sarracenia.flow.poll, sarracenia.flow.subscribe.  

The **flowMain** option allows a flow configuration to run a subclass of flow, instead of the default parent
class.  Example::

   flowMain subscribe

In a generic flow configuration file will configure the flow to act as a subscriber component.
One can create custom components by subclassing Flow and using the **flowMain** directive to have
it invoked. 

follow_symlinks <flag>
----------------------

The *follow_symlinks* option causes symbolic links to be traversed.  If *follow_symlinks* is set
and the destination of a symbolic link is a file, then that destination file should be posted as well as the link.
If the destination of the symbolic link is a directory, then the directory should be added to those being
monitored by watch.   If *follow_symlinks* is false, then no action related to the destination of the symbolic
link is taken.


force_polling <flag> (default: False)
-------------------------------------

By default, watch selects an (OS dependent) optimal method to watch a
directory. 

For large trees, the optimal method can be manyfold (10x or even
100x) faster to recognize when a file has been modified. In some cases,
however, platform optimal methods do not work (such as with some network
shares, or distributed file systems), so one must use a slower but more
reliable and portable polling method.  The *force_polling* keyword causes
watch to select the polling method in spite of the availability of a
normally better one.  

For a detailed discussion, see: `Detecting File Changes <../Explanation/DetectFileReady.html>`_

NOTE::

  When directories are consumed by processes using the subscriber *delete* option, they stay empty, and
  every file should be reported on every pass.  When subscribers do not use *delete*, watch needs to
  know which files are new.  It does so by noting the time of the beginning of the last polling pass.
  File are posted if their modification time is newer than that.  This will result in many multiple notification messages
  by watch, which can be minimized with the use of cache.   One could even depend on the cache
  entirely and turn on the *delete* option, which will have watch attempt to post the entire tree
  every time (ignoring mtime).

  **KNOWN LIMITATION**: When *force_polling* is set, the *sleep* setting should be
  at least 5 seconds. It is not currently clear why.

header <name>=<value>
---------------------

Add a <name> header with the given value to a notification message. Used to pass strings as metadata in the
notification messages to improve decision making for consumers.  Should be used sparingly. There are limits
on how many headers can be used, and minimizing the size of messages has important performance
impacts.


housekeeping <interval> (default: 300 seconds)
----------------------------------------------

The **housekeeping** option sets how often to execute periodic processing as determined by
the list of on_housekeeping plugins. By default, it prints a log message every houskeeping interval.

include config
--------------

include another configuration within this configuration.


inflight <string> (default: .tmp or NONE if post_broker set)
------------------------------------------------------------

The  **inflight**  option sets how to ignore files when they are being transferred
or (in mid-flight betweeen two systems). Incorrect setting of this option causes
unreliable transfers, and care must be taken.  See `Delivery Completion <../Explanation/FileCompletion.html>`_
for more details.

The value can be a file name suffix, which is appended to create a temporary name during
the transfer.  If **inflight**  is set to **.**, then it is a prefix, to conform with
the standard for "hidden" files on unix/linux.
If **inflight**  ends in / (example: *tmp/* ), then it is a prefix, and specifies a
sub-directory of the destination into which the file should be written while in flight.

Whether a prefix or suffix is specified, when the transfer is
complete, the file is renamed to its permanent name to allow further processing.

When detecting a file with sr3_post, sr3_cpost, or watch, or poll, the  **inflight** option
can also be specified as a time interval, for example, 10 for 10 seconds.
When set to a time interval, file posting process ensures that it waits until
the file has not been modified in that interval. So a file will
not be processed until it has stayed the same for at least 10 seconds.
This is the same as setting the **fileAgeMin** setting.

Lastly, **inflight** can be set to *NONE*, which case the file is written directly
with the final name, where the recipient will wait to receive a post notifying it
of the file's arrival.  This is the fastest, lowest overhead option when it is available.
It is also the default when a *post_broker* is given, indicating that some
other process is to be notified after delivery.

NOTE::

    When writing a file, if you see the error message::

        inflight setting: 300, not for downloads

    It is because the time interval setting is only for reading files. The writer
    cannot control how long a subsequent reader will wait to look at a file being
    downloaded, so specifying a minimum modification time is inappropriate.
    in looking at local files before generating a post, it is not used as say, a means
    of delaying sending files.


inline <flag> (default: False)
------------------------------

When posting messages, The **inline** option is used to have the file content
included in the post. This can be efficient when sending small files over high
latency links, a number of round trips can be saved by avoiding the retrieval
of the data using the URL.  One should only inline relatively small files,
so when **inline** is active, only files smaller than **inlineByteMax** bytes
(default: 1024) will actually have their content included in the post messages.
If **inlineOnly** is set, and a file is larger than inlineByteMax, the file
will not be posted.

inlineByteMax <size>
--------------------

The maximum size of messages to inline.

inlineEncoding text|binary|guess (default: guess)
_________________________________________________

when inlining file content, what sort of encoding should be done? Three choices:

 * text: the file content is assumed to be utf-8 text and encoded as such.
 * binary: the file content is unconditionally converted to base64 binary encoding.
 * guess: try making text, if that fails fall back to binary.


inlineOnly
----------

discard messages if the data is not inline.


inplace <flag> (default: On)
----------------------------

Large files may be sent as a series of parts, rather than all at once.
When downloading, if **inplace** is true, these parts will be appended to the file
in an orderly fashion. Each part, after it is inserted in the file, is announced to subscribers.
This can be set to false for some deployments of sarracenia where one pump will
only ever see a few parts, and not the entirety, of multi-part files.

The **inplace** option defaults to True.
Depending of **inplace** and if the message was a part, the path can
change again (adding a part suffix if necessary).


Instances
---------

Sometimes one instance of a component and configuration is not enough to process & send all available notifications.

**instances      <integer>     (default:1)**

The instance option allows launching several instances of a component and configuration.
When running sender for example, a number of runtime files are created.
In the ~/.cache/sarra/sender/configName directory::

  A .sender_configname.state         is created, containing the number instances.
  A .sender_configname_$instance.pid is created, containing the PID  of $instance process.

In directory ~/.cache/sarra/log::

  A .sender_configname_$instance.log  is created as a log of $instance process.

.. Note::

  While the brokers keep the queues available for some time, queues take resources on 
  brokers, and are cleaned up from time to time. A queue which is not accessed 
  and has too many (implementation defined) files queued will be destroyed.
  Processes which die should be restarted within a reasonable period of time to avoid
  loss of notifications. A queue which is not accessed for a long (implementation dependent)
  period will be destroyed. 

identity <string>
------------------

All file notification messages include a checksum.  It is placed in the amqp message header will have as an
entry *sum* with default value 'd,md5_checksum_on_data'.
The *sum* option tell the program how to calculate the checksum.
In v3, they are called Identity methods::

         cod,x      - Calculate On Download applying x
         sha512     - do SHA512 on file content  (default)
         md5        - do md5sum on file content
         md5name    - do md5sum checksum on filename 
         random     - invent a random value for each post.
         arbitrary  - apply the literal fixed value.

v2 options are a comma separated string.  Valid checksum flags are :

* 0 : no checksum... value in post is a random integer (only for testing/debugging.)
* d : do md5sum on file content 
* n : do md5sum checksum on filename
* p : do SHA512 checksum on filename and partstr [#]_
* s : do SHA512 on file content (default)
* z,a : calculate checksum value using algorithm a and assign after download.

.. [#] only implemented in C. ( see https://github.com/MetPX/sarracenia/issues/117 )


logEvents ( default: after_accept,after_work,on_housekeeping )
--------------------------------------------------------------

The set of points during notification message processing to emit standard log messages.
other values: on_start, on_stop, post, gather, ... etc... It is comma separated, and
if the list starts with a plus sign (+) then the selected events are appended to current value.
A minus signe (-) can be used to remove events from the set.

logLevel ( default: info )
--------------------------

The level of logging as expressed by python's logging. Possible values are :  critical, error, info, warning, debug.

logMetrics ( default: False )
-----------------------------

Write metrics to a daily metrics file for statistics gathering. can be used to generate statistics.
File is in the same directory as the logs, and has a date suffix.



logReject ( default: False )
----------------------------

Normally, messages rejection is done silently. When logReject is True, a log message will be generated for
each message rejected, and indicating the basis for the rejection.

logStdout ( default: False )
----------------------------

The *logStdout* disables log management. Best used on the command line, as there is
some risk of creating stub files before the configurations are completely parsed::

       sr3 --logStdout start

All launched processes inherit their file descriptors from the parent. so all output is like an interactive session.

This is in contrast to the normal case, where each instance takes care of its logs, rotating and purging periodically.
In some cases, one wants to have other software take care of logs, such as in docker, where it is preferable for all
logging to be to standard output.

It has not been measured, but there is a reasonable likelihood that use of *logStdout* with large configurations (dozens
of configured instances/processes) will cause either corruption of logs, or limit the speed of execution of all processes
writing to stdout.


logRotateCount <max_logs> ( default: 5 )
----------------------------------------

Maximum number of logs (both messages and metrics) archived.

logRotateInterval <interval>[<time_unit>] ( default: 1d )
---------------------------------------------------------

The duration of the interval with an optional time unit (ie 5m, 2h, 3d) for rotation of logs and metrics.


messageCountMax <count> (default: 0)
------------------------------------

If **messageCountMax** is greater than zero, the flow will exit after processing the given
number of messages.  This is normally used only for debugging.

messageRateMax <float> (default: 0)
-------------------------------------

if **messageRateMax** is greater than zero, the flow attempts to respect this delivery
speed in terms of messages per second. Note that the throttle is on messages obtained or generated
per second, prior to accept/reject filtering. the flow will sleep to limit the processing rate.


messageRateMin <float> (default: 0)
-------------------------------------

if **messageRateMin** is greater than zero, and the flow detected is lower than this rate,
a warning message will be produced:


message_ttl <duration>  (default: None)
---------------------------------------

The  **message_ttl**  option set the time a message can live in the queue.
Past that time, the message is taken out of the queue by the broker.

mirror <flag> (default: off)
----------------------------

The  **mirror**  option can be used to mirror the dd.weather.gc.ca tree of the files.
If set to  **True**  the directory given by the  **directory**  option
will be the basename of a tree. Accepted files under that directory will be
placed under the subdirectory tree leaf where it resides under dd.weather.gc.ca.
For example retrieving the following url, with options::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif
mirror settings can be changed between directory options.

no <count>
----------

(normally not used by humans)

Present on instances started by the sr3 management interface.
The no option is only used on the command line, and not intended for users.
It is an option for use by sr3 when spawning instances to inform each process
which instance it is. e.g instance 3 will be spawned with --no 3 

nodupe_basis <data|name|path> (default: path)
---------------------------------------------

A keyword option to identify which files are compared for
duplicate suppression purposes. Normally, the duplicate suppression uses the entire path
to identify files which have not changed. This allows for files with identical
content to be posted in different directories and not be suppressed. In some
cases, suppression of identical files should be done regardless of where in
the tree the file resides.  Set 'name' for files of identical name, but in
different directories to be considered duplicates. Set to 'data' for any file,
regardless of name, to be considered a duplicate if the checksum matches.


This is implemented as an alias for:

    callback_prepend nodupe.name

or:

    callback_prepend nodupe.data

More information: `Duplicate Suppresion <../Explanation/DuplicateSuppression.html>`_

fileAgeMax
----------

If files are older than this setting (default: 7h in poll, 0 in other components), 
then ignore them, they are too old to post. 0 deactivates the setting.

In a Poll:
  * default is 7 hours. should be less than nodupe_ttl to prevent re-ingest of duplicate data.
    (full discussion here: https://github.com/MetPX/sarracenia/issues/904 )

fileAgeMin
----------

If files are newer than this setting (default: 0), then ignore them, they are too
new to post. 0 deactivates the setting.

nodupe_ttl <off|on|999[smhdw]> 
------------------------------

When **nodupe_ttl** (also **suppress_duplicates*, and **cache** ) is set to a non-zero time 
interval, each new message is compared against ones received within that interval, to see if 
it is a duplicate. Duplicates are not processed further. What is a duplicate? A file with 
the same name (including parts header) and checksum. Every *hearbeat* interval, a cleanup 
process looks for files in the cache that have not been referenced in **cache** seconds, 
and deletes them, in order to keep the cache size limited. Different settings are 
appropriate for different use cases.

A raw integer interval is in seconds, if the suffix m,h,d, or w are used, then the interval
is in minutes, hours, days, or weeks. After the interval expires the contents are
dropped, so duplicates separated by a large enough interval will get through.
A value of 1d (day) or 1w (week) can be appropriate.  Setting the option without specifying
a time will result in 300 seconds (or 5 minutes) being the expiry interval.

Default value in a Poll is 8 hours, should be longer than nodupe_fileAgeMax to prevent
re-ingesting files that have aged out of the duplicate suppression cache.

**Use of the cache is incompatible with the default *parts 0* strategy**, one must specify an
alternate strategy.  One must use either a fixed blocksize, or always never partition files.
One must avoid the dynamic algorithm that will change the partition size used as a file grows.

**Note that the duplicate suppresion store is local to each instance**. When N
instances share a queue, the first time a posting is received, it could be
picked by one instance, and if a duplicate one is received it would likely
be picked up by another instance. **For effective duplicate suppression with instances**,
one must **deploy two layers of subscribers**. Use
a **first layer of subscribers (shovels)** with duplicate suppression turned
off and output with *post_exchangeSplit*, which route notification messages by checksum to
a **second layer of subscibers (winnow) whose duplicate suppression caches are active.**


outlet post|json|url (default: post)
------------------------------------

The **outlet** option is used to allow writing of notification messages to file instead of
posting to a broker. The valid argument values are:

**post:**

  post messages to an post_exchange

  **post_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**
  **post_exchange     <name>         (MANDATORY)**
  **post_topicPrefix <string>       (default: "v03")**
  **on_post           <script>       (default: None)**

  The **post_broker** defaults to the input broker if not provided.
  Just set it to another broker if you want to send the notifications
  elsewhere.

  The **post_exchange** must be set by the user. This is the exchange under
  which the notifications will be posted.

**json:**

  write each message (json/v03 encoded) to standard output.

**url:**

  just output the retrieval URL to standard output.

FIXME: The **outlet** option came from the C implementation ( *sr3_cpump*  ) and it has not
been used much in the python implementation.

overwrite <flag> (default: off)
-------------------------------

The  **overwrite**  option,if set to false, avoid unnecessary downloads under these conditions :

1- the file to be downloaded is already on the user's file system at the right place and

2- the checksum of the amqp message matched the one of the file.

The default is False.

path <path>
-----------

**post** evaluates the filesystem path from the **path** option
and possibly the **post_baseDir** if the option is used.

If a path defines a file then this file is watched.

If a path defines a directory then all files in that directory are watched...

This is also used to say which directories to look at for a poll

If this path defines a directory, all files in that directory are
watched and should **watch** find one (or more) directory(ies), it
watches it(them) recursively until all the tree is scanned.

The AMQP notification messages are made of the tree fields, the notification message time,
the **url** option value and the resolved paths to which were withdrawn
the *post_baseDir* present and needed.


permDefault, permDirDefault, permLog, permCopy
----------------------------------------------

Permission bits on the destination files written are controlled by the *permCopy* directives.
*permCopy* will apply the mode permissions posted by the source of the file.
If no source mode is available, the *permDefault* will be applied to files, and the
*permLog* will be applied to directories. If no default is specified,
then the operating system  defaults (on linux, controlled by umask settings)
will determine file permissions. (Note that the *chmod* option is interpreted as a synonym
for *permDefault*, and *chmod_dir* is a synonym for *permDirDefault*).

When set in a posting component, permCopy has the effect of including or excluding
the *mode* header from the messages.

when set in a polling component, permDefault has the of setting minimum permissions for
a file to be accepted.
(on an ls output that looks like: ---r-----, like a chmod 040 <file> command).
The **permDefault** options specifies a mask, that is the permissions must be
at least what is specified.

pollUrl <url>
-------------

Specification of a remote server resources to query with a poll 
See the `POLLING <../Explanation/CommandlineGuide.html#POLLING>`_ 
in the Command Line Guide.

post_baseDir <path> 
-------------------

The *post_baseDir* option supplies the directory path that, when combined (or found)
in the given *path*, gives the local absolute path to the data file to be posted.
The *post_baseDir* part of the path will be removed from the posted notification message.
For sftp urls it can be appropriate to specify a path relative to a user account.
Example of that usage would be: --post_baseDir ~user --url sftp:user@host
For file: url's, baseDir is usually not appropriate. To post an absolute path,
omit the --post_baseDir setting, and just specify the complete path as an argument.

post_baseUrl <url>
------------------

The **post_baseUrl** option sets how to get the file... it defines the protocol,
host, port, and optionally, the user. It is best practice to not include
passwords in urls.

post_broker <url>
-----------------

the broker url to post messages to see `broker <#broker>`_ for details

post_exchange <name> (default: xpublic)
---------------------------------------

The **post_exchange** option set under which exchange the new notification
will be posted. when publishing to a pump as an administrator, a common
choice for post_exchange is 'xpublic'.

When publishing a product, a user can trigger a script, using
flow callback entry_points such as **after_accept**, and **after_work** 
to modify messages generated about files prior to posting.

post_exchangeSplit <count> (default: 0)
---------------------------------------

The **post_exchangeSplit** option appends a two digit suffix resulting from
hashing the last character of the checksum to the post_exchange name,
in order to divide the output amongst a number of exchanges.  This is currently used
in high traffic pumps to allow multiple instances of winnow, which cannot be
instanced in the normal way.  Example::

    post_exchangeSplit 5
    post_exchange xwinnow

will result in posting messages to five exchanges named: xwinnow00, xwinnow01,
xwinnow02, xwinnow03 and xwinnow04, where each exchange will receive only one fifth
of the total flow.

post_format <name> (default: v03)
---------------------------------

Sets the message format for posted messages. the currently included values are:

* v02 ... used by all existing data pumps for most cases.
* v03 ... default in sr3 JSON format easier to work with.
* wis ... a experimental geoJSON format in flux for the World Meteorological Organization

When provided, this value overrides whatever can be deduced from the post_topicPrefix.


post_on_start
-------------

When starting watch, one can either have the program post all the files in the directories watched
or not. (not implemented in sr3_cpost)

post_topic <string> 
---------------------

Explicitly set a posting topic string, overriding the usual
group of settings. For sarracenia data pumps, this should never be needed,
as the use of post_exchange, post_topicPrefix, and relpath normally builds the right
value for topics for both posting and binding.



post_topicPrefix (default: topicPrefix)
---------------------------------------

Prepended to the sub-topic to form a complete topic hierarchy. 
This option applies to publishing.  Denotes the version of messages published 
in the sub-topics. (v03 refers to `<sr3_post.7.html>`_) defaults to whatever
was received. 


prefetch <N> (default: 1)
-------------------------

The **prefetch** option sets the number of messages to fetch at one time.
When multiple instances are running and prefetch is 4, each instance will obtain up to four
messages at a time.  To minimize the number of messages lost if an instance dies and have
optimal load sharing, the prefetch should be set as low as possible.  However, over long
haul links, it is necessary to raise this number, to hide round-trip latency, so a setting
of 10 or more may be needed.

queueName|queue|queue_name|qn 
-----------------------------

* queueName <name>

By default, components create a queue name that should be unique. The
default queue_name components create follows the following convention:

   **q_<brokerUser>.<programName>.<configName>.<random>.<random>**

Where:

* *brokerUser* is the username used to connect to the broker (often: *anonymous* )

* *programName* is the component using the queue (e.g. *subscribe* ),

* *configName* is the configuration file used to tune component behaviour.

* *random* is just a series of characters chosen to avoid clashes from multiple
  people using the same configurations

Users can override the default provided that it starts with **q_<brokerUser>**.

When multiple instances are used, they will all use the same queue, for trivial
multi-tasking. If multiple computers have a shared home file system, then the
queue_name is written to:

 ~/.cache/sarra/<programName>/<configName>/<programName>_<configName>_<brokerUser>.qname

Instances started on any node with access to the same shared file will use the
same queue. Some may want use the *queue_name* option as a more explicit method
of sharing work across multiple nodes.

queueBind
---------

On startup, by default, Sarracenia redeclares resources and bindings to ensure they
are uptodate.  If the queue already exists, These flags can be
set to False, so no attempt to declare the queue is made, or it´s bindings.
These options are useful on brokers that do not permit users to declare their queues.


queueDeclare
------------
FIXME: same as above.. is this normal?

On startup, by default, Sarracenia redeclares resources and bindings to ensure they
are uptodate.  If the queue already exists, These flags can be
set to False, so no attempt to declare the queue is made, or it´s bindings.
These options are useful on brokers that do not permit users to declare their queues.

randomize <flag>
----------------

Active if *-r|--randomize* appears in the command line... or *randomize* is set
to True in the configuration file used. If there are several notification messages because the 
file is posted by block (the *blocksize* option was set), the block notification messages 
are randomized meaning that they will not be posted

realpathAdjust <count> (Experimental) (default: 0)
--------------------------------------------------

The realpathAdjust option adjusts how much paths are resolved with the C standard realpath 
library routine. The count indicates how many path elements should be ignored, counting
from the beginning of the path with positive numbers, or the end with negative ones.
An adjustment of zero means to apply realpath to the entire path.

Implemented in C, but not python currently. 

realpathFilter <flag> (Experimental)
------------------------------------

the realpathFilter option resolves paths using the C standard realpath library routine,
but only for the purpose of applying accept reject filters. This is used only during
posting.

This option is being used to study some use cases, and may disappear in future.

Implemented in C, but not python currently. 


realpathPost <flag> (Experimental)
----------------------------------

The realpathPost option resolves paths given to their canonical ones, eliminating
any indirection via symlinks. The behaviour improves the ability of watch to
monitor trees, but the trees may have completely different paths than the arguments
given. This option also enforces traversing of symbolic links.

This option is being used to investigate some use cases, and may disappear in future.

sendTo <url>
---------------

Specification of a remote resource to deliver to in a sender.

rename <path>
-------------

With the *rename* option, the user can suggest a destination path for its files. If the given
path ends with '/' it suggests a directory path... If it doesn't, the option specifies a file renaming.
Often used with variable substitutions, to provide dynamic, patterned names.


report and report_exchange
--------------------------

NOTE: **NOT IMPLEMENTEDin sr3, expected to return in future version**
For each download, by default, an amqp report message is sent back to the broker.
This is done with option :

- **report <flag>  (default: True)**
- **report_exchange <report_exchangename> (default: xreport|xs_*username* )**

When a report is generated, it is sent to the configured *report_exchange*. Administrative
components post directly to *xreport*, whereas user components post to their own
exchanges (xs_*username*). The report daemons then copy the messages to *xreport* after validation.

These reports are used for delivery tuning and for data sources to generate statistical information.
Set this option to **False**, to prevent generation of reports.


reset <flag> (default: False)
-----------------------------

When **reset** is set, and a component is (re)started, its queue is
deleted (if it already exists) and recreated according to the component's
queue options.  This is when a broker option is modified, as the broker will
refuse access to a queue declared with options that differ from what was
set at creation.  It can also be used to discard a queue quickly when a receiver
has been shut down for a long period. If duplicate suppression is active, then
the reception cache is also discarded.

The AMQP protocol defines other queue options which are not exposed
via sarracenia, because sarracenia itself picks appropriate values.


retryEmptyBeforeExit: <boolean> (default: False)
------------------------------------------------

Used for sr_insects flow tests. Prevents Sarracenia from exiting while there are messages remaining in the retry queue(s). By default, a post will cleanly exit once it has created and attempted to publish messages for all files in the specified directory. If any messages are not successfully published, they will be saved to disk to retry later. If a post is only run once, as in the flow tests, these messages will never be retried unless retryEmptyBeforeExit is set to True.


retry_refilter <boolean> (default: False)
-----------------------------------------

The **retry_refilter** option alters how messages are reloaded when they are retrieved from
a retry queue. The default way (value: False) is to repeat the transfer using exactly
the same message as before. If **retry_refilter** is set (value: True) then all the
message's calculated fields will be discarded, and the processing re-started from the gather
phase (accept/reject processing will be repeated, destinations re-calculated.)

The normal retry behaviour is use when the remote has had a failure, and need to 
re-send later, while the retry_refilter option is used when recovering from configuration 
file errors, and some messages had incorrect selection or destination criteria.

retry_ttl <duration> (default: same as expire)
----------------------------------------------

The **retry_ttl** (retry time to live) option indicates how long to keep trying to send
a file before it is aged out of a the queue.  Default is two days.  If a file has not
been transferred after two days of attempts, it is discarded.

sanity_log_dead <interval> (default: 1.5*housekeeping)
------------------------------------------------------

The **sanity_log_dead** option sets how long to consider too long before restarting
a component.


shim_defer_posting_to_exit (EXPERIMENTAL)
-----------------------------------------

  (option specific to libsrshim)
  Postpones file posting until the process exits.
  In cases where the same file is repeatedly opened and appended to, this
  setting can avoid redundant notification messages.  (default: False)

shim_post_minterval *interval* (EXPERIMENTAL)
---------------------------------------------

  (option specific to libsrshim)
  If a file is opened for writing and closed multiple times within the interval,
  it will only be posted once. When a file is written to many times, particularly
  in a shell script, it makes for many notification messages, and shell script affects performance.
  subscribers will not be able to make copies quickly enough in any event, so
  there is little benefit, in say, 100 notification messages of the same file in the same second.
  It is wise set an upper limit on the frequency of posting a given file. (default: 5s)
  Note: if a file is still open, or has been closed after its previous post, then
  during process exit processing it will be posted again, even if the interval
  is not respected, in order to provide the most accurate final post.


shim_skip_parent_open_files (EXPERIMENTAL)
------------------------------------------

  (option specific to libsrshim)
  The shim_skip_ppid_open_files option means that a process checks
  whether the parent process has the same file open, and does not
  post if that is the case. (default: True)

sleep <time>
------------

The time to wait between generating events.  When files are written frequently, it is counter productive
to produce a post for every change, as it can produce a continuous stream of changes where the transfers
cannot be done quickly enough to keep up.  In such circumstances, one can group all changes made to a file
in *sleep* time, and produce a single post.

statehost <False|True> ( default: False )
-----------------------------------------

In large data centres, the home directory can be shared among thousands of
nodes. Statehost adds the node name after the cache directory to make it
unique to each node. So each node has it's own statefiles and logs.
example, on a node named goofy,  ~/.cache/sarra/log/ becomes ~/.cache/sarra/goofy/log.

strip <count|regexp> (default: 0)
---------------------------------

You can modify the relative mirrored directories with the **strip** option.
If set to N  (an integer) the first 'N' directories from the relative path
are removed. For example::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   strip     3
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/WGJ/201312141900_WGJ_PRECIP_SNOW.gif
when a regexp is provide in place of a number, it indicates a pattern to be removed
from the relative path.  For example if::

   strip  .*?GIF/

Will also result in the file being placed the same location.
Note that strip settings can be changed between directory options.

NOTE::
    with **strip**, use of **?** modifier (to prevent regular expression *greediness* ) is often helpful. 
    It ensures the shortest match is used.

    For example, given a file name:  radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.GIF
    The expression:  .*?GIF   matches: radar/PRECIP/GIF
    whereas the expression: .*GIF matches the entire name.

sourceFromExchange <flag> (default: off)
------------------------------------------

The **sourceFromExchange** option is mainly for use by administrators.
If messages received are posted directly from a source, the exchange used
is 'xs_<brokerSourceUsername>'. Such messages could be missing *source* and *from_cluster*
headings, or a malicious user may set the values incorrectly.
To protect against both problems, administrators should set the **sourceFromExchange** option.

When the option is set, values in the message for the *source* and *from_cluster* headers will then be overridden::

  self.msg.headers['source']       = <brokerUser>
  self.msg.headers['from_cluster'] = cluster

replacing any values present in the message. This setting should always be used when ingesting data from a
user exchange. These fields are used to return reports to the origin of injected data.
It is commonly combined with::

       *mirror true*
       *sourceFromExchange true*
       *directory ${PBD}/${YYYYMMDD}/${SOURCE}*

To have data arrive in the standard format tree.


subtopic <amqp pattern> (default: #)
------------------------------------

Within an exchange's postings, the subtopic setting narrows the product selection.
To give a correct value to the subtopic,
one has the choice of filtering using **subtopic** with only AMQP's limited wildcarding and
length limited to 255 encoded bytes, or the more powerful regular expression
based  **accept/reject**  mechanisms described below. The difference being that the
AMQP filtering is applied by the broker itself, saving the notices from being delivered
to the client at all. The  **accept/reject**  patterns apply to messages sent by the
broker to the subscriber. In other words,  **accept/reject**  are client side filters,
whereas **subtopic** is server side filtering.

It is best practice to use server side filtering to reduce the number of notification messages sent
to the client to a small superset of what is relevant, and perform only a fine-tuning with the
client side mechanisms, saving bandwidth and processing for all.

topicPrefix is primarily of interest during protocol version transitions,
where one wishes to specify a non-default protocol version of messages to
subscribe to.

Usually, the user specifies one exchange, and several subtopic options.
**Subtopic** is what is normally used to indicate messages of interest.
To use the subtopic to filter the products, match the subtopic string with
the relative path of the product.

For example, consuming from DD, to give a correct value to subtopic, one can
browse the our website  **http://dd.weather.gc.ca** and write down all directories
of interest.  For each directory tree of interest, write a  **subtopic**
option as follow:

 **subtopic  directory1.*.subdirectory3.*.subdirectory5.#**

::

 where:  
       *                matches a single directory name 
       #                matches any remaining tree of directories.

note:
  When directories have these wild-cards, or spaces in their names, they
  will be URL-encoded ( '#' becomes %23 )
  When directories have periods in their name, this will change
  the topic hierarchy.

  FIXME:
      hash marks are URL substituted, but did not see code for other values.
      Review whether asterisks in directory names in topics should be URL-encoded.
      Review whether periods in directory names in topics should be URL-encoded.

One can use multiple bindings to multiple exchanges as follows::

  exchange A
  subtopic directory1.*.directory2.#

  exchange B
  subtopic *.directory4.#

Will declare two separate bindings to two different exchanges, and two different file trees.
While default binding is to bind to everything, some brokers might not permit
clients to set bindings, or one might want to use existing bindings.
One can turn off queue binding as follows::

  subtopic None

(False, or off will also work.)

sundew_compat_regex_first_match_is_zero (default: off)
------------------------------------------------------

When numbering groups in match patterns, Sundew groups start from 0.
Python regular expressions use the zeroth group to represent the entire string, and each match
group starts from 1. It is considered less surprising to conform to Python conventions,
but doing so unilaterally would break compatbility.  So here is a switch to use
when bridging between Sundew, sarra v2 and sr3.  Eventually, this should always be off.
Examples:

* sundew_compat_regex_first_match_is_zero: True
* input url:  https://hpfx.collab.science.gc.ca/20231127/WXO-DD/meteocode/que/cmml/TRANSMIT.FPCN71.11.27.1000Z.xml
* accept pattern: .*/WXO-DD/meteocode/(atl|ont|pnr|pyr|que)/.*/TRANSMIT\.FP([A-Z][A-Z]).*([0-2][0-9][0-6][0-9]Z).*
* directory setting: /tmp/meteocode/${2}/${0}/${1}
* resulting directory:  /tmp/meteocode/1000Z/que/CN

in contrast, to get the same result:

* sundew_compat_regex_first_match_is_zero: False
* directory setting: /tmp/meteocode/${3}/${1}/${2}
* to get the same result.

folks who research python re will normally produce the latter version first.


timeCopy (default: on)
----------------------

On unix-like systems, when the *ls* commend or a file browser shows modification or
access times, it is a display of the posix *st_atime*, and *st_ctime* elements of a
struct struct returned by stat(2) call.  When *timeCopy* is on, headers
reflecting these values in the messages are used to restore the access and modification
times respectively on the subscriber system. To document delay in file reception,
this option can be turned off, and then file times on source and destination compared.

When set in a posting component, it has the effect of eliding the *atime* and *mtime*
headers from the messages.


timeout <interval> (default: 0)
-------------------------------

The **timeout** option, sets the number of seconds to wait before aborting a
connection or download transfer (applied per buffer during transfer).


timezone <string> (default: UTC)
--------------------------------

Interpret listings from an FTP server as being in the given timezone as per `pytz <pypi.org/project/pytz>`_
Examples: Canada/Pacific, Pacific/Nauru, Canada/Eastern, Europe/Paris
Has no effect other than in when polling an FTP server.


tlsRigour (default: medium)
---------------------------

tlsRigour can be set to: *lax, medium, or strict*, and gives a hint to the
application of how to configure TLS connections. TLS, or Transport Level
Security (used to be called Secure Socket Layer (SSL)) is the wrapping of
normal TCP sockets in standard encryption. There are many aspects of TLS
negotiations, hostname checking, Certificate checking, validation, choice of
ciphers. What is considered secure evolves over time, so settings which, a few
years ago, were considered secure, are currently aggressively deprecated. This
situation naturally leads to difficulties in communication due to different
levels of compliance with whatever is currently defined as rigourous encryption.

If a site being connected to, has, for example, and expired certificate, and
it is nevertheless necessary to use it, then set tlsRigour to *lax* and
the connection should succeed regardless.


topic <string> 
--------------

Explicitly set a subscribing topic string, overriding the value usually
derived from a group of settings. For sarracenia data pumps, this should never be needed,
as the use of *exchange*, *topicPrefix*, and *subtopic* normally builds the right
value.


topicPrefix (default: v03)
--------------------------

prepended to the sub-topic to form a complete topic hierarchy. 
This option applies to subscription bindings.
Denotes the version of messages received in the sub-topics. (v03 refers to `<sr3_post.7.html>`_)

users <flag> (default: false)
-----------------------------

As an adjunct when the *declare* action is used, to ask sr3 to declare users
on the broker, as well as queues and exchanges.

v2compatRenameDoublePost <flag> ( default: false)
-------------------------------------------------

version 3 of Sarracenia features improved logic around file renaming, using a single message per rename operation.
Version 2 required two posts.  When posting, in a mirroring situation, for consumption by v2 clients, this flag 
should be set. 

varTimeOffset (default: 0)
--------------------------

For example::

  varTimeOffset -7m 

will cause variable substitions that involve the date/time substitutions.
so in a pattern like ${YYYY}/${MM}/${DD} will be evaluated to be the
date, evaluated seven minutes in the past.




vip - ACTIVE/PASSIVE OPTIONS
----------------------------

The **vip** option indicates that a configuration must be active on only 
a single node in a cluster at a time, a singleton. This is typically 
required for a poll component, but it can be used in senders or other
cases.

**subscribe** can be used on a single server node, or multiple nodes
could share responsibility. Some other, separately configured, high availability
software presents a **vip** (virtual ip) on the active server. Should
the server go down, the **vip** is moved on another server, and processing
then happens using the new server that now has the vip active.
Both servers would run an **sr3 instance**::

 - **vip          <list>          []**

When you run only one **sr3 instance** on one server, these options are not set,
and subscribe will run in 'standalone mode'.

In the case of clustered brokers, you would set the options for the
moving vip.

**vip 153.14.126.3**

When an **sr3 instance** does not find the vip, it sleeps for 5 seconds and retries.
If it does, it consumes and processes a message and than rechecks for the vip.
Multiple vips form a list, where any individual address being active is enough.

SEE ALSO
========

`sr3(1) <sr3.1.html>`_ - Sarracenia main command line interface.

`sr3_post(1) <sr3_post.1.html>`_ - post file notification messages (python implementation.)

`sr3_cpost(1) <sr3_cpost.1.html>`_ - post file announcemensts (C implementation.)

`sr3_cpump(1) <sr3_cpump.1.html>`_ - C implementation of the shovel component. (copy messages)

**Formats:**

`sr3_post(7) <sr_post.7.html>`_ - the format of notification messages.

**Home Page:**

`https://metpx.github.io/sarracenia <https://metpx.github.io/sarracenia>`_ - Sarracenia: a real-time pub/sub data sharing management toolkit

