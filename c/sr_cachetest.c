
#include <openssl/sha.h>

#include "sr_cache.h"

unsigned char hash[SHA512_DIGEST_LENGTH];

unsigned char *hashstr( char *str )
{
   SHA512_CTX shactx;

   SHA512_Init( &shactx );
   SHA512_Update( &shactx, str, strlen(str) );
   SHA512_Final( hash, &shactx );
   return(hash);
}

int main( int argc, char *argv[] )
{
   struct sr_cache_t *cache=NULL;
   int ret;
   int population=0;

   int test_count=0;
   int success_count=0;

   hash[0]='s';
   hash[1]=',';
   hash[2]='\0';

   ret = sr_cache_check( &cache, 's', hashstr( "hoho" ), SHA512_DIGEST_LENGTH );
   if (ret > 0) {
       fprintf( stdout, "OK. added hoho to the cache\n" );
       success_count++;
   } else
       fprintf( stdout, "ERROR: failed to add hoho to the cache\n" );
   test_count++;

   ret = sr_cache_check( &cache, 's', hashstr( "haha" ), SHA512_DIGEST_LENGTH );
   if (ret > 0) {
       fprintf( stdout, "OK. added hoho to the cache\n" );
       success_count++;
   } else
       fprintf( stdout, "ERROR: failed to add hoho to the cache\n" );
   test_count++;

   ret = sr_cache_check( &cache, 's', hashstr( "hoho" ), SHA512_DIGEST_LENGTH );
   if (ret > 0) 
       fprintf( stdout, "ERROR: added hoho to the cache a second time\n" );
   else if ( ret == 0 )
   {
       fprintf( stdout, "OK refused to add hoho to the cache a second time\n" );
       success_count++;
   }
   test_count++;

   population=HASH_COUNT(cache);
   fprintf( stdout, "writing to cache to disk (save_cache)\n" );
   sr_cache_save( cache, "saved_cache_test.txt" );

   sr_cache_free( &cache );
   fprintf(stdout, "after free: cache=%p count=%d\n", cache, HASH_COUNT(cache) );
   if (HASH_COUNT(cache) == 0)
   {
       fprintf( stdout, "OK emptied successfully by cache_free\n" );
       success_count++;
   }
   test_count++;

   cache = sr_cache_load( "saved_cache_test.txt" );
   fprintf(stdout, "after load: cache=%p count=%d\n", cache, HASH_COUNT(cache) );
   if (HASH_COUNT(cache) == population)
   {
       fprintf( stdout, "OK successfully restored by cache_load\n" );
       success_count++;
   }
   test_count++;

   if (success_count == test_count )
   {
       fprintf( stdout, "OK: %d of %d tests passed\n", success_count, test_count );
       exit(0);
   }
   fprintf( stdout, "FAILED: %d of %d tests\n", test_count-success_count, test_count );
   exit(1); 
}
