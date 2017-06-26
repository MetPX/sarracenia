
/*
 copyright Government of Canada 2017 

 This file is part of sarracenia.
 The sarracenia suite is Free and is proudly provided by the Government of Canada
 Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2017

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

};



void config_uri_parse( char *src, UriUriA *ua, char *buf ) {

  /* 
   *
   */
  UriParserStateA state; 

  fprintf( stderr, "c_u_p 1\n" );
  state.uri = ua;
  
  strcpy( buf, src );

  fprintf( stderr, "c_u_p 2\n" );
  if (uriParseUriA(&state, buf ) != URI_SUCCESS) {
                // uriFreeUriMembersA(ua);
                return;
  } 
  fprintf( stderr, "c_u_p 3\n" );
  *(char*)(ua->scheme.afterLast) = '\0';
  *(char*)(ua->userInfo.afterLast) = '\0';
  *(char*)(ua->hostText.afterLast) = '\0';
  *(char*)(ua->portText.afterLast) = '\0';

  fprintf( stderr, "c_u_p 3\n" );
} 


char keyword_buf[255];

char *config_keyword_get(char *cfg, char *keyword ) {
  /* read cfg (dump of file in memory), looking a keyword opt.
     return the value, copied in keywrod_buf, and null terminated.
   */ 
  size_t lenk; 
  char *c;

  lenk = strlen(keyword);
  c=cfg;
  while( strncmp(c,keyword,lenk) ) {
     while ( *c != '\n' ) {
        if ( *c == '\0' ) return NULL;
        c++;
     } 
     c++;
  }

  c += lenk+1; // skip past keyword 
  lenk = strspn(c, " \t"); // skip intervening white space.
  c += lenk;

  lenk = strcspn(c,"\n"); // find the end of the line.

  strncpy((char*)keyword_buf,c,lenk);

  keyword_buf[lenk]='\0'; 

  return(keyword_buf);
}


char *config_file_read(char *filename) {

  struct stat finfo;
  char *cfgdat;
  int fd;
  int ret;
  char *token;
  int i;
  int lcount;
  char **cfgarray;


  stat(filename,&finfo);
      
  cfgdat = (char*)malloc(finfo.st_size+1);
  fd = open( filename, O_RDONLY );
  ret = read(fd,cfgdat,finfo.st_size);
  close(fd);

  if ( ret < finfo.st_size )  {
     fprintf( stderr, "sz wrong\n" );
     return NULL ;  
  }
  
  return cfgdat;
}


void main( char* argv, int argc ) {

  char *cfg;
  char **tag, *value;
  int i;
  UriParserStateA state; 
  struct UriPathSegmentStructA *pathelem;
  struct sr_config_t sr_c;

  cfg = config_file_read( "/home/peter/.config/sarra/post/test2.conf" );

  state.uri = &(sr_c.broker);
  
  fprintf( stderr, "1\n" );
/*
  strcpy( sr_c.brokeruricb, config_keyword_get(cfg, "broker") );

  if (uriParseUriA(&state, sr_c.brokeruricb ) != URI_SUCCESS) {
                uriFreeUriMembersA(&(sr_c.broker));
                return;
  } 
 */
  fprintf( stderr, "2\n" );

  config_uri_parse( config_keyword_get(cfg,"broker"), &(sr_c.broker), sr_c.brokeruricb );

  fprintf( stderr, "3\n" );

  printf( "config keyword get %s=%s\n", "broker", config_keyword_get(cfg,"broker") );
  printf( "config keyword get %s=%s\n", "sleep", config_keyword_get(cfg,"sleep") );
  printf( "config keyword get %s=%s\n", "url", config_keyword_get(cfg,"url") );
  printf( "config keyword get %s=%s\n", "exchange", config_keyword_get(cfg,"exchange") );

  printf( "broker, scheme=%s\n", sr_c.broker.scheme );
  printf( "broker, userInfo=%s \n", sr_c.broker.userInfo );
  printf( "broker, hostText=%s \n", sr_c.broker.hostText );
  printf( "broker, portText=%s \n", sr_c.broker.portText );

  //*(char*)(uri.pathHead.afterLast) = '\0';
  pathelem= sr_c.broker.pathHead;
  while ( pathelem != NULL )  {
      fprintf( stderr, "broker, pathelem=%s \n", pathelem->text );
      pathelem = pathelem->next;
  }

  // no, because storage is static in uricb...  uriFreeUriMembersA(&uri);
  exit(0);

}
