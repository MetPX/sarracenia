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

void do1file( struct sr_context *sr_c, char *fn ) 
{
    DIR *dir;
    struct dirent *e;
    struct stat sb;
    char ep[PATH_MAX];

    if ( lstat(fn, &sb) < 0 ) {
         fprintf( stderr, "failed to stat: %s\n", fn );
         return;
    }
    if (S_ISDIR(sb.st_mode)) 
    {
         dir=opendir(fn);
         if (!dir) {
             fprintf( stderr, "failed to open directory: %s\n", fn );
             return;
         }
         while ( e = readdir(dir) ) 
         {
             if ( !strcmp(e->d_name,".") || !strcmp(e->d_name,"..") ) 
                 continue;

             strcpy(ep,fn);
             strcat(ep,"/");
             strcat(ep,e->d_name );
             do1file(sr_c, ep);         
         }
         closedir(dir); 
    } else
         sr_post(sr_c,fn, &sb);

}


int main(int argc, char **argv)
{
  struct sr_context *sr_c;
  struct sr_config_t sr_cfg;
  char inbuff[PATH_MAX+1];
  ssize_t howlong;
  int consume,i,lastopt;
  
  if ( argc < 3 ) 
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
  sr_c = sr_context_connect( sr_c );

  if (!sr_c) {
     fprintf( stderr, "failed to establish sr context\n");
     return(1);
  }

  // i initialized by arg parsing above...
  for( ; i < argc ; i++ ) 
            do1file(sr_c,argv[i]);

  if ( sr_cfg.pipe ) 
      while( fgets(inbuff,PATH_MAX,stdin) > 0 ) 
      {
          inbuff[strlen(inbuff)-1]='\0';
          do1file(sr_c,inbuff);
      }

  sr_context_close(sr_c);

  return 0;
}
