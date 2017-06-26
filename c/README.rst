
C functionality is embryonic, there is no intent to build a complete
implementation, it is just a few fragments.

rationale:
  - in some environments getting python3 environment installed is hard
    (example: cray linux environment is a software environment from circa 2009)

  - talking about working on an in-process invocation of sr_post on file closes.


sample from reading:

cc -fPIC -c -Wall sr_poc.c 
cc -fPIC -c -Wall sr_context.c 
gcc -shared -Wl,-soname,libsr.so.1 -o libsr.so.1.0.0 sr_poc.o sr_context.o -ldl -lrabbitmq -lc

