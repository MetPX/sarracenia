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

#include "sr_version.h"
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
    if (mask&IN_CREATE) strcpy(evstr, "create");
    else if (mask&IN_MODIFY) strcpy(evstr, "modify");
    else if (mask&IN_MOVED_FROM) strcpy(evstr, "rename");
    else if (mask&IN_MOVED_TO) strcpy(evstr, "rename");
    else if (mask&IN_DELETE) strcpy(evstr, "delete");
    else sprintf( evstr, "dunno: %04x!", mask );
    if (mask&IN_ISDIR) strcat( evstr, ",directory" );
    return(evstr);
}

// see man 7 inotify for size of struct inotify_event
#define INOTIFY_EVENT_MAX  (sizeof(struct inotify_event) + NAME_MAX + 1)

static    int inot_fd=0;


static    int first_call = 1;
//struct timespec latest_min_mtim;

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

    //if (sr_c->cfg->debug)
    //    log_msg( LOG_DEBUG, "do1file starting on: %s\n", fn );
    /* apply the accept/reject clauses */

    // FIXME BUG: pattern to match is supposed to be complete URL, not just path...
    mask = isMatchingPattern( sr_c->cfg, fn );
    if ( (mask && !(mask->accepting)) || (!mask && !(sr_c->cfg->accept_unmatched)) )
    {
          log_msg( LOG_DEBUG, "rejecting: %s\n", fn );
          return;
    }

    if ( lstat(fn, &sb) < 0 ) {
         sr_post(sr_c,fn, NULL);       /* post file remove */
         return;
    }

    if (S_ISLNK(sb.st_mode)) 
    {   // process a symbolic link.
        if (sr_c->cfg->debug)
           log_msg( LOG_DEBUG, "debug: %s is a symbolic link. (follow=%s) posting\n", 
               fn, ( sr_c->cfg->follow_symlinks )?"on":"off" );

        //if (ts_newer( sb.st_mtim, latest_min_mtim ))
            sr_post(sr_c,fn, &sb);       // post the link itself.

    /* FIXME:  INOT  - necessary? I think symlinks can be skipped?
     */

        if ( ! ( sr_c->cfg->follow_symlinks ) )  return;

        if ( stat(fn, &sb) < 0 ) {  // repeat the stat, but for the destination.
             log_msg( LOG_ERROR, "failed to stat: %s\n", fn );
             return;
        }

        //if (ts_newer( latest_min_mtim, sb.st_mtim ) ) return; // only the link was new.

    }

    if (S_ISDIR(sb.st_mode))   // process a directory.
    {
         if (sr_c->cfg->debug)
             log_msg( LOG_DEBUG, 
                 "info: opening directory: %s, first_call=%s, recursive=%s, follow_symlinks=%s\n", 
                 fn, first_call?"on":"off", (sr_c->cfg->recursive)?"on":"off", 
                 (sr_c->cfg->follow_symlinks)?"on":"off" );

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
    {
        //if (ts_newer( sb.st_mtim, latest_min_mtim )) 
            sr_post(sr_c,fn, &sb);  // process a file
    }

}

struct rename_list {
       char *ofn;
       char *nfn;
       uint32_t cookie;
       struct rename_list *next;
};

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
    struct rename_list *old_names=NULL,*on=NULL, *prevon=NULL;

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

            log_msg( LOG_DEBUG, "bytes read: %d, sz ev: %ld, event: %04x %s: len=%d, fn=%s\n",
                    ret, sizeof(struct inotify_event)+e->len, e->mask,
                    inotify_event_2string(e->mask), e->len, fn );

            /* rename processing
               rename arrives as two events, old name MOVE_FROM, new name MOVE_TO.
               need to group them together by cookie to call sr_post_rename.
             */
            if ( ( (e->mask&IN_MOVED_FROM) == IN_MOVED_FROM) || ( (e->mask&IN_MOVED_TO) == IN_MOVED_TO ) )
            {
               log_msg( LOG_DEBUG, "rename, %sname=%s\n", ((e->mask&IN_MOVED_TO) == IN_MOVED_TO )?"new":"old", fn );
               if ( old_names ) {
                  prevon=NULL;
                  for( on = old_names; ( on && ( on->cookie != e->cookie )) ; on = on->next )
                       prevon = on ;
                  if (on) {
                      if ( on->ofn ) 
                      {
                         log_msg( LOG_DEBUG, "ok invoking rename ofn=%s %s\n", on->ofn, fn );
                         sr_post_rename( sr_c, on->ofn, fn );
                         free(on->ofn);
                      } else {
                         log_msg( LOG_DEBUG, "ok invoking rename %s nfn=%s\n", fn, on->nfn );
                         sr_post_rename( sr_c, fn, on->nfn );
                         free(on->nfn);
                      }
                      if (prevon)
                         prevon->next = on->next; 
                      else
                         old_names = on->next;
                      free(on); 
                      on=NULL;
                      continue;
                  }
               } 
               on=(struct rename_list *)malloc( sizeof( struct rename_list) );
               on->cookie = e->cookie;
               on->ofn=NULL;
               on->nfn=NULL;
               if ( (e->mask&IN_MOVED_TO) == IN_MOVED_TO )
                          on->nfn=strdup(fn);               
               else
                          on->ofn=strdup(fn);               
               on->next = old_names;
               old_names=on;
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

            log_msg( LOG_DEBUG, "looking in entries_done, for %s, result=%p\n", fn, tmpe );

            if (!tmpe) {
                new_entry = (struct hash_entry *)malloc( sizeof(struct hash_entry) );
                new_entry->fn = strdup(fn);
                HASH_ADD_KEYPTR( hh, entries_done, new_entry->fn, strlen(new_entry->fn), new_entry );
                log_msg( LOG_DEBUG, "e->mask=%04x from:  %04x  to: %04x \n", e->mask, IN_MOVED_FROM, IN_MOVED_TO );
                if ( !( e->mask & (IN_MOVED_FROM|IN_MOVED_TO)) )
                {
                    log_msg( LOG_DEBUG, "do one file: %s\n", fn );
                    do1file( sr_c, fn);
                }
            } else {
                log_msg( LOG_DEBUG, "entries_done hit! ignoring:%s\n", fn );
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

int sr_cpost_cleanup(struct sr_context *sr_c, struct sr_config_t *sr_cfg, int dolog)
{
  DIR   *dir;
  int    ret;
  char   cache_dir[PATH_MAX];
  char   cache_fil[PATH_MAX];
  struct stat sb;
  struct dirent *e;

  // if running, warn no cleanup
  if (sr_cfg->pid > 0)
  {
     ret=kill(sr_cfg->pid,0);
     if (!ret)
     {   // is running.
         fprintf( stderr, "cannot cleanup : sr_cpost configuration %s is running\n", sr_cfg->configname );
         return(1);
     }
  }

  sprintf( cache_dir, "%s/.cache/sarra/%s/%s", getenv("HOME"), sr_c->cfg->progname, sr_c->cfg->configname);

  if ( !sr_post_cleanup( sr_c ) ) 
     {
        log_msg( LOG_WARNING, "failed to delete exchange: %s\n", sr_cfg->exchange );
     }
  else  
     {
	log_msg( LOG_INFO, "exchange: %s deleted\n", sr_cfg->exchange );
     }
  sr_context_close(sr_c);
  sr_config_free(sr_cfg);

  dir = opendir( cache_dir );

  if (dir)
  {

      while( (e = readdir(dir)) )
      {
          if ( !strcmp(e->d_name,".") || !strcmp(e->d_name,"..") )
               continue;

          strcpy( cache_fil, cache_dir );
          strcat( cache_fil, "/" );
          strcat( cache_fil, e->d_name );

          if ( lstat( cache_fil, &sb ) < 0 )
               continue;

          if ( S_ISDIR(sb.st_mode) )
          {
               fprintf( stderr, "cannot cleanup : sr_cpost configuration %s directory\n", e->d_name );
          }
    
          ret = remove(cache_fil);
      }

      closedir(dir);

      ret = rmdir(cache_dir);
  }

  /* I don't think we should delete logs.
     Michel also mentioned, this doesn't delete old logs, so would need elaboration anyways.
  if (dolog)
  {
     ret = remove(sr_cfg->logfn);
  }
   */

  return(0);
}

void usage() 
{
     fprintf( stderr, "usage: sr_cpost %s <options> <paths>\n\n", __sarra_version__ );
     fprintf( stderr, "\taccept/reject <regex> - to filter files to post.\n" );
     fprintf( stderr, "\taccept_unmatch <boolean> - if not matched, accept? (default: true).\n" );
     fprintf( stderr, "\taction [start|stop|setup|cleanup|foreground] default: foreground\n" );
     fprintf( stderr, "\t\tstart - start a daemon running (will detach) and write to log.\n" );
     fprintf( stderr, "\t\thelp - view this usage.\n" );
     fprintf( stderr, "\t\tstop - stop a running daemon.\n" );
     fprintf( stderr, "\t\tlist - list configurations available.\n" );
     fprintf( stderr, "\t\tdeclare - declare broker resources (to be ready for subscribers to bind to.)\n" );
     fprintf( stderr, "\t\tsetup - bind queues to resources, declaring if needed.)\n" );
     fprintf( stderr, "\t\tcleanup - delete any declared broker resources.\n" );
     fprintf( stderr, "\t\tforeground - run as a foreground process logging to stderr (ideal for debugging.)\n" );
     fprintf( stderr, "\tbroker amqps://<user>@host - required - to lookup in ~/.config/sarra/credentials. MANDATORY\n" );
     fprintf( stderr, "\tchmod_log <mode> - permissions to set on log files (default: 0600)\n" );
     fprintf( stderr, "\tconfig|c <name> - Configuration file (to store options) MANDATORY\n" );
     fprintf( stderr, "\tdebug <on|off> - more verbose output. (default: off) \n" );
     fprintf( stderr, "\tdelete <on|off> - Assume Directories empty themselves. (default: off) \n" );
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
     fprintf( stderr, "\tpost_base_url <url>[,<url>]... - retrieval base url in the posted files.\n" );
     fprintf( stderr, "\t\t(a comma separated list of urls will result in alternation among multiple file postings.)\n" );
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
     fprintf( stderr, "\t<paths> - list of files and/or directories to post (same as *path* option.)\n\n" );
     fprintf( stderr, "This is a limited C implementation of sr_post(1), see man page for details\n\n" );
     fprintf( stderr, "does not support plugins. main difference: specifying sleep makes it act like sr_watch\n\n" );
     exit(1);
}


int main(int argc, char **argv)
{
    struct sr_context *sr_c;
    struct sr_config_t sr_cfg;
    char inbuff[PATH_MAXNUL];
    int consume,i,pass;
    int ret;
    char *one;

    struct timespec tsleep ;
    float elapsed;
    
    sr_config_init( &sr_cfg, "cpost" );
  

    i=1;
    while( i < argc ) 
    {
        if (argv[i][0] == '-') 
           consume = sr_config_parse_option( &sr_cfg, 
                  &(argv[i][ (argv[i][1] == '-' )?2:1 ]),  /* skip second hyphen if necessary */
                    argv[i+1], 
                  (argc>i+2)?argv[i+2]:NULL, 
                  1 );
        else
            break;
        if (consume < 0) return(1);

        if (!consume) break;
        i+=consume;
    }

    for (; i < argc; i++ )
    {
          if ( !strcmp( sr_cfg.action,"foreground") || !strcmp( sr_cfg.action, "enable" ) ||
               !strcmp( sr_cfg.action, "disable" ) || !strcmp( sr_cfg.action, "add" ) ||
               !strcmp( sr_cfg.action, "remove" ) || !strcmp( sr_cfg.action, "edit" )
             )
               sr_add_path(&sr_cfg, argv[i]);
          else 
               sr_config_read(&sr_cfg, argv[i], 1, 1 );
    }

    if ( !strcmp( sr_cfg.action, "add" ))
    {
        sr_config_add( &sr_cfg );
        exit(0);
    }

    if ( !strcmp( sr_cfg.action, "enable" ))
    {
        sr_config_enable( &sr_cfg );
        exit(0);
    }

    if ( !strcmp(sr_cfg.action, "help") || sr_cfg.help ) usage();

    if ( !strcmp( sr_cfg.action, "remove" ))
    {

        one = sr_config_find_one( &sr_cfg, sr_cfg.paths->path );
        if ( one && !strcmp( &(one[strlen(one)-5]),".conf"))
        {
            sr_config_read(&sr_cfg, one, 1, 1);
        }
        else
        {
            sr_config_remove( &sr_cfg );
            exit(0);
        }
    }

    if ( !strcmp( sr_cfg.action, "disable" ))
    {
        sr_config_disable( &sr_cfg );
        exit(0);
    }

    if ( !strcmp( sr_cfg.action, "edit" ))
    {
        sr_config_edit( &sr_cfg );
        exit(0);
    }

    if ( !strcmp( sr_cfg.action, "list" ))
    {
        sr_config_list( &sr_cfg );
        exit(0);
    }

    if (!sr_config_finalize( &sr_cfg, 0 ))
    {
        log_msg( LOG_ERROR, "something missing, failed to finalize config\n");
        sr_config_free(&sr_cfg);
        return(1);
    }

    if ( !strcmp( sr_cfg.action, "log" ))
    {
        sr_config_log( &sr_cfg );
        exit(0);
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
        sr_config_free(&sr_cfg);
        return(1);
    }

    sr_c = sr_context_connect( sr_c );
  
    if (!sr_c) 
    {
        log_msg( LOG_CRITICAL, "failed to establish sr_context\n");
        sr_config_free(&sr_cfg);
        return(1);
    }

    if ( !strcmp( sr_cfg.action, "cleanup" ) )
    {
        ret = sr_cpost_cleanup(sr_c,&sr_cfg,0);
        return(0);
    }

    if ( !strcmp( sr_cfg.action, "remove" ) )
    {
        ret = sr_cpost_cleanup(sr_c,&sr_cfg,1);
        if (ret == 0)
           {
           if (one) unlink(one);
           }
        return(0);
    }
  

    sr_post_init( sr_c );

    if ( ! sr_c->cfg->post_base_url )
    {
       log_msg( LOG_ERROR, "URL setting missing\n");
       return(0);
    }

    if ( !strcmp( sr_cfg.action, "setup" ) || !strcmp( sr_cfg.action, "declare" ) )
    {
       sr_context_close(sr_c);
       free(sr_c);
       sr_config_free(&sr_cfg);  
       exit(0);
    }

    if ( strcmp( sr_cfg.action, "foreground" ) )
    {
        daemonize(1);
    }
     
    // Assert: this is a working instance, not a launcher...
    if ( sr_config_activate( &sr_cfg ) ) 
    {
        log_msg( LOG_WARNING, "could not save pidfile %s: possible to run conflicting instances  \n", sr_cfg.pidfile );
    } 

    log_msg( LOG_INFO, "%s %s config: %s, pid: %d, starting\n", sr_cfg.progname, __sarra_version__, sr_cfg.configname,  sr_cfg.pid );

    pass=0;     // when using inotify, have to walk the tree to set the watches initially.
    //latest_min_mtim.tv_sec = 0;
    //latest_min_mtim.tv_nsec = 0;
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

           // FIXME: I think this breaks non Inotify walks...
           //if ( sr_cfg.force_polling && !sr_cfg.delete )
           //    latest_min_mtim = time_of_last_run();

           //log_msg( LOG_ERROR, "latest_min_mtime: %d, %d\n", latest_min_mtim.tv_sec, latest_min_mtim.tv_nsec );
       } else {

           dir_stack_check4events(sr_c); // inotify. process accumulated events.

       }

       if  (sr_cfg.sleep <= 0.0) break; // one shot.
  
       elapsed = sr_context_heartbeat_check(sr_c);

       if ( elapsed < sr_cfg.sleep ) 
       {
            tsleep.tv_sec = (long) (sr_cfg.sleep - elapsed);
            tsleep.tv_nsec =  (long) ((sr_cfg.sleep-elapsed)-tsleep.tv_sec);
            //log_msg( LOG_DEBUG, "debug: watch sleeping for %g seconds. \n", (sr_cfg.sleep-elapsed));
            nanosleep( &tsleep, NULL );
       } else 
            log_msg( LOG_INFO, "INFO: watch, one pass takes longer than sleep interval, not sleeping at all\n");
  
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
