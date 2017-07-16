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
#include <stdio.h>
#include <linux/limits.h>
#include <sys/types.h>
#include <dirent.h>
#include <sys/inotify.h>

#include "sr_post.h"

/* for each directory opened, store it's dev+inode pair.
   if you encounter another directory witht the same numbers, there is a loop.
   The FD is the file descriptor returned by an inotify_init.

 */ 

struct dir_stack {
   int ifd;                    // fd returned by inotify_init.
   dev_t dev;                  // info from stat buf of directory.
   ino_t ino;
   int   visited;
   struct dir_stack *next;     // pointer towards the top of the stack.
};

/* FIXME: crappy algorithm single linked stack, no optimizations at all.
   FIXME: once a directory is added, deletion is not handled 
          (case: directory exists, while code runs, directory is deleted, then
           the inode is re-used for a file or another directory. if it turns
           out to be a directory, then it will be in the stack, but not watched.
 */

static struct dir_stack *dir_stack_top = NULL;   /* insertion point (end of line.) */

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

int dir_stack_push( int fd, dev_t dev, ino_t ino )
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
       t->ifd = fd;
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

static    int first_call = 1;
static time_t latest_min_mtime = 0;

void do1file( struct sr_context *sr_c, char *fn ) 
{
    DIR *dir;
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

        if (sb.st_mtime > latest_min_mtime ) 
            sr_post(sr_c,fn, &sb);       // post the link itself.

    /* FIXME:  INOT  - necessary? I think symlinks can be skipped?
        if ( sr_c->cfg->inotify ) 
             ret = inotify_add_watch(xx, fn, inot_event_mask);
     */

        if ( ! ( sr_c->cfg->follow_symlinks ) )  return;

        if ( stat(fn, &sb) < 0 ) {  // repeat the stat, but for the destination.
             fprintf( stderr, "ERROR: failed to stat: %s\n", fn );
             return;
        }

        if (sb.st_mtime <= latest_min_mtime ) return; // only the link was new.

    }

    if (S_ISDIR(sb.st_mode))   // process a directory.
    {
         if (sr_c->cfg->debug)
             fprintf( stderr, 
                 "info: opening directory: %s, first_call=%s, recursive=%s, follow_symlinks=%s latest_min_mtime=%ld\n", 
                 fn, first_call?"on":"off", (sr_c->cfg->recursive)?"on":"off", 
                 (sr_c->cfg->follow_symlinks)?"on":"off", latest_min_mtime );

         if ( !first_call && !(sr_c->cfg->recursive) ) return;

         first_call=0;

    /* FIXME: INOT   
         if ( sr_c->cfg->inotify ) 
             xx = inotify_init(IN_NONBLOCK);
             xx would be supplied to dir_stack_push.
     */
         if ( !dir_stack_push( 0, sb.st_dev, sb.st_ino ) )
         {
             //close(xx);
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
        if (sb.st_mtime > latest_min_mtime ) 
            sr_post(sr_c,fn, &sb);  // process a file
    /* FIXME:  INOT 
        if ( sr_c->cfg->inotify ) 
             ret = inotify_add_watch(xx, fn, inot_event_mask);
     */

}

void usage() 
{
     fprintf( stderr, "usage: sr_cpost <options> <files>\n\n" );
     fprintf( stderr, "\t<options> - sr_post compatible configuration file.\n" );
     fprintf( stderr, "\t\tbroker amqps://<user>@host - required - to lookup in ~/.config/sarra/credentials.\n" );
     fprintf( stderr, "\t\tdebug <on|off> - more verbose output.\n" );
     fprintf( stderr, "\t\texchange <exchange> - required - name of exchange to publish to\n" );
     fprintf( stderr, "\t\taccept/reject <regex> - to filter files to post.\n" );
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
  int consume,i,firstpath;
  struct timespec tstart, tsleep, tend;
  time_t start_time_of_run;
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

  if (!sr_c) {
     fprintf( stderr, "failed to establish sr_context\n");
     return(1);
  }

  // i initialized by arg parsing above...
  firstpath=i;

  while (1) 
  {
     clock_gettime( CLOCK_REALTIME, &tstart );  
    
     time(&start_time_of_run);

     for(i=firstpath ; i < argc ; i++ ) 
     {
            first_call=1;
            do1file(sr_c,argv[i]);
     }
     if  (sr_c->cfg->sleep <= 0.0) break; // one shot.

     clock_gettime( CLOCK_REALTIME, &tend );  
     elapsed = ( tend.tv_sec + tend.tv_nsec/1000000000 ) - ( tstart.tv_sec + tstart.tv_nsec/1000000000 )  ;

     if ( elapsed < sr_cfg.sleep ) 
     {
          tsleep.tv_sec = (long) (sr_cfg.sleep - elapsed);
          tsleep.tv_nsec =  (long) ((sr_cfg.sleep-elapsed)-tsleep.tv_sec);
          if (sr_cfg.debug) 
               fprintf( stderr, "debug: watch sleeping for %g seconds. \n", (sr_cfg.sleep-elapsed));
          nanosleep( &tsleep, NULL );
     } else 
          fprintf( stderr, "INFO: watch, one pass takes longer than sleep interval, not sleeping at all\n");

     //latest_min_mtime = ( time(&this_second) > max_mtime ) ? max_mtime : this_second ;
     latest_min_mtime = start_time_of_run;

     //FIXME:  if ( ! sr_c->cfg->inotify ) ... only visit once in inotify method, but reset each time for polling.
         dir_stack_reset(); 
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

  return 0;
}
