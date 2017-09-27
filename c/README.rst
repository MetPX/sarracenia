
---------------------------------------
C-Implementation of a Sarracenia Client
---------------------------------------

This C functionality is embryonic, there is no intent to build a complete
implementation, it is just a few pieces meant to provide interoperability for
cases where either a python3 environment is either impractical, or where there
are performance concerns that this implementation would help with..

 - in some environments getting python3 environment installed is hard
   (example: cray linux environment is a software environment from circa 2009)

 - in-process invocation of sr_post on file closes (libsrshim.)

A library, libsarra is built, with external interfaces one can access from C 
using the entry points and data structures documented in sr_context.h, sr_post.h, 
and sr_consume.h files.  The library uses sr_config(7) style config files (see Limitations). 
A sample usage of the libraries is a command line binary, that can call the library::

   sr_cpost

This function takes the same options as sr_post, but the *sleep* argument, 
when supplied causes it to loop, checking for new items every *sleep* seconds 
(equivalent to sr_watch.) There is also a sample consumer::

  sr_cthneed

which obtains messages and, by default, prints them to standard output in json format identical
the the format used by the python implementation for save/restore functionality.
In order to have a complete downloader, one needs a script to parse the json output
and invoke an appropriate binary downloader.  One can use the 'output' switch
to choose other formats:
 
json:
  the default format, json compatible with python save/restore.

post:
  turns sr_cthneed into an sr_shovel, if cache is on, then it is a winnow.

url: 
  just print out the retrieval urls, rather than the entire message



There is also an LD_PRELOAD shim library example. (libsrshim.c) that
uses the posting api. sample usage::

   export SR_POST_CONFIG="mypost"
   export LD_PRELOAD=`pwd`/libsrshim.so.1.0.0

   cp libsrshim.c ~/test/hoho_my_darling.txt
   ln -s hoho haha
   rm haha

With the SR_POST_CONFIG set to "mypost", The libsrshim library will look in ~/.config/sarra/post/  for "mypost.conf."
With the LD_PRELOAD set to use the library, processes that run will call functions like 'close' that are in 
the shim library, and the shim library will apply the "mypost.conf" configuration to figure out whether it
should post the file being closed, and if so, to what broker.

Limitations of the C implementation
-----------------------------------

 - This library and tools do not work with any plugins from the python implementation.
 - This library is a single process, the *instances* setting is completely ignored.
 - The queue settings established by a consumer are not the same as those of the python
   implementation, so queues cannot be shared between the two.
 - The C is infected by python taste... 4 character indent, with spaces, all the time.


Build Dependencies
------------------

The librabbitmq version needs to be > 0.8,  this is newer than what is in ubuntu 16.04.
So you need to git clone from https://github.com/alanxz/rabbitmq-c  ... then built it there.


export RABBIT_BUILD=*directory where rabbit has been built*


librabbitmq-dev - AMQP client library written in C - Dev Files
libssl-dev  - OpenSSL client library (used for hash algorithms.)

run dependencies:
librabbitmq4 - AMQP client library written in C
libssl - OpenSSL client library.


  

Dorval Computing Centre
-----------------------

If you are in the Dorval computing centre environment, then SSM is available and 
a compatible version of rabbitmq-c can be obtained 

. ssmuse-sh -d /fs/ssm/main/opt/rabbitmqc/rabbitmqc-0.8.0
 
To load sr_cpost
. ssmuse-sh -d /fs/ssm/hpco/exp/sarrac-0.5
 


Plan:
  - figure out packaging?
  - if the local shim does not go well, step 2 is: sr_cwatch.


Developer Notes
---------------

whereami:
  - was looking at how to do partitioned (partflg='p') files, wrote footnote #1. 

  - result is that the cache is probably required before doing partition support.
    so thinking about doing the cache. DONE!

  - when sleep > 0, cpost now walks trees by keeping track of the start mtime of the last pass.
    algorithm based on *mtime* > start of previous pass... that's not necessarily good.

    for example search of new directory.
        whereas when you post a directory initially, is posts with mtime=0 first pass, so whole thing.
        but if a directory is added, mtime is already current, so only files that change in future
        will be posted... HMM...

  - FIXME: when 'start' if sleep <= 0 , should exit (not an error, compatibility with sr start all configs)

  - FIXME: require a configuration file (log & state files) ?  sr_subscribe does work without it, but...

  - do we go to the whole (copy directories into a file for comparison schtick?
    that's more sr_poll.... try the cache first.

worries/notes to self:

  - behaviour on posting and empty file results in a partstr 1,0,1,0,0
    partstrategy=1 (whole file), blocksize=0, blockcount=1, remainder=0, block=0.
    does that mean subscribers should try to download 0 bytes ? ... wondering if there 
    is something to do.  Should look at subscribers and confirm they do something sane.
 
   Footnote 1: FIXME: posting partitioned parts Not yet implemented.

   pseudo-code::

      if (psc == 'p') 
      {
              If you find a file that ends in .p.4096.20.13.0.Part, which
              decodes as: psc.blocksize.block_count.block_rem.block_num".Part"
              then adjust: 
                   - message to contain path with suffix included.
                   - path to feed into checksum calc.
              if the part file is not found, then skip to next part.

              this algo posts all the parts present on local disk.

            confusing things:
               - I don't think it is useful to post all parts, most likely
                 end up repeatedly posting many of the parts that way.
               - likely only want to post each part once, so then would need
                 a way to specify a particular part to post?

          sprintf( suffixstr, ".%c.%lu.%lu.%lu.%lu.Part", psc, sr_c->cfg->blocksize, 
              block_count, block_rem, block_num );
           part_fn = fn + suffixstr
             stat( partfn, partsb );  
          if (Parf_file_found) {
          } else {
             suffixtr[0]='\0';
          }
      };

