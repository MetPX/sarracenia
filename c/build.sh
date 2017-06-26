
cc -fPIC -c -Wall sr_poc.c 
gcc -fPIC -c -Wall sr_credentials.c 
gcc -fPIC -c -Wall sr_config.c 
cc -fPIC -c -Wall sr_context.c 
gcc -shared -Wl,-soname,libsr.so.1 -o libsr.so.1.0.0 sr_poc.o sr_context.o sr_config.o sr_credentials.o -ldl -lrabbitmq -luriparser -lc

gcc -fPIC -o sr_configtest sr_configtest.c sr_config.o sr_credentials.o -luriparser
gcc -fPIC -o sr_cpost sr_cpost.c sr_context.o sr_config.o sr_credentials.o -lrabbitmq -luriparser 
