
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

char *sr_credentials = NULL;

char *sr_credentials_fetch( char *s ) 
  /* search for the first credential that matches the search spec given.
   */
{
  char *start = sr_credentials;
  char *end = sr_credentials;
  char *result = NULL;
  int slen=strlen(s);

  //fprintf(stderr, "\nfetching: %s\n", s );

  while ( *end != '\0' ) 
  {
      //fprintf( stderr, "try:\n%s\n", start );
      int i=0;
      int smatching=0;

      while( start[i] == s[i] ) 
      {
          //fprintf( stderr, "start[i]=%c, s[i]=%c\n", start[i], s[i] );
          i++;
      }
      //fprintf( stderr, "out of loop: start[i]=%c, s[i]=%c\n", start[i], s[i] );
      if (i == slen) 
      {
         result= (char*)malloc(i+1);
         strncpy(result,start,i); 
         //fprintf( stderr, "result: %s\n", result );
         return(result);
      }

      if ( ( start[i] == ':' ) && ( s[i] == '@' ) ) 
      {
          smatching=i;
          //fprintf( stderr, "skipping password..\n" );
          while ( start[i] != '@' ) i++;

          //fprintf( stderr, "rest of url, start[i]=%c, s[smatching]=%c\n", 
          //        start[i], s[smatching] );

          while ( ( smatching < slen ) && start[i] == s[smatching] ) 
          {
             //fprintf( stderr, "start[i]=%c, i=%d s[smatching]=%c smatching=%d\n", 
             //     start[i], i, s[smatching], smatching );
             i++; smatching++; 
          }
          //fprintf( stderr, "out of loop, slen=%d, start[i]=%c, i=%d s[smatching]=%c smatching=%d\n", 
          //        slen, start[i], i, s[smatching], smatching );

          if ( (smatching >= slen-1) && ( (start[i] == ' ') || (start[i] == '/')  || (start[i] == '\t') || (start[i] == '\n') )) 
          {
             result= (char*)malloc(i+1);
             strncpy(result,start,i); 
             //fprintf( stderr, "result: %s\n", result );
             return(result);
          };
      }
      //fprintf( stderr, "nope!\n" );
      end=start+i;
      while ( ( *end != '\n' ) && ( *end != '\0' ) ) end++;
      start=end+1;
  }
  return(NULL);
}


void sr_credentials_init() {

  FILE *f;
  char cfnbuf[1024];
  struct stat sb;

  strcpy( cfnbuf, getenv("HOME"));
  strcat( cfnbuf, "/.config/sarra/credentials.conf" );
  
  stat( cfnbuf, &sb );
  sr_credentials = (char *)malloc(sb.st_size+1);
 
  //fprintf( stderr, "opening %s\n", cfnbuf );

  f = fopen( cfnbuf, "r" );
  fread(sr_credentials, sb.st_size, 1, f );
  sr_credentials[sb.st_size]='\0';
  fclose(f);

}

/* 

void main() {

 sr_credentials_init();
 
 sr_credentials_fetch( "amqp://guest:guest@localhost" );
 sr_credentials_fetch( "amqp://guest@localhost" );
 sr_credentials_fetch( "amqp://tsource@localhost/" );
 
}

 */ 
