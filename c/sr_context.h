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

  char settings[AMQP_MAX_SS];
  const char *exchange;
  const char *file;
  const char *url;
  const char *to;
  amqp_socket_t *socket;
  amqp_connection_state_t conn;
  int port;
  struct sr_config_t *cfg;
};


void sr_amqp_error_print(int x, char const *context);
/* utility functions for handling rabbitmq-c call return values.
   for rabbitmq-c routines that return an integer, process the output.
 */

void sr_amqp_reply_print(amqp_rpc_reply_t x, char const *context);
/* utility functions for handling rabbitmq-c call return values.
   if return value from a function is an amqp_rpc_reply_t, then feed it to this routine.
   context, is a descriptive string.
 */

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

void sr_context_close(struct sr_context *sr_c); 
/* clean up an initialized context.
   tears down the connection.
 */




 
