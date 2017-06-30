
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
       if ( (sr_cfg) && sr_cfg->debug )
           fprintf( stderr, "isMatchingPattern, testing mask: %s %-30s next=%p\n", 
                (entry->accepting)?"accept":"reject", entry->clause, (entry->next) );

       if ( !regexec(&(entry->regexp), chaine, (size_t)0, NULL, 0 ) ) {
           break; // matched
       }
       entry = entry->next; 
   }
   if ( (sr_cfg) && sr_cfg->debug )
   {
       if (entry) 
           fprintf( stderr, "isMatchingPattern: %s matched mask: %s %s\n",  chaine,
               (entry->accepting)?"accept":"reject", entry->clause );
       else
           fprintf( stderr, "isMatchingPattern: %s did not match any masks\n",  chaine );
   }
   return(entry);
}


void add_mask(struct sr_config_t *sr_cfg, char *directory, char *option, int accept )
{
    struct sr_mask_t *new_entry;
    struct sr_mask_t *next_entry;

    // if ( (sr_cfg) && sr_cfg->debug )
    //    fprintf( stderr, "adding mask: %s %s\n", accept?"accept":"reject", option );

    new_entry = (struct sr_mask_t *)malloc( sizeof(struct sr_mask_t) );
    new_entry->next=NULL;
    new_entry->directory = (directory?strdup(directory):NULL);
    new_entry->accepting = accept;
    new_entry->clause = strdup(option);
    regcomp( &(new_entry->regexp), option, REG_EXTENDED|REG_NOSUB );

    // append new entry to existing masks.
    if ( sr_cfg->masks == NULL ) 
    {
        sr_cfg->masks = new_entry;
    } else {
        next_entry = sr_cfg->masks;
        while( next_entry->next != NULL ) 
        {
            next_entry = next_entry->next;
        }
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
 /*
    return bitmask:  0-1 string value,  argument is a value 0-1
    0- 00 - unlikely to occur, there is no value, and returning false.
    1- 01 - value is false and argument provide ( -option no )
    2- 10 - value is true and argument omitted  ( -option    )
    3- 11 - value is true and argument provided ( -option yes ) 
  */
{

   if ((s == NULL ) || (*s=='-')) return(2);

   if ( !strcasecmp(s,"true") || 
        !strcasecmp(s,"on")  ||
        !strcasecmp(s,"yes")  ) 
     return (3);

   if ( !strcasecmp(s,"false") || 
        !strcasecmp(s,"off")  ||
        !strcasecmp(s,"no")  ) 
     return (1);

   return(0);
}

long int chunksize_from_str(char *s) 
{
   char u; // unit char spec.
   long unsigned int value;
   long unsigned int power;

   u = s[strlen(s)-1];
   if ((u == 'b') || (u=='B')) u = s[strlen(s)-2];

   value=atoll(s);
   power=0;
   switch(u) 
   { 
   case 'k': case 'K': power=10; break;
   case 'm': case 'M': power=20; break;
   case 'g': case 'G': power=30; break;
   case 't': case 'T': power=40; break;
   }
   return( value<<power);
   
}
#define TOKMAX (1024)

char token_line[TOKMAX];

// OPTIS - Option Is ... the option string matches x.

int sr_config_parse_option(struct sr_config_t *sr_cfg, char* option, char* argument) 
{

  char *brokerstr;
  int val;

  if ( strcspn(option," \t\n#") == 0 ) return(0);

  //if (sr_cfg->debug)
  //   fprintf( stderr, "option: %s,  argument: %s \n", option, argument );

  if ( !strcmp( option, "broker" ) || !strcmp( option, "b") ) 
  {
      brokerstr = sr_credentials_fetch(argument); 
      if ( brokerstr == NULL ) 
      {
          fprintf( stderr,"notice: no stored credential: %s.\n", argument );
          config_uri_parse( argument, &(sr_cfg->broker), sr_cfg->brokeruricb );
      } else {
          config_uri_parse( brokerstr, &(sr_cfg->broker), sr_cfg->brokeruricb );
      }
      sr_cfg->broker_specified=1;
      return(2);

  } else if ( !strcmp( option, "accept" ) || !strcmp( option, "get" ) ) {
      add_mask( sr_cfg, sr_cfg->directory, argument, 1 );
      return(2);

  } else if ( !strcmp( option, "accept_unmatch" ) || !strcmp( option, "accept_unmatched" ) || !strcmp( option, "au" ) 
    ) {
      val = StringIsTrue(argument);
      sr_cfg->accept_unmatched = val&2;
      return(1+(val&1));

  } else if ( !strcmp( option, "blocksize" ) ) {
      if (!argument) {
         fprintf( stderr, "blocksize argument missing\n");  
         return(1);
      }
      sr_cfg->blocksize = chunksize_from_str( argument );

      if ( sr_cfg->blocksize == 0 ) 
         sr_cfg->parts = 0;
      else if ( sr_cfg->blocksize == 1 )
         sr_cfg->parts = 1;
      else if ( sr_cfg->blocksize == 2 )
         sr_cfg->parts = 2;  // partstr=p (autocompute)
      else if ( sr_cfg->blocksize > 1 )
         sr_cfg->parts = 3;  // partstr=i (autocompute)

      return(2);

  } else if ( !strcmp( option, "config" ) || !strcmp(option,"include" ) || !strcmp(option, "c") ) {
      sr_config_read( sr_cfg, argument );
      return(2);

  } else if ( !strcmp( option, "debug" ) ) {
      val = StringIsTrue(argument);
      sr_cfg->debug = val&2;
      return(1+(val&1));

  } else if ( !strcmp( option, "directory" ) ) {
      sr_cfg->directory = strdup(argument);
      return(2);

  } else if ( !strcmp( option, "exchange" ) || !strcmp( option, "ex") ) {
      sr_cfg->exchange = strdup(argument);
      return(2);

  } else if ( !strcmp( option, "reject" ) ) {
      add_mask( sr_cfg, sr_cfg->directory, argument, 0 );
      return(2);
  } else if ( !strcmp( option, "sum" ) ) {
      sr_cfg->sum = argument[0];
      fprintf( stderr, "info: %s option not implemented, ignored.\n", option );
      return(2);
  } else if ( !strcmp( option, "to" ) ) {
      sr_cfg->to = strdup(argument);
      return(2);

  } else if ( !strcmp( option, "url" ) || !strcmp( option, "u" ) ) {
      sr_cfg->url = strdup(argument);
      return(2);

  } else {
      fprintf( stderr, "info: %s option not implemented, ignored.\n", option );
  } 
  return(0);
}

void sr_config_init( struct sr_config_t *sr_cfg ) 
{
  sr_credentials_init();
  sr_cfg->blocksize=1;
  sr_cfg->broker_specified=0;
  sr_cfg->debug=0;
  sr_cfg->accept_unmatched=1;
  sr_cfg->to=NULL;
  sr_cfg->directory=NULL;
  sr_cfg->masks=NULL;
  sr_cfg->parts=1;
  sr_cfg->sum='0';
  sr_cfg->url=NULL;
}

void sr_config_read( struct sr_config_t *sr_cfg, char *filename ) 
{
  FILE *f;
  char *option;
  char *argument;

  f = fopen( filename, "r" );
  if ( f == NULL ) {
    fprintf( stderr, "error: failed to fopen configuration file: %s\n", filename );
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

