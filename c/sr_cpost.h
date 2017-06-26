/* vim:set ft=c ts=2 sw=2 sts=2 et cindent: */

/*
 * Usage info after license block.
 *
 * This code is by Peter Silva copyright (c) 2017 part of MetPX.
 * copyright is to the Government of Canada. code is GPL.
 *
 * based on a amqp_sendstring from rabbitmq-c package
 * the original license is below:
 */

/* 
  Minimal c implementation to allow posting of sr_post(7) messages.
  It has a lot of limitations, and no error checking for now.

  how to use:

  in a shell, set the SW_AMQP_MINI_OPTS environment variable to a space 
  separated sequence of settings.  The settings are:

  protocol scheme ( amqps, or amqp ) whether to use SSL or not.
  broker hostname
  broker port 
  broker exchange
  broker username (AMQP username to connect to broker)
  broker password (password for AMQP username)
  base URL to advertise  (examples: file:, http://localhost, sftp://hoho@host )

  comma separated list of destinations to target (examples: localhost, all)
 
  there are no defaults, it will just die horribly if something is missing.

  export SR_AMQP_MINI_OPTS="amqp localhost 5672 xs_tsource tsource tspw sftp://peter@localhost localhost"

  then just:

  sr_cpost <file>

 building it:

  cc -o sr_cpost sr_cpost.c -lrabbitmq

 (debian package: librabbitmq, and librabbitmq-dev. )

 limitations:
    - Doesn't calculate checksums, enforces sum 0.
    - Doesn't do file partitioning strategies, enforced post as 1 part.
    - Doesn't support document_root, absolute paths posted.
    - Doesn't read sr configuration files, only uses the SR_ environment variable listed above.
    - as part of the no config file support, no accept/reject support     

 */
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <time.h>


#include <stdint.h>
#include <amqp_ssl_socket.h>
#include <amqp_tcp_socket.h>
#include <amqp.h>
#include <amqp_framing.h>

struct sr_context {

  char settings[255];
  char const *scheme;
  char const *exchange;
  char const *file;
  char const *hostname;
  char const *url;
  char const *user;
  char const *password;
  char const *to;
  amqp_socket_t *socket;
  amqp_connection_state_t conn;
  int port;
};


struct sr_context *sr_context_init();
/* context_init sets up a connection to a broker
   returns an sr_context ready for use by post

   connection establishment is done here.
 */

void sr_post(struct sr_context *sr_c, const char *fn ); 
/* post the given file name based on the established context.

   posts over an existing connection.

 */

void sr_context_close(struct sr_context *sr_c); 
/* clean up an initialized context.
   tears down the connection.
 */

void connect_and_post(const char *fn);
 /* do all of the above: connect, post, and close in one call.
    less efficient when you know you are doing many posts.
  */
