
#include "sr_context.h"

/*
  for use by sr_post to avoid duplicate postings, sr_winnow to suppress duplicated, perhaps other consumers as well.

  is the use of the hash enough of a key?  dunno.
 */

#include <openssl/sha.h>
#include <time.h>
#include "uthash.h"

struct sr_cache_t {
  unsigned char key[SHA512_DIGEST_LENGTH+1]; // Assumed longest possible hash. first character is algorithm marker.
  struct timespec created;
  UT_hash_handle hh;
};


int sr_cache_check( struct sr_cache_t *cache, char algo, char *value ); 
 /* 
   insert new item if it isn't in the cache.
   retun value:
       0 - present, so not added,
       1 - was not present, so added to cache.
 */


sr_cache_clean( struct sr_cache_t *cache, struct timespec *since );
 /* 
     remove entries in the cache older than since.
 */

sr_cache_free( struct sr_cache_t *cache, struct timespec *since );
 /* 
     remove all entries in the cache  (cleanup to discard.)
 */

sr_cache_save( struct sr_cache_t *cache, const char *fn);
 /* 
     remove entries in the cache older than since.
 */

struct sr_cache_t *sr_cache_load( const char *fn);
 /* 
     create an sr_cache based on the content of the named file.     
 */


