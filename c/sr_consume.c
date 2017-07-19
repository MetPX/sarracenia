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

#include "sr_consume.h"


static struct sr_message_t msg;

int sr_consume_cleanup(struct sr_context *sr_c)
{
  amqp_rpc_reply_t reply;

  amqp_queue_delete( sr_c->conn, 1, amqp_cstring_bytes(sr_c->cfg->queuename), 0, 0 );

  reply = amqp_get_rpc_reply(sr_c->conn);
  if (reply.reply_type != AMQP_RESPONSE_NORMAL ) {
      sr_amqp_reply_print(reply, "queue delete failed");
      return(0);
  }
  return(1);
}

int sr_consume_setup(struct sr_context *sr_c) 
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
      sr_amqp_reply_print(reply, "queue declare failed");
      return(0);
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
          sr_amqp_reply_print(reply, "binding failed");
          return(0);
      }
  }
  return(1);
}


void assign_field( const char* key, char *value )
 /* Assign the value of the field given by key to the corresponding member
    of the static msg struct.
  */
{
     char *s;

     //fprintf( stderr, "parsing: \"%s\" : \"%s\"\n", key, value );
     if ( !strcmp(key,"parts") ) {
         //FIXME: no error checking, invalid parts header will cause a bobo.
         msg.parts_s=value[0];
         s=strtok(&(value[2]),",");
         msg.parts_blksz = atol(s);
         s=strtok(NULL,",");
         msg.parts_blkcount = atol(s);
         s=strtok(NULL,",");
         msg.parts_rem = atol(s);
         s=strtok(NULL,",");
         msg.parts_num = atol(s);
     } else if ( !strcmp(key,"mode") ) {
         msg.mode=strtoul( value, NULL, 8);
     } else if ( !strcmp(key,"to_clusters") ) {
         strcpy(msg.to_clusters,value); 
     } else if ( !strcmp(key,"atime") ) {
         strcpy(msg.atime,value); 
     } else if ( !strcmp(key,"mtime") ) {
         strcpy(msg.mtime,value); 
     } else if ( !strcmp(key,"sum") ) {
         strcpy(msg.sum,value); 
     } else if ( !strcmp(key,"url") ) {
         strcpy(msg.url,value); 
     } else if ( !strcmp(key,"path") ) {
         strcpy(msg.path,value); 
     }

}

void json_dump_strheader(char *tag, char*value)
{
    printf( "\"%s\": \"%s\"", tag, value );
}

void sr_message_2json(struct sr_message_t *m)
{
     printf( "[" );
     printf( " \"%s\", {", m->routing_key );
     json_dump_strheader( "atime", m->atime );
     printf( ", " );
     printf( "\"mode\": \"%04o\"", m->mode );
     printf( ", " );
     json_dump_strheader( "mtime", m->mtime );
     printf( ", " );
     printf( "\"parts\": \"%c,%ld,%ld,%ld,%ld\"", 
           m->parts_s, m->parts_blksz, m->parts_blkcount, m->parts_rem, m->parts_num );
     printf( ", " );
     json_dump_strheader( "sum", m->sum );
     printf( ", " );
     json_dump_strheader( "to_clusters", m->to_clusters );
     printf( ", \"%s %s  %s\"", m->datestamp, m->url, m->path );
     printf( "]\n" );
}


struct sr_message_t *sr_consume(struct sr_context *sr_c) 
 /*
    read messages from the queue. dump to stdout in json format.

  */
{
    amqp_rpc_reply_t reply;
    amqp_frame_t frame;
    int result;
    char buf[2*PATH_MAXNUL];

    amqp_basic_deliver_t *d;
    amqp_basic_properties_t *p;
    int is_report;
    char *tok;
    size_t body_target;
    size_t body_received;
    char tag[AMQP_MAX_SS];
    char value[AMQP_MAX_SS];

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
        sr_amqp_reply_print(reply, "consume failed");
        return(NULL);
    }

    amqp_maybe_release_buffers(sr_c->conn);
    result = amqp_simple_wait_frame(sr_c->conn, &frame);

    //fprintf( stderr, "Result %d\n", result);
    if (result < 0) return(NULL);
  
    //fprintf( stderr, "Frame type %d, channel %d\n", frame.frame_type, frame.channel);

    if (frame.frame_type != AMQP_FRAME_METHOD) return(NULL);
  
    //fprintf( stderr, "Method %s\n", amqp_method_name(frame.payload.method.id));

    if (frame.payload.method.id != AMQP_BASIC_DELIVER_METHOD) return(NULL);
  
    d = (amqp_basic_deliver_t *) frame.payload.method.decoded;

    /*
    fprintf( stdout, " {\n\t\"exchange\": \"%.*s\",\n\t\"routingkey\": \"%.*s\",\n",
               (int) d->exchange.len, (char *) d->exchange.bytes,
               (int) d->routing_key.len, (char *) d->routing_key.bytes);
     */
  
    sprintf( msg.exchange, "%.*s",  (int) d->exchange.len, (char *) d->exchange.bytes );
    sprintf( msg.routing_key, "%.*s",  (int) d->routing_key.len, (char *) d->routing_key.bytes );

    is_report = ( ! strncmp( d->routing_key.bytes, "v02.report", 10 )  );
   
    result = amqp_simple_wait_frame(sr_c->conn, &frame);

    if (result < 0) return(NULL);
  
    if (frame.frame_type != AMQP_FRAME_HEADER) 
    {
            fprintf(stderr, "Expected header!");
            abort();
    }

    p = (amqp_basic_properties_t *) frame.payload.properties.decoded;

    for ( int i=0; i < p->headers.num_entries; i++ ) 
    {
            if ( p->headers.entries[i].value.kind == AMQP_FIELD_KIND_UTF8 )
            {
                sprintf( tag, "%.*s",  
                           (int) p->headers.entries[i].key.len, 
                        (char *) p->headers.entries[i].key.bytes );

                sprintf( value, "%.*s",  
                           (int) p->headers.entries[i].value.value.bytes.len, 
                        (char *) p->headers.entries[i].value.value.bytes.bytes );

                assign_field( tag, value );

              /*
                fprintf( stdout, "\t\"%.*s\": \"%.*s\",\n",
                     (int) p->headers.entries[i].key.len, 
                     (char *) p->headers.entries[i].key.bytes,
                     (int) p->headers.entries[i].value.value.bytes.len,
                     (char *) p->headers.entries[i].value.value.bytes.bytes
                 );
               */
            } else
                fprintf( stderr, "header not UTF8\n");
    }

    body_target = frame.payload.properties.body_size;
    body_received = 0;
  
    while (body_received < body_target) 
    {
            result = amqp_simple_wait_frame(sr_c->conn, &frame);

            if (result < 0) return(NULL);
    
            if (frame.frame_type != AMQP_FRAME_BODY) 
            {
                fprintf(stderr, "Expected body!");
                abort();
            }
    
        body_received += frame.payload.body_fragment.len;
        //assert(body_received <= body_target);
    
        strncpy( buf, (char*) frame.payload.body_fragment.bytes, (int)frame.payload.body_fragment.len );
        tok = strtok(buf," ");
        //fprintf( stdout, "\t\"datestamp\" : \"%s\",\n", tok);
        strcpy( msg.datestamp, tok );
        tok = strtok(NULL," ");
        //fprintf( stdout, "\t\"url\" : \"%s\", \n", tok);
        strcpy( msg.url, tok );
        tok = strtok(NULL," ");
        //fprintf( stdout, "\t\"path\" : \"%s\", \n", tok);
        strcpy( msg.path, tok );
        if (is_report) 
        {
                tok = strtok(NULL," ");
                //fprintf( stdout, "\t\"statuscode\" : \"%s\", \n", tok);
                msg.statuscode = atoi( tok );
                tok = strtok(NULL," ");
                //fprintf( stdout, "\t\"consumingurl\" : \"%s\", \n", tok);
                strcpy( msg.consumingurl, tok );
                tok = strtok(NULL," ");
                //fprintf( stdout, "\t\"consuminguser\" : \"%s\", \n", tok);
                strcpy( msg.consuminguser, tok );
                tok = strtok(NULL," ");
                //fprintf( stdout, "\t\"duration\" : \"%s\", \n", tok);
                msg.duration = atof( tok );
        } else {
            msg.statuscode=0;
            msg.consumingurl[0]='\0';
            msg.consuminguser[0]='\0';
            msg.duration=0.0;
       
        }
        //fprintf( stdout, " }\n");
    /*
    fprintf( stdout, "\t\"body\" : \"%.*s\"\n }\n",
                 (int) frame.payload.body_fragment.len, 
                 (char *)frame.payload.body_fragment.bytes 
            );
     */
    }
  
    if (body_received != body_target) return(NULL);
          /* Can only happen when amqp_simple_wait_frame returns <= 0 */
          /* We break here to close the connection */
    return(&msg);
}

