
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


void sr_cache_entry_path_write( FILE *fp, struct sr_cache_entry_t *e, struct sr_cache_entry_path_t *p )
{
  static char sumstr[ SR_SUMSTRLEN ]; /* made static to avoid putting on stack every call. */

  sumstr[0]=e->key[0];
  sumstr[1]=',';
  for (int i=1; i <= get_sumstrlen(e->key[0]); i++ )
      sprintf( &(sumstr[i*2]), "%02x", (unsigned char)(e->key[i]));
  fprintf(fp,"%s %s %s %s\n", sumstr, sr_time2str( &(p->created) ), p->path, p->partstr );
}

int sr_cache_check( struct sr_cache_t *cachep, char algo, void *ekey, char *path, char* partstr )
 /* 
   insert new item if it isn't in the cache.
   retun value:
       0 - present, so not added, but timestamp updated, so it doesn't age out so quickly.
       1 - was not present, so added to cache.
      -1 - key too long, could not be inserted anyways, so not present.
 */
{
   struct sr_cache_entry_t *c;
   char e[SR_CACHEKEYSZ];
   struct sr_cache_entry_path_t *p;

   tzset();
   e[0]=algo;
   if (get_sumstrlen(algo) < (SR_CACHEKEYSZ-1)) 
       memset(e+1, 0, SR_CACHEKEYSZ-1);
   memcpy(e+1, ekey, get_sumstrlen(algo) );

   HASH_FIND(hh,cachep->data,e,SR_CACHEKEYSZ,c);

   if (!c) 
   {
       c = (struct sr_cache_entry_t *)malloc(sizeof(struct sr_cache_entry_t));
       memcpy(c->key, e, SR_CACHEKEYSZ );
       c->paths=NULL;
       HASH_ADD_KEYPTR( hh, cachep->data, c->key, SR_CACHEKEYSZ, c );
   }

   for ( p = c->paths; p ; p=p->next )
   { 
          /* compare path and partstr */
           if ( !strcmp(p->path, path) && !strcmp(p->partstr,partstr) ) {
               clock_gettime( CLOCK_REALTIME, &(p->created) ); /* refresh cache timestamp */
               return(0); /* found in the cache already */
           }
   }

   /* not found, so add path to cache entry */
   p = (struct sr_cache_entry_path_t *)malloc(sizeof(struct sr_cache_entry_path_t));
   clock_gettime( CLOCK_REALTIME, &(p->created) );
   p->path = strdup(path);
   p->partstr = strdup(partstr);
   p->next = c->paths;
   c->paths = p;
   sr_cache_entry_path_write(cachep->fp,c,p);
   return(1);
}

void sr_cache_clean( struct sr_cache_t *cachep, float max_age )
 /* 
     remove entries in the cache not looked up in more than max_age seconds. 
 */
{
    struct sr_cache_entry_t *c, *tmpc;
    struct sr_cache_entry_path_t *e, *prev, *del;
    struct timespec since;
    int npaths;

    memset( &since, 0, sizeof(struct timespec) );
    clock_gettime( CLOCK_REALTIME, &since );
    fprintf( stderr, "cleaning out entries. current time: %s\n", sr_time2str( &since ) );

    since.tv_sec  -= (int)(max_age);
    since.tv_nsec -=   (int) ((max_age-(int)(max_age))*1e9);
    fprintf( stderr, "cleaning out entries older than: nsec=%g\n", (float)since.tv_nsec );

    fprintf( stderr, "cleaning out entries older than: %s valu=%ld\n", sr_time2str( &since ), since.tv_sec );

    HASH_ITER(hh, cachep->data, c, tmpc )
    {
        fprintf( stderr, "hash, start\n" );
        e = c->paths; 
        prev=NULL;
        while ( e )
        {
           fprintf( stderr, "\tchecking %s, touched=%ld difference: %ld\n", e->path, e->created.tv_sec,
                       e->created.tv_sec - since.tv_sec );
           if (e->created.tv_sec <= since.tv_sec) 
           {
              fprintf( stderr, "\tdeleting %s\n", e->path );
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
           } else  
           {
              e=e->next;
           }
              
       }
   
       if (! (c->paths) ) 
       {
           fprintf( stderr, "hash, deleting\n" );
           HASH_DEL(cachep->data,c);
           free(c);
       } else  {
           npaths=0; 
           for ( e = c->paths; e ; e=e->next ) npaths++;
           fprintf( stderr, "hash, done. pop=%d\n", npaths );
       }
   }
}

void sr_cache_free( struct sr_cache_t *cachep)
 /* 
     remove all entries in the cache  (cleanup to discard.)
 */
{
    struct sr_cache_entry_t *c, *tmpc;
   struct sr_cache_entry_path_t *e, *del ;

    HASH_ITER(hh, cachep->data, c, tmpc )
    {
        HASH_DEL(cachep->data,c);
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

int sr_cache_save( struct sr_cache_t *cachep, int to_stdout)
 /* 
     write entries in the cache to disk.
     returns a count of paths written to disk.
 */
{
    struct sr_cache_entry_t *c, *tmpc;
    struct sr_cache_entry_path_t *e;
    FILE *f;
    int count=0;
    char sumstr[ SR_SUMSTRLEN ];

    if (to_stdout) {
        f= stdout;
    } else {
        f = fopen( cachep->fn, "w" );
        if ( !f ) 
        {
            fprintf( stderr, "ERROR: failed to open cache file to save: %s\n", cachep->fn );
            return(0);
        }
    }
    HASH_ITER(hh, cachep->data, c, tmpc )
    {
       sumstr[0]=c->key[0];
       sumstr[1]=',';
       for (int i=1; i <= get_sumstrlen(c->key[0]); i++ )
           sprintf( &(sumstr[i*2]), "%02x", (unsigned char)(c->key[i]));
       for ( e = c->paths; e ; e=e->next )
       {       
          fprintf(f,"%s %s %s %s\n", sumstr, sr_time2str( &(e->created) ), e->path, e->partstr );
          count++;
       }
    }
    if (!to_stdout) fclose(f);
    return(count);
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


#define load_buflen (SR_CACHEKEYSZ*2 + SR_TIMESTRLEN + PATH_MAX + 24)

static char buf[ load_buflen ];

struct sr_cache_entry_t *sr_cache_load( const char *fn)
 /* 
     create an sr_cache based on the content of the named file.     
 */
{
    struct sr_cache_entry_t *c, *cache;
    struct sr_cache_entry_path_t *p;
    char *sum, *timestr, *path, *partstr;
    char key_val[SR_CACHEKEYSZ]; 
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
       sum = strtok( buf, " " );
   
       if (!sum) 
       {
           fprintf( stderr, "corrupt line in cache file %s: %s\n", fn, buf );
           continue;
       }

       timestr = strtok( NULL, " " );
   
       if (!timestr) 
       {
           fprintf( stderr, "no timestring, corrupt line in cache file %s: %s\n", fn, buf );
           continue;
       }

       path = strtok( NULL, " " );
   
       if (!path) 
       {
           fprintf( stderr, "no path, corrupt line in cache file %s: %s\n", fn, buf );
           continue;
       }

       partstr = strtok( NULL, " \n" );
   
       if (!partstr) 
       {
           fprintf( stderr, "no partstr, corrupt line in cache file %s: %s\n", fn, buf );
           continue;
       }

       /*
       fprintf( stderr, "fields: sum=+%s+, timestr=+%s+, path=+%s+, partstr=+%s+\n", 
           sum, timestr, path, partstr );
       */
       
       memset( key_val, 0, SR_CACHEKEYSZ );
       key_val[0] = buf[0];
       for (int i=1; i <= get_sumstrlen(buf[0]) ; i++ ) 
       {
            key_val[i]= convert_hex_digit(sum[2*i]) * 16 + convert_hex_digit(sum[2*i+1])  ;
       }

       HASH_FIND(hh,cache, key_val,SR_CACHEKEYSZ,c);

       if (!c) {
           c = (struct sr_cache_entry_t *)malloc(sizeof(struct sr_cache_entry_t));
           if (!c) 
           {
               fprintf( stderr, "out of memory reading cache file: %s, stopping at line: %s\n", fn, buf  );
               return(cache);
           }

           memcpy(c->key, key_val, SR_CACHEKEYSZ );
           c->paths=NULL;
           HASH_ADD_KEYPTR( hh, cache, c->key, SR_CACHEKEYSZ, c );
       }
       /* assert, c != NULL */

       /* add path to cache entry */
       p = (struct sr_cache_entry_path_t *)malloc(sizeof(struct sr_cache_entry_path_t));
       if (!p) 
       {
           fprintf( stderr, "out of memory 2, reading cache file: %s, stopping at line: %s\n", fn, buf  );
           return(cache);
       }

       memset( &(p->created), 0, sizeof(struct timespec) );
       memcpy( &(p->created), sr_str2time( timestr ), sizeof(struct timespec) );
       p->path = strdup(path);
       p->partstr = strdup(partstr);
       p->next = c->paths;
       c->paths = p;

    }
    fclose(f);
    return(cache);
}

struct sr_cache_t *sr_cache_open( const char *fn )
{
    struct sr_cache_t *c;

    c = (struct sr_cache_t *)malloc(sizeof(struct sr_cache_t));
    c->data = sr_cache_load(fn);
    c->fn =  strdup(fn);
    c->fp = fopen(fn,"a");

    /*
      FIXME:  Sarra needs to work exclusively in UTC.  Regardless of system TZ, all sarra dates
              should be in UTC, for cache, for logs, etc...  This is apparently difficult to do
              in Linux.

              I'm totally confused by timezones and DST in conversion of between strings and structs in time.
              I could not get this to work any other way.  This is BAD because it changes the TZ
              for the calling program.
    */
    putenv("TZ=UTC0");
    tzset();
    return(c);
}

void sr_cache_close( struct sr_cache_t *c )
{
   //sr_cache_save( c ); - since continually appending, no need for save.
   sr_cache_free( c );
   fclose(c->fp);
   free(c->fn);
   free(c);
}


