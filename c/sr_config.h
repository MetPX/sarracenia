
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
  UriUriA broker;
  char brokeruricb[1024];
  char *directory;
  char *exchange;
  struct sr_mask_t *masks;
  char *url;
  char *to;
  int  debug;
  int  accept_unmatched;
  
};

struct sr_mask_t *isMatchingPattern( struct sr_config_t *sr_cfg, const char* chaine );
 /* return pointer to matched pattern, if there is one, NULL otherwise.
  */

void sr_config_read( struct sr_config_t *sr_cfg, char *filename );

/* sr_config_read:
   read an sr configuration file, initialize the struct sr_config_t 
 */
