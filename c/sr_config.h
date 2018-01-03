
/*
 This file is part of metpx-sarracenia.
 The sarracenia suite is Free and is proudly provided by the Government of Canada
 Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2017

 author: Peter Silva

status: 
  This is just a beginning stub, it does basic stuff required for posting.
  and throws an *unimplemented* option for the rest.

  Purpose is to have something that parses the sarracenia configuration files in C.

 */

#ifndef SR_CONFIG_H

#define SR_CONFIG_H 1

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <regex.h>
#include <linux/limits.h>
#include <time.h>
#include <openssl/sha.h>

// for kill(2)
#include <sys/types.h>
#include <signal.h>

// AMQP stuff.
#include <stdint.h>
#include <amqp_ssl_socket.h>
#include <amqp_tcp_socket.h>
#include <amqp.h>
#include <amqp_framing.h>


#include "sr_util.h"
#include "sr_event.h"

// AMQP PROTOCOL LIMIT IMPOSED HERE... see definition of short strings.
// 255 characters, + terminating nul
#define AMQP_MAX_SS (255+1)

#define PATH_MAXNUL (PATH_MAX+1)

#include "sr_cache.h"

struct sr_path_t {
   char path[PATH_MAX];
   struct sr_path_t *next;
};

struct sr_topic_t {
  char topic[AMQP_MAX_SS]; 
  struct sr_topic_t *next;
};

struct sr_header_t {
  char *key;
  char *value;
  struct sr_header_t *next;
};

struct sr_mask_t {
  char* clause;
  char* directory;
  regex_t regexp;
  int   accepting;
  struct sr_mask_t *next;
};

struct sr_broker_t {
  int ssl;                     
  char *user;
  char *password;
  char *hostname;
  int   port;
  char *exchange;
  int   exchange_split;
  uint64_t last_delivery_tag;
  amqp_socket_t *socket;
  amqp_connection_state_t conn;
  int started;
  struct sr_broker_t *next; 
};


struct sr_config_t {
  int                 accept_unmatched;
  char*               action;
  long unsigned       blocksize; // if partitioned, how big are they?
  struct sr_broker_t *broker;
  float               cache;
  struct sr_cache_t  *cachep;
  mode_t              chmod_log;
  char               *configname;
  int                 debug;
  int                 delete;
  char               *directory;
  char               *post_base_dir;
  char                statehost;  // '0','s','f' meaning no, short fqdn
  char               *statehostval;  // actual hostname resulting from statehost.
  int                 durable;
  sr_event_t          events;
  char                *exchange;
  int                 expire;
  int                 follow_symlinks;
  int                 force_polling;
  float               heartbeat;
  int                 help;           // print usage and exit if set.
  int                 instance;
  char               *last_matched;  //have run isMatching.
  char               *list;          //method to generate initial input list:  file or queue
  int                 log;           // use a log file, rather than standard files.
  char               *logfn;           // use a log file, rather than standard files.
  int                 logseverity;      // severity of messages to log (regardless of where.)
  struct sr_mask_t   *masks;
  struct sr_mask_t   *match;
  int                 message_ttl;
  char               *outlet;
  int                 pid;
  char               *pidfile;
  char               *progname;
  struct sr_path_t   *paths;
  int                 pipe;  // pipe mode, read file names from standard input
  struct sr_broker_t *post_broker;
  char               *post_exchange;
  int                 post_exchange_split;
  char               *queuename;
  int                 realpath;
  int                 recursive;
  float               sleep;
  char                sumalgo; // checksum algorithm to use.
  char               *source;
  char               *to;
  struct sr_topic_t  *topics;
  char                topic_prefix[AMQP_MAX_SS];
  char               *post_base_url;
  struct sr_header_t *user_headers;
  
};

char *local_fqdn();
/*
   return a string containing the fully qualified domain name of the computer running
   the code.
 */

struct sr_mask_t *isMatchingPattern( struct sr_config_t *sr_cfg, const char* chaine );
 /* 
    return pointer to matched pattern, if there is one, NULL otherwise.
    if called multiple times, it returns a cached response from the previous call.
  */


int sr_config_parse_option( struct sr_config_t *sr_cfg, char *option, char* argument, char* arg2, int master );
 /* 
    update sr_cfg with the option setting (and it's argument) given
    return the number of arguments consumed:  0, 1, or 2.
  */

void sr_add_path( struct sr_config_t *sr_cfg, const char* path );
 /* 
    add a path to the list of paths to monitor.
  */


void sr_add_topic( struct sr_config_t *sr_cfg, const char* sub );
 /* 
    add a topic to the list of bindings, based on the current topic prefix
  */

char *sr_broker_uri( struct sr_broker_t *b );
 /*
   given a broker, print the corresponding uri string
  */


void sr_config_free( struct sr_config_t *sr_cfg );

void sr_config_init( struct sr_config_t *sr_cfg, const char *progname); 
 /* 
    Initialize an sr_config structure (setting defaults)

    progname sets where in the configuration file tree to look for defaults, as well
    as where the .cache files will be placed ( .(config|cache)/sarra/<progname>/<config>/ )
    config name is guessed later during read, and the cache directories are made
    when the config is finalized.

  */

int sr_config_read( struct sr_config_t *sr_cfg, char *filename, int abort, int master );

/* 
   sr_config_read:
   read an sr configuration file, initialize the struct sr_config_t 

   return 1 on success, 0 on failure.

   if *abort* is non-zero, then rather than returning a status, the routine 
   causes the program to exit.

   if *master* is set, then the file being read is a potential master configuration, that
   is a named configuration file that will correspond to a running process.
   if *master* is 0, then the file being read is only an include file.

 */

int sr_config_finalize( struct sr_config_t *sr_cfg, const int is_consumer );
 /* 
    after all options and files have been read, initialize 
    remaining values in an sr_config structure (setting defaults)
    prior to use.

    if is_consumer, then a queue will be needed, so perform queue guessing logic.

    return 1 on success, 0 on failure.
  */

int sr_config_activate( struct sr_config_t *sr_cfg );
/* 
   turn into a really running instance (that can modify state files). 
   Writes the pid to a save file, sets handler for exit.

   SIDE EFFECT: sets a signal handler for SIGTERM (to cleanly close cache on exit.)
 */


int sr_config_startstop( struct sr_config_t *sr_cfg);
/*
   process common actions: start|stop|status 

   killing existing instance, etc...

   return code:

   0 - operation is complete, should exit.
  <0 - operation errored, should exit. 
  >0 - operation succeeded, should continue.

   the action == 'status' then 
      return config_is_running?0:-1

 */

void sr_config_add( struct sr_config_t *sr_cfg );

void sr_config_disable( struct sr_config_t *sr_cfg );

void sr_config_edit( struct sr_config_t *sr_cfg );

void sr_config_enable( struct sr_config_t *sr_cfg );

void sr_config_log( struct sr_config_t *sr_cfg );

void sr_config_remove( struct sr_config_t *sr_cfg );



void sr_config_list( struct sr_config_t *sr_cfg );
/* list the available configurations for the given progname */

#endif
