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

int main(int argc, char **argv)
{
  struct sr_message_t *m;
  struct sr_context *sr_c;
  struct sr_config_t sr_cfg;
  int consume,i;
  
  if ( argc < 3 ) 
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
     fprintf( stderr, "failed to read configuration\n");
     return(1);
  }
  sr_c = sr_context_connect( sr_c );
  if (!sr_c) {
     fprintf( stderr, "failed to establish sr context\n");
     return(1);
  }
  if ( !strcmp( sr_cfg.action, "cleanup" ) )
  {
      sr_consume_cleanup(sr_c);
      return(0);
  }
  sr_consume_setup(sr_c);

  if ( !strcmp( sr_cfg.action, "setup" ) )
  {
      return(0);
  }

  while(1)
  {
      m=sr_consume(sr_c);
      if (m) sr_message_2json(m);      
  }
  sr_context_close(sr_c);

  return 0;
}
