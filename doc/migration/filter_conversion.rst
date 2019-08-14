==========
 MIGRATION
==========

-------------------------------------------
Sundew filter migration to sarracenia (PXATX)
-------------------------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite

.. contents::

DESCRIPTION
===========

This document suppose that the reader is familiar with the concepts and usage
of **sundew** and **sarracenia**. 

**sundew** filters supports a plugin mechanism that allows processing onto
received products in order to generate derivated products and insert them
in the sundew product flow. The *pxFilter* process reads its configuration
where an *fx_script* is declared, installed and used on all ingested products.

There are 2 types of such filters. The first type, most common, is a one to  
one filter where one received product is converted into one filtered product.
An example is where a GIF image is converted into a PNG one. The second type
is where on received product generates a bunch of filtered products we will
call it a one to many filter. An example if the collected wmo bulletins we 
get from UKMET. A filter split each file into several individual files. We
might have to do a third type for example if we collect a bunch of individual
files into one product all of this into a sarra plugin...

**sarracenia** supports a lot of possible plugins in all of its programs.
If we take the simpler form of filter one to one, and we want to translated
this into a **sarra** process we need to receive the posting of a local product,
 generate a resulting product and post the notification for it. It is easy to
see that can be done using an **sr-sarra** process. 


ONE TO ONE FILTER
=================


I will present one way that I used to implement a one to one filter.
There could be other alternatives... but this one worked nicely for me.

Lets go through the steps of making a one to one filter plugin.
The **sr-sarra** configuration will start similar to an sr_sender one 
because both requiere the announced products to be local to the server.
So typically something like::

       # broker is localhost

       broker amqp://feeder@localhost/
       exchange   xpublic

       # queueing local

       prefetch   10
       queue_name q_feeder.${PROGRAM}.${CONFIG}.${HOSTNAME}

       # base_dir 

       base_dir /apps/sarra/public_data

       # only the selected product
       accept_unmatch False

Of course this is only an example. You can narrow down the products
with more precise subtopic and even different exchanges. And of course,
we want to post the newly created product hence our config will also
have something like::

       # posting

       post_broker   amqp://feeder@localhost/
       post_exchange xpublic
       post_base_url http://${HOSTNAME}
       post_base_dir /apps/sarra/public_data


In between these two sections we need to set the plugin to convert the 
products and also define where the products will be placed. I will 
pretend that my filter converts images to PNG format images. The config
could look like::

       # converting the products

       on_file  None
       plugin   cvt_topng
       plugin   on_file_converted
       on_file  file_log

       # example for directory and product selection

       directory ${PBD}/${YYYYMMDD}/SSC-DATAINTERCHANGE/CHARTS/PNG/${HH}

       subtopic  *.SSC-DATAINTERCHANGE.CHARTS.IMV6.#
       accept   .*/SSC-DATAINTERCHANGE/CHARTS/IMV6/.*

Now lets explain the converting part of this configuration. As you guest, the
plugin cvt_topng is where the image will be converted. Here is how it is 
implemented. Our converting class needs to register itself as a replacement
for the http protocol. Why ?  because all the local product will be announced
as http://hostname and we want to catch what should be an http download and
turn it into a converting process.::

      class Cvt_Topng(object):

            # registering as http 

            def __init__(self,parent) :
                self.registered_list = [ 'http' ]

            def registered_as(self) :
                return self.registered_list

Next, it is very important to give a new name to the converted product.
If you live the target name as is, **sr-sarra** will match the notice
with the local product and will skip this message as an already downloaded
product. The next function in our class will be::

      def on_message(self,parent):

          fname = parent.msg.new_file
          fname = fname.replace('.imv6','')

          parent.msg.new_file = fname + '.png'

          return True

Now this new_file is unavailable on the localhost, we can use a **do_download**
or a **do_get** function to proceed with our conversion. I have implemented
my one to one filters with a **do_get** and in our case it looks like::

      def do_get(self, parent ):
          import subprocess
          self.parent = parent
          self.logger = parent.logger

          ipath = parent.base_dir + '/' + parent.msg.relpath
          opath = parent.msg.new_dir + '/' + parent.msg.new_file

          self.logger.info("converting %s to %s" % (os.path.basename(ipath),os.path.basename(opath)))

          # here an example of command

          cmd = 'topng ' + ipath + ' ' + opath

          try :
                  outp = subprocess.check_output( cmd, shell=True )
                  return True
          except:
                  logger.info('Exception details: ', exc_info=True)
                  logger.error("Unable to convert file %s" % ipath)

          return False

There is more work left with the existance of the new product. Each one to one
filter needs to adjust the message that will be posted. Since this is a common
task to all one to one filters, I made it a plugin itself and it is called
**on_file_converted**. Basically it contains an **on_file** function for the
task::

      # once the file converted, adjust message

      def on_file(self, parent ):
          import os,stat

          if parent.program_name != 'sr_sarra' : return True

          logger  = parent.logger
          msg     = parent.msg
          path    = msg.new_dir + '/' + msg.new_file

          lstat   = os.stat(path)

          # adjust part

          fsiz    = lstat[stat.ST_SIZE]
          partstr = '1,%d,1,0,0' % fsiz
          msg.partstr          = partstr
          msg.headers['parts'] = msg.partstr

          # adjust time

          if parent.preserve_time or 'mtime' in msg.headers :
             msg.headers['mtime'] = timeflt2str(lstat.st_mtime)
             msg.headers['atime'] = timeflt2str(lstat.st_atime)

          # adjust mode

          if parent.preserve_mode or 'mode' in msg.headers:
             msg.headers['mode']  = "%o" % ( lstat[stat.ST_MODE] & 0o7777 )

          # adjust checksum

          algo = msg.sumalgo
          algo.set_path(path)
          src  = open(path,'rb')
          while True:
                chunk = src.read(parent.bufsize)
                if not chunk : break
                algo.update(chunk)

          checksum = algo.get_value()

          msg.set_sum(msg.sumflg,checksum)
          msg.onfly_checksum = checksum

          return True

It is nice to think that, should there be changes in the message, this plugin
could be modified without having to modify all one to one filters.

CONSIDERATIONS WITH ONE TO ONE FILTERS
======================================

I wrote some of the migrated filters and there are some considerations
to be taken while implementing filters from **sundew**. 

I have tried to make the less use of the **sundew-extension** but when
requiered for some clients, a filter must change this inforemation too.
In our example, I also have this function::


      def correct_extension(self,parent) :

          if  not 'sundew_extension' in parent.msg.headers : return

          ext   = parent.msg.headers['sundew_extension']
          parts = ext.split(':')
          ext    = ":".join(parts[:3]) + ':PNG'

          parent.msg.headers['sundew_extension'] = ext

And in the code, it is called right after the conversion::

         try :
                  outp = subprocess.check_output( cmd, shell=True )
                  self.correct_extension(parent)
                  return True
         ...


It might also be requiered, depending on the products and the clients,
to add (or update) to the extension a datetime suffix for the new products.

I provide a plugin template and a config template and **on_file_converted**  ::

  sarra/examples/sarra/one_to_one_filter.conf
  sarra/plugins/one_to_one_filter.py
  sarra/plugins/on_file_converted.py


FINAL REMARKS ON ONE TO ONE FILTER
==================================

Usually a converter, say topng, will add the extension .png to the end product.
This was not the case in **sundew** where the *whatfn* was kept as is but
part of the *sundew_extension* was modified to show the new format.

Examining **on_file_converted** you will find an on_message function
that removes filter extensions from the filename. This was requiered because
old sundew clients needed to receive sarracenia converted products without
their specific extension name. When this is requiered, the **on_file_converted**
 plugin can be added to the sender config. So example, a converted product
to PNG, in sarra would have a .png extension. Should it be requiered to send
it to a sundew client with option *filename NONE*  without the plugin
the client would receive  *WHATFN.png:...:...*  with the plugin, it receives
the correct *WHATFN:...:...*

Note also that the on_file function of the **on_file_converted** plugin
is restricted to an **sr_sarra** process while the on_message function
is restricted to an **sr_sender** process.

If part of this document needs to be clarified please let me know


ONE TO MANY FILTER
==================

I will present one way that I have used to implement a one to many filter.
Most of what was said earlier in the **one to one filter** still holds.
The configuration of such an **sr_sarra** process follows the same rules.
The plugin requires the same http registering. An **on_message** function 
needs to change the value of **parent.msg.new_file** (the value may not be
relevant to the filename you will give to the extracted individual files.

I have made this code available in a template **sarra/plugins/one_to_many_filter.py**.

Each file extracted will requiere an individual message to be posted 
(unfortunately not available in parent). The code used in the plugin for
that would be like::

      # update message for parsed file

      def update_message(self, path ):
          import os,stat

          parent  = self.parent
          logger  = parent.logger
          msg     = parent.msg
          lstat   = os.stat(path)

          # adjust part

          fsiz    = lstat[stat.ST_SIZE]
          partstr = '1,%d,1,0,0' % fsiz
          msg.partstr          = partstr
          msg.headers['parts'] = msg.partstr

          # adjust time

          if parent.preserve_time or 'mtime' in msg.headers :
             msg.headers['mtime'] = timeflt2str(lstat.st_mtime)
             msg.headers['atime'] = timeflt2str(lstat.st_atime)

          # adjust mode

          if parent.preserve_mode or 'mode' in msg.headers:
             msg.headers['mode']  = "%o" % ( lstat[stat.ST_MODE] & 0o7777 )

          # adjust checksum

          algo = msg.sumalgo
          algo.set_path(path)
          src  = open(path,'rb')
          while True:
                chunk = src.read(parent.bufsize)
                if not chunk : break
                algo.update(chunk)

          checksum = algo.get_value()

          msg.set_sum(msg.sumflg,checksum)
          msg.onfly_checksum = checksum

          # adjust topic, notice

          msg.new_file    = os.path.basename(path)
          msg.new_relpath = path.replace(parent.base_dir,'')

          msg.set_topic(msg.topic_prefix,msg.new_relpath)
          msg.set_notice(msg.new_baseurl,msg.new_relpath)

Many things could be considered in this function (parts?) but for the
general usage it should be ok.  I used the **do_download** function to
do the extraction, and publishing as follow ::

      def do_download(self, parent ):
          self.parent = parent
          self.logger = parent.logger

          ipath  = parent.base_dir + '/' + parent.msg.relpath

          self.logger.info("splitting %s" % os.path.basename(ipath) )

          # HERE IS A FUNCTION THAT EXTRACTS/GENERATES THE FILES
          # AND RETURNS A LIST CONTAINING THE ABSOLUTE PATH FOR
          # THE FILES GENERATED

          opaths = self.FILE_PARSER(ipath)

          # if it did not work it is an error

          if not opaths or len(opaths) <= 0 : return False

          # publish all parsed files but last

          for p in opaths[:-1] :
              self.update_message(p)

              # publishing

              ok = parent.__on_post__()
              if ok and parent.reportback: msg.report_publish(201,'Published')

          # prepare message for last file
          # and let sarra post it as if it
          # was a normal downloaded product
          # from the incoming message

          self.update_message(opaths[-1])

          return True

There is a funny trick in that **do_download** function, I am leaving the last
publish to the parent. It mimics the usual sarra download functionnality where
once the product is downloaded, the process will take care of publishing it.

From the template plugin, one should implement the extraction of the files.
The idea in the template plugin is that the extraction is done in the right
**parent.msg.new_dir** directory... each file will get its uniq name. All
generated product absolute filepath are collected in the **opaths** python
list. This list is returned and the **do_download** function will take care
of publishing these new products. A snippet of code, just as a reference
is provided in the template ::

      # file parsing here

      def FILE_PARSER(self, ipath ):

          opaths = []

          # PARSE THE FILE HERE

          # EACH GENERATED FILE SHOULD HAVE A DIFFERENT PATH
          # THAT SHOULD LOOK LIKE

          # opath  = parent.msg.new_dir + '/' + new_extracted_filename

          # EACH SUCCESSFULL PATH IS APPENDED TO THE LIST

          # opaths.append(opath)

          # RETURN THE LIST OF ALL GENERATED FILES

          return opaths
