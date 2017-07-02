
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

There is also an LD_PRELOAD shim library example. (sr_poc.c) that
uses the posting api.

sample build instructions are in build.sh

The librabbitmq version needs to be > 0.8,  this is newer than what is in ubuntu 16.04.
So you need to git clone ... see build.sh


build dependencies:
liburiparser-dev - development files for uriparser
librabbitmq-dev - AMQP client library written in C - Dev Files
libssl-dev  - OpenSSL client library (used for hash algorithms.)

run dependencies:
liburiparser1 - URI parsing library compliant with RFC 3986
librabbitmq4 - AMQP client library written in C
libssl - OpenSSL client library.


Developer Notes:

whereami:
  - was looking at how to do partitioned files, wrote footnote #1 in sr_context.c
  - result was that the cache is probably required before doing partition support.
  - so thinking about doing the cache.
  


Plan:
  - local posting (mostly done.)
  - shim likely needs to work with symlink, unlink, and link calls as well as just close.
  - probably need to do symlinks (done) unlinks, links.
  - see how well it goes with shim.
  - figure out packaging?

  - if the local shim does not go well, step 2 is: sr_cwatch.
  - 




worries:

  - behaviour on posting and empty file results in a partstr 1,0,1,0,0
    partstrategy=1 (whole file), blocksize=0, blockcount=1, remainder=0, block=0.
    does that mean subscribers should try to download 0 bytes ? ... wondering if there 
    is something to do.  Should look at subscribers and confirm they do something sane.
 
