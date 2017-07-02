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

  call an sr_context_init to set things up.
  then sr_post will post files,
  then sr_close to tear the connection down.

  there is an all in one function: connect_and_post that does all of the above.

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

#include "sr_config.h"


struct sr_context {

  char settings[255];
  const char *scheme;
  const char *exchange;
  const char *file;
  const char *hostname;
  const char *url;
  const char *user;
  const char *password;
  const char *to;
  amqp_socket_t *socket;
  amqp_connection_state_t conn;
  int port;
  struct sr_config_t *cfg;
};


struct sr_context *sr_context_init_config(struct sr_config_t *sr_cfg);

/* context_init sets up a context.
   returns connection to a broker based on given configuration.
   returns an sr_context ready for use by connect.
 */


struct sr_context *sr_context_connect(struct sr_context *sr_c);
/* 
   returns open connection to a broker based on given configuration.
   returns an sr_context ready for use by post.
   connection establishment is done here.
 */

void sr_post(struct sr_context *sr_c, const char *fn, struct stat *sb); 
/* 
   post the given file name using the established context.
   (posts over an existing connection.)

   The struct stat is normally the result of lstat(fn,sb);
   sr_post reads:  st_size, st_atim, st_mtim, and st_mode.
   those fields are used to build the advertisement.

 */

void sr_context_close(struct sr_context *sr_c); 
/* clean up an initialized context.
   tears down the connection.
 */

void connect_and_post(const char *fn);
 /* do all of the above: connect, post, and close in one call.
    less efficient when you know you are doing many posts.
  */
