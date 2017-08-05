
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
#include <strings.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <ctype.h>

// for local_fqdn()
#include <sys/socket.h>
#include <netdb.h>


#include <time.h>

#include "sr_credentials.h"

#include "sr_config.h"



void sr_add_path( struct sr_config_t *sr_cfg, const char* option )
   /* Append to linked list of paths to post
    */
{
   struct sr_path_t *p;
   struct sr_path_t *n;

   p =  (struct sr_path_t *)malloc(sizeof (struct sr_path_t));
   if (p == NULL)
   {
       log_msg(LOG_ERROR, "malloc of path failed!\n" );
       return;
   }
   p->next = NULL;
   strcpy(p->path, option );

   if ( ! sr_cfg->paths )
   {
       sr_cfg->paths = p;
   } else {
       n=sr_cfg->paths;
       while( n->next ) n=n->next;
       n->next = p;
   }
}

void sr_add_topic( struct sr_config_t *sr_cfg, const char* sub )
  /* append to linked list of topics
   */
{
   struct sr_topic_t *t;
   struct sr_topic_t *n;

   t = (struct sr_topic_t *)malloc(sizeof (struct sr_topic_t));
   if (t == NULL) 
   {
       log_msg( LOG_ERROR,  "malloc of topic failed!\n" );
       return;
   }
   t->next = NULL;
   strcpy(t->topic,sr_cfg->topic_prefix);
   strcat(t->topic,".");
   strcat(t->topic, sub );

   if ( ! sr_cfg->topics ) 
   {
       sr_cfg->topics = t;
   } else {
       n=sr_cfg->topics;
       while( n->next ) n=n->next;
       n->next = t;
   }
}


struct sr_mask_t *isMatchingPattern(struct sr_config_t *sr_cfg, const char* chaine )
   /* return pointer to matched pattern, if there is one, NULL otherwise.
      if called repeatedly with the same argument, just return the same result.
    */
{
   struct sr_mask_t *entry;
   
   if (sr_cfg->last_matched && !strcmp(sr_cfg->last_matched,chaine)) 
       return(sr_cfg->match);

   if (sr_cfg->last_matched) free(sr_cfg->last_matched);
   sr_cfg->last_matched=strdup(chaine);

   entry = sr_cfg->masks;
   while( entry ) 
   {
       if ( (sr_cfg) && sr_cfg->debug )
           log_msg( LOG_DEBUG,  "isMatchingPattern, testing mask: %s %-30s next=%p\n", 
                (entry->accepting)?"accept":"reject", entry->clause, (entry->next) );

       if ( !regexec(&(entry->regexp), chaine, (size_t)0, NULL, 0 ) ) {
           break; // matched
       }
       entry = entry->next; 
   }
   if ( (sr_cfg) && sr_cfg->debug )
   {
       if (entry) 
           log_msg( LOG_DEBUG, "isMatchingPattern: %s matched mask: %s %s\n",  chaine,
               (entry->accepting)?"accept":"reject", entry->clause );
       else
           log_msg( LOG_DEBUG, "isMatchingPattern: %s did not match any masks\n",  chaine );
   }
   sr_cfg->match = entry;
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

#define NULTERM(x)  if (x != NULL) *x = '\0' ;

struct sr_broker_t *broker_uri_parse( char *src ) 
{
    /* copy src string to buf, adding nuls to separate path elements. 
       so each string is nul-treminated.
     */

    struct sr_broker_t *b;
    char buf[PATH_MAX];
    char *c, *d, *save;

    b = (struct sr_broker_t *)malloc( sizeof(struct sr_broker_t) );
    strcpy( buf, src );

    b->ssl = (buf[4] == 's');
    save = buf + 7 + (b->ssl);
    d = strchr( save, '@' );
    if (!d) 
    {
     free(b);
     return(NULL);
    } 
    // save points at user string, null terminated.
    *d='\0';
    c = d+1; // continuation point.
    d = strchr( save, ':' );
    if (d) {
       *d='\0';
       d++;
       b->password=strdup(d); 
    } else b->password=NULL;

    b->user = strdup(save);

    // c points at hostname
    save = c;
    d = strchr( save, ':' );
    if (d) { // port specified.
        d++;
        b->port = atoi(d);
        *d='\0';
    } else if (b->ssl) {
      b->port=5671;
    } else b->port=5672;
    if (!d) d = strchr(save,'/');
    if (d) *d='\0';
    b->hostname=strdup(save); 

    //fprintf( stderr, "broker ssl=%d, host: +%s+ , port: %d, user: +%s+ password: _%s_\n", 
    //   b->ssl, b->hostname, b->port, b->user, b->password );
    return(b);
} 

int sr_add_header(struct sr_config_t *cfg, char *s)
  /*
    Add a (user defined) header to the list of existing ones. 
    see StrinIsTrue for explanation of bitmask return values.
   */
{
  char *eq;
  struct sr_header_t *new_header;

  eq=strchr(s, '=');
  if (!eq) {
    return(0);
  }
  new_header = (struct sr_header_t *)malloc( sizeof(struct sr_header_t) );

  if (!new_header) {
    return(1);
  }
  *eq='\0';
  new_header->key=strdup(s);
  *eq='=';
  new_header->value=strdup(eq+1); 
  new_header->next=cfg->user_headers;
  cfg->user_headers=new_header; 
  return(3);
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

char *local_fqdn() 
/* 
   return the fully qualified hostname of the current machine
   mostly just a copy/paste from: 
      https://stackoverflow.com/questions/504810/how-do-i-find-the-current-machines-full-hostname-in-c-hostname-and-domain-info
 */
{
    
    struct addrinfo hints, *info, *p;
    int gai_result;
    
    char *found=NULL;
    static char hostname[1024];
    hostname[1023] = '\0';
    gethostname(hostname, 1023);
    
    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_UNSPEC; /*either IPV4 or IPV6*/
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_CANONNAME;
    
    if ((gai_result = getaddrinfo(hostname, "http", &hints, &info)) != 0) 
    {
        log_msg( LOG_CRITICAL, "cannot get hostname.  Getaddrinfo returned: %s\n", gai_strerror(gai_result));
        return(NULL);
    }
    
    for(p = info; p != NULL; p = p->ai_next) 
    {
        found=p->ai_canonname;
    }
    strcpy(hostname, found );
    freeaddrinfo(info);    
    return(hostname);
}

char *subarg( struct sr_config_t *sr_cfg, char *arg )
/* 
   do variable substitution in arguments to options.  There are some pre-defined ones, 
   if not found, punt to getenv.

   note, arg does get modified ( *e='\0' to terminate variable names, then returned to '}' after )
   should leave identical to during entry.
 */
{
  static char subargbuf[TOKMAX];
  char *c,*d, *var, *val, *e;

  if (!arg) return(NULL);
  c=arg;
  d=subargbuf;
  while( *c != '\0' ) 
  {
     if ( *c != '$' ) 
     {
         *d=*c;
         d++;
         c++;
         continue;
     }
     c++;
     if ( *c != '{' )
     {
        *d='$';
        d++;
        continue;
     }
     c++;
     var=c;
     e=var;
     while ( ( *e != '\0' ) && ( *e != '}' ) )
     {
        e++; 
     }
     if ( *e == '\0' ) 
     {
        log_msg( LOG_WARNING, "malformed argument: %s. returning unmodified.\n", arg );
        return(arg);
     }
     *e='\0';
     *d='\0'; // ready for catenation.
     if (!strcmp( var, "HOSTNAME" )) 
     {
          val = local_fqdn(); 

     } else if ( !strcmp( var, "PROGRAM" ) ) 
     {
          val = sr_cfg->progname;

     } else if ( !strcmp( var, "CONFIG" ) ) 
     {
          val = sr_cfg->configname;

     } else if ( !strcmp( var, "BROKER_USER" ) ) 
     {
          val=sr_cfg->broker->user;

     } else {
          val=getenv(var);
          if ( !val) {
              log_msg( LOG_WARNING, "malformed argument, Environment variable not set: %s\n", var );
              *e='}';
              log_msg( LOG_WARNING, "returning unmodified argument: %s.\n",  arg );
              return(arg);
          }
     }
     strcat(d,val);
     d += strlen(val);
     *e='}';
     c=e+1; 
  }
  *d='\0';
  log_msg( LOG_DEBUG, "argument after substitutions: %s\n", subargbuf );
  return(subargbuf);
  
}



char token_line[TOKMAX];

// OPTIS - Option Is ... the option string matches x.

int sr_config_parse_option(struct sr_config_t *sr_cfg, char* option, char* arg) 
{

  char *brokerstr, *argument;
  int val;
  char p[PATH_MAX];

  if ( strcspn(option," \t\n#") == 0 ) return(0);

  argument = subarg(sr_cfg, arg);

  if (sr_cfg->debug)
     log_msg( LOG_DEBUG, "option: %s,  argument: %s \n", option, argument );

  if ( !strcmp( option, "accept" ) || !strcmp( option, "get" ) ) {
      add_mask( sr_cfg, sr_cfg->directory, argument, 1 );
      return(2);

  } else if ( !strcmp( option, "accept_unmatch" ) || !strcmp( option, "accept_unmatched" ) || !strcmp( option, "au" ) ) {
      val = StringIsTrue(argument);
      sr_cfg->accept_unmatched = val&2;
      return(1+(val&1));

  } else if ( !strcmp( option, "action" ) ) {
      if (sr_cfg->action) free(sr_cfg->action);
      sr_cfg->action = strdup(argument);
      return(2);

  } else if ( !strcmp( option, "blocksize" ) || !strcmp( option, "parts") ) {
      if (!argument) {
         log_msg( LOG_ERROR, "parts (partition strategy) argument missing\n");  
         return(1);
      }
      sr_cfg->blocksize = chunksize_from_str( argument );

      return(2);

  } else if ( !strcmp( option, "broker" ) || !strcmp( option, "b") ) 
  {
      brokerstr = sr_credentials_fetch(argument); 
      if ( brokerstr == NULL ) 
      {
          log_msg( LOG_ERROR,"notice: no stored credential: %s.\n", argument );
          sr_cfg->broker = broker_uri_parse( argument );
      } else {
          sr_cfg->broker = broker_uri_parse( brokerstr );
      }
      free(brokerstr);
      return(2);

  } else if ( !strcmp( option, "cache" ) || !strcmp( option, "caching" ) || !strcmp( option, "suppress_duplicates" ) ) {
      if isalpha(*argument) {
          val = StringIsTrue(argument);
          sr_cfg->cache = (val&2) ? 900 : 0;
          return(1+(val&1));
      }
      sr_cfg->cache = atof(argument);
      return(2);

  } else if ( !strcmp( option, "chmod_log" ) ) {
      sscanf( argument, "%04o", &(sr_cfg->chmod_log) ); 
      return(2);

  } else if ( !strcmp( option, "config" ) || !strcmp(option,"include" ) || !strcmp(option, "c") ) {
      sr_config_read( sr_cfg, argument );
      return(2);

  } else if ( !strcmp( option, "debug" ) ) {
      val = StringIsTrue(argument);
      sr_cfg->debug = val&2;
      sr_cfg->logseverity=1;
      log_level=1;
      return(1+(val&1));

  } else if ( !strcmp( option, "directory" ) ) {
      sr_cfg->directory = strdup(argument);
      return(2);

  } else if ( !strcmp( option, "document_root" )|| !strcmp( option, "dr") ) {
      sr_cfg->documentroot = strdup(argument);
      return(2);

  } else if ( !strcmp( option, "durable" ) ) {
      val = StringIsTrue(argument);
      sr_cfg->durable = val&2;
      return(1+(val&1));

  } else if ( !strcmp( option, "events" ) || !strcmp( option, "e") ) {
      sr_cfg->events = parse_events(argument);
      return(2);

  } else if ( !strcmp( option, "exchange" ) || !strcmp( option, "ex") ) {
      sr_cfg->exchange = strdup(argument);
      return(2);

  } else if ( !strcmp( option, "flow" ) ) {
      sprintf(p,"flow=%s", argument );
      val = sr_add_header(sr_cfg, p);
      return(1+(val&1));

  } else if ( !strcmp( option, "follow_symlinks" ) || !strcmp( option, "fs") || !strcmp(option, "follow") ) {
      val = StringIsTrue(argument);
      sr_cfg->follow_symlinks = val&2;
      return(1+(val&1));

  } else if ( !strcmp( option, "force_polling" ) ) {
      val = StringIsTrue(argument);
      sr_cfg->force_polling = val&2;
      return(1+(val&1));

  } else if ( !strcmp( option, "heartbeat" ) ) {
      sr_cfg->heartbeat = atof(argument);
      return(2);

  } else if ( !strcmp( option, "header" ) ) {
      val = sr_add_header(sr_cfg, argument);
      return(1+(val&1));

  } else if ( !strcmp( option, "loglevel" ) ) {
      sr_cfg->logseverity = atoi(argument);
      log_level = sr_cfg->logseverity;
      return(2);

  } else if ( !strcmp( option, "log" ) ) {
      val = StringIsTrue(argument);
      sr_cfg->log = val&2;
      return(1+(val&1));

  } else if ( !strcmp( option, "queue" ) || !strcmp( option, "q" ) ) {
      sr_cfg->queuename = strdup(argument);
      return(2);
  } else if ( !strcmp( option, "reject" ) ) {
      add_mask( sr_cfg, sr_cfg->directory, argument, 0 );
      return(2);

  } else if ( !strcmp( option, "path" ) || !strcmp( option, "p") ) {
      sr_add_path( sr_cfg, argument );
      return(2);

  } else if ( !strcmp( option, "pipe" ) ) {
      val = StringIsTrue(argument);
      sr_cfg->pipe = val&2;
      return(1+(val&1));

  } else if ( !strcmp( option, "realpath" ) ) {
      val = StringIsTrue(argument);
      sr_cfg->realpath = val&2;
      return(1+(val&1));

  } else if ( !strcmp( option, "recursive" ) ) {
      val = StringIsTrue(argument);
      sr_cfg->recursive = val&2;
      return(1+(val&1));

  } else if ( !strcmp( option, "sleep" ) ) {
      sr_cfg->sleep = atof(argument);
      return(2);

  } else if ( !strcmp( option, "subtopic" ) || !strcmp( option, "sub") ) {
      sr_add_topic( sr_cfg, argument );
      return(2);

  } else if ( !strcmp( option, "sum" ) ) {
      sr_cfg->sumalgo = argument[0];
      return(2);
  } else if ( !strcmp( option, "to" ) ) {
      sr_cfg->to = strdup(argument);
      return(2);

  } else if ( !strcmp( option, "topic_prefix" ) || !strcmp( option, "tp") ) {
      strcpy( sr_cfg->topic_prefix, argument);
      return(2);

  } else if ( !strcmp( option, "url" ) || !strcmp( option, "u" ) ) {
      sr_cfg->url = strdup(argument);
      return(2);

  } else {
      log_msg( LOG_INFO, "info: %s option not implemented, ignored.\n", option );
  } 
  return(0);
}

void sr_config_free( struct sr_config_t *sr_cfg )
{
  struct sr_mask_t *e;

  if (sr_cfg->action) free(sr_cfg->action);
  if (sr_cfg->configname) free(sr_cfg->configname);
  if (sr_cfg->directory) free(sr_cfg->directory);
  if (sr_cfg->exchange) free(sr_cfg->exchange);
  if (sr_cfg->last_matched) free(sr_cfg->last_matched);
  if (sr_cfg->queuename) free(sr_cfg->queuename);
  if (sr_cfg->pidfile) free(sr_cfg->pidfile);
  if (sr_cfg->progname) free(sr_cfg->progname);
  if (sr_cfg->to) free(sr_cfg->to);
  if (sr_cfg->url) free(sr_cfg->url);

  if (sr_cfg->broker)
  {
     if (sr_cfg->broker->hostname) free(sr_cfg->broker->hostname);
     if (sr_cfg->broker->user) free(sr_cfg->broker->user);
     if (sr_cfg->broker->password) free(sr_cfg->broker->password);
     free(sr_cfg->broker);
  }
  while (sr_cfg->masks)
  {
       e=sr_cfg->masks;
       sr_cfg->masks = e->next;
       regfree(&(e->regexp));
       free(e->directory);
       free(e->clause);
       free(e);
  }
  while (sr_cfg->user_headers)
  {
       struct sr_header_t *tmph;
       tmph=sr_cfg->user_headers;
       free(tmph->key);
       free(tmph->value);
       sr_cfg->user_headers=tmph->next;
       free(tmph);
  }

  log_cleanup();
  sr_cache_close( sr_cfg->cachep );

}
void sr_config_init( struct sr_config_t *sr_cfg, const char *progname ) 
{
  char *c;

  sr_credentials_init();
  sr_cfg->action=strdup("foreground");
  sr_cfg->accept_unmatched=1;
  sr_cfg->blocksize=1;
  sr_cfg->broker=NULL;
  sr_cfg->cache=0;
  sr_cfg->cachep=NULL;
  sr_cfg->chmod_log=0600;
  sr_cfg->configname=NULL;
  sr_cfg->debug=0;
  sr_cfg->directory=NULL;
  sr_cfg->documentroot=NULL;
  sr_cfg->durable=1;
  sr_cfg->events= ( SR_MODIFY | SR_DELETE | SR_LINK ) ;
  sr_cfg->follow_symlinks=0;
  sr_cfg->force_polling=0;
  sr_cfg->instance=1;
  sr_cfg->last_matched=NULL;
  sr_cfg->log=0;
  sr_cfg->logfn=NULL;
  sr_cfg->logseverity=LOG_INFO;
  sr_cfg->masks=NULL;
  sr_cfg->match=NULL;
  sr_cfg->queuename=NULL;
  sr_cfg->paths=NULL;
  sr_cfg->pid=-1;
  sr_cfg->pidfile=NULL;
  sr_cfg->pipe=0;
  if (progname) { /* skip the sr_ prefix */
     c = strchr(progname,'_');
     if (c) sr_cfg->progname = strdup(c+1);
     else sr_cfg->progname = strdup(progname);
  } else 
     sr_cfg->progname=NULL;

  sr_cfg->realpath=0;
  sr_cfg->recursive=1;
  sr_cfg->sleep=0.0;
  sr_cfg->heartbeat=300.0;
  sr_cfg->sumalgo='s';
  sr_cfg->to=NULL;
  sr_cfg->user_headers=NULL; 
  strcpy( sr_cfg->topic_prefix, "v02.post" );
  sr_cfg->topics=NULL;
  sr_cfg->url=NULL;

  /* FIXME: should probably do this at some point.
  sprintf( p, "%s/.config/sarra/default.conf", getenv("HOME") );
  sr_config_read( sr_cfg, p );
   */
}

int sr_config_read( struct sr_config_t *sr_cfg, char *filename ) 
/* 
  search for the given configuration 
  return 1 if it was found and read int, 0 otherwise.

 */
{
  static int config_depth = 0;
  FILE *f;
  char *option;
  char *argument;
  char *c,*d;
  int plen;
  char p[PATH_MAX];

  /* set config name */
  if (! config_depth ) 
  {
      strcpy(p,filename);
      c=strrchr(p, '/' );
      if (c) c++;
      else c=p;

      d=strrchr(c,'.'); 
      if (d) *d='\0';
      sr_cfg->configname = strdup(c);
      config_depth++;
  }
  /* linux config location */
  if ( *filename != '/' ) 
  {
      sprintf( p, "%s/.config/sarra/%s/%s", getenv("HOME"), sr_cfg->progname, filename );

  } else {
      strcpy( p, filename );
  }
  plen=strlen(p);
  if ( strcmp(&(p[plen-5]), ".conf") )  // append .conf if not already there.
     strcat(p,".conf");

  // absolute paths in the normal places...
  if (sr_cfg->debug) 
        log_msg( LOG_ERROR, "sr_config_read trying to open: %s\n", p );

  f = fopen( p, "r" );
  if ( f == NULL )  // drop the suffix
  {
      plen=strlen(p);
      p[plen-5]='\0';
      plen -= 5; 
      f = fopen( p, "r" );
  }
  if ( f == NULL ) 
  {
     if (*filename != '/')  /* relative path, with or without suffix */
     { 
         strcpy( p, filename );
         if (sr_cfg->debug) 
             log_msg( LOG_ERROR, "sr_config_read trying to open: %s\n", p );
         f = fopen( p, "r" );
     }
     if ( f == NULL ) 
     {
         if ( strcmp(&(p[plen-5]), ".conf") ) 
         {
             strcat(p,".conf");
             if (sr_cfg->debug) 
                 log_msg( LOG_ERROR, "sr_config_read trying to open: %s\n", p );
             f = fopen( p, "r" );
         }
     }
  }

  if ( f==NULL ) 
  {
          log_msg( LOG_ERROR, "error: failed to find configuration: %s\n", filename );
          return(0);
  }

  while ( fgets(token_line,TOKMAX,f) != NULL ) 
   {
     //printf( "line: %s", token_line );

     if (strspn(token_line," \t\n") == strlen(token_line) ) 
     {
         continue; // blank line.
     }
     option   = strtok(token_line," \t\n");
     argument = strtok(NULL," \t\n");

     sr_config_parse_option(sr_cfg, option,argument);

  };
  fclose( f );

  return(1);
}


int sr_config_finalize( struct sr_config_t *sr_cfg, const int is_consumer)
{
  char p[PATH_MAX];
  char q[AMQP_MAX_SS];
  FILE *f;
  int ret;
  struct stat sb;

  if (! sr_cfg->configname )
     sr_cfg->configname=strdup("NONE");

  if (! sr_cfg->progname )
     sr_cfg->progname=strdup("NONE");

  // if the state directory is missing, build it.
  sprintf( p, "%s/.cache/%s/%s", getenv("HOME"), sr_cfg->progname, sr_cfg->configname ) ;
  ret = stat( p, &sb );
  if ( ret ) {
     sprintf( p, "%s/.cache", getenv("HOME") );
     mkdir( p, 0700 );
     strcat( p, "/" );
     strcat( p, "sarra" );
     mkdir( p, 0700 );
     strcat( p, "/" );
     strcat( p, sr_cfg->progname );
     mkdir( p, 0700 );
     strcat( p, "/" );
     strcat( p, sr_cfg->configname );
     mkdir( p, 0700 );
  }

  sprintf( p, "%s/.cache/sarra/log/sr_%s_%s_%03d.log", getenv("HOME"), 
      sr_cfg->progname, sr_cfg->configname, sr_cfg->instance );

  sr_cfg->logfn = strdup(p);

  if ( strcmp( sr_cfg->action, "foreground" )) 
      sr_cfg->log=1;

  if ( sr_cfg->log )
  {
      log_setup( sr_cfg->logfn , sr_cfg->chmod_log, sr_cfg->debug?LOG_DEBUG:(sr_cfg->logseverity) );
  }

  sprintf( p, "%s/.cache/sarra/%s/%s/i%03d.pid", getenv("HOME"), 
      sr_cfg->progname, sr_cfg->configname, sr_cfg->instance );

  sr_cfg->pidfile = strdup(p);
  f = fopen(p,"r");
  if ( f ) // read the pid from the file.
  {
         fgets(p,PATH_MAX,f);
         sr_cfg->pid=atoi(p);
         fclose(f);
  } 

  if (1) // why not? was gated on not being a consumer, but suspect consumers should use this also.
  {
     // FIXME: open and read cache file if present. seek to end.
     sprintf( p, "%s/.cache/sarra/%s/%s/recent_files_%03d.cache", getenv("HOME"), 
           sr_cfg->progname, sr_cfg->configname, sr_cfg->instance );
     if (sr_cfg->cache > 0) 
     {
         sr_cfg->cachep = sr_cache_open( p );
     } else {
         unlink(p);
     }
     return(1);
  }

  if (! sr_cfg->queuename ) { // was not specified, pick one.

     if (!sr_cfg->progname || !sr_cfg->configname || !sr_cfg->broker || !sr_cfg->broker->user ) 
     {
          log_msg( LOG_ERROR, "incomplete configuration, cannot guess queue\n"  );
          return(0);
     }
     sprintf( p, "%s/.cache/sarra/%s/%s/sr_%s.%s.%s", getenv("HOME"),
            sr_cfg->progname, sr_cfg->configname, sr_cfg->progname, sr_cfg->configname, sr_cfg->broker->user );
     f =  fopen( p, "r" );
     if ( f ) // read the queue name from the file.
     {
         fgets(p,PATH_MAX,f);
         sr_cfg->queuename=strdup(p);
         fclose(f);
     } else {
         sprintf( q, "q_%s.sr_%s.%s.%ld.%ld",
            sr_cfg->broker->user, sr_cfg->progname, sr_cfg->configname,
             random(), random() );
         sr_cfg->queuename=strdup(q);

         f = fopen( p, "w" ); // save the queue name for next time.
         if (f) 
         {
             if (sr_cfg->debug)
                log_msg( LOG_DEBUG, "writing %s to %s\n", q, p );
             fputs( q, f );
             fclose(f);
         }
     }
  }

  /*
  if (configname) {
     c= strrchr(configname,'.');
     if (!strcmp(c,".conf")) {
        strncpy(p,configname,(c-configname) );
        p[ (c-configname) ] = '\0';
        fprintf(stderr, "configname is: %s\n", p );
        cfg->configname=strdup(p);
     } else
        cfg->configname=strdup(configname);
  } else
     sr_cfg->configname=NULL;
  */
  return(1);
}

int sr_config_save_pid( struct sr_config_t *sr_cfg )
{
  FILE *f;

  sr_cfg->pid=getpid();
  f = fopen(sr_cfg->pidfile,"w");
  if ( f ) // read the pid from the file.
  {
         fprintf(f,"%d\n", sr_cfg->pid );
         fclose(f);
         return(0);
  } 
  return(-1);
}

