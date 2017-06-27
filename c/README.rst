
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


build dependencies:
liburiparser-dev - development files for uriparser
librabbitmq-dev - AMQP client library written in C - Dev Files

run dependencies:
liburiparser1 - URI parsing library compliant with RFC 3986
librabbitmq4 - AMQP client library written in C

