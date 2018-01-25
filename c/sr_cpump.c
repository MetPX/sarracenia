/* vim:set ft=c ts=2 sw=2 sts=2 et cindent: */

/*
 * Usage info after license block.
 *
 * This code is by Peter Silva copyright (c) 2017 part of MetPX.
 * copyright is to the Government of Canada. code is GPL.
 *
 */

/* 
  Minimal c implementation to allow posting of sr_post(7) messages.

  spits out ´unimplemented option´ where appropriate...
 */
#include <stdio.h>
#include <signal.h>
#include <unistd.h>

//for opendir/readdir
#include <dirent.h>



#include "sr_version.h"

#include "sr_consume.h"
#include "sr_post.h"

void usage()
{
    fprintf( stderr, "usage: sr_cpump %s <options> <action> <configuration>\n\n", __sarra_version__  );
    fprintf( stderr, "\t<options> - sr_post compatible configuration file.\n" );
    fprintf( stderr, "\tbroker amqps://<user>@host - required - to lookup in ~/.config/sarra/credentials.\n" );
    fprintf( stderr, "\tdebug <on|off> - more verbose output.\n" );
    fprintf( stderr, "\texchange <exchange> - required - name of exchange to bind to\n" );
    fprintf( stderr, "\taccept/reject <regex> - to filter files to post.\n" );
    fprintf( stderr, "\tqueue <name> - queue to declare & use.\n" );

    fprintf( stderr, "\tpost_exchange <exchange> name of exchange to publish to (default: xs_<brokerusername>.)\n" );
    fprintf( stderr, "\tpost_exchange_split <num> number of output exchanges (default: 1.)\n" );
    fprintf( stderr, "\theartbeat <on|off|integer> - clean cache interval.\n" );
    fprintf( stderr, "\tsuppress_duplicates|sd|cache|caching <on|off|integer> (default: off)\n" );
    fprintf( stderr, "\t\tsuppress duplicate receptions < *cache* seconds apart.  \"on\" means 15 minute caching (on=900).\n" );
    fprintf( stderr, "\t\tsuppress duplicate announcements < *cache* seconds apart.  \"on\" means 15 minute caching (on=900).\n" );
    fprintf( stderr, "\ttopic_prefix <string> - AMQP topic prefix (default: v02.post )\n" );
    fprintf( stderr, "\tto <destination> - clusters pump network should forward to (default: broker).\n" );
    fprintf( stderr, "\turl <url>[,<url>]... - retrieval base url in the posted files.\n" );
    fprintf( stderr, "\n\t<action> = [start|stop|setup|cleanup|foreground] default: foreground\n" );
    fprintf( stderr, "\t\tstart - start a daemon running (will detach) and write to log.\n" );
    fprintf( stderr, "\t\thelp - view this usage.\n" );
    fprintf( stderr, "\t\tlist - list existing configurations.\n" );
    fprintf( stderr, "\t\tstop - stop a running daemon.\n" );
    fprintf( stderr, "\t\tdeclare - declare broker resources (to be ready for subscribers to bind to.)\n" );
    fprintf( stderr, "\t\tsetup - bind queues to resources, declaring if needed.)\n" );
    fprintf( stderr, "\t\tcleanup - delete any declared broker resources.\n" );
    fprintf( stderr, "\t\tforeground - run as a foreground process logging to stderr (ideal for debugging.)\n" );
   
    fprintf( stderr, "\nThis is a limited C implementation of sr_subscribe(1), see man page for details\n\n" );
    fprintf( stderr, "\t\tcan only move messages (no downloading.), no plugin support.\n" );
    exit(1);
}

int sr_cpump_cleanup(struct sr_context *sr_c, struct sr_config_t *sr_cfg, int dolog)
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
         fprintf( stderr, "cannot cleanup : sr_cpump configuration %s is running\n", sr_cfg->configname );
         return(1);
     }
  }

  sprintf( cache_dir, "%s/.cache/sarra/%s/%s", getenv("HOME"), sr_c->cfg->progname, sr_c->cfg->configname);

  sr_consume_cleanup(sr_c);
  sr_post_cleanup( sr_c ); 
  sr_context_close(sr_c);

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
               fprintf( stderr, "cannot cleanup : sr_cpump configuration %s directory\n", e->d_name );
          }

          ret = remove(cache_fil);
      }

      closedir(dir);

      ret = rmdir(cache_dir);
  }

  /* PAS not sure, but currently don't think we should ever delete logs.
     MG also mentioned this code does not delete old logs, so missing a bit.
  if (dolog)
  {
     ret = remove(sr_cfg->logfn);
  }
   */
  return(0);
}

int main(int argc, char **argv)
{
  struct sr_message_t *m;
  struct sr_context *sr_c;
  struct sr_config_t sr_cfg;
  struct sr_mask_t *mask;
  int    consume,i,ret;
  char   *one;
  
  //if ( argc < 3 ) usage();
 
  sr_config_init( &sr_cfg, "cpump" );

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
      if (!consume) break;
      i+=consume;
  }

  for (; i < argc; i++ )
  {
        sr_add_path(&sr_cfg, argv[i]);
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
  
  if ( !strcmp( sr_cfg.action, "disable" ))
  {
        sr_config_disable( &sr_cfg );
        exit(0);
  }

  if ( sr_cfg.paths )
  {
        sr_config_read(&sr_cfg, sr_cfg.paths->path, 1, 1 );
  }

  if ( sr_cfg.help ) usage();

  if ( !strcmp( sr_cfg.action, "edit" ))
  {
        sr_config_edit( &sr_cfg );
        exit(0);
  }

  if ( !strcmp( sr_cfg.action, "remove") )
  {
      // remove anything but a config file
      if (sr_cfg.configname)
      {
         one = sr_config_find_one( &sr_cfg, sr_cfg.configname );
         if ( !one || strcmp( &(one[strlen(one)-5]),".conf"))
         {
            sr_config_remove( &sr_cfg );
            exit(0);
         }
      }
  }

  if ( !strcmp( sr_cfg.action, "list" ))
  {
        sr_config_list( &sr_cfg );
        exit(0);
  }
  
  if (!sr_config_finalize( &sr_cfg, 1))
  {
     log_msg( LOG_ERROR, "failed to finalize configuration\n");
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
  if (!sr_c) {
     log_msg( LOG_ERROR, "failed to build context from configuration\n");
     return(1);
  }
  sr_c = sr_context_connect( sr_c );
  if (!sr_c) {
     log_msg( LOG_ERROR, "failed to connect context.\n");
     return(1);
  }
  
  if ( !strcmp( sr_cfg.action, "remove" ))
  {

        ret = sr_cpump_cleanup(sr_c,&sr_cfg,1);
        if (ret == 0) sr_config_remove( &sr_cfg );
        exit(0);
  }

  // dont consume_setup or post_init if in cleanup
  // (just hangs when attempting to bind queue with cleaned up exchange)
  if ( strcmp( sr_cfg.action, "cleanup" ) ) {
     sr_consume_setup(sr_c);

     if (!strcmp(sr_cfg.outlet,"post"))
         sr_post_init( sr_c );
  }
  
  if ( !strcmp( sr_cfg.action, "setup" ) || !strcmp( sr_cfg.action, "declare") )
  {
        return(0);
  }

  if ( !strcmp( sr_cfg.action, "cleanup" ) )
  {
        ret = sr_cpump_cleanup(sr_c,&sr_cfg,0);
        return(0);
  }

  /*
  if ( !strcmp( sr_cfg.action, "start" ) )
  {
      log_msg( LOG_CRITICAL, "FIXME output file when running as daemon is broken, aborting.\n");
      return(0);
  }
   */

  if ( strcmp( sr_cfg.action, "foreground" ) )
  {
      if (! sr_cfg.outlet) 
      {
           log_msg( LOG_CRITICAL, "must specify output file when running as daemon.\n");
           return(1);
      }
      daemonize(0);
  }
 
  // Assert: this is a working instance, not a launcher...
  if ( sr_config_activate( &sr_cfg ) )
  {
        log_msg( LOG_WARNING, 
            "could not save pidfile %s: possible to run conflicting instances  \n", 
            sr_cfg.pidfile );
  }
  log_msg( LOG_INFO, "%s %s config: %s, pid: %d, queue: %s bound to exchange: %s starting\n", 
            sr_cfg.progname, __sarra_version__, sr_cfg.configname,  sr_cfg.pid, sr_cfg.queuename, sr_cfg.exchange );


  while(1)
  {

      // inlet: from queue, json, tree.
      m=sr_consume(sr_c);

      if (!m) break;

      log_msg( LOG_INFO, "received: %s\n", sr_message_2log(m) );

      /* apply the accept/reject clauses */
      // FIXME BUG: pattern to match is supposed to be complete URL, not just path...
      mask = isMatchingPattern( &sr_cfg, m->path);
      if ( (mask && !(mask->accepting)) || (!mask && !(sr_cfg.accept_unmatched)) )
      {
          log_msg( LOG_DEBUG, "rejecting: %s\n", m->path );
          continue; 
      }
      // check cache.
      if (sr_cfg.cachep)
      {
          ret = sr_cache_check( sr_cfg.cachep, m->parts_s, (unsigned char*)m->sum, m->path, sr_message_partstr(m) );
          if (!ret) continue; // cache hit.
      }
      // do_pump=NULL
 
      // outlet:
      if (m) {
        if ( !strcmp( sr_cfg.outlet, "json" ) ) sr_message_2json(m);      
        else if ( !strcmp( sr_cfg.outlet, "url" ) ) sr_message_2url(m);      
        else if ( !strcmp( sr_cfg.outlet, "post" ) ) sr_post_message(sr_c,m);      
      }

      sr_context_heartbeat_check( sr_c );

  }
  sr_context_close(sr_c);
  free(sr_c);
  sr_config_free(&sr_cfg);

  return(0);
}
