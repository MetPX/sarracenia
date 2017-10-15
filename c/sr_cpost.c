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

   would be straightforward to:
       - use an uthash for the stack, rather than a stack a hash list on id.
       - have each dir_stak entry have a hash_entry for the files modified within that directory,
         rather than one big one in check4events.  would bring the size of  'n' way down for various algos.
         also use relative paths, that way, rather than absolute ones used in current hash.

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
           log_msg( LOG_ERROR, "ERROR: failed to malloc adding to dir_stack for: %s\n", fn );
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
    else if (mask|IN_MOVED_FROM) strcpy(evstr, "rename");
    else if (mask|IN_MOVED_TO) strcpy(evstr, "rename");
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
    struct sr_mask_t *mask;
    char ep[PATH_MAXNUL];

  /*
    if (sr_c->cfg->debug)
        log_msg( LOG_DEBUG, "do1file starting on: %s\n", fn );
   */
    /* apply the accept/reject clauses */

    // FIXME BUG: pattern to match is supposed to be complete URL, not just path...
    mask = isMatchingPattern( sr_c->cfg, fn );
    if ( (mask && !(mask->accepting)) || (!mask && !(sr_c->cfg->accept_unmatched)) )
    {
          log_msg( LOG_DEBUG, "rejecting: %s\n", fn );
          return;
    }

    if ( lstat(fn, &sb) < 0 ) {
         log_msg( LOG_ERROR, "failed to lstat: %s\n", fn );
         return;
    }

    if (S_ISLNK(sb.st_mode)) 
    {   // process a symbolic link.
        if (sr_c->cfg->debug)
           log_msg( LOG_DEBUG, "debug: %s is a symbolic link. (follow=%s) posting\n", 
               fn, ( sr_c->cfg->follow_symlinks )?"on":"off" );

        if (ts_newer( sb.st_mtim, latest_min_mtim ))
            sr_post(sr_c,fn, &sb);       // post the link itself.

    /* FIXME:  INOT  - necessary? I think symlinks can be skipped?
     */

        if ( ! ( sr_c->cfg->follow_symlinks ) )  return;

        if ( stat(fn, &sb) < 0 ) {  // repeat the stat, but for the destination.
             log_msg( LOG_ERROR, "failed to stat: %s\n", fn );
             return;
        }

        if (ts_newer( latest_min_mtim, sb.st_mtim ) ) return; // only the link was new.

    }

    if (S_ISDIR(sb.st_mode))   // process a directory.
    {
         if (sr_c->cfg->debug)
             log_msg( LOG_DEBUG, 
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
               log_msg( LOG_ERROR, "failed to add_watch: %s\n", fn );
               return;
            }
         } else w=0;

         if ( !dir_stack_push( fn, w, sb.st_dev, sb.st_ino ) )
         {
             close(inot_fd);
             log_msg( LOG_ERROR, "info: loop detected, skipping: %s\n", fn );
             return;
         } //else 
           //log_msg( LOG_DEBUG, "pushed on stack: %s\n", fn );
                      
         dir=opendir(fn);
         if (!dir) 
         {
             log_msg( LOG_ERROR, "failed to open directory: %s\n", fn );
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
             log_msg( LOG_DEBUG, "info: closing directory: %s\n", fn );

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
    int rename_steps=0;
    char *oldname;
    char *newname;
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
                 log_msg( LOG_ERROR, "cannot find path for event %s\n",
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
            /* rename processing
               rename arrives as two events, old name MOVE_FROM, new name MOVE_TO.
               need to group them together to call sr_post_rename.
             */
            if ( e->mask == IN_MOVED_FROM)
            {
               log_msg( LOG_DEBUG, "rename, oldname=%s\n", fn );
               rename_steps++;
               oldname=strdup(fn);               
            }
            if ( e->mask == IN_MOVED_TO )
            {
               rename_steps++;
               newname=strdup(fn);               
               log_msg( LOG_DEBUG, "rename, newname=%s\n", fn );
            }
            if ( ( e->mask && (IN_MOVED_FROM|IN_MOVED_TO) ) && ( rename_steps == 2 )  )
            {
               log_msg( LOG_DEBUG, "ok invoking rename %s %s\n", oldname, newname );
               sr_post_rename( sr_c, oldname, newname );
               rename_steps=0;
               free(oldname); 
               free(newname);
               oldname=NULL;
               newname=NULL;
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
                if ( !( e->mask && (IN_MOVED_FROM|IN_MOVED_TO)) )
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
     fprintf( stderr, "usage: sr_cpost <options> <paths>\n\n" );
     fprintf( stderr, "\taccept/reject <regex> - to filter files to post.\n" );
     fprintf( stderr, "\taccept_unmatch <boolean> - if not matched, accept? (default: true).\n" );
     fprintf( stderr, "\taction [start|stop|setup|cleanup|foreground] default: foreground\n" );
     fprintf( stderr, "\t\tstart - start a daemon running (will detach) and write to log.\n" );
     fprintf( stderr, "\t\tstop - stop a running daemon.\n" );
     fprintf( stderr, "\t\tsetup - declare broker resources (to be ready for subscribers to bind to.)\n" );
     fprintf( stderr, "\t\tcleanup - delete any declared broker resources.\n" );
     fprintf( stderr, "\t\tforeground - run as a foreground process logging to stderr (ideal for debugging.)\n" );
     fprintf( stderr, "\tbroker amqps://<user>@host - required - to lookup in ~/.config/sarra/credentials. MANDATORY\n" );
     fprintf( stderr, "\tchmod_log <mode> - permissions to set on log files (default: 0600)\n" );
     fprintf( stderr, "\tconfig|c <name> - Configuration file (to store options) MANDATORY\n" );
     fprintf( stderr, "\tdebug <on|off> - more verbose output. (default: off) \n" );
     fprintf( stderr, "\tdocument_root|dr <path> - part of tree to subtract from advertised URL's.\n" );
     fprintf( stderr, "\tdurable <boolean> - AMQP parameter, exchange declared persist across broker restarts (default: true)\n" );
     fprintf( stderr, "\tevents <list> - types of file events to post (default: create,modify,link,delete )\n" );
     fprintf( stderr, "\t\tcreate - file creation (generally empty files are not interesting.)\n");
     fprintf( stderr, "\t\tmodify - when files being written are closed (most interesting.)\n");
     fprintf( stderr, "\t\tdelete - when files removed. \n");
     fprintf( stderr, "\t\tlink - when files are linked or symbolically linked removed (converted to symlink). \n");
     fprintf( stderr, "\texchange <exchange> - required - name of exchange to publish to (default: xs_<brokerusername>.)\n" );
     fprintf( stderr, "\tfollow_symlinks <boolean> - traverse_symlinks and post the other side (default: off)\n" );
     fprintf( stderr, "\tforce_polling <boolean> - walk the tree every time, instead of INOTIFY (default: off)\n" );
     fprintf( stderr, "\t\tPolling is slower and much more resource intensive than default method, use only when needed.\n" );
     fprintf( stderr, "\t\tExample: when using distributed cluster files systems with multiple writing nodes, like GPFS & lustre (or run on all nodes.)\n" );
     fprintf( stderr, "\theader <key>=<value> - post an arbitrary key=value attribute with file. OPTIONAL\n" );
     fprintf( stderr, "\theartbeat <on|off|integer> - clean cache interval.\n" );
     fprintf( stderr, "\tloglevel <integer> - print >= n:\n\t\t1-DEBUG, 2-info, 3-Warn, 4-ERROR, 5-CRITICAL.\n" );
     fprintf( stderr, "\tparts|blocksize <integer> - partition strategy (size of chunks): (default: 1) \n" );
     fprintf( stderr, "\t\t1- always send files in one chunk, \n" );
     fprintf( stderr, "\t\t0-guess chunk size\n" );
     fprintf( stderr, "\t\t>1 explicit chunk size  (can use (M/K/G[B] suffixes: eg. 50M -> 50 megabytes (base 2) ).\n" );
     fprintf( stderr, "\tpath <path> - a file/directory to post. (also on end of command line.) MANDATORY\n" );
     fprintf( stderr, "\tpipe <boolean> - accept file names to post from stdin (default: off).\n" );
     fprintf( stderr, "\trealpath <boolean> - resolve paths before posting (default: off)\n" );
     fprintf( stderr, "\trecursive <boolean> - walk subdirectories (default: off)\n" );
     fprintf( stderr, "\tsum <algo> - how to set fingerprint for posts: (default: s)\n" );
     fprintf( stderr, "\t\td-MD5 sum of entire file.\n" );
     fprintf( stderr, "\t\tn-MD5 sum of file name.\n" );
     fprintf( stderr, "\t\ts-SHA512 sum of entire file.\n" );
     fprintf( stderr, "\t\tN-SHA512 sum of file name.\n" );
     fprintf( stderr, "\tsleep <integer> - watch paths every *sleep* seconds (rather than once) (default: 0 (== off)).\n" );
     fprintf( stderr, "\tsuppress_duplicates|sd|cache|caching <on|off|integer> (default: off)\n" );
     fprintf( stderr, "\t\tsuppress duplicate announcements < *cache* seconds apart.  \"on\" means 15 minute caching (on=900).\n" );
     fprintf( stderr, "\ttopic_prefix <string> - AMQP topic prefix (default: v02.post )\n" );
     fprintf( stderr, "\tto <destination> - clusters pump network should forward to (default: broker).\n" );
     fprintf( stderr, "\turl <url>[,<url>]... - retrieval base url in the posted files.\n" );
     fprintf( stderr, "\t\t(a comma separated list of urls will result in alternation among multiple file postings.)\n" );

     fprintf( stderr, "\t<paths> - list of files and/or directories to post (same as *path* option.)\n\n" );
     fprintf( stderr, "This is a C implementation of sr_post(1), see man page for details\n\n" );
     exit(1);
}

void heartbeat(struct sr_context *sr_c) 
/* run this every heartbeat interval 
 */
{
   int cached_count;
   log_msg( LOG_INFO, "heartbeat processing start\n" );
   
   if (sr_c->cfg->cachep)
   {
       log_msg( LOG_INFO, "heartbeat starting to clean cache\n" );
       sr_cache_clean(sr_c->cfg->cachep, sr_c->cfg->cache );
       log_msg( LOG_INFO, "heartbeat cleaned, hashes left: %ld\n", HASH_COUNT(sr_c->cfg->cachep->data) );
       if (HASH_COUNT(sr_c->cfg->cachep->data) == 0) 
       {
          sr_c->cfg->cachep->data=NULL;
       }
       cached_count = sr_cache_save(sr_c->cfg->cachep, 0 );
       log_msg( LOG_INFO, "heartbeat after cleaning, cache stores %d entries.\n", cached_count );
   }
}

struct sr_cache_t *thecache=NULL;

void stop_handler(int sig)
{
     log_msg( LOG_INFO, "shutting down: signal %d received\n", sig);

     if (thecache)
         sr_cache_close( thecache );

     // propagate handler for further processing, likely trigger exit.
     signal( sig, SIG_DFL );
     raise(sig);
}


int main(int argc, char **argv)
{
    struct sr_context *sr_c;
    struct sr_config_t sr_cfg;
    char inbuff[PATH_MAXNUL];
    int consume,i,pass;
    int ret;
    struct timespec tstart, tsleep, tend;
    float elapsed;
    float since_last_heartbeat;
    
    if ( argc < 3 ) usage();
   
    sr_config_init( &sr_cfg, "cpost" );
  
    i=1;
    while( i < argc ) 
    {
        if (argv[i][0] == '-') 
           consume = sr_config_parse_option( &sr_cfg, 
                  &(argv[i][ (argv[i][1] == '-' )?2:1 ]),  /* skip second hyphen if necessary */
                    argv[i+1] );
        else
            break;
        if (consume < 0) return(1);

        if (!consume) break;
        i+=consume;
    }

    for (; i < argc; i++ )
    {
          if ( !strcmp(sr_cfg.action,"foreground") )
               sr_add_path(&sr_cfg, argv[i]);
          else
               sr_config_read(&sr_cfg, argv[i] );

    }

    if (!sr_config_finalize( &sr_cfg, 0 ))
    {
        log_msg( LOG_ERROR, "something missing, failed to finalize config\n");
        return(1);
    }

    // Check if already running. (conflict in use of state files.)

    ret = sr_config_startstop( &sr_cfg );

    if ( ret < 1 ) 
    {
        exit(abs(ret));
    }

    sr_c = sr_context_init_config( &sr_cfg );
    if (!sr_c) 
    {
        log_msg( LOG_CRITICAL, "failed to read config\n");
        return(1);
    }

    sr_c = sr_context_connect( sr_c );
  
    if (!sr_c) 
    {
        log_msg( LOG_CRITICAL, "failed to establish sr_context\n");
        return(1);
    }

    if ( !strcmp( sr_cfg.action, "cleanup" ) )
    {
        if ( !sr_post_cleanup( sr_c ) ) 
        {
            log_msg( LOG_WARNING, "failed to delete exchange: %s\n", 
                 sr_cfg.exchange );
            return(1);
        }
        log_msg( LOG_INFO, "exchange: %s deleted\n", sr_cfg.exchange );
        return(0);
    }
  
 /*
    FIXME: wait until next version of sarra is released... not permitted on old ones.
    warn for now, error exit on future versions.
  */
    if ( !strcmp( sr_cfg.action, "setup" ) || !strcmp( sr_cfg.action, "declare") )
    {
        if ( !sr_post_init( sr_c ) ) 
        {
        log_msg( LOG_WARNING, "failed to declare exchange: %s (talking to a pump < 2.16.7 ?) \n", sr_cfg.exchange );
        }
        return(0);
    }

    if ( strcmp( sr_cfg.action, "foreground" ) )
    {
        daemonize(1);
    }
     
    // Assert: this is a working instance, not a launcher...
    if ( sr_config_save_pid( &sr_cfg ) ) 
    {
        log_msg( LOG_WARNING, "could not save pidfile %s: possible to run conflicting instances  \n", sr_cfg.pidfile );
    } 
    if ( sr_cfg.cache > 0 )
    {
     thecache = sr_cfg.cachep;
     if ( signal( SIGTERM, stop_handler ) == SIG_ERR )
         log_msg( LOG_ERROR, "unable to set stop handler\n" );
     else
         log_msg( LOG_DEBUG, "set stop handler to cleanup cache on exit.\n" );
    }

    log_msg( LOG_INFO, "%s config: %s, pid: %d, starting\n", sr_cfg.progname, sr_cfg.configname,  sr_cfg.pid );

    pass=0;     // when using inotify, have to walk the tree to set the watches initially.
    latest_min_mtim.tv_sec = 0;
    latest_min_mtim.tv_nsec = 0;
    if (!sr_cfg.force_polling) 
    {
        inotify_event_mask=IN_DONT_FOLLOW; 

        if (sr_cfg.events|SR_CREATE) // includes mkdir & symlink.
            inotify_event_mask |= IN_CREATE|IN_MOVED_FROM|IN_MOVED_TO;  

        if (sr_cfg.events|SR_MODIFY) 
            inotify_event_mask |= IN_CLOSE_WRITE|IN_MOVED_FROM|IN_MOVED_TO;

        if (sr_cfg.events|SR_DELETE) 
            inotify_event_mask |= IN_DELETE;
  
        inot_fd = inotify_init1(IN_NONBLOCK|IN_CLOEXEC);
        if ( inot_fd < 0) 
            log_msg( LOG_ERROR, "inot init failed: error: %d\n", errno );
    }
  
    since_last_heartbeat = 0.0;
    clock_gettime( CLOCK_REALTIME, &tstart );  

    while (1) 
    {
      

       if (sr_cfg.force_polling || !pass ) 
       {
           log_msg( LOG_DEBUG, "starting polling loop pass: %d\n", pass);
           for(struct sr_path_t *i=sr_cfg.paths ; i ; i=i->next ) 
           {
              first_call=1;
              do1file(sr_c,i->path);
           }
           dir_stack_reset(); 

       } else {

           dir_stack_check4events(sr_c); // inotify. process accumulated events.

       }

       if  (sr_cfg.sleep <= 0.0) break; // one shot.
  
       clock_gettime( CLOCK_REALTIME, &tend );  
       elapsed = ( tend.tv_sec + (tend.tv_nsec/1e9) ) - 
                 ( tstart.tv_sec + (tstart.tv_nsec/1e9) )  ;
  
       since_last_heartbeat = since_last_heartbeat + elapsed ;

       //log_msg( LOG_DEBUG, "tend.tv_sec=%ld, tstart.tv_sec=%ld sr_cpost:  elapsed: %g since_last_heartbeat: %g hb: %g\n", 
       //      tend.tv_sec, tstart.tv_sec, elapsed, since_last_heartbeat, sr_cfg.heartbeat );

       clock_gettime( CLOCK_REALTIME, &tstart );  

       if (since_last_heartbeat >= sr_cfg.heartbeat )
       {
           heartbeat(sr_c);
           since_last_heartbeat = 0.0;
       } 

       if ( elapsed < sr_cfg.sleep ) 
       {
            tsleep.tv_sec = (long) (sr_cfg.sleep - elapsed);
            tsleep.tv_nsec =  (long) ((sr_cfg.sleep-elapsed)-tsleep.tv_sec);
            //log_msg( LOG_DEBUG, "debug: watch sleeping for %g seconds. \n", (sr_cfg.sleep-elapsed));
            nanosleep( &tsleep, NULL );
       } else 
            log_msg( LOG_INFO, "INFO: watch, one pass takes longer than sleep interval, not sleeping at all\n");
  
       latest_min_mtim = tstart;
       pass++; 
    }
  
    if ( sr_cfg.pipe ) 
    {
        if (sr_cfg.sleep > 0.0 ) {
           log_msg( LOG_ERROR, "sleep conflicts with pipe. pipe ignored.\n");
       } else
            while( fgets(inbuff,PATH_MAX,stdin) > 0 ) 
            {
                inbuff[strlen(inbuff)-1]='\0';
                do1file(sr_c,inbuff);
            }
    }
  
    sr_context_close(sr_c);
    free(sr_c);
    sr_config_free(&sr_cfg);  
    return(0);
}
