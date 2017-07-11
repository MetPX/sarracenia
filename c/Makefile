# 
# RABBITMQC_HOME is required - Rabbit-MQ C version
#

RABBIT_LIBDIR = ${RABBITMQC_HOME}/lib
RABBIT_INCDIR = -I${RABBITMQC_HOME}/include
RABBIT_LINK = -Wl,-rpath,${RABBIT_LIBDIR} -L${RABBIT_LIBDIR}
SARRA_LIBDIR = ${CURDIR}
SARRA_LINK = -Wl,-rpath,${SARRA_LIBDIR} -L${SARRA_LIBDIR}

CC = gcc
CFLAGS = -fPIC -g -std=gnu99

SARRA_OBJECT = libsarra.so.1.0.0 sr_context.o sr_config.o sr_event.o sr_credentials.o
EXT_LIB = -lrabbitmq -luriparser -lcrypto -lc
SHARED_LIB = libsrshim.so.1 -o libsrshim.so.1.0.0 libsrshim.c libsarra.so.1.0.0


all: 
	$(CC) $(CFLAGS) -c -Wall libsrshim.c
	$(CC) $(CFLAGS) -c -Wall sr_credentials.c
	$(CC) $(CFLAGS) -c -Wall sr_event.c
	$(CC) $(CFLAGS) -c -Wall sr_config.c
	$(CC) $(CFLAGS) -c -Wall $(RABBIT_INCDIR) sr_context.c
	$(CC) $(CFLAGS) -shared -Wl,-soname,libsarra.so.1 -o $(SARRA_OBJECT) -ldl $(RABBIT_LINK) $(EXT_LIB)
	$(CC) $(CFLAGS) -shared -Wl,-soname,$(SHARED_LIB) -ldl $(SARRA_LINK) $(RABBIT_LINK) $(EXT_LIB)
	if [ ! -f libsarra.so ]; \
	then \
		ln -s libsarra.so.1.0.0 libsarra.so ; \
	fi;
	if [ ! -f libsarra.so.1 ]; \
	then \
		ln -s libsarra.so.1.0.0 libsarra.so.1 ; \
	fi;
	$(CC) $(CFLAGS) -o sr_configtest sr_configtest.c -lsarra $(SARRA_LINK) -luriparser
	$(CC) $(CFLAGS) -o sr_cpost sr_cpost.c -lsarra $(SARRA_LINK) $(RABBIT_LINK) -lrabbitmq -luriparser -lcrypto


install:
	@mkdir bin lib
	@mv *.so lib
	@mv *.so.* lib
	@mv sr_cpost bin

clean:
	@rm -f *.o *.so *.so.* sr_cpost
	@rm -rf bin lib
