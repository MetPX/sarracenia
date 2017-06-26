
cc -fPIC -c -Wall sr_poc.c 
cc -fPIC -c -Wall sr_context.c 
gcc -shared -Wl,-soname,libsr.so.1 -o libsr.so.1.0.0 sr_poc.o sr_context.o -ldl -lrabbitmq -lc
