


#include <openssl/sha.h>
#include <openssl/md5.h>
#include <unistd.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <stdio.h>

#include "sr_util.h"

unsigned char hash[SHA512_DIGEST_LENGTH+1];

unsigned char *md5hash( char *str )
{
   MD5_CTX md5ctx;

   hash[0]='d';
   MD5_Init( &md5ctx );
   MD5_Update( &md5ctx, str, strlen(str) );
   MD5_Final( hash+1, &md5ctx );
   return(hash);
}

unsigned char *sha512hash( char *str )
{
   SHA512_CTX shactx;

   hash[0]='s';
   SHA512_Init( &shactx );
   SHA512_Update( &shactx, str, strlen(str) );
   SHA512_Final( hash+1, &shactx );
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

    unsigned char original_hash[SHA512_DIGEST_LENGTH+1];
    unsigned char rt_hash[SHA512_DIGEST_LENGTH+1];

    char osumstr[SR_SUMSTRLEN];
    char rtsumstr[SR_SUMSTRLEN];

    memcpy( original_hash, sha512hash( "hoho" ), SHA512_DIGEST_LENGTH + 1 );
    strcpy( osumstr, sr_hash2sumstr( original_hash ) );
    fprintf( stderr, "     original hash is: %s\n" , osumstr );

    memcpy( rt_hash, sr_sumstr2hash(osumstr), SHA512_DIGEST_LENGTH + 1 );
    strcpy( rtsumstr, sr_hash2sumstr( rt_hash ) );
    fprintf( stderr, "round-tripped hash is: %s\n" , rtsumstr );

    if ( !strcmp( osumstr, rtsumstr ) ) 
    {
        fprintf( stderr, "OK: sum string <-> hash strings are the same.\n" );
        success++;
    } else {
        fprintf( stderr, "FAIL: original sum strings and roundtripped ones are different\n" );
    }
    testcnt++;


    if ( !memcmp( original_hash, rt_hash, SHA512_DIGEST_LENGTH +1 ) )
    {     
        fprintf( stderr, "OK: original and round-tripped hashes are the same.\n" );
        success++;
    } else {
        fprintf( stderr, "FAIL: original sum hashes and roundtripped ones are different\n" );
    }
    testcnt++;

    t = time(NULL);
    log_msg( LOG_INFO, "              It is now: %s\n", ctime(&t) );

    /* FIXME, repeat for MD5, for N, n, L, R  */
    
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
