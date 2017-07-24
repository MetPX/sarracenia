
#include "sr_context.h"

/*
  for use by sr_post to avoid duplicate postings, sr_winnow to suppress duplicated, perhaps other consumers as well.

  is the use of the hash enough of a key?  dunno.
 */

#include <openssl/sha.h>
#include <time.h>
#include "uthash.h"

/*
  get time string conversion routines.
 */
#include "sr_config.h"

#include "sr_cache.h"


int sr_cache_check( struct sr_cache_t **cache, char algo, void *ekey, int ekeylen )
 /* 
   insert new item if it isn't in the cache.
   retun value:
       0 - present, so not added,
       1 - was not present, so added to cache.
      -1 - key too long, could not be inserted anyways, so not present.
 */
{
   struct sr_cache_t *c;
   char e[SR_CACHEKEYSZ];

   if (ekeylen > (SR_CACHEKEYSZ-1)) 
   {
       fprintf( stderr, "ERROR: failed inserting sr_cache key because it is too long!" );
       return(-1);
   }
   e[0]=algo;
   if (ekeylen < (SR_CACHEKEYSZ-1)) 
       memset(e+1, 0, SR_CACHEKEYSZ-1);
   memcpy(e+1, ekey, ekeylen );

   HASH_FIND(hh,*cache,e,SR_CACHEKEYSZ,c);

   if (!c) 
   { 
       c = (struct sr_cache_t *)malloc(sizeof(struct sr_cache_t));
       memcpy(c->key, e, SR_CACHEKEYSZ );
       HASH_ADD_KEYPTR( hh, *cache, c->key, SR_CACHEKEYSZ, c );
       return(1);
   } 
   return(0);
}

void sr_cache_clean( struct sr_cache_t **cache, struct timespec *since )
 /* 
     remove entries in the cache older than since. (resolution is in seconds.)
 */
{
    struct sr_cache_t *c, *tmpc;

    HASH_ITER(hh, *cache, c, tmpc )
    {
        if (c->created.tv_sec < since->tv_sec) {
            HASH_DEL(*cache,c);
            free(c);
        }
    }
}

void sr_cache_free( struct sr_cache_t *cache, struct timespec *since )
 /* 
     remove all entries in the cache  (cleanup to discard.)
 */
{
    struct sr_cache_t *c, *tmpc;

    HASH_ITER(hh, cache, c, tmpc )
    {
        HASH_DEL(cache,c);
        free(c);
    }
}

void sr_cache_save( struct sr_cache_t *cache, const char *fn)
 /* 
     remove entries in the cache older than since.
 */
{
    struct sr_cache_t *c, *tmpc;
    FILE *f;
    char sumstr[ SR_SUMSTRLEN ];

    f = fopen( fn, "w" );
    if ( !f ) 
    {
        fprintf( stderr, "ERROR: failed to open cache file to save: %s\n", fn );
        return;
    }
    HASH_ITER(hh, cache, c, tmpc )
    {
       sumstr[0]=c->key[0];
       sumstr[1]=',';
       for (int i=1; i < SR_CACHEKEYSZ; i++ )
           sprintf( &(sumstr[i*2]), "%02x", (unsigned char)(c->key[i]));
       
       fprintf(f,"%s %s\n", sumstr, sr_time2str( &(c->created) ) );
    }
    fclose(f);
}

int convert_hex_digit( char c )
 /* return ordinal value of digit assuming a character set that has a-f sequential in both lower and upper case.
    kind of based on ASCII, because numbers are assumed to be lower in collation than upper and lower case letters.
  */
{
   if ( c < ':' ) return(c - '0');
   if ( c < 'F' ) return(c - 'A' + 10);
   if ( c < 'f' ) return(c - 'a' + 10);
   return(-1);
}


struct sr_cache_t *sr_cache_load( const char *fn)
 /* 
     create an sr_cache based on the content of the named file.     
 */
{
    struct sr_cache_t *c, *cache;
    const int buflen = 80;
    char buf[ buflen ];
    FILE *f;

    f = fopen( fn, "r" );
    if ( !f ) 
    {
        fprintf( stderr, "ERROR: failed to open cache file to load: %s\n", fn );
        return(NULL);
    }
    cache = NULL;

    while( fgets( buf, buflen, f ) )
    {
       c = (struct sr_cache_t *)malloc(sizeof(struct sr_cache_t));
       c->key[0] = buf[0];
       int i=1;
       for ( ; i < SR_CACHEKEYSZ; i++ ) 
       {
            c->key[i]= convert_hex_digit(buf[2*i]) * 16 + convert_hex_digit(buf[2*i+1])  ;
       }
       memcpy( &(c->created), sr_str2time( buf+SR_CACHEKEYSZ ), sizeof(struct timespec) );

       HASH_ADD_KEYPTR( hh, cache, c->key, SR_CACHEKEYSZ, c );
        
    }
    fclose(f);
    return(cache);
}

