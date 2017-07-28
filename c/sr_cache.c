
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


int sr_cache_check( struct sr_cache_t **cachep, char algo, void *ekey, int ekeylen, char *path, char* partstr )
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
   struct sr_cache_path_t *e;

   if (ekeylen > (SR_CACHEKEYSZ-1)) 
   {
       fprintf( stderr, "ERROR: failed inserting sr_cache key because it is too long!" );
       return(-1);
   }
   e[0]=algo;
   if (ekeylen < (SR_CACHEKEYSZ-1)) 
       memset(e+1, 0, SR_CACHEKEYSZ-1);
   memcpy(e+1, ekey, ekeylen );

   HASH_FIND(hh,(*cachep),e,SR_CACHEKEYSZ,c);

   if (!c) 
   {
       c = (struct sr_cache_t *)malloc(sizeof(struct sr_cache_t));
       memcpy(c->key, e, SR_CACHEKEYSZ );
       c->paths=NULL;
       HASH_ADD_KEYPTR( hh, (*cachep), c->key, SR_CACHEKEYSZ, c );
   }

   for ( e = c->paths; e ; e=e->next )
   { 
          /* compare path and partstr */
           if ( !strcmp(e->path, path) && !strcmp(e->partstr,partstr) ) 
               return(0); /* found in the cache already */
   }

   /* not found, so add path to cache entry */
   e = (struct sr_cache_path_t *)malloc(sizeof(struct sr_cache_path_t));
   clock_gettime( CLOCK_REALTIME, &(e->created) );
   e->path = strdup(path);
   e->partstr = strdup(partstr);
   e->next = c->parts;
   c->parts = e;

   return(1);
}

void sr_cache_clean( struct sr_cache_t **cachep, struct timespec *since )
 /* 
     remove entries in the cache older than since. (resolution is in seconds.)
 */
{
    struct sr_cache_t *c, *tmpc;
   struct sr_cache_path_t *e, *prev, *del;

    HASH_ITER(hh, *cachep, c, tmpc )
    {
        e = c->paths; 
        while ( e )
        {
           if (e->created.tv_sec < since->tv_sec) 
           {
              del=e;

              if (!prev) {
                  c->paths = e->next;
                  prev=e;
              } else {
                  prev->next = e->next; 
              }
              e=e->next;

              free(del->path);
              free(del->partstr);
              free(del);
           } else  {
              e=e->next;
           }
              
        }
        if (! (c->paths) ) {
           HASH_DEL(*cachep,c);
           free(c);
        }
    }
}

void sr_cache_free( struct sr_cache_t **cachep)
 /* 
     remove all entries in the cache  (cleanup to discard.)
 */
{
    struct sr_cache_t *c, *tmpc;
   struct sr_cache_path_t *e, *del ;

    HASH_ITER(hh, (*cachep), c, tmpc )
    {
        HASH_DEL((*cachep),c);
        e = c->paths; 
        while( e )
        {
            del=e;
            e=e->next; 
            free(del->path);
            free(del->partstr);
            free(del);
        }
        free(c);
    }
}

void sr_cache_save( struct sr_cache_t *cache, const char *fn)
 /* 
     remove entries in the cache older than since.

FIXME: doesn't write paths yet...
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
FIXME: doesn't read paths yet...
  */
{
   if ( c < ':' ) return(c - '0');
   if ( c < 'F' ) return(c - 'A' + 10);
   if ( c < 'f' ) return(c - 'a' + 10);
   return(-1);
}


#define load_buflen (SR_CACHEKEYSZ*2 + SR_TIMESTRLEN + 4)

static char buf[ load_buflen ];

struct sr_cache_t *sr_cache_load( const char *fn)
 /* 
     create an sr_cache based on the content of the named file.     
 */
{
    struct sr_cache_t *c, *cache;
    FILE *f;
    int line_count=0;

    f = fopen( fn, "r" );
    if ( !f ) 
    {
        fprintf( stderr, "ERROR: failed to open cache file to load: %s\n", fn );
        return(NULL);
    }
    cache = NULL;

    while( fgets( buf, load_buflen, f ) )
    {
       line_count++;
       fprintf( stderr, "strlen(buf)=%ld loadbuflen: %d\n", strlen(buf), load_buflen );
       if (strlen( buf ) <  load_buflen-3) 
       {
          fprintf( stderr, "ERROR: cache file line %d too short, corrupted, skipping!\n", line_count );
          continue;
       }
       c = (struct sr_cache_t *)malloc(sizeof(struct sr_cache_t));
       c->key[0] = buf[0];
       int i=1;
       for ( ; i < SR_CACHEKEYSZ; i++ ) 
       {
            c->key[i]= convert_hex_digit(buf[2*i]) * 16 + convert_hex_digit(buf[2*i+1])  ;
       }
       memcpy( &(c->created), sr_str2time( buf+(SR_CACHEKEYSZ*2) ), sizeof(struct timespec) );

       HASH_ADD_KEYPTR( hh, cache, c->key, SR_CACHEKEYSZ, c );
    }
    fclose(f);
    return(cache);
}

