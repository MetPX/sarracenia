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

  In a shell, to use an sr_config(7) style configuration file:
  set the SR_POST_CONFIG environment variable to the name of the
  file to use.

 limitations:
    - Doesn't support document_root, absolute paths posted.

 */
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <time.h>
#include <fcntl.h>

#include <openssl/md5.h>
#include <openssl/sha.h>

#include <stdint.h>
#include <amqp_tcp_socket.h>
#include <amqp_ssl_socket.h>
#include <amqp.h>
#include <amqp_framing.h>

#include "sr_context.h"

char time2str_result[18];

char *time2str( struct timespec *tin ) {
   /* turn a timespec into an 18 character sr_post(7) conformant time stamp string.
      if argument is NULL, then the string should correspond to the current system time.
    */
   struct tm s;
   time_t when;
   struct timespec ts;
   long msec;

   if ( tin == NULL ) {
     clock_gettime( CLOCK_REALTIME , &ts);
     when = ts.tv_sec;
     msec = ts.tv_nsec/1000000 ;
   } else {
     when = tin->tv_sec;
     msec = tin->tv_nsec/1000000 ;
   }

   gmtime_r(&when,&s);
   /*                YYYY  MM  DD  hh  mm  ss */
   sprintf( time2str_result, "%04d%02d%02d%02d%02d%02d.%03ld", s.tm_year+1900, s.tm_mon+1, 
        s.tm_mday, s.tm_hour, s.tm_min, s.tm_sec, msec );
 
   return(time2str_result);
}


amqp_table_entry_t headers[10];
int hdrcnt;

void add_header( char *tag, const char * value ) {

  headers[hdrcnt].key = amqp_cstring_bytes(tag);
  headers[hdrcnt].value.kind = AMQP_FIELD_KIND_UTF8;
  headers[hdrcnt].value.value.bytes = amqp_cstring_bytes(value);
  hdrcnt++;

}

void amqp_error_print(int x, char const *context)
{
  if (x < 0) {
    fprintf(stderr, "%s: %s\n", context, amqp_error_string2(x));
    return;
  }
}

void amqp_reply_print(amqp_rpc_reply_t x, char const *context)
{
  switch (x.reply_type) {
  case AMQP_RESPONSE_NORMAL:
    return;

  case AMQP_RESPONSE_NONE:
    fprintf(stderr, "%s: missing RPC reply type!\n", context);
    break;

  case AMQP_RESPONSE_LIBRARY_EXCEPTION:
    fprintf(stderr, "%s: %s\n", context, amqp_error_string2(x.library_error));
    break;
  
  case AMQP_RESPONSE_SERVER_EXCEPTION:
    switch (x.reply.id) {
    case AMQP_CONNECTION_CLOSE_METHOD: {
      amqp_connection_close_t *m = (amqp_connection_close_t *) x.reply.decoded;
      fprintf(stderr, "%s: server connection error %uh, message: %.*s\n",
              context,
              m->reply_code,
              (int) m->reply_text.len, (char *) m->reply_text.bytes);
      break;
    }
    case AMQP_CHANNEL_CLOSE_METHOD: {
      amqp_channel_close_t *m = (amqp_channel_close_t *) x.reply.decoded;
      fprintf(stderr, "%s: server channel error %uh, message: %.*s\n",
              context,
              m->reply_code,
              (int) m->reply_text.len, (char *) m->reply_text.bytes);
      break;
    }
    default:
      fprintf(stderr, "%s: unknown server error, method id 0x%08X\n", context, x.reply.id);
      break;
    }
    break;
  }
}

// SHA512 being the longest digest...
char sumstr[ 2 * SHA512_DIGEST_LENGTH + 3 ];

void hash2sumstr( unsigned char *h, int l )
{
  int i;
  for(i=1; i < l+1; i++ )
     //printf( "h[%d] = %u\n", i, (unsigned char)h[i] );
     sprintf( &(sumstr[i*2]), "%02x", (unsigned char)h[i-1]);
  sumstr[2*i]='\0';
}

#define SUMBUFSIZE (4096*1024)

char *set_sumstr( char algo, const char* fn, unsigned long block_size, unsigned long block_count, 
       unsigned long block_rem, unsigned long block_num )
 /* 
   return a correct sumstring (assume it is big enough)  as per sr_post(7)
   algo = 
     '0' - no checksum, value is random.
     'd' - md5sum of block.
     'n' - md5sum of filename (fn).
     's' - sha512 sum of block.

   block starts at block_size * block_num, and ends 
  */
{
   MD5_CTX md5ctx;
   SHA512_CTX shactx;
   unsigned char hash[SHA512_DIGEST_LENGTH]; // Assumed longest possible hash.

   static int fd;
   static char buf[SUMBUFSIZE];
   long bytes_read ; 
   long how_many_to_read;
   char *just_the_name;

   unsigned long start = block_size * block_num ;
   unsigned long end;

   end =  (block_num == (block_count-1)) ? (start + block_rem) : (start +block_size );

   sumstr[0]=algo;
   sumstr[1]=',';
   sumstr[2]='\0'; 
   switch (algo) {

   case '0' :
       sprintf( sumstr+2, "%ld", random()%1000 );
       break;

   case 'd' :
       MD5_Init(&md5ctx);

       // keep file open through repeated calls.
       if ( ! (fd > 0) ) fd = open( fn, O_RDONLY );
       if ( fd < 0 ) 
       { 
           fprintf( stderr, "unable to read file for checksumming\n" );
           return(NULL);
       } 
       lseek( fd, start, SEEK_SET );
       fprintf( stderr, "checksumming start: %lu to %lu\n", start, end );
       while ( start < end ) 
       {
           how_many_to_read= ( SUMBUFSIZE < (end-start) ) ? SUMBUFSIZE : (end-start) ;

           bytes_read=read(fd,buf, how_many_to_read );           
           if ( bytes_read >= 0 ) 
           {
              MD5_Update(&md5ctx, buf, bytes_read );
              start += bytes_read;
           } else {
              fprintf( stderr, "error reading %s\n", fn );
              break;
           } 
       }

       // close fd, when end of file reached.
       if ( end >= ((block_count-1)*block_size+block_rem)) close(fd);

       MD5_Final(hash, &md5ctx);
       hash2sumstr(hash,MD5_DIGEST_LENGTH); 
       break;

   case 'n' :
       MD5_Init(&md5ctx);
       just_the_name = rindex(fn,'/')+1;
       MD5_Update(&md5ctx, just_the_name, strlen(just_the_name) );
       MD5_Final(hash, &md5ctx);
       hash2sumstr(hash,MD5_DIGEST_LENGTH); 
       break;
       
   case 's' :
       SHA512_Init(&shactx);

       // keep file open through repeated calls.
       if ( ! (fd > 0) ) fd = open( fn, O_RDONLY );
       if ( fd < 0 ) 
       { 
           fprintf( stderr, "unable to read file for checksumming\n" );
           return(NULL);
       } 
       lseek( fd, start, SEEK_SET );
       fprintf( stderr, "checksumming start: %lu to %lu\n", start, end );
       while ( start < end ) 
       {
           how_many_to_read= ( SUMBUFSIZE < (end-start) ) ? SUMBUFSIZE : (end-start) ;

           bytes_read=read(fd,buf, how_many_to_read );           

           fprintf( stderr, "checksumming how_many_to_read: %lu bytes_read: %lu\n", 
               how_many_to_read, bytes_read );

           if ( bytes_read >= 0 ) 
           {
              SHA512_Update(&shactx, buf, bytes_read );
              start += bytes_read;
           } else {
              fprintf( stderr, "error reading %s\n", fn );
              break;
           } 
       }

       // close fd, when end of file reached.
       if ( end >= ((block_count-1)*block_size+block_rem)) close(fd);

       SHA512_Final(hash, &shactx);
       hash2sumstr(hash,SHA512_DIGEST_LENGTH); 
       break;

   default:
       fprintf( stderr, "sum algorithm %c unimplemented\n", algo );
       return(NULL);
   }
   return(sumstr);

}

struct sr_context *sr_context_initialize(struct sr_context *sr_c) {

 /* set up a connection given a context.
  */

  signed int status;
  amqp_rpc_reply_t reply;
  amqp_channel_open_ok_t *open_status;

  if ( (sr_c->cfg!=NULL) && sr_c->cfg->debug )
     fprintf( stderr, "sr_context_initialize, new_connection AMQP_VERSION=%08x\n", AMQP_VERSION );

  sr_c->conn = amqp_new_connection();

  if ( !strcmp(sr_c->scheme,"amqps") ) {
     sr_c->socket = amqp_ssl_socket_new(sr_c->conn);
     if (!(sr_c->socket)) {
        fprintf( stderr, "failed to create SSL amqp client socket.\n" );
        return(NULL);
     }

     amqp_ssl_socket_set_verify_peer(sr_c->socket, 0);
     amqp_ssl_socket_set_verify_hostname(sr_c->socket, 0);

  } else {
     sr_c->socket = amqp_tcp_socket_new(sr_c->conn);
     if (!(sr_c->socket)) {
        fprintf( stderr, "failed to create AMQP client socket. \n" );
        return(NULL);
     }
  }

  status = amqp_socket_open(sr_c->socket, sr_c->hostname, sr_c->port);
  if (status < 0) {
    amqp_error_print(status, "failed opening AMQP socket");
    return(NULL);
  }

  reply = amqp_login(sr_c->conn, "/", 0, 131072, 0, AMQP_SASL_METHOD_PLAIN, sr_c->user, sr_c->password);
  if (reply.reply_type != AMQP_RESPONSE_NORMAL ) {
    amqp_reply_print(reply, "failed AMQP login");
    return(NULL);
  }

  open_status = amqp_channel_open(sr_c->conn, 1);
  if (open_status == NULL ) {
    fprintf(stderr, "failed AMQP amqp_channel_open\n");
    return(NULL);
  }

  reply = amqp_get_rpc_reply(sr_c->conn);
  if (reply.reply_type != AMQP_RESPONSE_NORMAL ) {
    amqp_reply_print(reply, "failed AMQP get_rpc_reply");
    return(NULL);
  }

  if ( (sr_c->cfg!=NULL) && sr_c->cfg->debug )
     fprintf( stderr, "sr_context_initialize, done!\n" );


  return(sr_c);
}


struct sr_context *sr_context_init_config(struct sr_config_t *sr_cfg) {

  struct sr_context *sr_c;
  char *buf;
  int len;

  sr_c = (struct sr_context *)malloc(sizeof(struct sr_context));

  sr_c->cfg = sr_cfg;

  if (!(sr_cfg->broker_specified)) 
  {
    fprintf( stderr, "no broker given\n" );
    return( NULL );
  }

  sr_c->scheme = sr_cfg->broker.scheme.first ;
  sr_c->hostname = sr_cfg->broker.hostText.first ;
  
  if ( sr_cfg->broker.portText.first == NULL ) {
     if ( !strcmp(sr_c->scheme,"amqps") ) sr_c->port = 5671;
     else sr_c->port= 5672;
  } else sr_c->port = atol( sr_cfg->broker.portText.first );
  

  if (sr_cfg->exchange==NULL) 
  {
    fprintf( stderr, "no exchange given\n" );
    return( NULL );
  }

  sr_c->exchange = sr_cfg->exchange ;
  
  len = strcspn(sr_cfg->broker.userInfo.first, ":");

  buf = (char *)malloc(len+1);

  strncpy(buf, sr_cfg->broker.userInfo.first, len );

  sr_c->user = buf;
  sr_c->password = sr_cfg->broker.userInfo.first + len +1 ;
  sr_c->url = sr_cfg->url;

  sr_c->to = ( sr_cfg->to == NULL ) ? sr_cfg->broker.hostText.first : sr_cfg->to;
  sr_c->socket = NULL;

  if ( (sr_c->cfg!=NULL) && sr_c->cfg->debug )
     fprintf( stderr, "debug broker: %s://%s:%s@%s:%d\n", 
       sr_c->scheme, sr_c->user, (sr_c->password)?"<pw>":"<null>", sr_c->hostname, sr_c->port );

  return( sr_context_initialize(sr_c) );

}


void sr_post(struct sr_context *sr_c, const char *fn ) {

  char routingkey[255];
  char message_body[1024];
  char partstr[255];
  struct stat sb;
  signed int status;
  int parthdridx;
  unsigned long block_count;
  unsigned long block_num;
  unsigned long block_rem;
  unsigned long tfactor;
  amqp_table_t table;
  amqp_basic_properties_t props;
  struct sr_mask_t *mask;
  char psc; // part strategy character.

  if ( (sr_c->cfg!=NULL) && sr_c->cfg->debug )
     fprintf( stderr, "sr_post called with: %s\n", fn );

  /* apply the accept/reject clauses */
  mask = isMatchingPattern(sr_c->cfg, fn);

  if ( (mask && !(mask->accepting)) || !(!mask && sr_c->cfg->accept_unmatched ))
  { //reject.
      if ( (sr_c->cfg!=NULL) && sr_c->cfg->debug )
         fprintf( stderr, "sr_post rejected: %s\n", fn );
      return;
  }

  if ( (sr_c->cfg!=NULL) && sr_c->cfg->debug )
     fprintf( stderr, "sr_post accepted posting to exchange:  %s\n", sr_c->exchange );

  strcpy(routingkey,"v02.post");
  if (fn[0] != '/' ) strcat(routingkey,".");

  strcat(routingkey,fn);
  for( int i=8; i< strlen(routingkey); i++ )
      if ( routingkey[i] == '/' ) routingkey[i]='.';

  if ( (sr_c->cfg!=NULL) && sr_c->cfg->debug )
     fprintf( stderr, "posting, routingkey: %s\n", routingkey );

  stat(fn,&sb);

  strcpy( message_body, time2str(NULL));
  strcat( message_body, " " );
  strcat( message_body, sr_c->url );
  strcat( message_body, " " );
  strcat( message_body, fn);

  if ( (sr_c->cfg!=NULL) && sr_c->cfg->debug )
     fprintf( stderr, "posting, message_body: %s\n", message_body );

  hdrcnt=0;

  add_header( "atime", time2str(&(sb.st_atim)));
  add_header( "mtime", time2str(&(sb.st_mtim)));
  add_header( "to_clusters", sr_c->to );

  if ( (sr_c->cfg!=NULL) && sr_c->cfg->debug )
      fprintf( stderr, "posting, to: %s blocksize=%lu, parts=%c\n", sr_c->to,  
          sr_c->cfg->blocksize, sr_c->cfg->parts+'0' );


  switch( sr_c->cfg->parts )
  {
    case 0: // autocompute 
         tfactor =  ( sr_c->cfg->blocksize > 2 )?(sr_c->cfg->blocksize):(50*1024*1024) ;
         if ( sb.st_size > 100*tfactor ) sr_c->cfg->blocksize= 10*tfactor;
         else if ( sb.st_size > 10*tfactor ) sr_c->cfg->blocksize= (unsigned long int)( (sb.st_size+9)/10);
         else if ( sb.st_size > tfactor ) sr_c->cfg->blocksize= (unsigned long int)( (sb.st_size+2)/3) ;
         else sr_c->cfg->blocksize=sb.st_size;
         psc='i' ;
         break;

    case 1: // send file as one piece.
         sr_c->cfg->blocksize=sb.st_size;
         psc='1' ;
         break;

    case 2: // partstr=p
         psc='p' ;
         break;

   default: // partstr=i
         psc='i' ;
         break;
  }

  parthdridx = hdrcnt;
  block_rem = sb.st_size%sr_c->cfg->blocksize ;
  block_count = ( sb.st_size / sr_c->cfg->blocksize ) + ( block_rem?1:0 );
  block_num = 0;
 
  while ( block_num < block_count ) 
  {
      hdrcnt = parthdridx;
      sprintf( partstr, "%c,%lu,%lu,%lu,%lu", psc, sr_c->cfg->blocksize, 
             block_count, block_rem, block_num );
      add_header( "parts", partstr );

      if (! set_sumstr( sr_c->cfg->sumalgo, fn, sr_c->cfg->blocksize, block_count, block_rem, block_num ) ) 
      {
         fprintf( stderr, "sr_post unable to generate %c checksum for: %s\n", sr_c->cfg->sumalgo, fn );
         return;
      }
      add_header( "sum", sumstr );

      if ( (sr_c->cfg!=NULL) && sr_c->cfg->debug )
         fprintf( stderr, "posting, parts: %s, sumstr: %s\n", partstr, sumstr );

      table.num_entries = hdrcnt;
      table.entries=headers;
    
      props._flags = AMQP_BASIC_HEADERS_FLAG | AMQP_BASIC_CONTENT_TYPE_FLAG | AMQP_BASIC_DELIVERY_MODE_FLAG;
      props.content_type = amqp_cstring_bytes("text/plain");
      props.delivery_mode = 2; /* persistent delivery mode */
      props.headers = table;

      status = amqp_basic_publish(sr_c->conn,
                                    1,
                                    amqp_cstring_bytes(sr_c->exchange),
                                    amqp_cstring_bytes(routingkey),
                                    0,
                                    0,
                                    &props,
                                    amqp_cstring_bytes(message_body));
     block_num++;

     /*
        FIXME: possible memory leak here where amqp_cstring_bytes conversion causes alloc on each post?
        need to look into it. would need to free after each publish, including sum and part headers
        which get re-written.
      */

     if ( status < 0 ) 
         fprintf( stderr, "ERROR: sr_post: publish of block %lu of %lu failed.\n", block_num, block_count );
     else if ( (sr_c->cfg!=NULL) && sr_c->cfg->debug )
         fprintf( stderr, "posting, publish block %lu of %lu.\n", block_num, block_count );

  }



}

void sr_context_close(struct sr_context *sr_c) {

  amqp_rpc_reply_t reply;
  signed int status;

  reply = amqp_channel_close(sr_c->conn, 1, AMQP_REPLY_SUCCESS);
  if (reply.reply_type != AMQP_RESPONSE_NORMAL) {
      fprintf( stderr, "sr_post: amqp channel close failed.\n");
  }

  reply = amqp_connection_close(sr_c->conn, AMQP_REPLY_SUCCESS);
  if (reply.reply_type != AMQP_RESPONSE_NORMAL) {
      fprintf( stderr, "sr_post: amqp connection close failed.\n");
  }

  status = amqp_destroy_connection(sr_c->conn);
  if (status < 0 ) {
      fprintf( stderr, "sr_post: amqp context close failed.\n");
  }

}

void connect_and_post(const char *fn) {

  static struct sr_config_t sr_cfg; 
  static int config_read = 0;
  struct sr_context *sr_c = NULL;
  char *setstr;

  setstr = getenv( "SR_POST_CONFIG" ) ;
  if ( setstr != NULL ){ 
     if ( config_read == 0 ) {
       sr_config_init(&sr_cfg);
       sr_config_read(&sr_cfg,setstr);
       config_read=1;
     }
     sr_c = sr_context_init_config(&sr_cfg);
  } 

  if (sr_c == NULL ) {
    fprintf( stderr, "failed to parse AMQP broker settings\n");
    return;
  }
  sr_post( sr_c, fn );

  sr_context_close(sr_c);

}


