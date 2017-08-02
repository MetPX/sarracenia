
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
};


struct sr_config_t {
  int               accept_unmatched;
  char*             action;
  long unsigned     blocksize; // if partitioned, how big are they?
  struct sr_broker_t *broker;
  float              cache;
  struct sr_cache_t *cachep;
  mode_t             chmod_log;
  char              *configname;
  int                debug;
  char              *directory;
  char              *documentroot;
  int                durable;
  sr_event_t         events;
  char              *exchange;
  int                follow_symlinks;
  int                force_polling;
  int                log;
  struct sr_mask_t  *masks;
  struct sr_mask_t  *match;
  char              *last_matched;  //have run isMatching.
  char              *queuename;
  char              *progname;
  struct sr_path_t  *paths;
  int                pipe;  // pipe mode, read file names from standard input
  int                realpath;
  int                recursive;
  float              sleep;
  char               sumalgo; // checksum algorithm to use.
  struct sr_topic_t *topics;
  char               topic_prefix[AMQP_MAX_SS];
  char              *url;
  struct sr_header_t *user_headers;
  char             *to;
  
};

struct sr_mask_t *isMatchingPattern( struct sr_config_t *sr_cfg, const char* chaine );
 /* return pointer to matched pattern, if there is one, NULL otherwise.
    if called multiple times, it returns a cached response from the previous call.
  */


int sr_config_parse_option( struct sr_config_t *sr_cfg, char *option, char* argument );
 /* update sr_cfg with the option setting (and it's argument) given
    return the number of arguments consumed:  0, 1, or 2.
  */

void sr_add_path( struct sr_config_t *sr_cfg, const char* path );
 /* add a path to the list of paths to monitor.
  */


void sr_add_topic( struct sr_config_t *sr_cfg, const char* sub );
 /* add a topic to the list of bindings, based on the current topic prefix
  */

void sr_config_free( struct sr_config_t *sr_cfg );

void sr_config_init( struct sr_config_t *sr_cfg, const char *progname); 
 /* Initialize an sr_config structure (setting defaults)

    progname sets where in the configuration file tree to look for defaults, as well
    as where the .cache files will be placed ( .(config|cache)/sarra/<progname>/<config>/ )
    config name is guessed later during read, and the cache directories are made
    when the config is finalized.

  */

int sr_config_read( struct sr_config_t *sr_cfg, char *filename );

/* sr_config_read:
   read an sr configuration file, initialize the struct sr_config_t 
   return 1 on success, 0 on failure.
 */

int sr_config_finalize( struct sr_config_t *sr_cfg, const int is_consumer );
 /* 
    after all options and files have been read, initialize 
    remaining values in an sr_config structure (setting defaults)
    prior to use.

    if is_consumer, then a queue will be needed, so perform queue guessing logic.

   return 1 on success, 0 on failure.
  */

#endif
