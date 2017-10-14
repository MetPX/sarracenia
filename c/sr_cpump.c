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

#include "sr_consume.h"
#include "sr_post.h"

void usage()
{
    fprintf( stderr, "usage: sr_cpost <options> <files>\n\n" );
    fprintf( stderr, "\t<options> - sr_post compatible configuration file.\n" );
    fprintf( stderr, "\t\tbroker amqps://<user>@host - required - to lookup in ~/.config/sarra/credentials.\n" );
    fprintf( stderr, "\t\tdebug <on|off> - more verbose output.\n" );
    fprintf( stderr, "\t\texchange <exchange> - required - name of exchange to bind to\n" );
    fprintf( stderr, "\t\taccept/reject <regex> - to filter files to post.\n" );
    fprintf( stderr, "\t\tqueue <name> - queue to declare & use.\n" );

    fprintf( stderr, "\nThis is a stripped down C implementation of sr_subscribe(1), see man page for details\n\n" );
    fprintf( stderr, "examples of missing features: \n\n" );
    fprintf( stderr, "\t\tno cache.\n" );
    fprintf( stderr, "\t\tcan only display messages (no downloading.)\n" );
    exit(1);
}

int main(int argc, char **argv)
{
  struct sr_message_t *m;
  struct sr_context *sr_c;
  struct sr_config_t sr_cfg;
  struct sr_mask_t *mask;
  int consume,i,ret;
  
  if ( argc < 3 ) usage();
 
  sr_config_init( &sr_cfg, "cpump" );

  i=1;
  while( i < argc ) 
  {
      if (argv[i][0] == '-') 
         consume = sr_config_parse_option( &sr_cfg, 
              &(argv[i][ (argv[i][1] == '-' )?2:1 ]),  /* skip second hyphen if necessary */
              argv[i+1] );
      else
          break;
      if (!consume) break;
      i+=consume;
  }

  for (; i < argc; i++ )
  {
        sr_add_path(&sr_cfg, argv[i]);
  }
  if ( sr_cfg.paths )
  {
        sr_config_read(&sr_cfg, sr_cfg.paths->path );
  }
  if (!sr_config_finalize( &sr_cfg, 1))
  {
     log_msg( LOG_ERROR, "failed to finalize configuration\n");
     return(1); 
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
  sr_consume_setup(sr_c);

  if (!strcmp(sr_cfg.outlet,"post"))
      sr_post_init( sr_c );
  
  if ( !strcmp( sr_cfg.action, "setup" ) || !strcmp( sr_cfg.action, "declare") )
  {
        return(0);
  }

  if ( !strcmp( sr_cfg.action, "cleanup" ) )
  {
      sr_consume_cleanup(sr_c);
      sr_post_cleanup( sr_c ); 
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
  if ( sr_config_save_pid( &sr_cfg ) )
  {
        log_msg( LOG_WARNING, 
            "could not save pidfile %s: possible to run conflicting instances  \n", 
            sr_cfg.pidfile );
  }
  log_msg( LOG_INFO, "%s config: %s, pid: %d, queue: %s bound to exchange: %s starting\n", 
            sr_cfg.progname, sr_cfg.configname,  sr_cfg.pid, sr_cfg.queuename, sr_cfg.exchange );

  while(1)
  {

      // inlet: from queue, json, tree.
      m=sr_consume(sr_c);

      log_msg( LOG_INFO, "received: %s\n", sr_message_2log(m) );

      /* apply the accept/reject clauses */
      // FIXME BUG: patter to match is supposed to be complete URL, not just path...
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
  }
  sr_context_close(sr_c);
  free(sr_c);
  sr_config_free(&sr_cfg);

  return(0);
}
