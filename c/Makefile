

# 
# if rabbitmq library is provided by SSM package, RABBITMQC_HOME is required. 
# 
ifdef RABBITMQC_HOME
RABBIT_LIBDIR = ${RABBITMQC_HOME}/lib
RABBIT_INCDIR = -I${RABBITMQC_HOME}/include
RABBIT_LINK = -Wl,-rpath,${RABBIT_LIBDIR} -L${RABBIT_LIBDIR}
endif

# If rabbitmq library is only built (not installed) then set RABBIT_BUILD
ifdef RABBIT_BUILD
RABBIT_LIBDIR=${RABBIT_BUILD}/build/librabbitmq
RABBIT_INCDIR = -I${RABBIT_BUILD}/librabbitmq
RABBIT_LINK = -Wl,-rpath,${RABBIT_LIBDIR} -L${RABBIT_LIBDIR}
endif

SARRA_LIBDIR = ${CURDIR}
SARRA_LINK = -Wl,-rpath,${SARRA_LIBDIR} -L${SARRA_LIBDIR}

# if neither variable is set, then it is assumed to be available from default environment.

CC = gcc
CFLAGS = -fPIC -g -std=gnu99 -Wall -D_GNU_SOURCE $(RABBIT_INC)

SARRA_OBJECT = sr_post.o sr_consume.o sr_context.o sr_config.o sr_event.o sr_credentials.o sr_cache.o sr_util.o
SARRA_LIB = libsarra.so.1.0.0 
EXT_LIB = -lrabbitmq -luriparser -lcrypto -lc
SHARED_LIB = libsrshim.so.1 -o libsrshim.so.1.0.0 libsrshim.c libsarra.so.1.0.0

.c.o: 
	$(CC) $(CFLAGS) -c  $<

all: $(SARRA_OBJECT)
	$(CC) $(CFLAGS) -shared -Wl,-soname,libsarra.so.1 -o libsarra.so.1.0.0 $(SARRA_OBJECT) -ldl $(RABBIT_LINK) $(EXT_LIB)
	$(CC) $(CFLAGS) -shared -Wl,-soname,$(SHARED_LIB) -ldl $(SARRA_LINK) $(RABBIT_LINK) $(EXT_LIB)
	if [ ! -f libsarra.so ]; \
	then \
		ln -s libsarra.so.1.0.0 libsarra.so ; \
	fi;
	if [ ! -f libsarra.so.1 ]; \
	then \
		ln -s libsarra.so.1.0.0 libsarra.so.1 ; \
	fi;
	$(CC) $(CFLAGS) -o sr_configtest sr_configtest.c -lsarra $(SARRA_LINK) -lrabbitmq $(RABBIT_LINK) -luriparser -lcrypto
	$(CC) $(CFLAGS) -o sr_utiltest sr_utiltest.c -lsarra $(SARRA_LINK) -lrabbitmq $(RABBIT_LINK) -luriparser -lcrypto
	$(CC) $(CFLAGS) -o sr_cachetest sr_cachetest.c -lsarra $(SARRA_LINK) -lrabbitmq $(RABBIT_LINK) -luriparser -lcrypto
	$(CC) $(CFLAGS) -o sr_cpost sr_cpost.c -lsarra $(SARRA_LINK) -lrabbitmq $(RABBIT_LINK) -luriparser -lcrypto
	$(CC) $(CFLAGS) -o sr_csub2json sr_csub2json.c -lsarra $(SARRA_LINK) -lrabbitmq $(RABBIT_LINK) -luriparser -lcrypto


install:
	@mkdir build build/bin build/lib build/include
	@mv *.so build/lib
	@mv *.so.* build/lib
	@mv sr_cpost build/bin
	@cp *.h build/include/

clean:
	@rm -f *.o *.so *.so.* sr_cpost sr_configtest sr_utiltest sr_csub2json sr_cachetest sr_cache_save.test
	@rm -rf build

test:
	./sr_configtest test_post.conf 
	./sr_utiltest 
	./sr_cachetest
