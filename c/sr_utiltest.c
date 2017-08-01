


#include <openssl/sha.h>
#include <openssl/md5.h>
#include <unistd.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <stdio.h>

#include "sr_util.h"

unsigned char hash[SHA512_DIGEST_LENGTH];

unsigned char *md5hash( char *str )
{
   MD5_CTX md5ctx;

   MD5_Init( &md5ctx );
   MD5_Update( &md5ctx, str, strlen(str) );
   MD5_Final( hash, &md5ctx );
   return(hash);
}

unsigned char *sha512hash( char *str )
{
   SHA512_CTX shactx;

   SHA512_Init( &shactx );
   SHA512_Update( &shactx, str, strlen(str) );
   SHA512_Final( hash, &shactx );
   return(hash);
}

int main( int argc, char *argv[] )
{
 
    struct timespec tsnow;
    struct timespec tsrt;
    time_t t;
    char timestring[60];
    char *tscp;
    int  testcnt=0;
    int  success=0;

    t = time(NULL);
    log_msg( LOG_INFO, "              It is now: %s\n", ctime(&t) );

    clock_gettime( CLOCK_REALTIME, &tsnow );

    log_msg( LOG_INFO, "       starting time is: %ld\n", tsnow.tv_sec );
    tscp = sr_time2str( &tsnow );
    memset( timestring, 0, 60 );
    memcpy( timestring, tscp, strlen(tscp) );
    log_msg( LOG_DEBUG, "text version ot time is: %s\n", timestring );

    memcpy( &tsrt, sr_str2time( timestring ), sizeof(struct timespec) ); 
    log_msg( LOG_DEBUG, " round tripped, time is: %ld\n", tsrt.tv_sec );
    log_msg( LOG_DEBUG, "          difference is: %ld\n", tsrt.tv_sec - tsnow.tv_sec );
    tscp = sr_time2str( &tsrt );
    memcpy( timestring, tscp, strlen(tscp) );

    log_msg( LOG_DEBUG, "text version ot time is: %s\n", timestring );
   
    if ( tsrt.tv_sec - tsnow.tv_sec ) 
    { 
        log_msg( LOG_ERROR, "Failed to roundtrip time through conversion routines, see difference above, should be 0\n" );
    } else
        success++;

    testcnt++;

    printf( "%s %d/%d tests passed\n", (success>=testcnt)?"OK":"FAILED", success, testcnt );
    exit( !(success>=testcnt) );
}
