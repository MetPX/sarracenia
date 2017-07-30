
#include "sr_context.h"

/*
  for use by sr_post to avoid duplicate postings, sr_winnow to suppress duplicated, perhaps other consumers as well.

  is the use of the hash enough of a key?  dunno.
 */

#ifndef SR_CACHE_H
#define SR_CACHE_H 1

#include <openssl/sha.h>
#include <time.h>
#include "uthash.h"

#define SR_CACHEKEYSZ (SHA512_DIGEST_LENGTH+1)

struct sr_cache_path_t {
  char *path;
  char *partstr;
  struct timespec created;
  struct sr_cache_path_t *next;
};

struct sr_cache_t {
  unsigned char key[SR_CACHEKEYSZ]; // Assumed longest possible hash. first character is algorithm marker.
  struct sr_cache_path_t *paths;
  UT_hash_handle hh;
};


int sr_cache_check( struct sr_cache_t **cachep, char algo, void *ekey, char*path, char *partstr ); 
 /* 
   insert new item with key value = ekey, and lenghth = ekeylen. if it isn't in the cache.
   retun value:
       0 - present, so not added,
       1 - was not present, so added to cache.
       <0 - something bad happenned
 */


void sr_cache_clean( struct sr_cache_t **cachep, struct timespec *since );
 /* 
     remove entries in the cache older than since.
 */

void sr_cache_free( struct sr_cache_t **cachep );
 /* 
     remove all entries in the cache  (cleanup to discard.)
 */

void sr_cache_save( struct sr_cache_t *cache, const char *fn);
 /* 
     write entire cache to the given file name.
 */

struct sr_cache_t *sr_cache_load( const char *fn);
 /* 
     create an sr_cache based on the content of the named file.     
 */

#endif
