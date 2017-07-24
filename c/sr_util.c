

/* need this define to get strptime
   if I don't give a value, it takes me back to the 1980's.  
   got values from feature_test_macros page... >700 seemed like the best one.

#define _XOPEN_SOURCE (800)
 */
#define _GNU_SOURCE


#include <stdio.h>
#include <stdlib.h>

#include "sr_util.h"

// SHA512 being the longest digest...
char sumstr[ SR_SUMSTRLEN ];

char *sr_hash2sumstr( unsigned char *h, int l )
{
  int i;
  for(i=1; i < l+1; i++ )
     sprintf( &(sumstr[i*2]), "%02x", (unsigned char)h[i-1]);
  sumstr[2*i]='\0';
  return(sumstr);
}

char time2str_result[19];

char *sr_time2str( struct timespec *tin ) {
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


