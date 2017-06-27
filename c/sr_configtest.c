
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
#include "sr_config.h"

#define FNAME   "/home/peter/.config/sarra/post/test2.conf" 

int main( int argc, char *const *argv ) {

  char *cfg;
  char **tag, *value;
  int i;
  UriParserStateA state; 
  struct UriPathSegmentStructA *pathelem;
  struct sr_config_t sr_cfg;

  printf( "reading: %s\n", argv[1] );

  sr_config_init( &sr_cfg );
  sr_config_read( &sr_cfg, argv[1] );


  printf( "broker, scheme=%s\n", sr_cfg.broker.scheme );
  printf( "broker, userInfo=%s \n", sr_cfg.broker.userInfo );
  printf( "broker, hostText=%s \n", sr_cfg.broker.hostText );
  printf( "broker, portText=%s \n", sr_cfg.broker.portText );
  printf( "posting exchange=%s \n", sr_cfg.exchange);
  printf( "posting url=%s \n", sr_cfg.url);

  //*(char*)(uri.pathHead.afterLast) = '\0';
  pathelem= sr_cfg.broker.pathHead;
  while ( pathelem != NULL )  {
      fprintf( stderr, "broker, pathelem=%s \n", pathelem->text );
      pathelem = pathelem->next;
  }

  // no, because storage is static in uricb...  uriFreeUriMembersA(&uri);
  exit(0);

}
