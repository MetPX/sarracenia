
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

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <regex.h>

#include <uriparser/Uri.h>

struct sr_mask_t {
  char* clause;
  char* directory;
  regex_t regexp;
  int   accepting;
  struct sr_mask_t *next;
};

struct sr_config_t {
  int               accept_unmatched;
  long unsigned     blocksize; // if partitioned, how big are they?
  UriUriA           broker;
  int               broker_specified;
  char              brokeruricb[1024];
  int               debug;
  char             *directory;
  char             *exchange;
  struct sr_mask_t *masks;
  int              parts;  // partition strategy.
  char             sumalgo; // checksum algorithm to use.
  char             *url;
  char             *to;
  
};

struct sr_mask_t *isMatchingPattern( struct sr_config_t *sr_cfg, const char* chaine );
 /* return pointer to matched pattern, if there is one, NULL otherwise.
  */

int sr_config_parse_option( struct sr_config_t *sr_cfg, char *option, char* argument );
 /* update sr_cfg with the option setting (and it's argument) given
    return the number of arguments consumed:  0, 1, or 2.
  */


void sr_config_init( struct sr_config_t *sr_cfg );
 /* Initialize an sr_config structure (setting defaults)
  */

void sr_config_read( struct sr_config_t *sr_cfg, char *filename );

/* sr_config_read:
   read an sr configuration file, initialize the struct sr_config_t 
 */
