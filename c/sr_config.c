
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

struct sr_mask_t *isMatchingPattern(struct sr_config_t *sr_cfg, const char* chaine )
   /* return pointer to matched pattern, if there is one, NULL otherwise.
    */
{
   struct sr_mask_t *entry;
   
   entry = sr_cfg->masks;
   while( entry ) 
   {
       if ( regexec(&(entry->regexp), chaine, (size_t)0, NULL, 0 ) )
           break; // matched
       entry = entry->next; 
   }
   return(entry);
}


void add_mask(struct sr_config_t *sr_cfg, char *directory, char *option, int accept )
{
    struct sr_mask_t *new_entry;
    struct sr_mask_t *next_entry;

    if ( (sr_cfg) && sr_cfg->debug )
        fprintf( stderr, "adding mask: %s, accept=%d\n", option, accept );

    new_entry = (struct sr_mask_t *)malloc( sizeof(struct sr_mask_t) );
    new_entry->next=NULL;
    new_entry->directory = (directory?strdup(directory):NULL);
    new_entry->accepting = accept;
    regcomp( &(new_entry->regexp), option, REG_EXTENDED|REG_NOSUB );

    // append new entry to existing masks.
    if ( sr_cfg->masks == NULL ) 
    {
        sr_cfg->masks = new_entry;
    } else {
        next_entry = sr_cfg->masks;
        while( next_entry->next != NULL ) 
           next_entry = next_entry->next;
        next_entry->next = new_entry;
    }
}


void config_uri_parse( char *src, UriUriA *ua, char *buf ) 
{
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

int StringIsTrue(const char *s) 
{

   if (s == NULL ) return(1);

   if ( !strcasecmp(s,"true") || 
        !strcasecmp(s,"on")  ||
        !strcasecmp(s,"yes")  ) 
     return (1);

   return(0);
}

#define TOKMAX (1024)

char token_line[TOKMAX];

void sr_config_parse_option(struct sr_config_t *sr_cfg, char* option, char* argument) 
{

  char *brokerstr;

  if ( strcspn(option," \t\n#") == 0 ) return;

  if (sr_cfg->debug)
     fprintf( stderr, "option: %s,  argument: %s \n", option, argument );

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
  } else if ( !strcmp( option, "accept" ) || !strcmp( option, "get" ) ) {
      add_mask( sr_cfg, sr_cfg->directory, option, 1 );
  } else if ( !strcmp( option, "accept_unmatch" ) ) {
      sr_cfg->accept_unmatched = StringIsTrue(argument);
  } else if ( !strcmp( option, "config" ) || !strcmp(option,"include" )) {
      sr_config_read( sr_cfg, argument );
  } else if ( !strcmp( option, "debug" ) ) {
      sr_cfg->debug = StringIsTrue(argument);
  } else if ( !strcmp( option, "directory" ) ) {
      sr_cfg->directory = strdup(argument);
  } else if ( !strcmp( option, "exchange" ) ) {
      sr_cfg->exchange = strdup(argument);
  } else if ( !strcmp( option, "reject" ) ) {
      add_mask( sr_cfg, sr_cfg->directory, option, 0 );
  } else if ( !strcmp( option, "to" ) ) {
      sr_cfg->to = strdup(argument);
  } else if ( !strcmp( option, "url" ) ) {
      sr_cfg->url = strdup(argument);
  } else {
      fprintf( stderr, "info: %s option not implemented, ignored.\n", option );
  } 
}

void sr_config_init( struct sr_config_t *sr_cfg ) 
{
  sr_credentials_init();
  sr_cfg->debug=0;
  sr_cfg->accept_unmatched=1;
  sr_cfg->to=NULL;
  sr_cfg->directory=NULL;
  sr_cfg->masks=NULL;
  sr_cfg->url=NULL;
}

void sr_config_read( struct sr_config_t *sr_cfg, char *filename ) 
{
  FILE *f;
  char *option;
  char *argument;

  f = fopen( filename, "r" );
  if ( f == NULL ) {
    fprintf( stderr, "fopen of %s failed\n", filename );
    return;
  }

  while ( fgets(token_line,TOKMAX,f) != NULL ) 
   {
     //printf( "line: %s", token_line );

     if (strspn(token_line," \t\n") == strlen(token_line) ) 
     {
         continue; // blank line.
     }
     option   = strtok(token_line," \t\n");
     argument = strtok(NULL,"\n");

     sr_config_parse_option(sr_cfg, option,argument);

  };
  fclose( f );
}

