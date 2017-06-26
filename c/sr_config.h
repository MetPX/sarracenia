
/*
 This file is part of metpx-sarracenia.
 The sarracenia suite is Free and is proudly provided by the Government of Canada
 Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2017

 author: Peter Silva

status: 
  This is just a beginning stub, not working at all. 

  Purpose is to have something that parses the sarracenia configuration files in C.

 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include <uriparser/Uri.h>


struct sr_config_t {
  UriUriA broker;
  char brokeruricb[1024];
  char *exchange;
  char *url;
  char *to;
  int  debug;
};

void sr_config_read( struct sr_config_t *sr_cfg, char *filename );

/* sr_config_read:
   read an sr configuration file, initialize the struct sr_config_t 
 */
