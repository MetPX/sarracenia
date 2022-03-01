
Porting v2 Plugins to Sr3
=========================

This is a guide to porting plugins from Sarracenia version 2.X (metpx-sarracenia) to Sarracenia version 3.x (metpx-sr3)
If you are new to Sarracenia, and have no experience or need to look at v2 plugins, don't read this. it will just
confuse you. This guide is for those who need to take existing v2 plugins and port them to v3.
You are better off getting a fresh look by looking at the jupyter notebook examples::

    https://github.com/MetPX/sarracenia/tree/v03_wip/jupyter

Which provide an introduction to v3 without confusing references to v2.  In fact, Those notebooks
are probably a good pre-requisite for everyone, to understand how v3 plugins work, before trying
to port v2 ones. 

Sample v3 plugin::

    https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/log.py

Generally speaking v2 plugins were bolted onto existing code to allow some modification of behaviour.
v2 plugins when through a first generation, when only single routines were declared (e.g. *on_message*), 
and a second generation, when whole classes (e.g. *plugin*) were declared, but still in a stilted way.

Sr3 plugins are core design elements, composed together to implement part of Sarracenia itself. V3 plugins 
should be easier for Python programmers to debug and implement, and are strictly more flexible and powerful
than the v2 mechanism.

 * v3 uses standard python syntax, not v2's strange things ... e.g. *self.plugins*, *parent.logger*, Why doesn't *import* work?
 * standard python import; Syntax errors are detected and reported *the normal way*
 * v3 classes are designed to be usable outside the CLI itself (see jupyter notebook examples)
   callable by application programmers in their own code, like any other python library.
 * v3 classes can be sub-classed to add core functionality, like new message or file transport protocols.
 
There are also a couple walkthrough videos on Youtube showing simple v2 -> v3 ports:
 - `Sender (10 min) <https://www.youtube.com/watch?v=rUazjoGzPac>`_
 - `Poll (20 min) <https://www.youtube.com/watch?v=P20M9ojn_Zw>`_

File Placement
==============

v2 places configuration files under ~/.config/sarra, and state files under ~/.cache/sarra

v3 places configuration files under ~/.config/sr3, and state files under ~/.cache/sr3

v2 has a C implementation of sarra called sarrac. The C implementation for v3, is called sr3c,
and is the same as the v2 one, except it uses the new file locations.

Command Line Difference
=======================

Briefly, the sr3 entry point is used to start/stop/status things::

  v2:  sr_*component* start config

  v3:  sr3 start *component*/config

In sr3, one can also use file globbing style specifications to ask for a command
to be invoked on a group of configurations, wheras in v2, one could only operate on one at a time.

sr3_post is an exception to this change in that it works like v2's sr_post did, being
a tool for interactive posting.


What Will Work Without Change
=============================

The first step in porting a configuration subscribe/X to v3, is just to copy the configuration file from
~/.config/sarra to the corresponding location in ~/.config/sr3 and try::

   sr3 show subscribe/X

The *show* command is new in sr3 and provides a way to view the configuration after 
it has been parsed. Most of it should work, unless you have do_* plugins. 

Examples of things that should work:

* all settings from v2 config files should be recognized by the v3 option parser, and converted
  to v3 equivalents, when they exist. v2 option -> v3 option some examples:

  * accept_scp_threshold -> accel_threshold
  * heartbeat -> housekeeping
  * chmod_log -> default_log_mode
  * loglevel -> logLevel
  * post_base_url -> post_baseUrl
  * post_rate_limit -> message_rate_max
  * cache, suppress_duplicates ->  nodupe_ttl
  * topic_prefix -> topicPrefix 

  The topic_prefix in v2 is 'v02.post'  in v3, the default is 'v03'. If topic_prefix is omitted 
  you will need to add the line *topicPrefix v02.post* to get the same behaviour as v2. Could 
  also be placed in ~/.config/sr3/default.conf if the case is too common.
  One might have to similarly override the sr3 default for post_topicPrefix.

* all on_message, on_file, on_post, on_heartbeat, routines will work, by sr3 using 
  the flowcb/v2wrapper.py plugin which will be automatically invoked when v2 plugins are 
  seen in the config file.

  Note that ideally, v2wrapper is used as a crutch to allow one to have a functional configuration
  quickly. There is a performance hit to using v2wrapper, and 


Things that will not work:

* do_*  they are just fundamentally different in v3.

If you have a configuration with a do_* plugin, then you need this guide, from day 1.
to set a configuration to use a plugin, in v2 one used the *plugin* option.
The equivalent to that in v3 is *callback*::

  v2: plugin x
  v3: callback x3

where x3 is the v3 ported version of the plugin made for v2. for this shorthand to work,
there should be a file named x3.py somewhere in the PYTHONPATH (~/.config/plugins is added
for convenience.) and that python source file needs to have a class X3.py declared in it
(same as the file name but first letter capitalized.)  If you need to name it differently
there is a longer form that allows one to violate the convention::

  flowCallback x3.MyFavouriteClass

the individual routine plugin declarations on_message, on_file, etc... are not a way of
doing things in v3. You declare callbacks, and have them contain the entry points you need.


Coding Differences between plugins in v2 vs. Sr3
================================================

The API for adding or customizing functionality in sr3 is quite different from v2.
In general, v3 plugins:

* **are usually subclassed from sarracenia.flowcb.FlowCB.**

  In v2, one would declare::

      class Msg_Log(object): 

  v3 plugins are normal python source files (no magic at the end.)
  they are subclassed from sarracenia.flowcb::

      from sarracenia.flowcb import FlowCB

      class myplugin(FlowCB):

  To create an *after_accept* plugin in *myplugin* class, define a function
  with that name, and the appropriate signature.

* **are pythonic, not weird** : In v2, you need the last line to include something like::

     self.plugin = 'Msg_Delay'

  for a second generation plugin, the first generation ones had
  something like::

      msg_2localfile = Msg_2LocalFile(None)
      self.on_message = msg_2localfile.on_message

  at the end to assign entry points explicitly. either way a naive python
  of the file would invariably fail without some sort of test harness being
  wrapped around it. (**In v3, delete these lines (usually located at the bottom of the file**)

  In v2, there were strange issues with imports, resulting in people putting
  import statements within some functions. That problem is fixed in v3;
  put the necessary imports at the beginning of the file, like any other python
  module **and remove the imports located within functions**.

  in v3 one can at least check syntax by doing *import X* in any python interpreter.

* **v3 plugins can be used by application programmers.** The plugins aren't
  bolted on after the fact, but a core element, implementing duplicate 
  suppression, reception and transmission of messages, file monitoring,
  etc.. understanding v3 plugins gives people important clues to being
  able to work on sarracenia itself.

  v3 plugins can be *imported* into existing applications to add the ability
  to interact with sarracenia pumps without using the Sarracenia CLI.
  see jupyter tutorials. 

* **use standard python logging** ::

      import logging
  
  Make sure the following logger declaration is after the **last _import_** in the top of the file::

      logger = logging.getLogger(__name__)

      #when you want a log message:
      logger.warning( ... )
      
      # In VI you can use the global replace:
      :%s/parent.logger/logger/g

  In v3 plugins: *logger.x* replaces *parent.logger.x* found in v2 plugins.
  In v2, to test outside the app, one had to build a test harness that had
  parent.logger declared. sometimes there is also self.logger x... dunno why...
  don't ask.


* *have options as an argument to the __init__(self, options): routine*.
  by convention, most modules include::

       self.o = options 

  so in v2 if you need to access settings, *replace parent.setting by self.o.setting*.
  
      # In VI you can use the global replace:
      :%s/parent/self.o/g

   Likewise in the __init__ function needs the self.o with options

* **you can see what options are active by starting a component with the 'show' command** ::

      sr3 show subscribe/myconf

  these settings can be access from self.o

* in the settings generally, **look for replacement of many underscores with camelCase** in sr3, as per WMO standardization.
  the exception being post\_  where the underscore seems to better match intent.  so:

  *  post_base_dir becomes post_baseDir,   
  *  post_broker is unchanged. 
  *  post_base_url -> post_baseUrl

* **messages are python dictionaries** , so `msg.relpath` becomes `msg['relPath']`
  v3 messages, as dictionaries are the default internal representation.

* **plugins operate on batches of messages** v2 *on_message* gets parent as a parameter,
  and the message is in parent.message. In v3, *after_accept* has worklist as an
  option, which is python list of messages, maximum length being fixed by the
  *batch* option. So the general organization for after_accept, and after_work is::

      new_incoming=[]
      for message in old_list:
          if good:
             new_incoming.append(message)
          if bad:
             worklist.rejected.append(message)
      worklist.incoming=new_incoming
      
  Note: plugins must be moved from the /plugins directory to the /flowcb directory, 
  and specifically, on_message plugins that turn into after_accept ones should be 
  placed in the flowcb/accept directory (so simialr plugins can be grouped together).
  
  In *after_work*, the replacement for v2 *on_file*, the operations are on:

  * worklist.ok (transfer succeeded.)
  * worklist.failed (transfers that failed.)

  In the case of receiving a .tar file and expanding into to individual files,
  the *after_work* routine would change the worklist.ok to contain messages for
  the individual files, rather than the original collective .tar.

  Note: on_file plugins that become after_work plugins should be placed in the
  /flowcb/after_work directory
  
* **No Need to set message fields in plugins**
  in v2, one would need to set partstr, and sumstr for v2 messages in plugins. 
  This required an excessive understanding of message formats, and meant that 
  changing message formats required modifying plugins (v03 message format is
  not supported by most v2 plugins, for example). To build a message from a 
  local file in a v3 plugin::

     import sarracenia

     m = sarracenia.Message.fromFileData(sample_fileName, self.o, os.stat(sample_fileName) )

  just look at  `do_poll -> poll`_


* **rarely, involve subclassing of moth or transfer classes.**
  The sarracenia.moth class implements support for message queueing protocols
  that support topic hierarchy based subscriptions. There are currently
  two subclasses of Moth: amqp (for rabbitmq), and mqtt.  It would be
  great for someone to add an amq1 (for qpid amqp 1.0 support.)

  It might be reasonable to add an SMTP class there for sending email,
  not sure.

  The sarracenia.transfer classes include http, ftp, and sftp today.
  They are used to interact with remote services that provide a fileish
  interface (supporting things like listing files, and downloading and/or
  sending.) Other sub-classes such as S3, IPFS, or webdav, would be 
  great additions.


Configuration Files
===================

in v2, the primary configuration option to declare a plugin is::

   plugin X

Generally speaking, there should be a file plugins/x.py
with a class X.py in that file in either ~/.config/plugins
or in the sarra/plugins directory in the package itself.
This is already a second generation style of plugin declaration
in Sarracenia. The original version, one declared individual
entry points::

    on_message, on_file, on_post, on_..., do_... 

In Sr3, the above entries are taken to be requests for v2
plugins, and should only be used for continuity reasons.
Ideally, one should invoke v3 plugins like so::

   callback x

Where x will be a subclass of sarracenia.flowcb, which
will contain a class X (first letter capitalized) in the
file x.py a in the python search path, or in the
*sarracenia/flowcb* directory included as part of the package.
This is actually a shorthand version of the python import.
If you need to declare a callback that does not obey that
convention, one can also use a more flexible but longer-winded::

  flowcb sarracenia.flowcb.x.X

the above two are equivalent. The flowcb version can be used to import classes 
that don't match the convention of the x.X (a file named x.py containing a class called X.py)

Configuration Upgrade
=====================

Once a plugin is ported, one can also arrange for the v3 option parser to recognize a v2
plugin invocation and replace it with a v3 one.  looking in sarracenia/config.py,
there is a data structure *convert_to_v3*.  A sample entry would be::

    .
    .
    .
    'on_message' : {
             'msg_delete': [ 'flowCallback': 'sarracenia.flowcb.filter.deleteflowfiles.DeleteFlowFiles' ]
    .
    .
    .


A v2 config file containing a line *on_message msg_delete* would be replaced by the parser with
effectively::

    flowCallback sarracenia.flowcb.filter.deleteflowfiles.DeleteFlowFiles



Options
=======

In v2, one would declare settings to be used by a plugin in the __init__ routine, with 
the *declare_option*.::

    parent.declare_option('poll_usgs_stn_file')

it the values are always of type *list*, so usually, one uses the value by
picking the first value::

    parent.poll_usgs_stn_file[0]

In v3, that would be replaced with::

    self.o.add_option( option='poll_usgs_stn_file', kind='str', default_value='hoho' )

where in version 3 there is now types and default value setting included without additional 
code. it would be referred to in other routines like so::

    self.o.poll_usgs_stn_file



    
Mapping Entry Points
====================

for a comprehensive look at the v3 entry points, have a look at:

https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/__init__.py

for details.

on_message, on_post --> after_accept
------------------------------------

v2: receives one message, returns True/False


v3: receives worklist 
    modify worklist.incoming 
    transferring rejected messages to worklist.rejected, or worklist.failed.

Sample flow::

  def after_accept(self, worklist):

     ...

     new_incoming=[]
     for m in worklist.incoming:

          if message is useful to us:
             new_incoming.append(m)
          else
             worklist.rejected.append(m)        
 
     worklist.incoming = new_incoming



examples:
  v2: plugins/msg_gts2wistopic.py
  v3: flowcb/wistree.py


on_file --> after_work
----------------------

v2: receives one message, returns True/False

v3: receives worklist 
    modify worklist.ok (transfer has already happenned.) 
    transferring rejected messages to worklist.rejected, or worklist.failed.

    can also be used to work on worklist.failed (retry logic does this.)

examples:


on_heartbeat -> on_housekeeping
-------------------------------

v2: receives parent as argument.
    will work unchanged.


v3: only receives self (which should have self.o replacing parent)

examples:

  * v2: hb_cache.py -- cleans out cache (references sr_cache.)
  * v3: flowcb/nodupe.py -- implements entire caching routine.



do_poll -> poll
-----------------

v2: call do_poll from plugin.

 * protocol to use the do_poll routine is identified by registered_as() entry point
    which is mandatory to provide.
 * requires manually constructing fields for messages, is message verison specific,
   (generally do not support v03 messages.)
 * explicitly calls poll entry points.
 * runs, one must worry about whether one has the vip or not to decide what processing
   to do in each plugin.
 * poll_without_vip setting available.

v3: define poll in a flowcb class.

 * poll only runs when has_vip is true.

 * registered_as() entry point is moot.

 * gather runs always, and is used to subscribe to post done by node that has the vip,
   allowing the nodupe cache to be kept uptodate.

 * api defined to build messages from file data regardless of message format.

 * returns a list of messages to be filtered and posted.


To build a message, without a local file, use fromFileInfo sarracenia.message factory::
  
     import dateparser
     import paramiko
     import sarracenia

     gathered_messages=[]

     m = sarracenia.Message.fromFileInfo(sample_fileName, cfg)

builds an message from scratch.

One can also build an supply a simulated stat record to fromFileInfo factory,
using the *paramiko.SFTPAttributes()* class. For example, using the dateparser 
routines to convert however the remote server lists the date and time, as well 
as determine the file size and permissions in effect::


     pollmtime = dateparser.parse( ... , settings={ ... TO_TIMEZONE='utc' } )
     mtimestamp = time.mktime( pollmtime.timetuple() )

     fsize = info_from_poll #about the size of the file to download
     st = paramiko.SFTPAttributes()
     st.st_mtime=mtimstamp
     st.st_atime=mtimestamp
     st.st_size=fsize
     st.st_mode=0o666 
     m = sarracenia.Message.fromFileInfo(sample_fileName, cfg, st)

One should fill in the *SFTPAttributes* record if possible, since the duplicate
cache use metadata if available. The better the metadata, the better the
detection of changes to existing files.

Once the message is built, append it to the list::

     gathered_messages.append(m) 
  
and at the end::

     return gathered_messages

 

vip processing in poll
~~~~~~~~~~~~~~~~~~~~~~

If you have vip set in v2, all participating nodes poll the upstream server
and maintain the list of current files, they just don't publish the result.
So if you have 8 servers sharing a vip, all eight are polling, kind of sad.
There is also the poll_no_vip setting, and plugins often have to check if they
have the vip or not.

In v3, only the server with the vip polls. The plugins don't need to check.
The other participating servers subscribe to where the poll posts to,
to keep update their recent_files cache.

examples:
 * flowcb/poll/airnow.py

on_html_page -> subclass flowcb/poll
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is a v2 plugin nsa_mls_nrt.py::

    #!/usr/bin/env python3                                                                                                                          
                                                  
    class Html_parser():                                                                                                                            
                                                  
        def __init__(self,parent):                                                                                                                  
                                                  
            parent.logger.debug("Html_parser __init__")
            import html.parser
    
            self.parent = parent
            self.logger = parent.logger
    
            self.parser = html.parser.HTMLParser()
            self.parser.handle_starttag = self.handle_starttag
            self.parser.handle_data     = self.handle_data
    
    
        def handle_starttag(self, tag, attrs):
            for attr in attrs:
                c,n = attr
                if c == "href" and n[-1] != '/':
                   self.myfname = n.strip().strip('\t')
    
        def handle_data(self, data):
            import time
    
            if 'MLS-Aura' in data:
                   self.logger.debug("data %s" %data)
                   self.entries[self.myfname] = '-rwxr-xr-x 1 101 10 ' +'_' + ' ' + 'Jan 1 00:01' + ' ' + data
                   self.logger.debug("(%s) = %s" % (self.myfname,self.entries[self.myfname]))
            if self.myfname == None : return
            if self.myfname == data : return
            ''' 
            # at this point data is a filename like
            name = data.strip().strip('\t')
    
            parts = name.split('_')
            if len(parts) != 3 : return
    
            words = parts[1].split('.')
            sdate  = ' '.join(words[:4])
            t      = time.strptime(sdate,'%Y %j %H %M')
    
            # accept file if 1 month old in sec  60 sec* 60min * 24hr * 31days
    
            epochf = time.mktime(t)
            now    = time.time()
            elapse = now - epochf
    
            if elapse > self.month_in_secs : return
    
            # build an ls line from date in file ... size set to 0  since not provided
    
            mydate = time.strftime('%b %d %H:%M',t)
     
            mysize = '_'
     
            self.entries[self.myfname] = '-rwxr-xr-x 1 101 10 ' + mysize + ' ' + mydate + ' ' + data
            self.logger.debug("(%s) = %s" % (self.myfname,self.entries[self.myfname]))
            '''
    
        def parse(self,parent):
            self.logger.debug("Html_parser parse")
            self.entries = {}
            self.myfname = None
    
            self.logger.debug("data %s" % parent.data)
            self.parser.feed(parent.data)
            self.parser.close()
    
            parent.entries = self.entries
    
            return True
    
    html_parser = Html_parser(self)
    self.on_html_page = html_parser.parse

The plugin has a main "parse" routine, which invokes the html.parser class, where data_handler
is called for each line, gradually building the self.entries dictionary where each entry is
a string constructed to resemble a line of *ls* command output.

This plugin is a near exact copy of the html_page.py plugin used by default.
The on_html_page entry point for plugins is replaced by a completely different
mechanism. Most of the logic of v2 poll in sr3 is in the new sarracenia.FlowCB.Poll class.
Logic from the v2 plugins/html_page.py, used by default, is now part of this 
new Poll class, subclassed from flowcb, so basic HTML parsing is built-in.

Another change from v2 is that there was far more string manipulation in the old
version. in sr3 polls, most string maniupulation has been replaced by filling an 
paramiko.SFTPAttributes structure as soon as possible.

So the way to replace on_html_page in sr3 is by sub-classing Poll.  Here is an 
sr3 version of same plugin (nasa_mls_nrt.py)::

    import logging
    import paramiko
    import sarracenia
    from sarracenia import nowflt, timestr2flt
    from sarracenia.flowcb.poll import Poll
    
    logger = logging.getLogger(__name__)
    
    class Nasa_mls_nrt(Poll):
    
        def handle_data(self, data):
    
            st = paramiko.SFTPAttributes()
            st.st_mtime = 0
            st.st_mode = 0o775
            st.filename = data
    
            if 'MLS-Aura' in data:
                   logger.debug("data %s" %data)
                   #self.entries[self.myfname] = '-rwxr-xr-x 1 101 10 ' +'_' + ' ' + 'Jan 1 00:01' + ' ' + data
                   self.entries[data]=st
    
                   logger.info("(%s) = %s" % (self.myfname,st))
            if self.myfname == None : return
            if self.myfname == data : return

( https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/poll/nasa_mls_nrt.py )
and matching config file provided here:
( https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/examples/poll/nasa-mls-nrt.conf )

The new class is declared as a subclass of Poll, and only the needed
The HTML routine (handle_data) need be written to override the behaviour
provided by the parent class.

This solution is less than half the size of the v2 one, and permits
all manner of flexibility by allowing replacement of any or all elements
of the poll class.


on_line -> poll subclassing
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similarly to on_html_page above, all uses of on_line in the previous version
were about re-formatting lines to be parseable. the on_line routine can be
similarly sub-classed to replace it.  One had to modify the parent.line
string to be parseable by the built in *ls* style line parsing.

In sr3, on_line is expected to return a populated paramiko.SFTPAttributes field, similar
to the way on_html_page works (but only a single one instead of a dictionary of them.)
With the more flexible date parsing in sr3, there has been no identified need for on_line
on which to build an example.



do_send -> send:
~~~~~~~~~~~~~~~~

v2: do_send could be either a standalone routine, or associated with a protocol type

* based on registered_as()  so the destination determines whether it is used or not.

* accepts parent as an argument.
 
* returns True on success, False on failure.

* will typically have a registered_as() entry point to say which protocols to use a sender for.

    
v3: send(self,msg) 

* use the provided msg to do sending.

* returns True on success, False on failure.

* registered as is not used anymore, can be deleted.

* The send entry_point overrides all sends, and is not protocol specific.
  To add support for new protocols, subclass sarracenia.transfer instead.


examples:
  * flowcb/send/email.py


do_download -> download:
------------------------

create a flowCallback class with a *download* entry point.

* accepts a single message as an argument.

* returns True if download succeeds.

* if it returns False, the retry logic applies (download will be called again
  then placed on the retry queue.)

* use msg['new_dir'], msg['new_file'], msg['new_inflight_path'] 
  to respect settings such as *inflight* and place file properly.
  (unless changing that is motivation for the plugin.)

* might be a good idea to verify the checksum of the downloaded data.
  if the checksum of the file downloaded does not agree with what is in
  the message, duplicate suppression fails, and looping results.
   
* one case of download is when retrievalURL is not a normal file download.
  in v03, there is a retPath fields for exactly this case. This new feature
  can be used to eliminate the need for download plugins.  Example:

  in v2:

      * https://github.com/MetPX/sarracenia/blob/v2_stable/sarra/plugins/poll_noaa.py 

      * https://github.com/MetPX/sarracenia/blob/v2_stable/sarra/plugins/download_noaa.py

  is ported to sr3:

      * https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/poll/noaa_hydrometric.py

  The ported result sets the new field *retPath* ( retrieval path ) instead of new_dir and new_file 
  fields, and normal processing of the *retPath* field in the message will do a good download, no
  plugin required. 




v3 only: post,gather
--------------------

The polling/posting is actually done in flow callback (flowcb) classes.
The exit status does not matter, all such routines will be called in order.

The return of a gather is a list of messages to be appended to worklist.incoming

The return of post is undefined. The whole point is to create a side-effect
that affects some other process or server.


examples: 
 * flowcb/gather/file.py - read files from disk (for post and watch)
 * flowcb/gather/message.py - how messages are received by all components
 * flowcb/post/message.py - how messages are posted by all components.
 * flowcb/poll/nexrad.py - this polls NOAA's AWS server for data.
   install a configuration to use it with *sr3 add poll/aws-nexrad.conf* 


v3 Complex Examples
-------------------


flowcb/nodupe
~~~~~~~~~~~~~

duplicate suppression in v3, has:

*  an after_accept routing the prunes duplicates from worklist.incoming.
   ( adding non-dupes to the reception cache.)


flowcb/retry 
~~~~~~~~~~~~

  * has an after_accept function to append messages to the 
    incoming queue, in order to trigger another attempt to process them.
  * has an after_work routine doing something unknown... FIXME.
  * has a post function to take failed downloads and put them
    on the retry list for later consideration.
