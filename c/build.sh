
cat >>/dev/null <<EOT
It turns out that the earliest version of librabbitmq that really works with current SSL
is >= 0.8, which is newer than that was shipped in ubuntu 16, much less ubuntu 14.

so, on most machines, need to download rabbitmq-c library and link to the locally built version.

I get it by:

git clone https://github.com/alanxz/rabbitmq-c.git
then build it (see README.md in there.)

Then link to is, with instructions something like below:
EOT

RABBIT_INCDIR=/local/home/peter/src/rabbitmq-c/librabbitmq
RABBIT_LIBDIR=/local/home/peter/src/rabbitmq-c/build/librabbitmq
RABBIT_INCDIR=/home/peter/src/rabbitmq-c/librabbitmq
RABBIT_LIBDIR=/home/peter/src/rabbitmq-c/build/librabbitmq
CFLAGS=" -fPIC -g "

gcc $CFLAGS -c -Wall sr_poc.c 
gcc $CFLAGS -c -Wall sr_credentials.c 
gcc $CFLAGS -c -Wall sr_config.c 
gcc $CFLAGS -c -Wall -I${RABBIT_INCDIR} sr_context.c 
gcc $CFLAGS -shared -Wl,-soname,libsrshim.so.1 -o libsrshim.so.1.0.0 sr_poc.o sr_context.o sr_config.o sr_credentials.o -ldl -Wl,-rpath,/home/peter/src/rabbitmq-c/build/librabbitmq -L/home/peter/src/rabbitmq-c/build/librabbitmq -lrabbitmq -luriparser -lcrypto -lc 

gcc $CFLAGS -o sr_configtest sr_configtest.c sr_config.o sr_credentials.o -luriparser
gcc $CFLAGS -o sr_cpost sr_cpost.c sr_context.o sr_config.o sr_credentials.o -Wl,-rpath,${RABBIT_LIBDIR} -L${RABBIT_LIBDIR} -lrabbitmq -luriparser -lcrypto

# using libcrypto from libssl for hash algorithms.
