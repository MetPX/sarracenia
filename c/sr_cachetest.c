
#include <openssl/sha.h>

#include "sr_cache.h"

unsigned char hash[SHA512_DIGEST_LENGTH];

unsigned char *hashstr( char *str )
{
   SHA512_CTX shactx;

   fprintf( stderr, "called to hash is: %s len=%ld\n", str, strlen(str) ) ;
   SHA512_Init( &shactx );
   SHA512_Update( &shactx, str, strlen(str) );
   SHA512_Final( hash, &shactx );
   fprintf( stderr, "hash is: %s\n", sr_hash2sumstr( hash, SHA512_DIGEST_LENGTH )) ;
   return(hash);
}

int main( int argc, char *argv[] )
{
   struct sr_cache_t *cache=NULL;
   int ret;

   hash[0]='s';
   hash[1]=',';
   hash[2]='\0';

   ret = sr_cache_check( &cache, 's', hashstr( "hoho" ), SHA512_DIGEST_LENGTH );
   if (ret > 0) 
       fprintf( stderr, "OK. added hoho to the cache\n" );
   else
       fprintf( stderr, "ERROR: failed to add hoho to the cache\n" );

   sr_cache_save( cache, "saved_cache_1.txt" );

   ret = sr_cache_check( &cache, 's', hashstr( "hoho" ), SHA512_DIGEST_LENGTH );
   if (ret > 0) 
       fprintf( stderr, "ERROR: added hoho to the cache a second time\n" );
   else if ( ret == 0 )
       fprintf( stderr, "OK refused to add hoho to the cache a second time\n" );

   sr_cache_save( cache, "saved_cache_2.txt" );
}
