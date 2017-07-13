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
  It has a lot of limitations, and no error checking for now.

  how to use:

  In a shell, to use an sr_config(7) style configuration file:
  set the SR_POST_CONFIG environment variable to the name of the
  file to use.

 
 limitations:
    - Doesn't support document_root, absolute paths posted.
    - Doesn't support cache.
    - does support csv for url, to allow load spreading.
    - seems to be about 30x faster than python version.

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
#include <linux/limits.h>

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


#define HDRMAX (20)
amqp_table_entry_t headers[HDRMAX];

int hdrcnt = 0 ;

void header_reset() {
    hdrcnt = 0 ;
}

void header_add( char *tag, const char * value ) {

  if ( hdrcnt >= HDRMAX ) 
  {
     fprintf( stderr, "ERROR too many headers! ignoring %s=%s\n", tag, value );
     return;
  }
  headers[hdrcnt].key = amqp_cstring_bytes(tag);
  headers[hdrcnt].value.kind = AMQP_FIELD_KIND_UTF8;
  headers[hdrcnt].value.value.bytes = amqp_cstring_bytes(value);
  hdrcnt++;
  //fprintf( stderr, "Adding header: %s=%s hdrcnt=%d\n", tag, value, hdrcnt );
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

   case '0' : case 'R' : case 'L' :  // null checksum, removal, or symlinks.
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
       //fprintf( stderr, "checksumming start: %lu to %lu\n", start, end );
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
       //fprintf( stderr, "checksumming start: %lu to %lu\n", start, end );
       while ( start < end ) 
       {
           how_many_to_read= ( SUMBUFSIZE < (end-start) ) ? SUMBUFSIZE : (end-start) ;

           bytes_read=read(fd,buf, how_many_to_read );           

           //fprintf( stderr, "checksumming how_many_to_read: %lu bytes_read: %lu\n", 
           //    how_many_to_read, bytes_read );

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

void set_url( char* m, char* spec ) 
  /* append a url spec to the given message buffer
   */
{
  static const char* cu_url = NULL;
  char *sp;

  if ( strchr(spec,',') ) {
     //fprintf( stderr, "1 picking url, set=%s, cu=%s\n", spec, cu_url );
     if (cu_url) {
         cu_url = strchr(cu_url,','); // if there is a previous one, pick the next one.
         //fprintf( stderr, "2 picking url, set=%s, cu=%s\n", spec, cu_url );
     }
     if (cu_url) {
         cu_url++;                    // skip to after the comma.
         //fprintf( stderr, "3 picking url, set=%s, cu=%s\n", spec, cu_url );
     } else {
         cu_url = spec ;                // start from the beginning.
         //fprintf( stderr, "4 picking url, set=%s, cu=%s\n", spec, cu_url );
     }
     sp=strchr(cu_url,',');
     if (sp) strncat( m, cu_url, sp-cu_url );
     else strcat( m, cu_url );
  } else  {
     strcat( m, spec );
  }
}

unsigned long int set_blocksize( long int bssetting, size_t fsz )
{
      unsigned long int tfactor =  (50*1024*1024) ;

      switch( bssetting )
      {
        case 0: // autocompute 
             if ( fsz > 100*tfactor ) return( 10*tfactor );
             else if ( fsz > 10*tfactor ) return( (unsigned long int)( (fsz+9)/10) );
             else if ( fsz > tfactor ) return( (unsigned long int)( (fsz+2)/3) ) ;
             else return(fsz);
             break;

        case 1: // send file as one piece.
             return(fsz);
             break;

       default: // partstr=i
             return(bssetting);
             break;
      }

}


struct sr_context *sr_context_connect(struct sr_context *sr_c) {

 /* set up a connection given a context.
  */

  signed int status;
  amqp_rpc_reply_t reply;
  amqp_channel_open_ok_t *open_status;

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
     fprintf( stderr, "sr_context_connect succeeded!\n" );

  return(sr_c);
}


struct sr_context *sr_context_init_config(struct sr_config_t *sr_cfg) 
{

  struct sr_context *sr_c;
  char *buf;
  int len;
  struct timespec ts;

  // seed for random checksums... random enough...
  clock_gettime( CLOCK_REALTIME , &ts);
  srandom(ts.tv_nsec);

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
  {
     fprintf( stderr, "debug broker: %s://%s:%s@%s:%d\n", 
       sr_c->scheme, sr_c->user, (sr_c->password)?"<pw>":"<null>", sr_c->hostname, sr_c->port );
  }
  
  return( sr_c );

}

void sr_consume_init(struct sr_context *sr_c) 
 /*
    declare a queue and bind it to the configured exchange.

  */
{
  amqp_rpc_reply_t reply;
  amqp_boolean_t  passive = 0;
  amqp_boolean_t  durable = 1;
  amqp_boolean_t  exclusive = 0;
  amqp_boolean_t  auto_delete = 0;
  struct sr_topic_t *t;

  amqp_queue_declare_ok_t *r = amqp_queue_declare( 
             sr_c->conn, 
             1, 
             amqp_cstring_bytes(sr_c->cfg->queuename), 
             passive,
             durable, 
             exclusive, 
             auto_delete, 
             amqp_empty_table 
  );
  /* FIXME how to parse r for error? */

  reply = amqp_get_rpc_reply(sr_c->conn);
  if (reply.reply_type != AMQP_RESPONSE_NORMAL ) {
      amqp_reply_print(reply, "queue declare failed");
      return;
  }

  /*
    FIXME: topic bindings are not working properly...
   */
  if ( ! sr_c->cfg->topics ) 
  {
      add_topic(sr_c->cfg, "#" );
  }
  //fprintf( stderr, " topics: %p, string=+%s+\n", sr_c->cfg->topics,  sr_c->cfg->topics  );

  for( t = sr_c->cfg->topics; t ; t=t->next )
  {
      if (sr_c->cfg->debug) 
          fprintf( stderr, " binding queue: %s to exchange: %s topic: %s\n",
              sr_c->cfg->queuename, sr_c->cfg->exchange, t->topic );
      amqp_queue_bind(sr_c->conn, 1, 
            amqp_cstring_bytes(sr_c->cfg->queuename), 
            amqp_cstring_bytes(sr_c->cfg->exchange), 
            amqp_cstring_bytes(t->topic),
            amqp_empty_table);

      reply = amqp_get_rpc_reply(sr_c->conn);
      if (reply.reply_type != AMQP_RESPONSE_NORMAL ) {
          amqp_reply_print(reply, "binding failed");
          return;
      }
  }
}



void sr_consume(struct sr_context *sr_c) 
 /*
    read messages from the queue. dump to stdout in json format.

  */
{
    amqp_rpc_reply_t reply;
    amqp_frame_t frame;
    int result;
    char buf[2*PATH_MAX];

    amqp_basic_deliver_t *d;
    amqp_basic_properties_t *p;
    int is_report;
    char *tok;
    size_t body_target;
    size_t body_received;

    amqp_basic_consume(sr_c->conn, 1, 
          amqp_cstring_bytes(sr_c->cfg->queuename), 
          amqp_empty_bytes, // consumer_tag
          0,  // no_local
          1,  // no_ack
          0,  // exclusive
          amqp_empty_table);

    reply = amqp_get_rpc_reply(sr_c->conn);
    if (reply.reply_type != AMQP_RESPONSE_NORMAL ) 
    {
        amqp_reply_print(reply, "consume failed");
        return;
    }

    while (1) {

        amqp_maybe_release_buffers(sr_c->conn);
        result = amqp_simple_wait_frame(sr_c->conn, &frame);

        //fprintf( stderr, "Result %d\n", result);
        if (result < 0) break;
  
        //fprintf( stderr, "Frame type %d, channel %d\n", frame.frame_type, frame.channel);

        if (frame.frame_type != AMQP_FRAME_METHOD) continue;
  
        //fprintf( stderr, "Method %s\n", amqp_method_name(frame.payload.method.id));

        if (frame.payload.method.id != AMQP_BASIC_DELIVER_METHOD) continue;
  
        d = (amqp_basic_deliver_t *) frame.payload.method.decoded;

        /*
        fprintf( stderr, "Delivery %u, exchange %.*s routingkey %.*s\n",
               (unsigned) d->delivery_tag,
               (int) d->exchange.len, (char *) d->exchange.bytes,
               (int) d->routing_key.len, (char *) d->routing_key.bytes);
         */ 
        fprintf( stdout, " {\n\t\"exchange\": \"%.*s\",\n\t\"routingkey\": \"%.*s\",\n",
               (int) d->exchange.len, (char *) d->exchange.bytes,
               (int) d->routing_key.len, (char *) d->routing_key.bytes);
  
        is_report = ( ! strncmp( d->routing_key.bytes, "v02.report", 10 )  );
   
        result = amqp_simple_wait_frame(sr_c->conn, &frame);

        if (result < 0) break;
  
        if (frame.frame_type != AMQP_FRAME_HEADER) {
            fprintf(stderr, "Expected header!");
            abort();
        }

        p = (amqp_basic_properties_t *) frame.payload.properties.decoded;

        /*
        if (p->_flags & AMQP_BASIC_CONTENT_TYPE_FLAG) 
            fprintf( stderr, "Content-type: %.*s\n",
                 (int) p->content_type.len, (char *) p->content_type.bytes);

        fprintf( stderr, "Num headers received %d \n", p->headers.num_entries);
        */
        for ( int i=0; i < p->headers.num_entries; i++ ) 
        {
            if ( p->headers.entries[i].value.kind == AMQP_FIELD_KIND_UTF8 )
            {
                fprintf( stdout, "\t\"%.*s\": \"%.*s\",\n",
                     (int) p->headers.entries[i].key.len, 
                     (char *) p->headers.entries[i].key.bytes,
                     (int) p->headers.entries[i].value.value.bytes.len,
                     (char *) p->headers.entries[i].value.value.bytes.bytes
                 );
            } else
                fprintf( stderr, "header not UTF8\n");
        }

        body_target = frame.payload.properties.body_size;
        body_received = 0;
  
        while (body_received < body_target) {
            result = amqp_simple_wait_frame(sr_c->conn, &frame);

            if (result < 0) break;
    
            if (frame.frame_type != AMQP_FRAME_BODY) {
                fprintf(stderr, "Expected body!");
                abort();
            }
    
            body_received += frame.payload.body_fragment.len;
            //assert(body_received <= body_target);
    
            strncpy( buf, (char*) frame.payload.body_fragment.bytes, (int)frame.payload.body_fragment.len );
            tok = strtok(buf," ");
            fprintf( stdout, "\t\"datestamp\" : \"%s\",\n", tok);
            tok = strtok(NULL," ");
            fprintf( stdout, "\t\"url\" : \"%s\", \n", tok);
            tok = strtok(NULL," ");
            fprintf( stdout, "\t\"path\" : \"%s\", \n", tok);
            if (is_report) {
                tok = strtok(NULL," ");
                fprintf( stdout, "\t\"statuscode\" : \"%s\", \n", tok);
                tok = strtok(NULL," ");
                fprintf( stdout, "\t\"consumingurl\" : \"%s\", \n", tok);
                tok = strtok(NULL," ");
                fprintf( stdout, "\t\"consuminguser\" : \"%s\", \n", tok);
                tok = strtok(NULL," ");
                fprintf( stdout, "\t\"duration\" : \"%s\", \n", tok);
            }
            fprintf( stdout, " }\n");
            
            /*
            fprintf( stdout, "\t\"body\" : \"%.*s\"\n }\n",
                 (int) frame.payload.body_fragment.len, 
                 (char *)frame.payload.body_fragment.bytes 
            );
            */
        }
  
        if (body_received != body_target) break;
          /* Can only happen when amqp_simple_wait_frame returns <= 0 */
          /* We break here to close the connection */
    }
    return;   
}

void sr_post(struct sr_context *sr_c, const char *pathspec, struct stat *sb ) {

  char routingkey[255];
  char message_body[1024];
  char partstr[255];
  char modebuf[6];
  char linkstr[PATH_MAX];
  char fn[PATH_MAX];
  int  linklen;
  char atimestr[18];
  char mtimestr[18];
  char sumalgo;
  signed int status;
  int commonhdridx;
  unsigned long block_size;
  unsigned long block_count;
  unsigned long block_num;
  unsigned long block_rem;
  amqp_table_t table;
  amqp_basic_properties_t props;
  struct sr_mask_t *mask;
  char psc;                     // part strategy character.

  if (*pathspec != '/' ) // need absolute path.
  { 
      getcwd( fn, PATH_MAX);
      strcat( fn, "/" );
      strcat( fn, pathspec);
  } else {
      strcpy( fn, pathspec );
  }

  if ( (sr_c->cfg!=NULL) && sr_c->cfg->debug )
     fprintf( stderr, "sr_cpost called with: %s sb=%p\n", fn, sb );

  /* apply the accept/reject clauses */
  mask = isMatchingPattern(sr_c->cfg, fn);

  if ( (mask && !(mask->accepting)) || (!mask && !(sr_c->cfg->accept_unmatched)) )
  {
      if ( (sr_c->cfg) && sr_c->cfg->debug ) fprintf( stderr, "rejecting: %s\n", fn );
      return;
  }
  if ( sb && S_ISDIR(sb->st_mode) ) {
      if ( (sr_c->cfg) && sr_c->cfg->debug )
          fprintf( stderr, "sr_cpost cannot post directories: %s\n", fn );
      return;
  }
  if ( (sr_c->cfg) && sr_c->cfg->debug )
     fprintf( stderr, "sr_cpost accepted posting to exchange:  %s\n", sr_c->exchange );

  strcpy(routingkey,"v02.post");

  strcat(routingkey,fn);
  for( int i=8; i< strlen(routingkey); i++ )
      if ( routingkey[i] == '/' ) routingkey[i]='.';

  if ( (sr_c->cfg) && sr_c->cfg->debug )
     fprintf( stderr, "posting, routingkey: %s\n", routingkey );

  strcpy( message_body, time2str(NULL));
  strcat( message_body, " " );
  set_url( message_body, sr_c->cfg->url );
  strcat( message_body, " " );
  strcat( message_body, fn);

  if ( (sr_c->cfg) && sr_c->cfg->debug )
     fprintf( stderr, "sr_cpost message_body: %s sumalgo:%c sb:%p event:%x\n", 
          message_body, sr_c->cfg->sumalgo, sb, sr_c->cfg->events );

  header_reset();

  header_add( "to_clusters", sr_c->to );

  sumalgo = sr_c->cfg->sumalgo;
  block_count = 1;

  if ( !sb ) {
      if ( ! ((sr_c->cfg->events)&SR_DELETE) ) return;
      sumalgo='R';
  } else if ( S_ISLNK(sb->st_mode) ) {
      if ( ! ((sr_c->cfg->events)&SR_LINK) ) return;
      sumalgo='L';
      linklen = readlink( fn, linkstr, PATH_MAX );
      linkstr[linklen]='\0';
      header_add( "link", linkstr );

  } else {  /* regular files, add mode and determine block parameters */
      if ( ! ((sr_c->cfg->events)&(SR_CREATE|SR_MODIFY)) ) return;

      if ( access( fn, R_OK ) ) return; // will not be able to checksum if we cannot read.

      strcpy( atimestr, time2str(&(sb->st_atim)));
      header_add( "atime", atimestr);

      strcpy( mtimestr, time2str(&(sb->st_mtim)));
      header_add( "mtime", mtimestr );
      sprintf( modebuf, "%04o", (sb->st_mode & 07777) );
      header_add( "mode", modebuf);
      block_size = set_blocksize( sr_c->cfg->blocksize, sb->st_size );
      psc = (block_size < sb->st_size )? 'i':'1' ;

      if ( block_size == 0 ) {
          block_rem = 0;
      } else {
          block_rem = sb->st_size%block_size ;
          block_count = ( sb->st_size / block_size ) + ( block_rem?1:0 );
      }
  }
 
  commonhdridx = hdrcnt; // save location of headers common to all messages.
  block_num = 0;

  while ( block_num < block_count ) 
  { /* Footnote 1: FIXME: posting partitioned parts not implemented, see end notes */
      hdrcnt = commonhdridx;

      if ( ( sumalgo != 'L' ) && ( sumalgo != 'R' ) )  {

          sprintf( partstr, "%c,%lu,%lu,%lu,%lu", psc, block_size, 
              block_count, block_rem, block_num );
          header_add( "parts", partstr );
      }

      if (! set_sumstr( sumalgo, fn, block_size, block_count, block_rem, block_num ) ) 
      {
         fprintf( stderr, "sr_cpost unable to generate %c checksum for: %s\n", sumalgo, fn );
         return;
      }
      header_add( "sum", sumstr );

      table.num_entries = hdrcnt;
      table.entries=headers;

      props._flags = AMQP_BASIC_HEADERS_FLAG | AMQP_BASIC_CONTENT_TYPE_FLAG | AMQP_BASIC_DELIVERY_MODE_FLAG;
      props.content_type = amqp_cstring_bytes("text/plain");
      props.delivery_mode = 2; /* persistent delivery mode */
      props.headers = table;

      status = amqp_basic_publish(sr_c->conn, 1, amqp_cstring_bytes(sr_c->exchange), 
          amqp_cstring_bytes(routingkey), 0, 0, &props, amqp_cstring_bytes(message_body));

      block_num++;

      if ( status < 0 ) 
          fprintf( stderr, "ERROR: sr_cpost: publish of block %lu of %lu failed.\n", block_num, block_count );
      else if ( (sr_c->cfg) && sr_c->cfg->debug )
          fprintf( stderr, "posting, publish block %lu of %lu.\n", block_num, block_count );

  }
}

void sr_context_close(struct sr_context *sr_c) {

  amqp_rpc_reply_t reply;
  signed int status;

  reply = amqp_channel_close(sr_c->conn, 1, AMQP_REPLY_SUCCESS);
  if (reply.reply_type != AMQP_RESPONSE_NORMAL) {
      fprintf( stderr, "sr_cpost: amqp channel close failed.\n");
      return;
  }

  reply = amqp_connection_close(sr_c->conn, AMQP_REPLY_SUCCESS);
  if (reply.reply_type != AMQP_RESPONSE_NORMAL) {
      fprintf( stderr, "sr_cpost: amqp connection close failed.\n");
      return;
  }

  status = amqp_destroy_connection(sr_c->conn);
  if (status < 0 ) 
  {
      fprintf( stderr, "sr_cpost: amqp context close failed.\n");
      return;
  }

}

void connect_and_post(const char *fn) {

  static struct sr_config_t sr_cfg; 
  static int config_read = 0;
  struct sr_mask_t *mask; 
  struct sr_context *sr_c = NULL;
  char *setstr;
  struct stat sb;

  if ( !fn ) 
  {
     fprintf( stderr, "post null\n" );
     return;
  }

  setstr = getenv( "SR_POST_CONFIG" ) ;
  if ( setstr != NULL )
  { 
     if ( config_read == 0 ) 
     {
       sr_config_init(&sr_cfg);
       sr_config_read(&sr_cfg,setstr);
       config_read=1;
     }
     sr_c = sr_context_init_config(&sr_cfg);
  } 
  if (!sr_c) return;
 
  mask = isMatchingPattern(&sr_cfg, fn);
  if ( (mask && !(mask->accepting)) || (!mask && !(sr_cfg.accept_unmatched)) )
  { //reject.
      fprintf( stderr, "mask: %p, mask->accepting=%d accept_unmatched=%d\n", 
            mask, mask->accepting, sr_cfg.accept_unmatched );
      if (sr_cfg.debug) fprintf( stderr, "sr_cpost rejected 2: %s\n", fn );
      return;
  }

  sr_c = sr_context_connect(sr_c);
  if (sr_c == NULL ) 
  {
    fprintf( stderr, "failed to parse AMQP broker settings\n");
    return;
  }
  if ( lstat( fn, &sb ) ) sr_post( sr_c, fn, NULL );
  else sr_post( sr_c, fn, &sb );
  sr_context_close(sr_c);
}



