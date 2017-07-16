
C functionality is embryonic, there is no intent to build a complete
implementation, it is just a few fragments.

rationale:
  - in some environments getting python3 environment installed is hard
    (example: cray linux environment is a software environment from circa 2009)

  - talking about working on an in-process invocation of sr_post on file closes.

one can access from C directly using the sr_context.h routines.
It uses sr_config(7) style config files, but a lot of options are 
unimplemented.

So there is a command line binary, that can call the library:

   sr_cpost

There is also an LD_PRELOAD shim library example. (sr_srshim.c) that
uses the posting api.

sample build instructions are in build.sh

The librabbitmq version needs to be > 0.8,  this is newer than what is in ubuntu 16.04.
So you need to git clone ... then 

export RABBIT_BUILD=*directory where rabbit has been built*




build dependencies:
liburiparser-dev - development files for uriparser
librabbitmq-dev - AMQP client library written in C - Dev Files
libssl-dev  - OpenSSL client library (used for hash algorithms.)

run dependencies:
liburiparser1 - URI parsing library compliant with RFC 3986
librabbitmq4 - AMQP client library written in C
libssl - OpenSSL client library.


  

Dorval Computing Centre
-----------------------

If you are in the Dorval computing centre environment, then SSM is available and 
a compatible version of rabbitmq-c can be obtained 

. ssmuse-sh -d /fs/ssm/main/opt/rabbitmqc/rabbitmqc-0.8.0
 
To load sr_cpost
. ssmuse-sh -d /fs/ssm/hpco/exp/sarrac-0.1
 


Plan:
  - figure out packaging?
  - if the local shim does not go well, step 2 is: sr_cwatch.


Developer Notes:

whereami:
  - was looking at how to do partitioned (partflg='p') files, wrote footnote #1. 

  - result is that the cache is probably required before doing partition support.
    so thinking about doing the cache.

  - when sleep > 0, cpost now walks trees by keeping track of the start mtime of the last pass.
    algorithm based on *mtime* > start of previous pass... that's not necessarily good.

    for example search of new directory.
        whereas when you post a directory initially, is posts with mtime=0 first pass, so whole thing.
        but if a directory is added, mtime is already current, so only files that change in future
        will be posted... HMM...

  - FIXME: did all this with *second* resolution, might want to go hi-res.

  - do we go to the whole (copy directories into a file for comparison schtick?
    that's more sr_poll.

worries/notes to self:

  - behaviour on posting and empty file results in a partstr 1,0,1,0,0
    partstrategy=1 (whole file), blocksize=0, blockcount=1, remainder=0, block=0.
    does that mean subscribers should try to download 0 bytes ? ... wondering if there 
    is something to do.  Should look at subscribers and confirm they do something sane.
 
   Footnote 1: FIXME: posting partitioned parts Not yet implemented.

   pseudo-code
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
               - perhaps require cache to suppress repeats?

          sprintf( suffixstr, ".%c.%lu.%lu.%lu.%lu.Part", psc, sr_c->cfg->blocksize, 
              block_count, block_rem, block_num );
           part_fn = fn + suffixstr
             stat( partfn, partsb );  
          if (Parf_file_found) {
          } else {
             suffixtr[0]='\0';
          }
      };

