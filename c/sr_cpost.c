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
 * ***** BEGIN LICENSE BLOCK *****
 * Version: MIT
 *
 * Portions created by Alan Antonuk are Copyright (c) 2012-2013
 * Alan Antonuk. All Rights Reserved.
 *
 * Portions created by VMware are Copyright (c) 2007-2012 VMware, Inc.
 * All Rights Reserved.
 *
 * Portions created by Tony Garnock-Jones are Copyright (c) 2009-2010
 * VMware, Inc. and Tony Garnock-Jones. All Rights Reserved.
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use, copy,
 * modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * ***** END LICENSE BLOCK *****
 */

/* 
  Minimal c implementation to allow posting of sr_post(7) messages.
  It has a lot of limitations, and no error checking for now.

  how to use:

  in a shell, set the SW_AMQP_MINI_OPTS environment variable to a space 
  separated sequence of settings.  The settings are:

  protocol scheme ( amqps, or amqp ) whether to use SSL or not.
  broker hostname
  broker port 
  broker exchange
  broker username (AMQP username to connect to broker)
  broker password (password for AMQP username)
  base URL to advertise  (examples: file:, http://localhost, sftp://hoho@host )

  comma separated list of destinations to target (examples: localhost, all)
 
  there are no defaults, it will just die horribly if something is missing.

  export SR_AMQP_MINI_OPTS="amqp localhost 5672 xs_tsource tsource tspw sftp://peter@localhost localhost"

  then just:

  sr_cpost <file>

 building it:

  cc -o sr_cpost sr_cpost.c -lrabbitmq

 (debian package: librabbitmq, and librabbitmq-dev. )

 limitations:
    - Doesn't calculate checksums, enforces sum 0.
    - Doesn't do file partitioning strategies, enforced post as 1 part.
    - Doesn't support document_root, absolute paths posted.
    - Doesn't do a lot of things... 
 */
#include <stdio.h>

#include "sr_context.h"


int main(int argc, char **argv)
{
  struct sr_context *sr_c;
  struct sr_config_t sr_cfg;
  int consume,i,lastopt;
  
  if ( argc < 3 ) 
  {
     fprintf( stderr, "usage: sr_cpost <config> <files>\n\n" );
     fprintf( stderr, "\t<config> - sr_post compatible configuration file.\n" );
     fprintf( stderr, "\t<files> - list of files to post\n\n" );
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
     fprintf( stderr, "failed to establish sr context\n");
     return(1);
  }

  // i set before...
  for( ; i < argc ; i++ ) { 
     sr_post(sr_c,argv[i]);
  }

  sr_context_close(sr_c);

  return 0;
}
