
=========================
Porting V2 Plugins to Sr3
=========================

This is a guide to porting plugins from Sarracenia version 2.X (metpx-sarracenia) to 
Sarracenia version 3.x (metpx-sr3)

.. Contents::

.. warning:: If you are new to Sarracenia, and have no experience or need to look at v2 plugins,
   don't read this. it will just confuse you. **This guide is for those who need to take existing
   v2 plugins and port them to Sr3.**  You are better off getting a fresh look by looking at the
   `jupyter notebook examples <../Tutorials>`_ which provide an introduction to sr3 without
   the confusing references to v2.
   
.. warning:: Even if you actually need to port v2 plugins to sr3, you still should likely be
   familiar with sr3 plugins before attempting to port one. Resources for that:

   `writing Sarra Plugins <../Explanation/SarraPluginDev.html>`_
   
    Another resource is the `jupyter notebook examples <../Tutorials>`_ 

    The material here describes how v2 plugins worked in detail, without necessarily
    describing sr3 ones. Some knowledge of sr3 callback's is necessary.

`Sample Sr3 plugin <../Reference/flowcb.html#module-sarracenia.flowcb.log>`_

Generally speaking v2 plugins were bolted onto existing code to allow some modification 
of behaviour. First generation V2 plugins had only single routines declared (e.g. *on_message*), 
while second generation ones used a whole classes (e.g. *plugin*) were declared, but 
still in a stilted way.

Sr3 plugins are core design elements, composed together to implement part of 
Sarracenia itself. V3 plugins should be easier for Python programmers to debug 
and implement, and are more flexible and powerful than the v2 mechanism.

 * v3 uses standard python syntax, not v2's strange *self.plugins*, *parent.logger*,
   and oh gee why doesn't *import* work?
 * Standard python imports; Syntax errors are detected and reported *the normal way*
 * v3 classes are designed to be usable outside the CLI itself (see jupyter notebook examples)
   callable by application programmers in their own code, like any other python library.
 * v3 classes can be sub-classed to add core functionality, like new notification message or file 
   transport protocols.
 
.. tip::
  There are also a couple walkthrough videos on Youtube showing simple v2 -> v3 ports:
   - `Sender (10 min) <https://www.youtube.com/watch?v=rUazjoGzPac>`_
   - `Poll (20 min) <https://www.youtube.com/watch?v=P20M9ojn_Zw>`_

File Placement
--------------

v2 places configuration files under ~/.config/sarra, and state files under ~/.cache/sarra

v3 places configuration files under ~/.config/sr3, and state files under ~/.cache/sr3

v2 has a C implementation of sarra called sarrac. The C implementation for v3, is called sr3c,
and is the same as the v2 one, except it uses the v3 file locations.

Command Line Difference
-----------------------

Briefly, the sr3 entry point is used to start/stop/status things::

  v2:  sr_*component* start config

  v3:  sr3 start *component*/config

In sr3, one can also use file globbing style specifications to ask for a command
to be invoked on a group of configurations, wheras in v2, one could only operate on one at a time.

.. caution::
  **sr3_post** is an exception to this change in that it works like v2's sr_post did, being
  a tool for interactive posting.


What Will Work Without Change
-----------------------------

The first step in porting a configuration subscribe/X to v3, is just to copy the 
configuration file from ~/.config/sarra to the corresponding location in ~/.config/sr3 and try::

   sr3 show subscribe/X

The *show* command is new in sr3 and provides a way to view the configuration after 
it has been parsed. Most of it should work, unless you have do_* plugins. 
As an alternative to copying the old configuration file, one can use::

  sr3 convert subscribe/X

To do all the mechanical changes of directives, and to have a more sr3 centric 
configuration file that will better match current documentation.

Examples of things that should work:

* all settings from v2 config files should be recognized by the v3 option parser, and converted
  to v3 equivalents, ie:

  ========================== ===============
  v2 Option                  sr3 Option
  ========================== ===============
  accept_scp_threshold       accelThreshold
  heartbeat                  housekeeping
  chmod_log                  permLog
  loglevel                   logLevel
  post_base_url              post_baseUrl
  post_rate_limit            messageRateMax
  cache, suppress_duplicates nodupe_ttl
  topic_prefix               topicPrefix 
  ========================== ===============

  For the full list, look at the `Release Notes <UPGRADING.html>`_ 

  The topic_prefix in v2 is 'v02.post'  in v3, the default is 'v03'. If topic_prefix is omitted 
  you will need to add the line *topicPrefix v02.post* to get the same behaviour as v2. Could 
  also be placed in ~/.config/sr3/default.conf if the case is too common.
  One might have to similarly override the sr3 default for post_topicPrefix.

* all on_message, on_file, on_post, on_heartbeat, routines will work, by sr3 using 
  the flowcb/v2wrapper.py plugin which will be automatically invoked when v2 plugins are 
  seen in the config file.

.. Note:: Ideally, v2wrapper is used as a crutch to allow one to have a functional configuration
  quickly. There is a performance hit to using v2wrapper.


What Won't Work Without Change
------------------------------

* do_*  they are just fundamentally different in v3.

If you have a configuration with a do_* plugin, then you need this guide, from day 1.
to set a configuration to use a plugin, in v2 one used the *plugin* option::

   plugin <pluginName>

The equivalent to that in v3 is *callback*::

   callback <pluginName>

For this shorthand to work there should be a file named <pluginName>.py somewhere in the
PYTHONPATH (~/.config/plugins is added for convenience.) and that python source file needs
to have a class <PluginName> declared in it (same as the file name but first letter capitalized.)
If you need to name it differently there is a longer form that allows one to violate the
convention::

  flowCallback <pluginName>.MyFavouriteClass

This is equivalent to *import <pluginName>* followed by instantiating and instance of
the *<pluginName>.MyFavoriteClass()* so that the entry points get called at the right time.
The individual routine plugin declarations on_message, on_file, etc... are not a way of
doing things in v3. in v3 callbacks are declared, and they contain the entry points you need.

* DESTFNSCRIPT work similar in v3 to v2, but the API is made to match v3 flowCallbacks,
  the new routines, one returns the new filename as output, instead of modifying a field
  in the notification message.



Coding Differences between plugins in v2 vs. Sr3
------------------------------------------------

The API for adding or customizing functionality in sr3 is quite different from v2.
In general, v3 plugins:

* **are usually subclassed from sarracenia.flowcb.FlowCB.**

  In v2, one would declare::

      class Msg_Log(object): 

  v3 plugins are normal python source files (no magic at the end.)
  they are subclassed from sarracenia.flowcb::

      from sarracenia.flowcb import FlowCB

      class MyPlugin(FlowCB):
        ...the rest of the plugin class..
        
         def after_accept(self, worklist):
           ...code to run in callback...

  To create an *after_accept* plugin in *MyPlugin* class, define a function
  with that name, and the appropriate signature.

* v3 plugins **are pythonic, not weird** :
  In v2, you need the last line to include something like::

     self.plugin = 'Msg_Delay'

  the first generation ones at the end had something like this to assign entry points explicitly::

      msg_2localfile = Msg_2LocalFile(None)
      self.on_message = msg_2localfile.on_message

  either way a naive python portion of the file would invariably fail without some sort of test
  harness being wrapped around it. 
  
  .. Tip:: In v3, delete these lines (usually located at the bottom of the file)

  In v2, there were strange issues with imports, resulting in people putting
  import statements inside functions. That problem is fixed in v3, you can check your import syntax
  by doing *import X* in any python interpreter.

  .. Tip:: Put the necessary imports at the beginning of the file, like any other python module
           **and remove the imports located within functions when porting**.

* **v3 plugins can be used by application programmers.** The plugins aren't
  bolted on after the fact, but a core element, implementing duplicate 
  suppression, reception and transmission of notification messages, file monitoring,
  etc.. understanding v3 plugins gives people important clues to being
  able to work on sarracenia itself.

  v3 plugins can be *imported* into existing applications to add the ability
  to interact with sarracenia pumps without using the Sarracenia CLI.
  see jupyter tutorials. 

* v3 Plugins now use **standard python logging** ::

      import logging
  
  Make sure the following logger declaration is after the **last _import_** in the top of the v3 plugin::

      logger = logging.getLogger(__name__)

      # To log a notification message:
      logger.debug( ... )
      logger.info( ... )
      logger.warning( ... )
      logger.error( ... )
      logger.critical( ... )
      
  When porting v2 -> v3 plugins: *logger.x* replaces *parent.logger.x*.
  Sometimes there is also self.logger x... dunno why... don't ask.
  
  .. Tip:: In VI you can use the global replace to make quick work when porting::
  
             :%s/parent.logger/logger/g

* in v2, **parent** is a mess.  The *self* object varied depending on which entry points were 
  called. For example, *self* in __init__ is Not the same as *self* in on_message. As a result, all state
  is stored in parent. the parent object contained options, and settings, and instance
  variables. 
 
  For actual attributes, sr3 now operates the way python programmers expect: self, is
  the same self, in __init__() and all the other entry points, so one can set state
  for the plugin using self.x attributes in the the plugin code.

* v3 plugins *have options as an argument to the __init__(self, options): routine* rather
  than in v2 where they were in the parent object. By convention, in most modules the 
  __init__ function includes a::

       self.o = options
       self.o.add_option('OptionName', Type, DefaultValue)
       
  .. Tip:: In vi you can use the global replace::
  
             :%s/parent/self.o/g

* v2 options are all lists, sr3 options are typed, and default type is str.
  in v2 you will see::

          parent.option[0] 

  This shows up because one needs to extract the first value given from the list.
  If the option type is not list, should become::

          self.o.option

  This happens often.  

* you can see what options are active by starting a component with the 'show' command**::

          sr3 show subscribe/myconf

  these settings can be accessed from self.o


* In sr3 settings, **look for replacement of many underscores with camelCase.** 
  Underscore is now reserved for cases where it represents a grouping of options, or 
  options related to a given class. For example, post\_  settings retained the first underscore, but not the rest.  so:

  *  custom_setting_thing -> customSettingThing
  *  post_base_dir -> post_baseDir
  *  post_broker is unchanged. 
  *  post_base_url -> post_baseUrl

  for example, in a v2 plugin, it would be parent.post_base_url, in v3, the same setting would be self.o.post_baseUrl.
  See `Upgrading <Upgrading.html>` for a list of equivalent options.
  See `sr3_option(7) <../Reference/sr3_options.7.html>` for reference information on each option.

* In v2, *parent.msg* stored the messages, with some fields as built-in attributes, and others as headers.
  In v3 **notification messages are now python dictionaries** , so a v2 `msg.relpath` becomes `msg['relPath']` in v3.
  
  rather than being passed via parent, there is a *worklist* option passed to those plugin entry points that manipulate
  messages.  for example, an *on_message(self,parent)* in a v2 plugin becomes an *after_accept(self,worklist)* in sr3.
  the worklist.incoming contains all the messages that have passed accept/reject filtering, and will be processed
  (for download, send, or post) so the logic will look like::

     for msg in worklist.incoming:
         do the same logic as in the v2 plugin. 
         for one message at a time in the loop.
         
  mappings of all the entry points are described in the `Mapping v2 Entry Points to v3 Callbacks`_
  section later in this document.

  Each v3 notification message acts like a python dictionary.  Below is a table mapping 
  fields from the v2 sarra representation to the one in sr3:

  ================ =================== ==========================================================
  v2               sr3                 Notes
  ================ ================================== ==========================================================
  msg.pubtime      msg['pubTime']                     when the message was originally published (standard field)
  msg.baseurl      msg['baseUrl']                     root of the url tree of posted file (standard field)
  msg.relpath      msg['relPath']                     relative path concatenated to baseUrl for canonical path
  *no equivalent*  msg['retPath']                     opaque retrieval path to override canonical one.
  msg.notice       no equivalent                      calculated from other field on v2 write
  msg.new_subtopic msg['new_subtopic']                avoid in sr3... calculated from relPath
  msg.new_dir      msg['new_dir']                     name of the directory where files will be written
  msg.new_file     msg['new_file']                    name of the file to be writen in new_dir
  msg.headers      msg                                the in memory sr3 message is a dict, includes headers
  msg.headers['x'] msg['x']                           headers are dict items.
  msg.message_ttl  msg['message_ttl']                 same setting.
  msg.exchange     msg['exchange']                    the channel on which the message was received.
  msg.logger       logger                             pythonic logging setup describe above.
  msg.parts        msg['size']                        just omit, use sarracenia.Message constructor.
  msg.sumflg       msg['integrity']                   just omit, use sarracenia.Message constructor.
  msg.sumstr       v2wrapper.sumstrFromMessage(msg)   the literal string for a v2 checksum field.     
  parent.msg       worklist.incoming                  v2 is 1 message at a time, sr3 has lists or messages.
  ================ ================================== ==========================================================

* the pubTime, baseUrl, relPath, retPath, size, integrity, are all standard message fields
  better described in `sr_post(7) <../Reference/sr_post.7.html>`_

* if one needs to store per message state, then one can declare temporary fields in the message,
  that will not be forwarded when the message is published. There is a set field *msg['_deleteOnPost']*  ::

      msg['my_new_field'] = my_new_value
      msg['_deleteOnPost'] |= set(['my_new_field'])

  Sarracenia will delete the given field from the message before posting for downstream consumers.

* in older versions of v2 (<2.17), there was msg.local_file, and msg.remote_file, some old plugins may contain
  that. They represented destination in the subscribe and sender cases, respectively.
  both were replaced by new_dir concatenated with new_file to cover both cases.
  separation of the directory and file name was considered an improvement.

* in v2 *parent* was the sr_subscribe object, which had all of it's instance variables, none of which
  were intended for use by plugins. In plugin __init__() functions, they may be referred to 
  as *self* rather than *parent*:

  ====================================== ===================================== ==================================================
  v2                                     sr3                                   Notes
  ====================================== ===================================== ==================================================
  parent.cache                           *none*                                instance of the duplicate suppression cache.
  parent.consumer                        *none*                                instance of sr_consumer class ...
  parent.currentDir                      msg['new_dir'] ?                      equivalent depends on purpose of use.
  parent.destination                     self.o.pollUrl                        in a poll
  parent.destination                     self.o.sendTo                      in a sender
  parent.masks                           *none*                                internals of sr_subscribe class.
  parent.program_name                    self.o.program_name                   name of the program being run e.g. 'sr_subscribe'
  parent.publisher                       *none*                                instance of Publisher class from sr_amqp.py
  parent.post_hc                         *none*                                instance of HostConnect class from sr_amqp.py
  parent.pulls                           self.o.masks                          used in polls, example poll.cocorahs_precip.py
  parent.retry                           *none*                                instance of the retry queue.
  parent.msg.set_notice(b,r)             msg['baseUrl'] = b, msg['relPath']=r  v2 uses v2 messages internally, sr3 uses... v3.
  parent.user_cache_dir                  self.o.cfg_run_dir                    actually one level down... new place is better.
  ====================================== ===================================== ==================================================

  There are dozens (hundreds?) of these attributes that were intended as internal data to the
  sr_subscribe class, and should not really be available to plugins. 
  Most of them don't show up, but if a developer found someting, it might be present.
  Hard to predict what a plugin developer using one of these values intended.

* In v3 **plugins operate on batches of notification messages**. v2 *on_message* gets parent as a parameter,
  and the notification message is in parent.message. In v3, *after_accept* has worklist as an
  option, which is python list of messages, maximum length being fixed by the
  *batch* option. So the general organization for after_accept, and after_work is::

      new_incoming=[]
      for message in old_list:
          if good:
             new_incoming.append(message)
          if bad:
             worklist.rejected.append(message)
      worklist.incoming=new_incoming
      
  .. Note:: plugins must be moved from the /plugins directory to the /flowcb directory, 
            and specifically, on_message plugins that turn into after_accept ones should be 
            placed in the flowcb/accept directory (so simialr plugins can be grouped together).
  
  In *after_work*, the replacement for v2 *on_file*, the operations are on:

  * worklist.ok (transfer succeeded.)
  * worklist.failed (transfers that failed.)

  In the case of receiving a .tar file and expanding into to individual files,
  the *after_work* routine would change the worklist.ok to contain notification messages for
  the individual files, rather than the original collective .tar.

  .. Note:: on_file plugins that become after_work plugins should be placed in the
            /flowcb/after_work directory
  
* **Must not set notification message fields (like partstr, sumstr) in plugins.**
  In v2, one would need to set **partstr**, and **sumstr** for v2 notification messages in plugins. 
  This required an excessive understanding of notification message formats, and meant that 
  changing notification message formats required modifying plugins (v03 notification message format is
  not supported by most v2 plugins, for example). To build a notification message from a 
  local file in a v3 plugin::

     import sarracenia

     m = sarracenia.Message.fromFileData(sample_fileName, self.o, os.stat(sample_fileName) )

  Setting **partstr** and **sumstr** are specific to v2 messages, and will not be interpreted 
  properly in sr3.  The encoding of this information is completely different in v03 messages,
  and sr3 supports alternate message encodings which may be different again. Setting of these
  fields manually is actively counter-productive. The same applies with checksum logic found in v2 plugins. 
  The checksum is already performed when the new notification message is being generated so most likely
  any message fields such as **sumalgo** and other **algo** fields can be discarded.

  For an example of using the message builder, look at  `do_poll -> poll`_


* v3 plugins **rarely, involve subclassing of moth or transfer classes.**
  The sarracenia.moth class implements support for notification message queueing protocols
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
-------------------

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
file x.py somewhere in the python search path, or in the
*sarracenia/flowcb* directory included as part of the package.
This is actually a shorthand version of the python import.
If you need to declare a callback that does not obey that
convention, one can also use a more flexible but longer-winded::

  flowcb sarracenia.flowcb.x.X

the above two are equivalent. The flowcb version can be used to import classes 
that don't match the convention of the x.X (a file named x.py containing a class called X)

Configuration Upgrade
---------------------

Once a plugin is ported, one can also arrange for the v3 option parser to recognize a v2
plugin invocation and replace it with a v3 one.  looking in /sarracenia/config.py#L144,
there is a data structure *convert_to_v3*.  A sample entry would be::

    .
    .
    .
    'on_message' : {
             'msg_delete': [ 'flowCallback': 'sarracenia.flowcb.filter.deleteflowfiles.DeleteFlowFiles' ]
    .
    .
    .


A v2 config file containing a line *on_message msg_delete* will be replaced by the parser with::

    flowCallback sarracenia.flowcb.filter.deleteflowfiles.DeleteFlowFiles



Options
-------

In v2, one would declare settings to be used by a plugin in the __init__ routine, with 
the *declare_option*.::

    parent.declare_option('poll_usgs_stn_file')

The values are always of type *list*, so usually, one uses the value by picking the first value::

    parent.poll_usgs_stn_file[0]

In v3, that would be replaced with::

    self.o.add_option( option='poll_usgs_stn_file', kind='str', default_value='hoho' )

Where in v3 there are now types ( as seen in the sarracenia/config.py#L777 file) and default value setting included without additional 
code. it would be referred to in other routines like so::

    self.o.poll_usgs_stn_file



    
Mapping v2 Entry Points to v3 Callbacks 
---------------------------------------

for a comprehensive look at the v3 entry points, have a look at:

https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/__init__.py

for details.

on_message, on_post --> after_accept
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

v2: receives one notification message, returns True/False


v3: receives worklist 
    modify worklist.incoming 
    transferring rejected notification messages to worklist.rejected, or worklist.failed.

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
~~~~~~~~~~~~~~~~~~~~~~

v2: receives one notification message, returns True/False

v3: receives worklist 
    modify worklist.ok (transfer has already happenned.) 
    transferring rejected notification messages to worklist.rejected, or worklist.failed.

    can also be used to work on worklist.failed (retry logic does this.)

examples:
   v3: flowcb/work/age.py
 
.. Danger:: THERE ARE NO v2 EXAMPLES?!?! 
            TODO: add some examples
            See: `Table of v2 and sr3 Equivalents`_

on_heartbeat -> on_housekeeping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

v2: receives parent as argument.
    will work unchanged.


v3: only receives self (which should have self.o replacing parent)

examples:

  * v2: hb_cache.py -- cleans out cache (references sr_cache.)
  * v3: flowcb/nodupe.py -- implements entire caching routine.



do_poll -> poll
~~~~~~~~~~~~~~~

v2: call do_poll from plugin.

 * protocol to use the do_poll routine is identified by registered_as() entry point
    which is mandatory to provide.
 * requires manually constructing fields for notification messages, is notification message verison specific,
   (generally do not support v03 notification messages.)
 * explicitly calls poll entry points.
 * runs, one must worry about whether one has the vip or not to decide what processing
   to do in each plugin.
 * poll_without_vip setting available.
 * parent.pulls is a list of *get* directives (which are different from accept)
 * often paired with download\_something plugins where a partial message is built with the poll
   and the download one is specialized to to the actual download.


v3: define poll in a flowcb class.

 * poll only runs when has_vip is true. (so remove any has_vip() tests, unneeded.)
   also consult section on virtual ip addresses below.

 * registered_as() entry point is moot.

 * gather runs always, and is used to subscribe to post done by node that has the vip,
   allowing the nodupe cache to be kept uptodate.

 * api defined to build notification messages from file data regardless of notification message format.

 * get is gone, poll uses accept like any other component.

 * the combination with download plugins is generally replaced by a single plugin that implements
   alternate naming using *retPath* field. so it is all done in one plugin.

 * returns a list of notification messages to be filtered and posted.


To build a notification message, without a local file, use fromFileInfo sarracenia.message factory::
  
     import dateparser
     import paramiko
     import sarracenia

     gathered_messages=[]

     m = sarracenia.Message.fromFileInfo(sample_fileName, cfg)

builds an notification message from scratch.

One can also build and supply a simulated stat record to fromFileInfo factory,
using the *paramiko.SFTPAttributes()* class. For example, using the dateparser 
routines to convert. However, the remote server lists the date and time, as well 
as determines the file size and permissions in effect::


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

Once the notification message is built, append it to the list::

     gathered_messages.append(m) 
  
and at the end::

     return gathered_messages

 

Virtual IP processing in poll
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In v2 if you have a vIP set, all participating nodes poll the upstream server
and maintain the list of current files, they just don't publish the result.
So if you have 8 servers sharing a vIP, all eight are polling, kind of sad.
There is also the poll_no_vip setting, and plugins often have to check if they
have the vIP or not.

In v3, only the server with the vIP polls. The plugins don't need to check.
The other participating servers subscribe to where the poll posts to,
to update their recent_files cache.

examples:
 * flowcb/poll/airnow.py

on_html_page -> subclass flowcb/poll
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is a v2 plugin nsa_mls_nrt.py:

.. code-block:: python

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
sr3 version of same plugin (nasa_mls_nrt.py):

.. code-block:: python

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
---------------------------

Similarly to on_html_page above, all uses of on_line in the previous version
were about re-formatting lines to be parseable. the on_line routine can be
similarly sub-classed to replace it.  One had to modify the parent.line
string to be parseable by the built in *ls* style line parsing.

In sr3, on_line is expected to return a populated paramiko.SFTPAttributes field, similar
to the way on_html_page works (but only a single one instead of a dictionary of them.)
With the more flexible date parsing in sr3, there has been no identified need for on_line
on which to build an example.



do_send -> send:
----------------

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

* accepts a single notification message as an argument.

* returns True if download succeeds.

* if it returns False, the retry logic applies (download will be called again
  then placed on the retry queue.)

* use msg['new_dir'], msg['new_file'], msg['new_inflight_path'] 
  to respect settings such as *inflight* and place file properly.
  (unless changing that is motivation for the plugin.)

* might be a good idea to verify the checksum of the downloaded data.
  if the checksum of the file downloaded does not agree with what is in
  the notification message, duplicate suppression fails, and looping results.
   
* one case of download is when retrievalURL is not a normal file download.
  in v03, there is a retPath fields for exactly this case. This new feature
  can be used to eliminate the need for download plugins.  Example:

  in v2:

      * https://github.com/MetPX/sarracenia/blob/v2_stable/sarra/plugins/poll_noaa.py 

      * https://github.com/MetPX/sarracenia/blob/v2_stable/sarra/plugins/download_noaa.py

  is ported to sr3:

      * https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/poll/noaa_hydrometric.py

  The ported result sets the new field *retPath* ( retrieval path ) instead of new_dir and new_file 
  fields, and normal processing of the *retPath* field in the notification message will do a good download, no
  plugin required. 


DESTFNSCRIPT
~~~~~~~~~~~~

DESTFNSCRIPT is re-cast as a flowcb entry point, where the directive is now formatted
similarly to the flowcallback in the configuration


v2 configuration::

    accept .*${HOSTNAME}.*AWCN70_CWUL.*       DESTFNSCRIPT=sender_renamer_add_date.py

v2 plugin code::

    import sys, os, os.path, time, stat

    # this renamer takes file name like : AACN01_CWAO_160316___00009:cmcin:CWAO:AA:1:Direct:20170316031754 
    # and returns :                       AACN01_CWAO_160316___00009_20170316031254

    class Renamer(object):

      def __init__(self) :
          pass

      def perform(self,parent):
 
          path = parent.new_file
          tok=path.split(":")

          datestr = time.strftime('%Y%m%d%H%M%S',time.gmtime())
          #parent.logger.info('Valeur_path: %s' % datstr)

          new_path=tok[0] + '_' + datestr
          parent.new_file = new_path
          return True 

    renamer=Renamer()
    self.destfn_script=renamer.perform


Turns into sr3

sr3 configuration::

   accept .*${HOSTNAME}.*AWCN70_CWUL.*       DESTFNSCRIPT=sender_renamer_add_date.Sender_Renamer_Add_Date
 
In sr3, as for any flowcallback invocation, one needs to use a traditional python class invocation
and add to it the name of the class within the file.  This notation is equivalent to python *from*
statement *from sender_renamer_add_date import Sender_Renamer_Add_Date*

flow callback code::

   import logging,time

   from sarracenia.flowcb import FlowCB

   logger = logging.getLogger(__name__)

   class Sender_Renamer_Add_Date(FlowCB):

      def __init__(self,options):
          self.o = options
          pass

      def destfn(self,msg) -> str:

          logger.info('before: m=%s' % msg )
          relPath = msg["relPath"].split('/')
          datestr = time.strftime('%Y%m%d%H%M%S',time.gmtime())
          return relPath[-1] + '_' + datestr

Example of debugging sr3 destfn functions::

    fractal% python3
    Python 3.10.4 (main, Jun 29 2022, 12:14:53) [GCC 11.2.0] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from sender_renamer_add_date import Sender_Renamer_Add_Date
    >>> fb=Sender_Renamer_Add_Date(None)
    >>> msg = { 'relPath' : 'relative/path/to/file.txt' }
    >>> fb.destfn(msg)
    'file.txt_20220725130328'
    >>> 




v3 only: post,gather
--------------------

The polling/posting is actually done in flow callback (flowcb) classes.
The exit status does not matter, all such routines will be called in order.

The return of a gather is a list of notification messages to be appended to worklist.incoming

The return of post is undefined. The whole point is to create a side-effect
that affects some other process or server.


examples: 
 * flowcb/gather/file.py - read files from disk (for post and watch)
 * flowcb/gather/message.py - how notification messages are received by all components
 * flowcb/post/message.py - how notification messages are posted by all components.
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

  * has an after_accept function to append notification messages to the 
    incoming queue, in order to trigger another attempt to process them.
  * has an after_work routine doing something unknown... FIXME.
  * has a post function to take failed downloads and put them
    on the retry list for later consideration.


Table of v2 and sr3 Equivalents
-------------------------------

Here is an overview of plugins included in Sarracenia, 
One can browse the two trees, and using the table below,
can review, compare and contrast the implementations.

* V2 plugins are under: https://github.com/MetPX/sarracenia/tree/v2_stable/sarra/plugins
* Sr3 plugins are under: https://github.com/MetPX/sarracenia/tree/v03_wip/sarracenia/flowcb

The naming also gives an example of the name convention mapping... e.g. plugins whos v2 name start with:

* msg\_... -> filter/... or accept/...
* file\_... -> work/...
* poll\_... -> poll/... or gather/...
* hb\_... -> housekeeping/...

are mapped to the sr3 conventional directories at right.

Relative paths from the above given folders are in the table:

+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| V2 plugins (all in one directory...)            | Sr3 flow callbacks (treeified)                                                                                                               |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| data\_...                                       | subclass sarracenia.transfer class instead                                                                                                   |
|                                                 |                                                                                                                                              |
| modify file data during transfer                | no example available consult source code                                                                                                     |
|                                                 |                                                                                                                                              |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| destfn_sample.py                                | `destfn/sample.py <../Reference/flowcb.html#module-sarracenia.flowcb.destfn.sample>`_                                                        |
|                                                 |                                                                                                                                              |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| file_age.py                                     | `work/age.py <../Reference/flowcb.html#module-sarracenia.flowcb.work.age>`_                                                                  |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| file_delete.py                                  | `work/delete.py <../Reference/flowcb.html#module-sarracenia.flowcb.work.delete>`_                                                            |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| file_email.py                                   | `send/email.py <../Reference/flowcb.html#module-sarracenia.flowcb.work.email>`_                                                              |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| file_rxpipe.py                                  | `work/rxpipe.py  <../Reference/flowcb.html#module-sarracenia.flowcb.work.rxpipe>`_                                                           |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| hb_memory                                       | `housekeeping/resources.py  <../Reference/flowcb.html#module-sarracenia.flowcb.housekeeping.resources>`_                                     |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| html_page.py                                    | subclass sarracenia.transfer class instead.                                                                                                  |
|                                                 |                                                                                                                                              |
|                                                 | no example available consult source code.                                                                                                    |
|                                                 |                                                                                                                                              |
|                                                 | also see poll/nasa_mls_nrt.py for example of                                                                                                 |
|                                                 | parsing custom resmote server lines.                                                                                                         |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_2http.py                                    | `accept/tohttp.py <../Reference/flowcb.html#module-sarracenia.flowcb.accept.tohttp>`_                                                        |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_2localfile.py, msg_2local.py (not sure)     | `accept/tolocalfile.py <../Reference/flowcb.html#module-sarracenia.flowcb.accept.tolocalfile>`_                                              |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_delete.py                                   | `filter/deleteflowfiles.py <../Reference/flowcb.html#module-sarracenia.flowcb.filter.deleteflowfiles>`_                                      |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_fdelay.py                                   | `filter/fdelay.py <../Reference/flowcb.html#module-sarracenia.flowcb.filter.fdelay>`_                                                        |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_filter_wmo2msc.py                           | `filter/wmo2msc.py <../Reference/flowcb.html#module-sarracenia.flowcb.filter.wmo2msc>`_                                                      |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_log.py,file_log.py, hb_log.py, post_log.py  | `log.py  <../Reference/flowcb.html#module-sarracenia.flowcb.log>`_                                                                           |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_pclean.py, msg_pclean_f90.py                | `pclean.py <../Reference/flowcb.html#module-sarracenia.flowcb.pclean>`_                                                                      |
|                                                 | `filter/pcleanf90.py <../Reference/flowcb.html#module-sarracenia.flowcb.filter.pcleanf92>`_                                                  |
|                                                 |                                                                                                                                              |
| msg_pclean_f92.py                               | filter/pcleanf92.py <../Reference/flowcb.html#module-sarracenia.flowcb.filter.pcleanf92>`_                                                   |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| post_rate_limit.py                              | built-in messageRateMax processing                                                                                                           |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_rename_dmf.py                               | `accept/renamedmf.py <../Reference/flowcb.html#module-sarracenia.flowcb.accept.renamedmf>`_                                                  |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_rename_whatfn.py                            | `accept/renamewhatfn.py <../Reference/flowcb.html#module-sarracenia.flowcb.accept.renamewhatfn>`_                                            |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_rename4jicc.py                              | `accept/rename4jicc.py <../Reference/flowcb.html#module-sarracenia.flowcb.accept.rename4jicc>`_                                              |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_stopper.py                                  | built-in messageCountMax processing                                                                                                          |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_sundew_pxroute.py                           | `accept/sundewpxroute.py <../Reference/flowcb.html#module-sarracenia.flowcb.accept.sundewpxroute>`_                                          |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_speedo.py                                   | `accept/speedo.py <../Reference/flowcb.html#module-sarracenia.flowcb.accept.speedo>`_                                                        |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_to_clusters.py                              | `accept/toclusters.py <../Reference/flowcb.html#module-sarracenia.flowcb.accept.toclusters>`_                                                |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| msg_WMO_type_suffix.py                          | `accept/wmotypesuffix.py <../Reference/flowcb.html#module-sarracenia.accept.wmotypesuffix>`_                                                 |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| hard-coded built-in duplicate suppression       | `nodupe/__init__.py <../Reference/flowcb.html#module-sarracenia.flowcb.nodupe>`_                                                             |
|                                                 |                                                                                                                                              |
| hb_cache.py                                     |                                                                                                                                              |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| hard-coded built-in message subscriber          | `gather/message.py <../Reference/flowcb.html#module-sarracenia.flowcb.gather.message>`_                                                      |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| hard-coded built-in message poster              | `post/message.py <../Reference/flowcb.html#module-sarracenia.flowcb.post.message>`_                                                          |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| hard-coded built-in file scan or noticing.      | `gather/file.py <../Reference/flowcb.html#module-sarracenia.flowcb.gather.file>`_                                                            |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| hard-coded builtin retry logic                  | `retry.py <../Reference/flowcb.html#module-sarracenia.flowcb.retry>`_                                                                        |
|                                                 |                                                                                                                                              |
| hb_retry.py                                     |                                                                                                                                              |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| poll_email.py                                   | `poll/mail.py <../Reference/flowcb.html#module-sarracenia.flowcb.poll.mail>`_                                                                |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| poll_nexrad.py                                  | `poll/nexrad.py <../Reference/flowcb.html#module-sarracenia.flowcb.poll.nexrad>`_                                                            |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| poll_noaa.py                                    | `poll/noaa_hydrometric.py <../Reference/flowcb.html#module-sarracenia.flowcb.poll.noaa_hydrometric>`_                                        |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| poll_usgs.py                                    | `poll/usgs.py <../Reference/flowcb.html#module-sarracenia.flowcb.poll.usgs>`_                                                                |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
| spare                                           |                                                                                                                                              |
+-------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
 
