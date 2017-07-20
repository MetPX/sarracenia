/* vim:set ft=c ts=2 sw=2 sts=2 et cindent: */

/*
 * Usage info after license block.
 *
 * This code is by Peter Silva copyright (c) 2017 part of MetPX.
 * copyright is to the Government of Canada. code is GPL.
 *
 * based on a amqp_sendstring from rabbitmq-c package
 * the original license is below:
 */

/* 
  Minimal c implementation to allow posting of sr_post(7) messages.

  spits out ´unimplemented option´ where appropriate...
 */
#include <linux/limits.h>
#include <errno.h>
#include <sys/types.h>
#include <dirent.h>
#include <stdlib.h>
#include <sys/inotify.h>
#include <unistd.h>


/*
   https://troydhanson.github.io/uthash/userguide.html

 */

#include "uthash.h"


/* 
  for each directory opened, store it's dev+inode pair.
  if you encounter another directory witht the same numbers, there is a loop.
  The FD is the file descriptor returned by an inotify_init.

 */ 

struct hash_entry {
    char *fn;                  // key & payload
    UT_hash_handle hh;
};

#include "sr_post.h"

static  int   inotify_event_mask;  // translation of sr_events to inotify events.

struct dir_stack {
   char *path;                // path of directory.
   int wd;                    // fd returned by inotify_init.
   dev_t dev;                 // info from stat buf of directory.
   ino_t ino;
   int   visited;
   struct dir_stack *next;    // pointer towards the top of the stack.
};

/* FIXME: crappy algorithm single linked stack, no optimizations at all.
   FIXME: once a directory is added, deletion is not handled 
          (case: directory exists, while code runs, directory is deleted, then
           the inode is re-used for a file or another directory. if it turns
           out to be a directory, then it will be in the stack, but not watched.
 */

static struct dir_stack *dir_stack_top = NULL;   /* insertion point (end of line.) */
int dir_stack_size = 0;

/* 
   at the beginning of each poll, need to walk the tree again.
   so reset *visited* to 0 for entire stack.  These get set to true
   at the next iteration.
 */
void dir_stack_reset()
{
   for( struct dir_stack *s = dir_stack_top ; s ; s=s->next )
       s->visited=0;

}

int dir_stack_push( char *fn, int wd, dev_t dev, ino_t ino )
 /* add the given directory to the list of ones that are being scanned.

    Return value:  1 if this is a new directory and it has been added.
                   0 if the directory is a duplicate, and was not added.
  */
{
   struct dir_stack *t, *i, *present;

   present=NULL;
   if ( dir_stack_top ) 
   {
      i=dir_stack_top;
      while( !present && i )
      {
          if ((i->dev == dev) && ( i->ino == ino )) present=i;
          i = i->next;
      }
   } 
   if (!present) 
   {
       t= (struct dir_stack *)(malloc(sizeof(struct dir_stack)));
       if (!t)
       {
           fprintf( stderr, "ERROR: failed to malloc adding to dir_stack for: %s\n", fn );
           return(0);
       }

       dir_stack_size++;
       t->path = strdup(fn);
       t->wd = wd;
       t->dev = dev;
       t->ino = ino;
       t->visited = 1;
       t->next = dir_stack_top;
       dir_stack_top = t;
       return(1); 
   } else {
       if (present->visited)
       { 
           return(0);
       } 
       present->visited++;
       return (1);
   }
}

char evstr[80];

char *inotify_event_2string( uint32_t mask )
{
    
    if (mask|IN_CREATE) strcpy(evstr, "create");
    else if (mask|IN_MODIFY) strcpy(evstr, "modify");
    else if (mask|IN_DELETE) strcpy(evstr, "delete");
    else strcpy( evstr, "dunno!" );
    if (mask|IN_ISDIR) strcat( evstr, ",directory" );
    return(evstr);
}

// see man 7 inotify for size of struct inotify_event
#define INOTIFY_EVENT_MAX  (sizeof(struct inotify_event) + NAME_MAX + 1)

static    int inot_fd=0;


static    int first_call = 1;
struct timespec latest_min_mtim;

int ts_newer( struct timespec a, struct timespec b)
   /*  return true is a is newer than b.
    */
{
   if ( a.tv_sec > b.tv_sec ) return (1);
   if ( a.tv_sec < b.tv_sec ) return (0);
   if ( a.tv_nsec > b.tv_nsec ) return(1);
   return(0);
}


void do1file( struct sr_context *sr_c, char *fn ) 
{
    DIR *dir;
    int w;
    struct dirent *e;
    struct stat sb;
    char ep[PATH_MAXNUL];

  /*
    if (sr_c->cfg->debug)
        fprintf( stderr, "debug: do1file starting on: %s\n", fn );
   */

    if ( lstat(fn, &sb) < 0 ) {
         fprintf( stderr, "failed to lstat: %s\n", fn );
         return;
    }


    if (S_ISLNK(sb.st_mode)) 
    {   // process a symbolic link.
        if (sr_c->cfg->debug)
           fprintf( stderr, "debug: %s is a symbolic link. (follow=%s) posting\n", 
               fn, ( sr_c->cfg->follow_symlinks )?"on":"off" );

        if (ts_newer( sb.st_mtim, latest_min_mtim ))
            sr_post(sr_c,fn, &sb);       // post the link itself.

    /* FIXME:  INOT  - necessary? I think symlinks can be skipped?
     */

        if ( ! ( sr_c->cfg->follow_symlinks ) )  return;

        if ( stat(fn, &sb) < 0 ) {  // repeat the stat, but for the destination.
             fprintf( stderr, "ERROR: failed to stat: %s\n", fn );
             return;
        }

        if (ts_newer( latest_min_mtim, sb.st_mtim ) ) return; // only the link was new.

    }

    if (S_ISDIR(sb.st_mode))   // process a directory.
    {
         if (sr_c->cfg->debug)
             fprintf( stderr, 
                 "info: opening directory: %s, first_call=%s, recursive=%s, follow_symlinks=%s latest_min_mtim=%ld.%09ld\n", 
                 fn, first_call?"on":"off", (sr_c->cfg->recursive)?"on":"off", 
                 (sr_c->cfg->follow_symlinks)?"on":"off", latest_min_mtim.tv_sec, latest_min_mtim.tv_nsec );

         if ( !first_call && !(sr_c->cfg->recursive) ) return;

         first_call=0;

        /* FIXME:  INOT 
         */
        if ( ! sr_c->cfg->force_polling ) 
        {
            w = inotify_add_watch( inot_fd, fn, inotify_event_mask);
            if (w < 0)
            {
               fprintf( stderr, "failed to add_watch: %s\n", fn );
               return;
            }
         } else w=0;

         if ( !dir_stack_push( fn, w, sb.st_dev, sb.st_ino ) )
         {
             close(inot_fd);
             fprintf( stderr, "info: loop detected, skipping: %s\n", fn );
             return;
         } else 
             fprintf( stderr, "FIXME: pushed on stack: %s\n", fn );
                      
         dir=opendir(fn);
         if (!dir) 
         {
             fprintf( stderr, "failed to open directory: %s\n", fn );
             return;
         }
         while ( ( e = readdir(dir)) ) 
         {
             if ( !strcmp(e->d_name,".") || !strcmp(e->d_name,"..") ) 
                 continue;

             strcpy( ep, fn );
             strcat( ep, "/" );
             strcat( ep, e->d_name );
             do1file( sr_c, ep);         
         }
         closedir(dir); 

         if (sr_c->cfg->debug)
             fprintf( stderr, "info: closing directory: %s\n", fn );

    } else 
        if (ts_newer( sb.st_mtim, latest_min_mtim )) 
            sr_post(sr_c,fn, &sb);  // process a file


}


void dir_stack_check4events( struct sr_context *sr_c )
 /* at the end of each sleeping interval, read the queue of outstanding events
    and process them.
  */
{
    char buff[PATH_MAX*4];
    char fn[PATH_MAX];
    char *p;
    struct inotify_event *e;
    struct dir_stack *d;
    int ret;
    struct hash_entry *new_entry, *entries_done, *tmpe = NULL;

    /* fixme: MISSING: process pending list
            - go sequentially through the pending list,
              removing things if they succeed.
     */ 
    entries_done = NULL; 

    /* normal event processing. */

    /* FIXME: MISSING: initialize done_list? */

    while ( ( ret = read( inot_fd, buff, sizeof buff ) ) > 0 )
    {
        for( p=buff; 
             p < (buff+ret) ; 
             p+= sizeof(struct inotify_event) + e->len )
        {
            e = (struct inotify_event *)p;

            for ( d = dir_stack_top; d && ( e->wd != d->wd ) ; d=d->next );
            if (!d) 
            {
                 fprintf( stderr, "ERROR: cannot find path for event %s\n",
                     e->name );
                 continue;
            } 
            sprintf( fn, "%s/%s", d->path, e->name ); 
            if (sr_c->cfg->debug)
            {
                printf( "bytes read: %d, sz ev: %ld, event: %s: len=%d, fn=%s\n",
                    ret, sizeof(struct inotify_event)+e->len,
                    inotify_event_2string(e->mask), e->len, fn );
            }
            /* FIXME: missing: check for repeats. if post succeeds, remove from list.
                  if post fails, move to *pending* list.
 
               done_list and pending_list options: 
                  1. build a linked list of fn-strings, search... O(n^2)... blch, but small n?
                  2. build a linked list of hashes of the strings (faster per string.)
                     store the list in order, so faster search.
               best to do 1 first, and then optimize later if necessary.                     
             */
            HASH_FIND_STR( entries_done, fn, tmpe );
            if (!tmpe) {
                new_entry = (struct hash_entry *)malloc( sizeof(struct hash_entry) );
                new_entry->fn = strdup(fn);
                HASH_ADD_KEYPTR( hh, entries_done, new_entry->fn, strlen(new_entry->fn), new_entry );
                do1file( sr_c, fn);
            } 
        }
    }

    /* empty out done list */
    HASH_ITER( hh, entries_done, tmpe , new_entry ) 
    {
       free(tmpe->fn);
       HASH_DEL(entries_done, tmpe);
       free(tmpe);
    }
}

void usage() 
{
     fprintf( stderr, "usage: sr_cpost <options> <files>\n\n" );
     fprintf( stderr, "\t<options> - sr_post compatible configuration file.\n" );
     fprintf( stderr, "\t\taccept/reject <regex> - to filter files to post.\n" );
     fprintf( stderr, "\t\taction [setup|cleanup|foreground] \n" );
     fprintf( stderr, "\t\tbroker amqps://<user>@host - required - to lookup in ~/.config/sarra/credentials.\n" );
     fprintf( stderr, "\t\tdebug <on|off> - more verbose output.\n" );
     fprintf( stderr, "\t\texchange <exchange> - required - name of exchange to publish to\n" );
     fprintf( stderr, "\t\tto <destination> - clusters pump network should forward to.\n" );
     fprintf( stderr, "\t\turl <url>[,<url>]... - retrieval base url in the posted files.\n" );
     fprintf( stderr, "\t\t    (a comma separated list of urls will result in alternation.)" );

     fprintf( stderr, "\t<files> - list of files to post\n\n" );
     fprintf( stderr, "This is a stripped down C implementation of sr_post(1), see man page for details\n\n" );
     fprintf( stderr, "examples of missing features: \n\n" );
     fprintf( stderr, "\t\tno cache.\n" );
     fprintf( stderr, "\t\tcan only post files (not directories.)\n" );
     exit(1);
}


int main(int argc, char **argv)
{
    struct sr_context *sr_c;
    struct sr_config_t sr_cfg;
    char inbuff[PATH_MAXNUL];
    int consume,i,firstpath,pass;
    struct timespec tstart, tsleep, tend;
    float elapsed;
    
    if ( argc < 3 ) usage();
   
    sr_config_init( &sr_cfg );
  
    i=1;
    while( i < argc ) 
    {
        if (argv[i][0] == '-') 
           consume = sr_config_parse_option( &sr_cfg, &(argv[i][1]), argv[i+1] );
        else
            break;
        if (!consume) break;
        i+=consume;
    }
    
    sr_c = sr_context_init_config( &sr_cfg );
    if (!sr_c) {
        fprintf( stderr, "failed to read config\n");
        return(1);
    }
    
    sr_c = sr_context_connect( sr_c );
  
    if (!sr_c) 
    {
        fprintf( stderr, "failed to establish sr_context\n");
        return(1);
    }

    if ( !strcmp( sr_cfg.action, "cleanup" ) )
    {
        if ( !sr_post_cleanup( sr_c ) ) 
        {
            fprintf( stderr, "failed to delete exchange: %s\n", 
                 sr_cfg.exchange );
            return(1);
        }
        fprintf( stderr, "exchange: %s deleted\n", sr_cfg.exchange );
        return(0);
    }
  
    if ( !sr_post_init( sr_c ) ) 
    {
        fprintf( stderr, "failed to declare exchange: %s\n", sr_cfg.exchange );
        return(1);
    }

    if ( !strcmp( sr_cfg.action, "setup" ) )
    {
        return(0);
    }
  
  
    firstpath=i;     // i initialized by arg parsing above...
    pass=0;     // when using inotify, have to walk the tree to set the watches initially.
    latest_min_mtim.tv_sec = 0;
    latest_min_mtim.tv_nsec = 0;
    if (!sr_cfg.force_polling) 
    {
        inotify_event_mask=IN_DONT_FOLLOW|IN_ONESHOT; 
        if (sr_cfg.events|SR_CREATE) inotify_event_mask |= IN_CREATE;  // includes mkdir & symlink.
        if (sr_cfg.events|SR_MODIFY) inotify_event_mask |= IN_CLOSE_WRITE;
        if (sr_cfg.events|SR_DELETE) inotify_event_mask |= IN_DELETE;
  
        inot_fd = inotify_init1(IN_NONBLOCK|IN_CLOEXEC);
        if ( inot_fd < 0) 
            fprintf( stderr, "error: inot init failed: error: %d\n", errno );
    }
  
    while (1) 
    {
       clock_gettime( CLOCK_REALTIME, &tstart );  
      
       if (sr_cfg.force_polling || !pass ) 
       {
           fprintf( stderr, "starting polling loop pass: %d\n", pass);
           for(i=firstpath ; i < argc ; i++ ) 
           {
              first_call=1;
              do1file(sr_c,argv[i]);
           }
           dir_stack_reset(); 
       } else {
           dir_stack_check4events(sr_c); // inotify. process accumulated events.
       }
       if  (sr_cfg.sleep <= 0.0) break; // one shot.
  
       clock_gettime( CLOCK_REALTIME, &tend );  
       elapsed = ( tend.tv_sec + tend.tv_nsec/1000000000 ) - 
                 ( tstart.tv_sec + tstart.tv_nsec/1000000000 )  ;
  
       if ( elapsed < sr_cfg.sleep ) 
       {
            tsleep.tv_sec = (long) (sr_cfg.sleep - elapsed);
            tsleep.tv_nsec =  (long) ((sr_cfg.sleep-elapsed)-tsleep.tv_sec);
            // fprintf( stderr, "debug: watch sleeping for %g seconds. \n", (sr_cfg.sleep-elapsed));
            nanosleep( &tsleep, NULL );
       } else 
            fprintf( stderr, "INFO: watch, one pass takes longer than sleep interval, not sleeping at all\n");
  
       latest_min_mtim = tstart;
       pass++; 
    }
  
    if ( sr_cfg.pipe ) 
    {
        if (sr_cfg.sleep > 0.0 ) {
           fprintf( stderr, "ERROR: sleep conflicts with pipe. pipe ignored.\n");
       } else
            while( fgets(inbuff,PATH_MAX,stdin) > 0 ) 
            {
                inbuff[strlen(inbuff)-1]='\0';
                do1file(sr_c,inbuff);
            }
    }
  
    sr_context_close(sr_c);
  
    return(0);
}
