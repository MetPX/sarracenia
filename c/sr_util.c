

/* need this define to get strptime
   if I don't give a value, it takes me back to the 1980's.  
   got values from feature_test_macros page... >700 seemed like the best one.

#define _XOPEN_SOURCE (800)
 */
#define _GNU_SOURCE

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

#include <stdio.h>
#include <stdlib.h>
#include <openssl/md5.h>
#include <string.h>

#include "sr_util.h"


/* size of buffer used to read the file content in calculating checksums.
 */
#define SUMBUFSIZE (4096*1024)

// SHA512 being the longest digest...
char sumstr[ SR_SUMSTRLEN ];

int get_sumstrlen( char algo )
{
  switch(algo) {
    case 'd' : case 'n' : 
        return(MD5_DIGEST_LENGTH);

    case '0' : case 'N' : case 'R' : case 's' : 
        return(SHA512_DIGEST_LENGTH);

    default: 
        return(0);
  }
}


char *set_sumstr( char algo, const char* fn, const char* partstr, char *linkstr,
          unsigned long block_size, unsigned long block_count, unsigned long block_rem, unsigned long block_num 
     )
 /* 
   return a correct sumstring (assume it is big enough)  as per sr_post(7)
   algo = 
     '0' - no checksum, value is random. -> now same as N.
     'd' - md5sum of block.
     'n' - md5sum of filename (fn).
     'L' - now sha512 sum of link value.
     'N' - md5sum of filename (fn) + partstr.
     'R' - no checksum, value is random. -> now same as N.
     's' - sha512 sum of block.

   block starts at block_size * block_num, and ends 
  */
{
   MD5_CTX md5ctx;
   SHA512_CTX shactx;
   unsigned char hash[SHA512_DIGEST_LENGTH]; // Assumed longest possible hash.

   static int fd;
   static char buf[SUMBUFSIZE];
   long bytes_read ; 
   long how_many_to_read;
   const char *just_the_name=NULL;

   unsigned long start = block_size * block_num ;
   unsigned long end;

   end = start + ((block_num < (block_count -(block_rem!=0)))?block_size:block_rem) ;
 
   //fprintf( stderr, "start: %ld, end: %ld\n", start, end );

   sumstr[0]=algo;
   sumstr[1]=',';
   sumstr[2]='\0'; 

   switch (algo) {

   case '0' : 
       sprintf( sumstr+2, "%ld", random()%1000 );
       break;

   case 'd' :
       MD5_Init(&md5ctx);

       // keep file open through repeated calls.
       //fprintf( stderr, "opening %s to checksum\n", fn );

       if ( ! (fd > 0) ) fd = open( fn, O_RDONLY );
       if ( fd < 0 ) 
       { 
           fprintf( stderr, "unable to read file for checksumming\n" );
           strcpy(sumstr+3,"deadbeef0");
           return(NULL);
       } 
       lseek( fd, start, SEEK_SET );
       //fprintf( stderr, "checksumming start: %lu to %lu\n", start, end );
       while ( start < end ) 
       {
           how_many_to_read= ( SUMBUFSIZE < (end-start) ) ? SUMBUFSIZE : (end-start) ;

           bytes_read=read(fd,buf, how_many_to_read );           
           if ( bytes_read > 0 ) 
           {
              MD5_Update(&md5ctx, buf, bytes_read );
              start += bytes_read;
           } else {
              fprintf( stderr, "error reading %s for MD5\n", fn );
              strcpy(sumstr+3,"deadbeef1");
              return(NULL);
           } 
       }

       // close fd, when end of file reached.
       if ((block_count == 1)  || ( end >= ((block_count-1)*block_size+block_rem))) 
       { 
             close(fd);
             fd=0;
       }

       MD5_Final(hash, &md5ctx);
       sr_hash2sumstr(hash,MD5_DIGEST_LENGTH); 
       //fprintf( stderr, "sumstr=%s\n", sumstr );
       break;

   case 'n' :
       MD5_Init(&md5ctx);
       just_the_name = rindex(fn,'/')+1;
       if (!just_the_name) just_the_name=fn;
       MD5_Update(&md5ctx, just_the_name, strlen(just_the_name) );
       MD5_Final(hash, &md5ctx);
       sr_hash2sumstr(hash,MD5_DIGEST_LENGTH); 
       break;
       
   
   case 'L' : // symlink case
        just_the_name=linkstr;       

   case 'R' : // null, or removal.

   case 'N' :
       SHA512_Init(&shactx);
       if (!just_the_name) {
           just_the_name = rindex(fn,'/')+1;
           if (!just_the_name) just_the_name=fn;
           strcpy( buf, just_the_name);
           if (strlen(partstr) > 0 ) { 
               strcat( buf, " " );
               strcat( buf, partstr );
           }     
           just_the_name=buf;
       }
       SHA512_Update(&shactx, just_the_name, strlen(just_the_name) );
       SHA512_Final(hash, &shactx);
       sr_hash2sumstr(hash,SHA512_DIGEST_LENGTH); 
       break;

   case 's' :
       SHA512_Init(&shactx);

       // keep file open through repeated calls.
       if ( ! (fd > 0) ) fd = open( fn, O_RDONLY );
       if ( fd < 0 ) 
       { 
           fprintf( stderr, "unable to read file for SHA checksumming\n" );
           strcpy(sumstr+3,"deadbeef2");
           return(NULL);
       } 
       lseek( fd, start, SEEK_SET );
       //fprintf( stderr, "DBG checksumming start: %lu to %lu\n", start, end );
       while ( start < end ) 
       {
           how_many_to_read= ( SUMBUFSIZE < (end-start) ) ? SUMBUFSIZE : (end-start) ;

           bytes_read=read(fd,buf, how_many_to_read );           

            //fprintf( stderr, "checksumming how_many_to_read: %lu bytes_read: %lu\n", 
            //   how_many_to_read, bytes_read );

           if ( bytes_read >= 0 ) 
           {
              SHA512_Update(&shactx, buf, bytes_read );
              start += bytes_read;
           } else {
              fprintf( stderr, "error reading %s for SHA\n", fn );
              strcpy(sumstr+3,"deadbeef3");
              return(NULL);
           } 
       }

       // close fd, when end of file reached.
       if ((block_count == 1)  || ( end >= ((block_count-1)*block_size+block_rem))) 
       { 
             close(fd);
             fd=0;
       }
       SHA512_Final(hash, &shactx);
       sr_hash2sumstr(hash,SHA512_DIGEST_LENGTH); 
       break;

   default:
       fprintf( stderr, "sum algorithm %c unimplemented\n", algo );
       return(NULL);
   }
   return(sumstr);

}

char *sr_hash2sumstr( unsigned char *h, int l )
{
  int i;
  for(i=1; i < l+1; i++ )
     sprintf( &(sumstr[i*2]), "%02x", (unsigned char)h[i-1]);
  sumstr[2*i]='\0';
  return(sumstr);
}

char time2str_result[19];

char *sr_time2str( struct timespec *tin ) 
{
   /* turn a timespec into an 18 character sr_post(7) conformant time stamp string.
      if argument is NULL, then the string should correspond to the current system time.
    */
   struct tm s;
   time_t when;
   struct timespec ts;
   long msec;

   if ( tin ) {
     when = tin->tv_sec;
     msec = tin->tv_nsec/1000000 ;
   } else {
     clock_gettime( CLOCK_REALTIME , &ts);
     when = ts.tv_sec;
     msec = ts.tv_nsec/1000000 ;
   }

   gmtime_r(&when,&s);
   /*                         YYYY  MM  DD  hh  mm  ss */
   sprintf( time2str_result, "%04d%02d%02d%02d%02d%02d.%03ld", s.tm_year+1900, s.tm_mon+1,
        s.tm_mday, s.tm_hour, s.tm_min, s.tm_sec, msec );

   //fprintf( stderr, "time2str, input: %ld.%ld setting: %s\n", when, msec, time2str_result );
   return(time2str_result);
}

struct timespec ts;

struct timespec *sr_str2time( char *s )
  /* inverse of above: convert 18 character string into a timespec.
   */
{
  struct tm tm;

  timezone=0; // FIXME: awfully hacky way to ensure UTC interpretation. better ideas?
              // timezone is set in time.h
  strptime( s, "%Y%m%d%H%M%%S", &tm);
  ts.tv_sec = mktime(&tm);
  ts.tv_nsec = atoi(s+15)*1000000;
  return(&ts);
}


