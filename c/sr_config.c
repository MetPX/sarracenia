
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

#include "sr_credentials.h"

#include "sr_config.h"


#define NULTERM(x)  if (x != NULL) *x = '\0' ;

void config_uri_parse( char *src, UriUriA *ua, char *buf ) {
  /* copy src string to buf, adding nuls to separate path elements. 
     so each string is nul-treminated.
   */

  UriParserStateA state; 
  state.uri = ua;
  strcpy( buf, src );
  if (uriParseUriA(&state, buf ) != URI_SUCCESS) return;

  NULTERM( (char*)(ua->scheme.afterLast) );
  NULTERM( (char*)(ua->userInfo.afterLast) );
  NULTERM( (char*)(ua->hostText.afterLast) );
  NULTERM( (char*)(ua->portText.afterLast) );
} 

int StringIsTrue(const char *s) {

   if (s == NULL ) return(1);

   if ( !strcasecmp(s,"true") || 
        !strcasecmp(s,"on")  ||
        !strcasecmp(s,"yes")  ) 
     return (1);

   return(0);
}

#define TOKMAX (1024)

char token_line[TOKMAX];

void parse(struct sr_config_t *sr_cfg, char* option, char* argument) 
{

  char *brokerstr;

  if ( strcspn(option," \t\n#") == 0 ) return;

  // printf( "option: %s,  argument: %s \n", option, argument );
  if ( !strcmp( option, "broker" ) ) 
  {
      brokerstr = sr_credentials_fetch(argument); 
      if ( brokerstr == NULL ) 
      {
          fprintf( stderr,"notice: no stored credential: %s.\n", argument );
          config_uri_parse( argument, &(sr_cfg->broker), sr_cfg->brokeruricb );
      } else {
          config_uri_parse( brokerstr, &(sr_cfg->broker), sr_cfg->brokeruricb );
      }
  } else if ( !strcmp( option, "url" ) ) {
      sr_cfg->url = strdup(argument);
  } else if ( !strcmp( option, "exchange" ) ) {
      sr_cfg->exchange = strdup(argument);
  } else if ( !strcmp( option, "to" ) ) {
      sr_cfg->to = strdup(argument);
  } else if ( !strcmp( option, "debug" ) ) {
      sr_cfg->debug = StringIsTrue(argument);
  } else {
      fprintf( stderr, "info: %s option not implemented, ignored.\n", option );
  } 
}

void sr_config_read( struct sr_config_t *sr_cfg, char *filename ) 
{
  FILE *f;
  char *option;
  char *argument;

  f = fopen( filename, "r" );
  if ( f == NULL ) {
    fprintf( stderr, "fopen of %s failed", filename );
    return;
  }
  // Initialization...
  sr_credentials_init();
  sr_cfg->debug=0;
  sr_cfg->to=NULL;

  while ( fgets(token_line,TOKMAX,f) != NULL ) 
   {
     //printf( "line: %s", token_line );

     if (strspn(token_line," \t\n") == strlen(token_line) ) 
     {
         continue; // blank line.
     }
     option   = strtok(token_line," \t\n");
     argument = strtok(NULL," \t\n");

     parse(sr_cfg, option,argument);

  };
  fclose( f );
}

