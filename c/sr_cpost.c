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

#include "sr_post.h"

static int first_call = 1;

static time_t latest_min_mtime = 0;

void do1file( struct sr_context *sr_c, char *fn ) 
{
    DIR *dir;
    struct dirent *e;
    struct stat sb;
    char ep[PATH_MAXNUL];

    if (sr_c->cfg->debug)
        fprintf( stderr, "debug: do1file starting on: %s\n", fn );

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
             fprintf( stderr, "info: opening directory: %s, first_call=%s, recursive=%s\n", 
                 fn, first_call?"on":"off", (sr_c->cfg->recursive)?"on":"off" );

         if ( !first_call && !(sr_c->cfg->recursive) ) return;

         first_call=0;

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
    
     if (sr_cfg.debug) 
          fprintf( stderr, "debug: poll sleeping latest_min_mtime=%ld. \n", latest_min_mtime);

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
               fprintf( stderr, "debug: poll sleeping for %g seconds. \n", (sr_cfg.sleep-elapsed));
          nanosleep( &tsleep, NULL );
     } else 
          fprintf( stderr, "INFO: poll takes longer than sleep interval, not sleeping at all\n");

     //latest_min_mtime = ( time(&this_second) > max_mtime ) ? max_mtime : this_second ;
     latest_min_mtime = start_time_of_run;

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
